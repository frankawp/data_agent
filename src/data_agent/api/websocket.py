"""
WebSocket 聊天端点

实现双向通信和 Human-in-the-Loop 功能：
- 用户可以在 AI 工作期间发送反馈
- 安全模式下 SQL 执行需要用户确认
- 支持取消执行
"""

import asyncio
import json
import logging
import queue
import threading
from typing import Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from langchain_core.messages import AIMessage, ToolMessage

from ..agent.deep_agent import DataAgent
from ..config.modes import get_mode_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# DataAgent 实例（每个会话一个）
_agents: Dict[str, DataAgent] = {}

# 用户反馈队列（每个会话一个）
_feedback_queues: Dict[str, asyncio.Queue] = {}

# 待确认的工具调用（每个会话一个）
_pending_confirmations: Dict[str, Dict[str, Any]] = {}

# 线程池用于执行同步的 DataAgent 方法
_executor = ThreadPoolExecutor(max_workers=4)


# ============ 消息类型定义 ============

class ClientMessage(BaseModel):
    """客户端发送的消息"""
    type: str  # "user_message" | "feedback" | "decision" | "cancel"
    content: Optional[str] = None
    decision: Optional[str] = None  # "approve" | "edit" | "reject"
    tool_call_id: Optional[str] = None
    edited_args: Optional[Dict[str, Any]] = None


class ServerMessage(BaseModel):
    """服务端发送的消息"""
    type: str
    # 根据 type 不同，包含不同字段


# ============ 辅助函数 ============

def get_or_create_agent(session_id: str) -> DataAgent:
    """获取或创建 DataAgent 实例"""
    if session_id not in _agents:
        # 创建 agent 前，设置 API 友好的模式
        mode_manager = get_mode_manager()
        # 关闭 plan_mode 避免用户确认提示
        mode_manager.set("plan", "off")
        # 开启自动执行
        mode_manager.set("auto", "on")

        # 传递 session_id 确保导出文件保存到正确的会话目录
        _agents[session_id] = DataAgent(session_id=session_id)
    return _agents[session_id]


async def send_json(websocket: WebSocket, data: Dict[str, Any]):
    """发送 JSON 消息"""
    await websocket.send_text(json.dumps(data, ensure_ascii=False))


def is_sql_tool(tool_name: str) -> bool:
    """判断是否为 SQL 工具"""
    sql_tools = {"execute_sql", "query_database", "run_sql"}
    return tool_name.lower() in sql_tools or "sql" in tool_name.lower()


def needs_confirmation(tool_name: str, tool_args: Dict[str, Any]) -> bool:
    """
    判断工具调用是否需要用户确认

    仅在安全模式开启时，SQL 操作需要确认。
    Python 执行不需要确认（沙盒保护）。
    """
    mode_manager = get_mode_manager()

    # 安全模式关闭时，不需要确认
    if not mode_manager.config.safe_mode:
        return False

    # 只有 SQL 工具需要确认
    return is_sql_tool(tool_name)


def format_confirmation_description(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """格式化确认请求的描述"""
    if is_sql_tool(tool_name):
        query = tool_args.get("query", tool_args.get("sql", ""))
        return f"[安全模式] 即将执行 SQL:\n```sql\n{query}\n```"
    return f"即将执行 {tool_name}"


# ============ WebSocket 端点 ============

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, session_id: str = "default"):
    """
    WebSocket 聊天端点

    消息协议:

    客户端 → 服务端:
    - { type: "user_message", content: "..." }  新消息
    - { type: "feedback", content: "..." }      AI 工作期间的反馈
    - { type: "decision", decision: "approve"|"edit"|"reject", tool_call_id: "...", edited_args?: {...} }
    - { type: "cancel" }                         取消执行

    服务端 → 客户端:
    - { type: "tool_call", tool_name: "...", args: {...}, tool_call_id: "...", step: N }
    - { type: "tool_result", tool_name: "...", result: "...", tool_call_id: "...", step: N }
    - { type: "confirmation_request", tool_name: "...", args: {...}, tool_call_id: "...", description: "..." }
    - { type: "thinking", content: "..." }
    - { type: "message", content: "..." }
    - { type: "feedback_ack", message: "..." }
    - { type: "error", error: "..." }
    - { type: "done" }
    """
    await websocket.accept()
    logger.info(f"WebSocket 连接已建立: session_id={session_id}")

    # 初始化会话的反馈队列
    if session_id not in _feedback_queues:
        _feedback_queues[session_id] = asyncio.Queue()

    # 当前是否正在处理消息
    is_processing = False
    # 取消标志
    cancel_flag = threading.Event()

    try:
        while True:
            # 接收客户端消息
            raw_message = await websocket.receive_text()

            try:
                client_msg = json.loads(raw_message)
                msg_type = client_msg.get("type", "")

                if msg_type == "user_message":
                    # 新消息 - 开始处理
                    if is_processing:
                        await send_json(websocket, {
                            "type": "error",
                            "error": "正在处理上一条消息，请稍候"
                        })
                        continue

                    is_processing = True
                    cancel_flag.clear()
                    user_content = client_msg.get("content", "")

                    # 在后台任务中处理消息
                    asyncio.create_task(
                        process_user_message(
                            websocket, session_id, user_content,
                            cancel_flag, lambda: setattr_wrapper(locals(), 'is_processing', False)
                        )
                    )
                    # 注意：is_processing 会在 process_user_message 完成后被设置为 False

                elif msg_type == "feedback":
                    # 用户反馈 - 添加到反馈队列
                    feedback_content = client_msg.get("content", "")
                    if feedback_content:
                        await _feedback_queues[session_id].put(feedback_content)
                        await send_json(websocket, {
                            "type": "feedback_ack",
                            "message": f"已收到您的反馈: {feedback_content[:50]}..."
                        })
                        logger.info(f"收到用户反馈: {feedback_content[:100]}")

                elif msg_type == "decision":
                    # 用户决定 - 处理确认请求
                    decision = client_msg.get("decision", "")
                    tool_call_id = client_msg.get("tool_call_id", "")
                    edited_args = client_msg.get("edited_args")

                    if session_id in _pending_confirmations and tool_call_id in _pending_confirmations[session_id]:
                        pending = _pending_confirmations[session_id][tool_call_id]
                        pending["decision"] = decision
                        pending["edited_args"] = edited_args
                        pending["event"].set()  # 唤醒等待的线程
                        logger.info(f"用户决定: {decision} for {tool_call_id}")
                    else:
                        await send_json(websocket, {
                            "type": "error",
                            "error": f"未找到待确认的工具调用: {tool_call_id}"
                        })

                elif msg_type == "cancel":
                    # 取消执行
                    cancel_flag.set()
                    await send_json(websocket, {
                        "type": "message",
                        "content": "执行已取消"
                    })
                    await send_json(websocket, {"type": "done"})
                    is_processing = False
                    logger.info("用户取消执行")

                else:
                    await send_json(websocket, {
                        "type": "error",
                        "error": f"未知的消息类型: {msg_type}"
                    })

            except json.JSONDecodeError:
                await send_json(websocket, {
                    "type": "error",
                    "error": "无效的 JSON 格式"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket 连接已断开: session_id={session_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        try:
            await send_json(websocket, {
                "type": "error",
                "error": str(e)
            })
        except:
            pass
    finally:
        # 清理资源
        if session_id in _feedback_queues:
            del _feedback_queues[session_id]
        if session_id in _pending_confirmations:
            del _pending_confirmations[session_id]


def setattr_wrapper(d: dict, key: str, value: Any):
    """辅助函数，用于在 lambda 中设置变量"""
    d[key] = value


async def process_user_message(
    websocket: WebSocket,
    session_id: str,
    user_message: str,
    cancel_flag: threading.Event,
    on_complete: callable
):
    """
    处理用户消息

    在后台运行 DataAgent，同时监听用户反馈和确认请求。
    """
    try:
        agent = get_or_create_agent(session_id)

        # 事件队列用于线程间通信
        event_queue: queue.Queue = queue.Queue()
        step_counter = [0]
        subagent_step_counter = [0]

        # 初始化确认存储
        if session_id not in _pending_confirmations:
            _pending_confirmations[session_id] = {}

        def on_thinking(content: str):
            """思考内容回调"""
            if cancel_flag.is_set():
                return
            event_queue.put({
                "type": "thinking",
                "content": content
            })

        def on_tool_call(tool_name: str, tool_args: dict):
            """工具调用回调"""
            if cancel_flag.is_set():
                return

            step_counter[0] += 1
            tool_call_id = f"tc_{session_id}_{step_counter[0]}"

            # 检查是否需要确认
            if needs_confirmation(tool_name, tool_args):
                # 需要确认 - 发送确认请求并等待
                confirmation_event = threading.Event()
                _pending_confirmations[session_id][tool_call_id] = {
                    "tool_name": tool_name,
                    "args": tool_args,
                    "event": confirmation_event,
                    "decision": None,
                    "edited_args": None
                }

                event_queue.put({
                    "type": "confirmation_request",
                    "tool_name": tool_name,
                    "args": tool_args,
                    "tool_call_id": tool_call_id,
                    "description": format_confirmation_description(tool_name, tool_args)
                })

                # 等待用户决定（最多等待 5 分钟）
                if confirmation_event.wait(timeout=300):
                    pending = _pending_confirmations[session_id].get(tool_call_id, {})
                    decision = pending.get("decision", "reject")

                    if decision == "reject":
                        # 用户拒绝 - 抛出异常中断执行
                        raise InterruptedError(f"用户拒绝执行 {tool_name}")
                    elif decision == "edit" and pending.get("edited_args"):
                        # 用户编辑了参数 - 更新 tool_args
                        tool_args.update(pending["edited_args"])
                else:
                    # 超时 - 默认拒绝
                    raise InterruptedError(f"确认超时，取消执行 {tool_name}")

                # 清理
                if tool_call_id in _pending_confirmations.get(session_id, {}):
                    del _pending_confirmations[session_id][tool_call_id]

            # 发送工具调用事件
            event_queue.put({
                "type": "tool_call",
                "tool_name": tool_name,
                "args": tool_args,
                "tool_call_id": tool_call_id,
                "step": step_counter[0]
            })

        def on_tool_result(tool_name: str, result: str):
            """工具结果回调"""
            if cancel_flag.is_set():
                return
            event_queue.put({
                "type": "tool_result",
                "tool_name": tool_name,
                "result": result,
                "step": step_counter[0]
            })

        def on_subagent_tool_call(data: dict):
            """子代理工具调用回调"""
            if cancel_flag.is_set():
                return
            subagent_step_counter[0] += 1
            event_queue.put({
                "type": "subagent_tool_call",
                "subagent_name": data.get("subagent_name", "unknown"),
                "tool_name": data.get("tool_name", "unknown"),
                "args": data.get("tool_args", {}),
                "step": subagent_step_counter[0],
            })

        def on_subagent_tool_result(data: dict):
            """子代理工具结果回调"""
            if cancel_flag.is_set():
                return
            event_queue.put({
                "type": "subagent_tool_result",
                "subagent_name": data.get("subagent_name", "unknown"),
                "tool_name": data.get("tool_name", "unknown"),
                "result": data.get("result", ""),
                "step": subagent_step_counter[0],
            })

        def run_chat():
            """在线程中运行聊天"""
            try:
                if cancel_flag.is_set():
                    return

                # 设置子代理回调
                agent.set_subagent_callbacks(
                    on_tool_call=on_subagent_tool_call,
                    on_tool_result=on_subagent_tool_result,
                )

                # 检查反馈队列并添加到消息中
                feedback_messages = []
                try:
                    while True:
                        feedback = _feedback_queues[session_id].get_nowait()
                        feedback_messages.append(feedback)
                except (asyncio.QueueEmpty, KeyError):
                    pass

                # 如果有反馈，添加到用户消息中
                final_message = user_message
                if feedback_messages:
                    feedback_text = "\n".join(f"[用户反馈]: {f}" for f in feedback_messages)
                    final_message = f"{user_message}\n\n{feedback_text}"

                response = agent.chat_stream(
                    final_message,
                    on_thinking=on_thinking,
                    on_tool_call=on_tool_call,
                    on_tool_result=on_tool_result
                )

                event_queue.put({
                    "type": "message",
                    "content": response
                })

            except InterruptedError as e:
                event_queue.put({
                    "type": "message",
                    "content": str(e)
                })
            except Exception as e:
                logger.error(f"聊天处理错误: {e}")
                event_queue.put({
                    "type": "error",
                    "error": str(e)
                })
            finally:
                agent.clear_subagent_callbacks()
                event_queue.put({"type": "done"})

        # 启动聊天线程
        chat_thread = threading.Thread(target=run_chat, daemon=True)
        chat_thread.start()

        # 从事件队列读取并发送到 WebSocket
        while True:
            try:
                # 非阻塞检查事件队列
                event = event_queue.get(timeout=0.1)
                await send_json(websocket, event)

                if event.get("type") == "done":
                    break

            except queue.Empty:
                # 检查是否取消
                if cancel_flag.is_set():
                    break
                continue
            except Exception as e:
                logger.error(f"发送事件错误: {e}")
                break

        # 等待线程结束
        chat_thread.join(timeout=1.0)

    except Exception as e:
        logger.error(f"处理消息错误: {e}")
        await send_json(websocket, {
            "type": "error",
            "error": str(e)
        })
        await send_json(websocket, {"type": "done"})
    finally:
        on_complete()


# ============ HTTP 端点（兼容） ============

@router.get("/ws/status")
async def websocket_status():
    """WebSocket 服务状态"""
    return {
        "status": "ok",
        "active_sessions": list(_agents.keys()),
        "pending_confirmations": {
            sid: list(pending.keys())
            for sid, pending in _pending_confirmations.items()
        }
    }
