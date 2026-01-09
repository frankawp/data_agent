"""核心Agent创建逻辑"""

import os
from typing import Optional, List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ..tools.sql_tools import SQL_TOOLS
from ..tools.python_tools import PYTHON_TOOLS
from ..tools.data_tools import DATA_TOOLS
from ..tools.ml_tools import ML_TOOLS
from ..tools.graph_tools import GRAPH_TOOLS
from ..dag.generator import DAGGenerator
from ..dag.visualizer import DAGVisualizer
from ..state.graph_state import DataAgentState
from .zhipu_llm import ChatZhipuAI


class DataAgent:
    """数据开发Agent

    负责与用户交互、生成DAG计划、执行数据分析任务
    """

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "claude-sonnet-4-5-20250929",
        db_connection: str = None,
        provider: str = "anthropic",
        base_url: str = None
    ):
        """初始化Agent

        Args:
            api_key: API密钥
            model_name: 模型名称
            db_connection: 数据库连接字符串
            provider: LLM提供商（anthropic或zhipu）
            base_url: API基础URL（仅用于zhipu）
        """
        self.provider = provider

        # 初始化LLM
        if provider == "zhipu":
            # 使用智谱AI
            if not api_key:
                raise ValueError("使用智谱AI时必须提供api_key参数")

            self.llm = ChatZhipuAI(
                api_key=api_key,
                model=model_name,
                base_url=base_url or "https://open.bigmodel.cn/api/paas/v4"
            )
        else:
            # 使用Anthropic（默认）
            # 设置API密钥
            if api_key:
                os.environ["ANTHROPIC_API_KEY"] = api_key
            elif not os.environ.get("ANTHROPIC_API_KEY"):
                raise ValueError("请提供ANTHROPIC_API_KEY环境变量或api_key参数")

            self.llm = ChatAnthropic(
                model=model_name,
                temperature=0.7
            )

        # 数据库连接
        self.db_connection = db_connection

        # 初始化DAG生成器
        self.dag_generator = DAGGenerator(self.llm)

        # 收集所有工具
        self.all_tools = (
            SQL_TOOLS +
            PYTHON_TOOLS +
            DATA_TOOLS +
            ML_TOOLS +
            GRAPH_TOOLS
        )

        # 系统提示词
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tools_desc = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.all_tools
        ])

        return f"""你是一个专业的数据开发助手，擅长帮助用户进行数据分析和处理。

## 你的能力

### 可用工具
{tools_desc}

### 工作流程
1. **理解需求**: 与用户交流，明确他们的数据分析目标
2. **生成计划**: 当需求明确后，生成一个DAG执行计划
3. **确认计划**: 向用户展示DAG计划，等待确认
4. **执行任务**: 按照DAG执行计划，调用相应的工具完成任务

## 交互原则

1. **多轮对话**: 不要急于生成DAG，先通过对话充分理解用户需求
2. **明确目标**: 确保理解用户想要完成什么任务
3. **数据源**: 了解数据来源（数据库、文件等）
4. **分析类型**: 了解用户想做什么类型的分析（统计分析、机器学习、图分析等）
5. **输出格式**: 了解用户期望的输出格式

## 何时生成DAG

当你充分理解了以下信息后，可以生成DAG计划：
- 用户的分析目标
- 数据源信息（数据库、表、文件等）
- 需要的分析类型
- 预期的输出结果

## 回复风格

- 使用中文交流
- 简洁、专业、友好
- 必要时询问澄清问题
- 对技术概念进行适当解释
"""

    async def chat(
        self,
        user_message: str,
        state: Optional[DataAgentState] = None
    ) -> DataAgentState:
        """与用户对话

        Args:
            user_message: 用户消息
            state: 当前状态（可选）

        Returns:
            更新后的状态
        """
        # 初始化状态
        if state is None:
            state = {
                "messages": [],
                "user_goal": "",
                "dag_plan": None,
                "dag_confirmed": False,
                "execution_results": [],
                "current_phase": "interaction",
                "intermediate_data": {},
                "db_connection": self.db_connection,
                "error": None
            }

        # 添加用户消息
        state["messages"].append(HumanMessage(content=user_message))

        # 添加系统消息（如果是首次对话）
        if len(state["messages"]) == 1:
            state["messages"].insert(0, SystemMessage(content=self.system_prompt))

        # 调用LLM
        response = await self.llm.ainvoke(state["messages"])
        state["messages"].append(AIMessage(content=response.content))

        # 分析响应，判断是否需要生成DAG
        if self._should_generate_dag(state):
            state["current_phase"] = "planning"
            state["user_goal"] = user_message

            # 生成DAG
            conversation_history = [msg.content for msg in state["messages"]]
            dag = await self.dag_generator.generate_dag(
                user_message,
                conversation_history,
                {"db_connection": self.db_connection} if self.db_connection else None
            )

            state["dag_plan"] = dag.to_dict()
            state["current_phase"] = "confirmation"

            # 生成确认消息
            visualizer = DAGVisualizer()
            dag_text = visualizer.to_execution_plan(dag)

            confirmation_msg = f"""
我已经为您生成了执行计划：

{dag_text}

请确认是否执行此计划？
- 输入 'y' 或 'yes' 开始执行
- 输入 'n' 或 'no' 取消
- 输入 'm' 修改计划
"""
            state["messages"].append(AIMessage(content=confirmation_msg))

        return state

    def _should_generate_dag(self, state: DataAgentState) -> bool:
        """判断是否应该生成DAG

        Args:
            state: 当前状态

        Returns:
            是否应该生成DAG
        """
        # 如果已经有DAG，不再生成
        if state.get("dag_plan"):
            return False

        # 如果处于执行或确认阶段，不再生成
        if state.get("current_phase") in ["confirmation", "execution"]:
            return False

        # 获取最近的AI响应
        ai_messages = [msg for msg in state["messages"] if isinstance(msg, AIMessage)]
        if not ai_messages:
            return False

        last_ai_message = ai_messages[-1].content.lower()

        # 如果AI明确表示要生成计划，则生成
        keywords = ["我为您生成", "让我为您规划", "执行计划", "dag"]
        return any(keyword in last_ai_message for keyword in keywords)

    async def confirm_dag(
        self,
        confirmed: bool,
        state: DataAgentState
    ) -> DataAgentState:
        """确认或拒绝DAG

        Args:
            confirmed: 是否确认
            state: 当前状态

        Returns:
            更新后的状态
        """
        if confirmed:
            state["dag_confirmed"] = True
            state["current_phase"] = "execution"
            state["messages"].append(
                AIMessage(content="好的，开始执行DAG计划...")
            )
        else:
            # 重置状态
            state["dag_plan"] = None
            state["dag_confirmed"] = False
            state["current_phase"] = "interaction"
            state["messages"].append(
                AIMessage(content="已取消。请告诉我您的需求，我会重新为您规划。")
            )

        return state

    def get_state_summary(self, state: DataAgentState) -> str:
        """获取状态摘要

        Args:
            state: 当前状态

        Returns:
            状态摘要文本
        """
        phase = state.get("current_phase", "interaction")
        phase_names = {
            "interaction": "交互中",
            "planning": "规划中",
            "confirmation": "等待确认",
            "execution": "执行中"
        }

        summary = f"当前阶段: {phase_names.get(phase, phase)}\n"

        if state.get("dag_plan"):
            summary += f"DAG计划: {state['dag_plan']['name']}\n"

        if state.get("execution_results"):
            summary += f"已执行节点: {len(state['execution_results'])}\n"

        return summary
