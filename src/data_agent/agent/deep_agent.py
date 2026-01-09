"""
DeepAgent 数据分析实现

基于 DeepAgents 框架构建的数据分析 Agent。
"""

from typing import Optional

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langgraph.graph.state import CompiledStateGraph

from ..config.settings import get_settings
from ..tools import (
    execute_sql,
    query_with_duckdb,
    query_parquet,
    analyze_dataframe,
    statistical_analysis,
    analyze_large_dataset,
    train_model,
    predict,
    evaluate_model,
    create_graph,
    graph_analysis,
)
from ..tools.sql_tools import list_tables, describe_table


# 数据分析专用系统提示
DATA_AGENT_PROMPT = """你是一个专业的数据分析 Agent，专门帮助用户进行数据查询、分析和可视化。

## 可用工具

### SQL 数据库工具
- `list_tables`: 列出数据库中的所有表
- `describe_table`: 获取指定表的结构信息
- `execute_sql`: 执行 SQL 查询（仅支持 SELECT，自动防止危险操作）
- `query_with_duckdb`: 使用 DuckDB 执行高性能分析查询
- `query_parquet`: 直接查询 Parquet 文件

### 数据分析工具
- `analyze_dataframe`: 分析 DataFrame 的基本统计信息
- `statistical_analysis`: 执行统计分析（正态性检验、相关性、t检验等）
- `analyze_large_dataset`: 使用 DuckDB 分析大数据集

### 机器学习工具
- `train_model`: 训练机器学习模型（支持分类、回归、聚类）
- `predict`: 使用训练好的模型进行预测
- `evaluate_model`: 评估模型性能

### 图分析工具
- `create_graph`: 创建图结构
- `graph_analysis`: 执行图算法分析

## 工作流程

1. **理解需求**: 仔细理解用户的数据分析需求
2. **规划任务**: 使用 write_todos 工具将复杂任务分解为步骤
3. **执行查询**: 调用相应工具获取和分析数据
4. **汇总结果**: 将分析结果以清晰的格式呈现给用户

## 重要提示

- 请直接调用工具获取真实数据，不要编造数据
- 对于复杂任务，先规划步骤再执行
- 查询结果过长时会自动保存到文件，可用 read_file 查看
- SQL 查询仅支持 SELECT，自动阻止危险操作
"""


def create_data_agent(
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> CompiledStateGraph:
    """
    创建数据分析 DeepAgent

    Args:
        model: 模型名称，默认使用智谱 AI glm-4
        system_prompt: 自定义系统提示，默认使用数据分析专用提示

    Returns:
        CompiledStateGraph: 编译后的 Agent 图
    """
    settings = get_settings()

    # 初始化模型
    if model is None:
        # 使用智谱 AI 模型
        llm = init_chat_model(
            model=settings.zhipu_model,
            model_provider="openai",
            api_key=settings.zhipu_api_key,
            base_url=settings.zhipu_base_url,
        )
    elif isinstance(model, str):
        llm = init_chat_model(model)
    else:
        llm = model

    # 定义工具列表
    tools = [
        # SQL 工具
        execute_sql,
        list_tables,
        describe_table,
        query_with_duckdb,
        query_parquet,
        # 数据分析工具
        analyze_dataframe,
        statistical_analysis,
        analyze_large_dataset,
        # 机器学习工具
        train_model,
        predict,
        evaluate_model,
        # 图分析工具
        create_graph,
        graph_analysis,
    ]

    # 创建 DeepAgent
    agent = create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt or DATA_AGENT_PROMPT,
    )

    return agent


class DataAgent:
    """
    数据分析 Agent 封装类

    提供更简洁的接口来使用 DeepAgent。
    """

    def __init__(self, model: Optional[str] = None):
        """
        初始化数据分析 Agent

        Args:
            model: 模型名称，默认使用配置中的模型
        """
        self.agent = create_data_agent(model=model)
        self._messages = []

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

        # 调用 Agent
        result = self.agent.invoke({"messages": self._messages})

        # 获取响应
        messages = result.get("messages", [])
        if messages:
            response = messages[-1].content
            self._messages = messages  # 更新消息历史
        else:
            response = "抱歉，无法处理您的请求。"

        return response

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
