"""
DeepAgent核心实现

基于LangGraph构建的数据分析Agent。
"""

import logging
from typing import Dict, Any, Optional, Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..state.graph_state import AgentState, AgentPhase, create_initial_state
from ..dag.models import DAGPlan
from ..dag.generator import DAGGenerator
from ..dag.visualizer import DAGVisualizer
from .executor import DAGExecutor
from .zhipu_llm import create_zhipu_llm
from ..config.prompts import MAIN_AGENT_PROMPT, CONVERSATION_PROMPT
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class DataAgent:
    """
    数据分析Agent

    支持多轮对话、自动生成DAG执行计划、执行数据分析任务。
    """

    def __init__(self):
        """初始化Agent"""
        self.settings = get_settings()
        self.llm = create_zhipu_llm()
        self.dag_generator = DAGGenerator()
        self.dag_executor = DAGExecutor()
        self.visualizer = DAGVisualizer()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建Agent状态图"""
        graph = StateGraph(AgentState)

        # 添加节点
        graph.add_node("conversation", self._conversation_node)
        graph.add_node("planning", self._planning_node)
        graph.add_node("confirmation", self._confirmation_node)
        graph.add_node("execution", self._execution_node)

        # 设置入口
        graph.set_entry_point("conversation")

        # 添加条件边
        graph.add_conditional_edges(
            "conversation",
            self._route_after_conversation,
            {
                "continue": "conversation",
                "plan": "planning",
                "end": END,
            }
        )

        graph.add_edge("planning", "confirmation")

        graph.add_conditional_edges(
            "confirmation",
            self._route_after_confirmation,
            {
                "execute": "execution",
                "modify": "planning",
                "cancel": END,
            }
        )

        graph.add_edge("execution", END)

        return graph.compile()

    def _conversation_node(self, state: AgentState) -> Dict[str, Any]:
        """
        对话节点

        与用户进行多轮对话，理解需求。
        """
        messages = state["messages"]

        # 构建系统提示
        system_msg = SystemMessage(content=f"{MAIN_AGENT_PROMPT}\n\n{CONVERSATION_PROMPT}")

        # 调用LLM
        response = self.llm.invoke([system_msg] + messages)

        return {
            "messages": [response],
            "iteration_count": state.get("iteration_count", 0) + 1,
        }

    def _planning_node(self, state: AgentState) -> Dict[str, Any]:
        """
        规划节点

        根据对话内容生成DAG执行计划。
        """
        messages = state["messages"]

        # 提取用户需求
        user_messages = [m for m in messages if isinstance(m, HumanMessage)]
        if user_messages:
            user_request = user_messages[-1].content
        else:
            user_request = "未知需求"

        # 获取上下文
        context = state.get("context", {})
        context_str = "\n".join(f"{k}: {v}" for k, v in context.items())

        # 生成DAG
        try:
            dag_plan = self.dag_generator.generate(user_request, context_str)

            # 生成可视化
            mermaid = self.visualizer.to_mermaid(dag_plan)

            # 构建响应
            response_content = f"""我已经理解您的需求，为您生成了以下执行计划：

**执行计划**: {dag_plan.name}

```mermaid
{mermaid}
```

**任务列表**:
"""
            for i, node in enumerate(dag_plan.nodes, 1):
                deps = f"(依赖: {', '.join(node.dependencies)})" if node.dependencies else ""
                response_content += f"{i}. **{node.name}** - 使用 `{node.tool}` {deps}\n"

            response_content += "\n是否执行此计划？请回复「执行」或「修改」。"

            return {
                "messages": [AIMessage(content=response_content)],
                "dag_plan": dag_plan.to_dict(),
                "current_phase": AgentPhase.CONFIRMATION,
            }

        except Exception as e:
            logger.error(f"DAG生成失败: {e}")
            return {
                "messages": [AIMessage(content=f"抱歉，生成执行计划时出错: {str(e)}")],
                "error": str(e),
            }

    def _confirmation_node(self, state: AgentState) -> Dict[str, Any]:
        """
        确认节点

        等待用户确认执行计划。
        """
        # 这个节点主要是等待用户输入
        # 实际的确认逻辑在路由函数中处理
        return {}

    def _execution_node(self, state: AgentState) -> Dict[str, Any]:
        """
        执行节点

        执行DAG计划中的所有任务。
        """
        dag_dict = state.get("dag_plan")
        if not dag_dict:
            return {
                "messages": [AIMessage(content="没有可执行的计划。")],
                "error": "无DAG计划",
            }

        dag_plan = DAGPlan.from_dict(dag_dict)

        # 执行进度回调
        def on_progress(node):
            logger.info(f"节点 {node.id} ({node.name}): {node.status.value}")

        # 执行DAG
        try:
            results = self.dag_executor.execute(dag_plan, on_node_complete=on_progress)

            # 构建结果报告
            response_content = "**执行结果**:\n\n"

            for node in dag_plan.nodes:
                icon = "✓" if node.status.value == "completed" else "✗"
                response_content += f"{icon} **{node.name}**: {node.status.value}\n"

                if node.result:
                    # 截断过长的结果
                    result_str = str(node.result)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "..."
                    response_content += f"```\n{result_str}\n```\n"

                if node.error:
                    response_content += f"   错误: {node.error}\n"

            if dag_plan.is_successful():
                response_content += "\n✓ 所有任务执行完成！"
            else:
                response_content += "\n✗ 部分任务执行失败。"

            return {
                "messages": [AIMessage(content=response_content)],
                "execution_results": results,
                "current_phase": AgentPhase.COMPLETED,
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "messages": [AIMessage(content=f"执行过程中出错: {str(e)}")],
                "error": str(e),
            }

    def _route_after_conversation(
        self,
        state: AgentState
    ) -> Literal["continue", "plan", "end"]:
        """
        对话后的路由决策

        根据对话内容决定下一步行动。
        """
        messages = state["messages"]
        if not messages:
            return "end"

        last_message = messages[-1]

        # 检查是否是AI消息
        if isinstance(last_message, AIMessage):
            # 检查是否包含[READY_TO_PLAN]标记
            if "[READY_TO_PLAN]" in last_message.content:
                return "plan"
            # AI已回复，结束本轮等待用户输入
            return "end"

        # 检查用户消息
        if isinstance(last_message, HumanMessage):
            content = last_message.content.lower()

            # 检查退出命令
            if content in ["退出", "exit", "quit", "q"]:
                return "end"

            # 检查是否请求生成计划
            if any(kw in content for kw in ["生成计划", "开始分析", "执行", "开始"]):
                return "plan"

            # 用户输入，继续对话
            return "continue"

        # 检查迭代次数
        if state.get("iteration_count", 0) >= self.settings.max_iterations:
            return "end"

        return "end"

    def _route_after_confirmation(
        self,
        state: AgentState
    ) -> Literal["execute", "modify", "cancel"]:
        """
        确认后的路由决策
        """
        messages = state["messages"]
        if not messages:
            return "cancel"

        last_message = messages[-1]

        if isinstance(last_message, HumanMessage):
            content = last_message.content.lower()

            if any(kw in content for kw in ["执行", "确认", "开始", "是", "yes", "y"]):
                return "execute"
            elif any(kw in content for kw in ["修改", "改", "调整"]):
                return "modify"
            else:
                return "cancel"

        return "cancel"

    def chat(self, user_input: str, state: Optional[AgentState] = None) -> tuple:
        """
        处理用户输入

        Args:
            user_input: 用户输入
            state: 当前状态（可选）

        Returns:
            tuple: (响应文本, 更新后的状态)
        """
        if state is None:
            state = create_initial_state()

        # 添加用户消息
        state["messages"] = state.get("messages", []) + [HumanMessage(content=user_input)]

        # 运行图
        result = self.graph.invoke(state)

        # 获取最新的AI响应（最后一条AI消息）
        messages = result.get("messages", [])
        response = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                response = msg.content
                break

        return response, result

    async def achat(self, user_input: str, state: Optional[AgentState] = None) -> tuple:
        """
        异步处理用户输入

        Args:
            user_input: 用户输入
            state: 当前状态（可选）

        Returns:
            tuple: (响应文本, 更新后的状态)
        """
        if state is None:
            state = create_initial_state()

        state["messages"] = state.get("messages", []) + [HumanMessage(content=user_input)]

        result = await self.graph.ainvoke(state)

        # 获取最新的AI响应（最后一条AI消息）
        messages = result.get("messages", [])
        response = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                response = msg.content
                break

        return response, result


def build_agent_graph() -> StateGraph:
    """
    构建Agent状态图

    Returns:
        StateGraph: 编译后的状态图
    """
    agent = DataAgent()
    return agent.graph


def create_agent() -> DataAgent:
    """
    创建Agent实例

    Returns:
        DataAgent: Agent实例
    """
    return DataAgent()
