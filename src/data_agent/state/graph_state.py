"""数据Agent的状态定义"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class DataAgentState(TypedDict):
    """数据Agent的状态定义

    用于管理整个对话和执行流程的状态
    """
    # 对话历史（使用add_messages函数处理追加）
    messages: Annotated[List[BaseMessage], add_messages]

    # 用户目标描述
    user_goal: str

    # DAG执行计划（JSON格式）
    dag_plan: Optional[Dict[str, Any]]

    # DAG是否已确认
    dag_confirmed: bool

    # 执行结果列表
    execution_results: List[Dict[str, Any]]

    # 当前阶段：interaction/planning/confirmation/execution
    current_phase: str

    # 中间数据存储（用于节点间数据传递）
    intermediate_data: Dict[str, Any]

    # 数据库连接信息
    db_connection: Optional[str]

    # 错误信息
    error: Optional[str]
