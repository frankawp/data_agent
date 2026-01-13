"""
子代理工具监听中间件

监听子代理的工具调用，通过回调函数通知外部（如 SSE 流），
但不影响主代理的上下文。
"""

from typing import Any, Callable, Optional

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command


class SubAgentCallbackHolder:
    """
    子代理回调的可变容器

    由于 DataAgent 实例会被缓存复用，而每个 SSE 请求需要独立的回调函数
    来将事件推送到各自的 event_queue，因此使用此容器来支持动态更新回调。

    使用方式：
    1. DataAgent 创建时，创建一个 CallbackHolder 实例
    2. 将 CallbackHolder 传给 middleware
    3. 每次 SSE 请求前，更新 CallbackHolder 中的回调函数
    4. 请求结束后，清空回调函数

    Attributes:
        on_tool_call: 工具调用开始时的回调函数
        on_tool_result: 工具执行完成时的回调函数
    """

    def __init__(self):
        self.on_tool_call: Optional[Callable[[dict], None]] = None
        self.on_tool_result: Optional[Callable[[dict], None]] = None

    def set_callbacks(
        self,
        on_tool_call: Optional[Callable[[dict], None]] = None,
        on_tool_result: Optional[Callable[[dict], None]] = None,
    ) -> None:
        """设置回调函数"""
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result

    def clear_callbacks(self) -> None:
        """清空回调函数"""
        self.on_tool_call = None
        self.on_tool_result = None


class SubAgentToolMonitor(AgentMiddleware):
    """
    监听子代理工具调用的中间件

    当子代理执行工具时，触发回调函数通知外部系统（如 SSE 流），
    使前端能够实时展示子代理的执行进度。

    关键特性：
    - 不影响工具执行结果
    - 不污染主代理的上下文
    - 支持同步执行模式
    - 支持动态更新回调（通过 CallbackHolder）
    """

    # 需要定义 tools 属性，即使为空
    tools = []

    def __init__(
        self,
        subagent_name: str,
        callback_holder: Optional[SubAgentCallbackHolder] = None,
    ):
        """
        初始化子代理工具监听中间件

        Args:
            subagent_name: 子代理名称，用于标识事件来源
            callback_holder: 回调持有者，支持动态更新回调函数
        """
        self.subagent_name = subagent_name
        self._callback_holder = callback_holder
        self._step_counter = 0

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """
        拦截子代理的工具调用

        在工具执行前后触发回调，但不修改执行逻辑。

        Args:
            request: 工具调用请求，包含 tool_call、tool、state、runtime
            handler: 工具执行处理器

        Returns:
            工具执行结果（ToolMessage 或 Command）
        """
        # 提取工具信息
        tool_call = request.tool_call
        tool_name = tool_call.get("name", "unknown") if isinstance(tool_call, dict) else getattr(tool_call, "name", "unknown")
        tool_args = tool_call.get("args", {}) if isinstance(tool_call, dict) else getattr(tool_call, "args", {})

        # 增加步骤计数
        self._step_counter += 1

        # 通知工具调用开始（通过 callback_holder 获取当前回调）
        on_tool_call = self._callback_holder.on_tool_call if self._callback_holder else None
        if on_tool_call:
            try:
                on_tool_call({
                    "subagent_name": self.subagent_name,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "step": self._step_counter,
                })
            except Exception:
                # 回调失败不应影响工具执行
                pass

        # 执行工具
        result = handler(request)

        # 通知工具执行完成（通过 callback_holder 获取当前回调）
        on_tool_result = self._callback_holder.on_tool_result if self._callback_holder else None
        if on_tool_result:
            try:
                # 提取结果内容
                if isinstance(result, ToolMessage):
                    result_content = result.content if isinstance(result.content, str) else str(result.content)
                elif isinstance(result, Command):
                    result_content = "[Command returned]"
                else:
                    result_content = str(result)

                # 限制结果长度，避免过长
                max_length = 1000
                if len(result_content) > max_length:
                    result_content = result_content[:max_length] + "... (truncated)"

                on_tool_result({
                    "subagent_name": self.subagent_name,
                    "tool_name": tool_name,
                    "result": result_content,
                    "step": self._step_counter,
                })
            except Exception:
                # 回调失败不应影响工具执行
                pass

        return result

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Any],
    ) -> ToolMessage | Command:
        """
        异步版本的工具调用拦截

        Args:
            request: 工具调用请求
            handler: 异步工具执行处理器

        Returns:
            工具执行结果
        """
        # 提取工具信息
        tool_call = request.tool_call
        tool_name = tool_call.get("name", "unknown") if isinstance(tool_call, dict) else getattr(tool_call, "name", "unknown")
        tool_args = tool_call.get("args", {}) if isinstance(tool_call, dict) else getattr(tool_call, "args", {})

        # 增加步骤计数
        self._step_counter += 1

        # 通知工具调用开始（通过 callback_holder 获取当前回调）
        on_tool_call = self._callback_holder.on_tool_call if self._callback_holder else None
        if on_tool_call:
            try:
                on_tool_call({
                    "subagent_name": self.subagent_name,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "step": self._step_counter,
                })
            except Exception:
                pass

        # 执行工具（异步）
        result = await handler(request)

        # 通知工具执行完成（通过 callback_holder 获取当前回调）
        on_tool_result = self._callback_holder.on_tool_result if self._callback_holder else None
        if on_tool_result:
            try:
                if isinstance(result, ToolMessage):
                    result_content = result.content if isinstance(result.content, str) else str(result.content)
                elif isinstance(result, Command):
                    result_content = "[Command returned]"
                else:
                    result_content = str(result)

                max_length = 1000
                if len(result_content) > max_length:
                    result_content = result_content[:max_length] + "... (truncated)"

                on_tool_result({
                    "subagent_name": self.subagent_name,
                    "tool_name": tool_name,
                    "result": result_content,
                    "step": self._step_counter,
                })
            except Exception:
                pass

        return result
