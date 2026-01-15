"""
聊天 API 模块

直接使用现有 DataAgent 处理对话，不依赖 copilotkit Python SDK。
支持流式输出，实时显示工具执行过程。
"""

import asyncio
import json
import queue
import threading
from typing import Optional, List, Dict, Any, Generator
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langchain_core.messages import AIMessage, ToolMessage

from ..agent.deep_agent import DataAgent
from ..config.modes import get_mode_manager

router = APIRouter()

# DataAgent 实例（每个会话一个）
_agents: Dict[str, DataAgent] = {}

# 线程池用于执行同步的 DataAgent 方法
_executor = ThreadPoolExecutor(max_workers=4)


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ToolCallInfo(BaseModel):
    """工具调用信息"""
    tool_name: str
    args: Dict[str, Any]
    result: str


class ChatRequest(BaseModel):
    messages: Optional[List[Message]] = None  # 完整消息列表
    message: Optional[str] = None  # 简单消息（兼容简化格式）
    session_id: Optional[str] = "default"
    stream: Optional[bool] = False  # 默认非流式，因为流式需要额外处理


class ChatResponse(BaseModel):
    message: Message
    tool_calls: Optional[List[ToolCallInfo]] = None


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


def _sync_chat_with_tools(agent: DataAgent, user_message: str) -> tuple:
    """
    同步执行聊天并提取工具调用信息（在线程池中运行）

    Returns:
        tuple: (response_text, tool_calls_list)
    """
    # 构建消息
    agent._messages.append({"role": "user", "content": user_message})

    # 调用 Agent
    result = agent.agent.invoke({"messages": agent._messages})

    # 解析响应
    messages = result.get("messages", [])
    response_text = ""
    tool_calls_list = []

    # 用于匹配工具调用和结果
    tool_call_map = {}  # tool_id -> {tool_name, args}

    for msg in messages:
        if isinstance(msg, AIMessage):
            # 提取最终文本响应
            if msg.content:
                response_text = msg.content
            # 提取工具调用信息
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_id = tc.get("id", "")
                    tool_name = tc.get("name", "unknown")
                    tool_args = tc.get("args", {})
                    tool_call_map[tool_id] = {
                        "tool_name": tool_name,
                        "args": tool_args,
                        "result": ""
                    }
        elif isinstance(msg, ToolMessage):
            # 匹配工具结果
            tool_id = getattr(msg, "tool_call_id", "")
            if tool_id in tool_call_map:
                tool_call_map[tool_id]["result"] = msg.content if isinstance(msg.content, str) else str(msg.content)

    # 转换为列表
    for tool_info in tool_call_map.values():
        tool_calls_list.append(tool_info)

    # 更新消息历史
    if messages:
        agent._messages = messages

    if not response_text:
        response_text = "抱歉，无法处理您的请求。"

    return response_text, tool_calls_list


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    处理聊天请求

    复用现有 DataAgent 的对话能力。
    API 模式下默认关闭 plan_mode，避免需要用户确认。
    返回工具调用信息供前端展示。
    """
    try:
        agent = get_or_create_agent(request.session_id)

        # 获取用户消息（支持两种格式）
        user_message = None

        # 优先使用简单消息格式
        if request.message:
            user_message = request.message
        # 其次从 messages 列表获取最后一条用户消息
        elif request.messages:
            for msg in reversed(request.messages):
                if msg.role == "user":
                    user_message = msg.content
                    break

        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        # 在线程池中执行同步的 chat 方法
        loop = asyncio.get_event_loop()
        response_text, tool_calls_list = await loop.run_in_executor(
            _executor,
            _sync_chat_with_tools,
            agent,
            user_message
        )

        # 转换为 ToolCallInfo 对象列表
        tool_calls = [
            ToolCallInfo(
                tool_name=tc["tool_name"],
                args=tc["args"],
                result=tc["result"]
            )
            for tc in tool_calls_list
        ] if tool_calls_list else None

        return ChatResponse(
            message=Message(role="assistant", content=response_text),
            tool_calls=tool_calls,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天请求

    使用 Server-Sent Events (SSE) 实时发送：
    - tool_call: 工具调用开始
    - tool_result: 工具执行结果
    - thinking: AI 思考内容
    - message: 最终消息
    - done: 完成标记
    """
    try:
        agent = get_or_create_agent(request.session_id)

        # 获取用户消息（支持两种格式）
        user_message = None

        # 优先使用简单消息格式
        if request.message:
            user_message = request.message
        # 其次从 messages 列表获取最后一条用户消息
        elif request.messages:
            for msg in reversed(request.messages):
                if msg.role == "user":
                    user_message = msg.content
                    break

        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        # 使用队列在线程间传递事件
        event_queue: queue.Queue = queue.Queue()
        step_counter = [0]  # 使用列表以便在闭包中修改

        def on_thinking(content: str):
            """思考内容回调"""
            event_queue.put({
                "event": "thinking",
                "data": {"content": content}
            })

        def on_tool_call(tool_name: str, tool_args: dict):
            """工具调用回调"""
            step_counter[0] += 1
            event_queue.put({
                "event": "tool_call",
                "data": {
                    "step": step_counter[0],
                    "tool_name": tool_name,
                    "args": tool_args
                }
            })

        def on_tool_result(tool_name: str, result: str):
            """工具结果回调"""
            event_queue.put({
                "event": "tool_result",
                "data": {
                    "step": step_counter[0],
                    "tool_name": tool_name,
                    "result": result
                }
            })

        # 子代理工具调用回调（仅多 Agent 模式有效）
        subagent_step_counter = [0]  # 子代理步骤计数器

        def on_subagent_tool_call(data: dict):
            """子代理工具调用回调"""
            subagent_step_counter[0] += 1
            event_queue.put({
                "event": "subagent_tool_call",
                "data": {
                    "subagent_name": data.get("subagent_name", "unknown"),
                    "tool_name": data.get("tool_name", "unknown"),
                    "args": data.get("tool_args", {}),
                    "step": subagent_step_counter[0],
                }
            })

        def on_subagent_tool_result(data: dict):
            """子代理工具结果回调"""
            event_queue.put({
                "event": "subagent_tool_result",
                "data": {
                    "subagent_name": data.get("subagent_name", "unknown"),
                    "tool_name": data.get("tool_name", "unknown"),
                    "result": data.get("result", ""),
                    "step": subagent_step_counter[0],
                }
            })

        def run_chat():
            """在线程中运行聊天"""
            try:
                # 设置子代理回调（仅多 Agent 模式有效）
                agent.set_subagent_callbacks(
                    on_tool_call=on_subagent_tool_call,
                    on_tool_result=on_subagent_tool_result,
                )

                response = agent.chat_stream(
                    user_message,
                    on_thinking=on_thinking,
                    on_tool_call=on_tool_call,
                    on_tool_result=on_tool_result
                )
                event_queue.put({
                    "event": "message",
                    "data": {"content": response}
                })
            except Exception as e:
                event_queue.put({
                    "event": "error",
                    "data": {"error": str(e)}
                })
            finally:
                # 清空子代理回调
                agent.clear_subagent_callbacks()
                event_queue.put({"event": "done", "data": {}})

        # 启动聊天线程
        chat_thread = threading.Thread(target=run_chat)
        chat_thread.start()

        def generate_events() -> Generator[str, None, None]:
            """生成 SSE 事件流"""
            while True:
                try:
                    event = event_queue.get(timeout=0.1)
                    event_type = event.get("event", "unknown")
                    event_data = json.dumps(event.get("data", {}), ensure_ascii=False)
                    yield f"event: {event_type}\ndata: {event_data}\n\n"

                    if event_type == "done":
                        break
                except queue.Empty:
                    # 发送心跳保持连接
                    yield ": heartbeat\n\n"
                    continue

        return StreamingResponse(
            generate_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/reset")
async def reset_chat(session_id: str = "default"):
    """重置聊天会话"""
    if session_id in _agents:
        del _agents[session_id]
    return {"status": "ok", "message": f"Session {session_id} reset"}


@router.get("/chat/sessions")
async def list_sessions():
    """列出所有活跃会话"""
    return {"sessions": list(_agents.keys())}
