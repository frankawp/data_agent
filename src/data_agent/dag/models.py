"""
DAG数据模型

定义DAG节点和执行计划的数据结构。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import json


class NodeStatus(str, Enum):
    """节点执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DAGNode:
    """
    DAG节点

    表示执行计划中的一个任务节点。
    """
    id: str
    name: str
    tool: str
    params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "tool": self.tool,
            "params": self.params,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DAGNode":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            tool=data["tool"],
            params=data.get("params", {}),
            dependencies=data.get("dependencies", []),
            status=NodeStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
            execution_time=data.get("execution_time", 0.0),
        )

    def is_ready(self, completed_nodes: set) -> bool:
        """检查节点是否可以执行（所有依赖已完成）"""
        return all(dep in completed_nodes for dep in self.dependencies)


@dataclass
class DAGPlan:
    """
    DAG执行计划

    包含多个节点和它们之间的依赖关系。
    """
    nodes: List[DAGNode] = field(default_factory=list)
    name: str = "执行计划"
    description: str = ""

    def __post_init__(self):
        """初始化后处理"""
        self._node_map: Dict[str, DAGNode] = {}
        self._update_node_map()

    def _update_node_map(self):
        """更新节点映射"""
        self._node_map = {node.id: node for node in self.nodes}

    def add_node(self, node: DAGNode):
        """添加节点"""
        self.nodes.append(node)
        self._node_map[node.id] = node

    def get_node(self, node_id: str) -> Optional[DAGNode]:
        """获取节点"""
        return self._node_map.get(node_id)

    def get_edges(self) -> List[Tuple[str, str]]:
        """获取所有边（依赖关系）"""
        edges = []
        for node in self.nodes:
            for dep in node.dependencies:
                edges.append((dep, node.id))
        return edges

    def topological_sort(self) -> List[DAGNode]:
        """
        拓扑排序

        返回按执行顺序排列的节点列表。

        Raises:
            ValueError: 如果存在循环依赖
        """
        in_degree = {node.id: len(node.dependencies) for node in self.nodes}
        queue = [node for node in self.nodes if in_degree[node.id] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for other in self.nodes:
                if node.id in other.dependencies:
                    in_degree[other.id] -= 1
                    if in_degree[other.id] == 0:
                        queue.append(other)

        if len(result) != len(self.nodes):
            raise ValueError("DAG存在循环依赖")

        return result

    def get_ready_nodes(self) -> List[DAGNode]:
        """获取当前可执行的节点（依赖已完成且状态为pending）"""
        completed = {node.id for node in self.nodes if node.status == NodeStatus.COMPLETED}
        return [
            node for node in self.nodes
            if node.status == NodeStatus.PENDING and node.is_ready(completed)
        ]

    def validate(self) -> List[str]:
        """
        验证DAG合法性

        Returns:
            错误列表，空列表表示验证通过
        """
        errors = []

        # 检查节点ID唯一性
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            errors.append("存在重复的节点ID")

        # 检查依赖是否存在
        for node in self.nodes:
            for dep in node.dependencies:
                if dep not in self._node_map:
                    errors.append(f"节点 {node.id} 依赖不存在的节点 {dep}")

        # 检查循环依赖
        try:
            self.topological_sort()
        except ValueError:
            errors.append("存在循环依赖")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "nodes": [node.to_dict() for node in self.nodes],
        }

    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DAGPlan":
        """从字典创建"""
        nodes = [DAGNode.from_dict(n) for n in data.get("nodes", [])]
        plan = cls(
            nodes=nodes,
            name=data.get("name", "执行计划"),
            description=data.get("description", ""),
        )
        return plan

    @classmethod
    def from_json(cls, json_str: str) -> "DAGPlan":
        """从JSON创建"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_progress(self) -> Dict[str, int]:
        """获取执行进度"""
        status_counts = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
        }
        for node in self.nodes:
            status_counts[node.status.value] += 1
        return status_counts

    def is_completed(self) -> bool:
        """检查是否全部完成"""
        return all(
            node.status in [NodeStatus.COMPLETED, NodeStatus.SKIPPED, NodeStatus.FAILED]
            for node in self.nodes
        )

    def is_successful(self) -> bool:
        """检查是否成功完成（无失败节点）"""
        return self.is_completed() and all(
            node.status != NodeStatus.FAILED for node in self.nodes
        )
