"""
Agent状态定义

定义LangGraph中Agent的状态结构。
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Annotated, TYPE_CHECKING
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

if TYPE_CHECKING:
    from ..dag.models import DAGPlan


class AgentPhase(str, Enum):
    """Agent执行阶段"""
    CONVERSATION = "conversation"  # 对话阶段
    PLANNING = "planning"          # 规划阶段
    CONFIRMATION = "confirmation"  # 确认阶段
    EXECUTION = "execution"        # 执行阶段
    COMPLETED = "completed"        # 完成阶段


class AgentState(TypedDict):
    """
    Agent状态

    存储Agent在执行过程中的所有状态信息。
    """
    # 消息历史（使用add_messages reducer自动合并）
    messages: Annotated[List[BaseMessage], add_messages]

    # 当前执行阶段
    current_phase: AgentPhase

    # DAG执行计划
    dag_plan: Optional[Dict[str, Any]]

    # 执行结果
    execution_results: Dict[str, Any]

    # 虚拟文件系统（用于存储中间结果）
    files: Dict[str, str]

    # 用户确认标志
    user_confirmed: bool

    # 错误信息
    error: Optional[str]

    # 上下文信息（如数据库表结构等）
    context: Dict[str, Any]

    # 迭代计数
    iteration_count: int


def create_initial_state() -> AgentState:
    """
    创建初始状态

    Returns:
        AgentState: 初始状态
    """
    return {
        "messages": [],
        "current_phase": AgentPhase.CONVERSATION,
        "dag_plan": None,
        "execution_results": {},
        "files": {},
        "user_confirmed": False,
        "error": None,
        "context": {},
        "iteration_count": 0,
    }


def update_phase(state: AgentState, phase: AgentPhase) -> AgentState:
    """
    更新执行阶段

    Args:
        state: 当前状态
        phase: 新阶段

    Returns:
        AgentState: 更新后的状态
    """
    return {**state, "current_phase": phase}


def update_dag_plan(state: AgentState, dag_plan: "DAGPlan") -> AgentState:
    """
    更新DAG计划

    Args:
        state: 当前状态
        dag_plan: 新的DAG计划

    Returns:
        AgentState: 更新后的状态
    """
    return {**state, "dag_plan": dag_plan.to_dict()}


def add_execution_result(
    state: AgentState,
    node_id: str,
    result: Any
) -> AgentState:
    """
    添加执行结果

    Args:
        state: 当前状态
        node_id: 节点ID
        result: 执行结果

    Returns:
        AgentState: 更新后的状态
    """
    results = state.get("execution_results", {}).copy()
    results[node_id] = result
    return {**state, "execution_results": results}


def write_file(state: AgentState, filename: str, content: str) -> AgentState:
    """
    写入虚拟文件

    Args:
        state: 当前状态
        filename: 文件名
        content: 文件内容

    Returns:
        AgentState: 更新后的状态
    """
    files = state.get("files", {}).copy()
    files[filename] = content
    return {**state, "files": files}


def read_file(state: AgentState, filename: str) -> Optional[str]:
    """
    读取虚拟文件

    Args:
        state: 当前状态
        filename: 文件名

    Returns:
        Optional[str]: 文件内容，不存在返回None
    """
    return state.get("files", {}).get(filename)


def set_error(state: AgentState, error: str) -> AgentState:
    """
    设置错误信息

    Args:
        state: 当前状态
        error: 错误信息

    Returns:
        AgentState: 更新后的状态
    """
    return {**state, "error": error}


def increment_iteration(state: AgentState) -> AgentState:
    """
    增加迭代计数

    Args:
        state: 当前状态

    Returns:
        AgentState: 更新后的状态
    """
    count = state.get("iteration_count", 0)
    return {**state, "iteration_count": count + 1}


def should_continue(state: AgentState, max_iterations: int = 10) -> bool:
    """
    检查是否应继续执行

    Args:
        state: 当前状态
        max_iterations: 最大迭代次数

    Returns:
        bool: 是否继续
    """
    # 检查错误
    if state.get("error"):
        return False

    # 检查迭代次数
    if state.get("iteration_count", 0) >= max_iterations:
        return False

    # 检查是否完成
    if state.get("current_phase") == AgentPhase.COMPLETED:
        return False

    return True
