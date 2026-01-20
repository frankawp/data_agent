"""
DeepAgent 数据分析实现

基于 DeepAgents 框架构建的数据分析 Agent。
支持会话隔离，每个会话拥有独立的沙箱和导出目录。
使用多 Agent 模式（subagents）进行任务分工。
"""

from typing import Optional, Callable

from langchain_core.messages import AIMessage, ToolMessage
from rich.console import Console

from ..config.settings import get_settings
from ..config.modes import get_mode_manager
from ..session import SessionManager, get_session_by_id, set_current_session
from .plan_executor import PlanExecutor, StepStatus
from .llm import create_llm
from .compactor import ConversationCompactor
from .multi_agent import create_multi_agent
from .middleware import SubAgentCallbackHolder


class DataAgent:
    """
    数据分析 Agent 封装类

    提供更简洁的接口来使用 DeepAgent。
    支持运行时模式切换（Plan Mode、Auto Execute 等）。
    支持会话隔离，每个会话拥有独立的沙箱和导出目录。
    使用多 Agent 模式（subagents）进行任务分工。
    """

    def __init__(
        self,
        model: Optional[str] = None,
        console: Optional[Console] = None,
        session_id: Optional[str] = None,
    ):
        """
        初始化数据分析 Agent

        Args:
            model: 模型名称，默认使用配置中的模型
            console: Rich Console 实例，用于 Plan Mode 交互
            session_id: 会话 ID，不提供则自动生成
        """
        # 获取或创建会话管理器（会话隔离的关键）
        # 优先复用现有会话，保留已配置的数据库连接等状态
        existing_session = get_session_by_id(session_id) if session_id else None
        if existing_session:
            self._session = existing_session
        else:
            self._session = SessionManager(session_id=session_id)

        # 设置为当前会话，确保工具能访问会话配置
        set_current_session(self._session)

        # 创建回调持有者，支持动态更新回调
        self._subagent_callback_holder = SubAgentCallbackHolder()

        # 创建多 Agent
        self.agent = create_multi_agent(
            model=model,
            callback_holder=self._subagent_callback_holder,
        )

        self._messages = []
        self._mode_manager = get_mode_manager()
        self._console = console or Console()
        self._plan_executor = PlanExecutor(self._console)
        self._pending_tool_confirmation = None  # 待确认的工具调用
        self._compactor = ConversationCompactor(create_llm())  # 对话压缩器

    def _prepare_messages(self, messages: list) -> list:
        """
        准备发送给 Agent 的消息

        当 token 使用率超过阈值时，执行 compact 操作。

        Args:
            messages: 原始消息列表

        Returns:
            处理后的消息列表（可能已压缩）
        """
        settings = get_settings()
        max_tokens = settings.max_context_tokens
        threshold = settings.compact_threshold
        keep_ratio = settings.compact_keep_ratio

        if not self._compactor.should_compact(messages, max_tokens, threshold):
            return messages

        # 计算压缩前的 token 数
        before_tokens = self._compactor.count_tokens(messages)

        # 执行 compact
        compacted = self._compactor.compact(messages, max_tokens, keep_ratio)

        # 计算压缩后的 token 数
        after_tokens = self._compactor.count_tokens(compacted)

        # 打印提示
        if self._console:
            usage_before = before_tokens / max_tokens * 100
            usage_after = after_tokens / max_tokens * 100
            self._console.print(
                f"[dim]对话历史已压缩: {before_tokens:,} → {after_tokens:,} tokens "
                f"({usage_before:.1f}% → {usage_after:.1f}%)[/dim]"
            )

        return compacted

    def chat(self, user_input: str) -> str:
        """
        与 Agent 对话

        Args:
            user_input: 用户输入

        Returns:
            str: Agent 响应
        """
        # 构建消息
        self._messages.append({"role": "user", "content": user_input})

        # 准备消息（可能触发 compact）
        messages_to_send = self._prepare_messages(self._messages)

        # 调用 Agent
        result = self.agent.invoke({"messages": messages_to_send})

        # 获取响应
        messages = result.get("messages", [])
        if messages:
            response = messages[-1].content
            self._messages = messages  # 更新消息历史
        else:
            response = "抱歉，无法处理您的请求。"

        return response

    def set_console(self, console: Console) -> None:
        """设置 Console 实例"""
        self._console = console
        self._plan_executor = PlanExecutor(console)

    def chat_stream(
        self,
        user_input: str,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[str, dict], None]] = None,
        on_tool_result: Optional[Callable[[str, str], None]] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
    ) -> str:
        """
        流式与 Agent 对话，显示思考过程

        支持 Plan Mode 和 Auto Execute 模式。

        Args:
            user_input: 用户输入
            on_thinking: 思考内容回调函数 (content)
            on_tool_call: 工具调用回调函数 (tool_name, tool_args)
            on_tool_result: 工具结果回调函数 (tool_name, result)
            should_cancel: 取消检查回调函数，返回 True 时中断执行

        Returns:
            str: Agent 最终响应
        """
        # 检查是否需要 Plan Mode
        if self._plan_executor.should_plan(user_input):
            return self._execute_with_plan(user_input, on_thinking, on_tool_call, on_tool_result, should_cancel)

        # 正常执行流程
        return self._execute_stream(user_input, on_thinking, on_tool_call, on_tool_result, should_cancel)

    def _execute_with_plan(
        self,
        user_input: str,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[str, dict], None]] = None,
        on_tool_result: Optional[Callable[[str, str], None]] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
    ) -> str:
        """使用 Plan Mode 执行任务"""
        executor = self._plan_executor

        # 1. 生成规划提示
        plan_prompt = executor.generate_plan_prompt(user_input)

        # 2. 调用 LLM 生成计划
        self._console.print("[dim]正在生成执行计划...[/dim]")
        plan_response = self._get_single_response(plan_prompt)

        # 3. 解析计划
        plan = executor.parse_plan_response(plan_response, user_input)
        if not plan:
            # 解析失败，回退到普通模式
            self._console.print("[yellow]无法生成计划，将直接执行任务[/yellow]")
            return self._execute_stream(user_input, on_thinking, on_tool_call, on_tool_result, should_cancel)

        # 4. 用户确认
        if not executor.confirm_plan(plan):
            return "已取消执行。"

        # 5. 分步执行（每个步骤使用独立的消息上下文）
        self._console.print()
        for step in plan.steps:
            # 检查是否被中断
            if should_cancel and should_cancel():
                raise InterruptedError("用户中断")

            executor.update_step_status(plan, step.index, StepStatus.RUNNING)
            executor.display_progress(plan)

            # 创建步骤执行提示
            step_prompt = executor.create_execution_prompt(plan, step)

            # 执行步骤（使用独立上下文）
            try:
                step_result = self._execute_step_isolated(
                    step_prompt,
                    on_thinking,
                    on_tool_call,
                    on_tool_result,
                    should_cancel
                )
                executor.update_step_status(plan, step.index, StepStatus.COMPLETED, step_result)
            except InterruptedError:
                executor.update_step_status(plan, step.index, StepStatus.FAILED, "用户中断")
                raise
            except Exception as e:
                executor.update_step_status(plan, step.index, StepStatus.FAILED, str(e))
                self._console.print(f"[red]步骤 {step.index} 执行失败: {e}[/red]")

        # 6. 显示最终进度
        executor.display_progress(plan)
        self._console.print()

        # 7. 汇总结果
        return executor.summarize_results(plan)

    def _execute_step_isolated(
        self,
        step_prompt: str,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[str, dict], None]] = None,
        on_tool_result: Optional[Callable[[str, str], None]] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
    ) -> str:
        """
        使用独立消息上下文执行单个步骤

        Plan Mode 中每个步骤使用此方法，避免消息历史混乱。
        """
        # 检查是否被中断
        if should_cancel and should_cancel():
            raise InterruptedError("用户中断")
        verbose = self._mode_manager.get("verbose")

        # 使用独立的消息列表（不影响主对话历史）
        step_messages = [{"role": "user", "content": step_prompt}]

        final_response = ""
        tool_calls_pending = {}

        # 使用 invoke 而不是 stream，更稳定
        try:
            result = self.agent.invoke({"messages": step_messages})
            messages = result.get("messages", [])

            for msg in messages:
                if isinstance(msg, AIMessage):
                    if msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tool_name = tool_call.get("name", "unknown")
                            tool_args = tool_call.get("args", {})
                            tool_id = tool_call.get("id", "")
                            tool_calls_pending[tool_id] = tool_name

                            if on_tool_call:
                                on_tool_call(tool_name, tool_args)

                    if msg.content:
                        if verbose and on_thinking:
                            on_thinking(msg.content)
                        final_response = msg.content

                elif isinstance(msg, ToolMessage):
                    tool_id = getattr(msg, "tool_call_id", "")
                    tool_name = tool_calls_pending.get(tool_id, "unknown")
                    result_content = msg.content if isinstance(msg.content, str) else str(msg.content)

                    if on_tool_result:
                        on_tool_result(tool_name, result_content)

        except Exception as e:
            raise e

        return final_response

    def _get_single_response(self, prompt: str) -> str:
        """获取单次 LLM 响应（不使用工具）"""
        messages = [{"role": "user", "content": prompt}]
        result = self.agent.invoke({"messages": messages})
        response_messages = result.get("messages", [])
        if response_messages:
            return response_messages[-1].content
        return ""

    def _execute_stream(
        self,
        user_input: str,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_tool_call: Optional[Callable[[str, dict], None]] = None,
        on_tool_result: Optional[Callable[[str, str], None]] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
    ) -> str:
        """执行流式对话（核心实现）"""
        # 获取模式设置
        verbose = self._mode_manager.get("verbose")

        # 构建消息
        self._messages.append({"role": "user", "content": user_input})

        # 准备消息（可能触发 compact）
        messages_to_send = self._prepare_messages(self._messages)

        final_response = ""
        tool_calls_pending = {}  # 记录待处理的工具调用
        collected_messages = list(messages_to_send)  # 收集流式处理中的消息
        processed_msg_ids = set()  # 跟踪已处理的消息 ID，避免重复处理历史消息

        # 记录已存在的消息 ID（历史消息）
        for msg in messages_to_send:
            msg_id = getattr(msg, "id", None)
            if msg_id:
                processed_msg_ids.add(msg_id)

        # 流式调用 Agent
        for event in self.agent.stream({"messages": messages_to_send}):
            # 在每次迭代检查取消
            if should_cancel and should_cancel():
                raise InterruptedError("用户中断")
            for node_name, node_output in event.items():
                # 跳过中间件事件（None 值或非 dict）
                if node_output is None:
                    continue
                if not isinstance(node_output, dict):
                    continue

                # 获取消息列表
                messages = node_output.get("messages", [])

                # 处理 Overwrite 对象（LangGraph 状态更新机制）
                if hasattr(messages, "value"):
                    messages = messages.value

                if not isinstance(messages, list):
                    continue

                for msg in messages:
                    # 跳过已处理的消息（避免历史消息重复输出）
                    msg_id = getattr(msg, "id", None)
                    if msg_id and msg_id in processed_msg_ids:
                        continue
                    if msg_id:
                        processed_msg_ids.add(msg_id)

                    # 收集消息用于更新历史
                    collected_messages.append(msg)

                    if isinstance(msg, AIMessage):
                        # AI 消息 - 可能包含思考或工具调用
                        if msg.tool_calls:
                            # 有工具调用
                            for tool_call in msg.tool_calls:
                                tool_name = tool_call.get("name", "unknown")
                                tool_args = tool_call.get("args", {})
                                tool_id = tool_call.get("id", "")
                                tool_calls_pending[tool_id] = tool_name

                                if on_tool_call:
                                    on_tool_call(tool_name, tool_args)

                        # 记录文本内容（可能是思考或最终回复）
                        if msg.content:
                            # verbose 模式下显示思考过程
                            if verbose and on_thinking:
                                on_thinking(msg.content)
                            final_response = msg.content

                    elif isinstance(msg, ToolMessage):
                        # 工具返回结果
                        tool_id = getattr(msg, "tool_call_id", "")
                        tool_name = tool_calls_pending.get(tool_id, "unknown")
                        result_content = msg.content if isinstance(msg.content, str) else str(msg.content)

                        if on_tool_result:
                            on_tool_result(tool_name, result_content)

        # 更新消息历史
        self._messages = collected_messages

        return final_response

    def clear_history(self):
        """清除对话历史"""
        self._messages = []

    def invoke(self, input_dict: dict) -> dict:
        """
        直接调用底层 Agent

        Args:
            input_dict: 输入字典，包含 messages 键

        Returns:
            dict: Agent 输出
        """
        return self.agent.invoke(input_dict)

    async def ainvoke(self, input_dict: dict) -> dict:
        """
        异步调用底层 Agent

        Args:
            input_dict: 输入字典

        Returns:
            dict: Agent 输出
        """
        return await self.agent.ainvoke(input_dict)

    @property
    def session(self) -> SessionManager:
        """获取当前会话管理器"""
        return self._session

    @property
    def session_id(self) -> str:
        """获取当前会话 ID"""
        return self._session.session_id

    @property
    def export_dir(self):
        """获取当前会话的导出目录"""
        return self._session.export_dir

    def list_exports(self) -> list:
        """列出当前会话的所有导出文件"""
        return self._session.list_exports()

    def set_subagent_callbacks(
        self,
        on_tool_call: Optional[Callable[[dict], None]] = None,
        on_tool_result: Optional[Callable[[dict], None]] = None,
    ) -> None:
        """
        设置子代理回调函数

        用于 SSE 流式请求，在请求开始前设置回调，结束后清空。

        Args:
            on_tool_call: 子代理工具调用开始时的回调
            on_tool_result: 子代理工具执行完成时的回调
        """
        if self._subagent_callback_holder:
            self._subagent_callback_holder.set_callbacks(on_tool_call, on_tool_result)

    def clear_subagent_callbacks(self) -> None:
        """清空子代理回调函数"""
        if self._subagent_callback_holder:
            self._subagent_callback_holder.clear_callbacks()
