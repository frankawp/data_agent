"""DAG数据模型和生成模块"""

from .models import DAGNode, DAGPlan, NodeStatus
from .visualizer import DAGVisualizer

# 延迟导入以避免循环依赖
def __getattr__(name):
    if name == "DAGGenerator":
        from .generator import DAGGenerator
        return DAGGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["DAGNode", "DAGPlan", "NodeStatus", "DAGGenerator", "DAGVisualizer"]
