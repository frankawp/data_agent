"""Agent核心模块"""

from .zhipu_llm import create_zhipu_llm

# 延迟导入以避免循环依赖
def __getattr__(name):
    if name == "DataAgent":
        from .core import DataAgent
        return DataAgent
    if name == "build_agent_graph":
        from .core import build_agent_graph
        return build_agent_graph
    if name == "DAGExecutor":
        from .executor import DAGExecutor
        return DAGExecutor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["build_agent_graph", "DataAgent", "DAGExecutor", "create_zhipu_llm"]
