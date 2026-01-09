"""DAG数据模型定义"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json


class DAGNode(BaseModel):
    """DAG节点

    代表执行计划中的一个任务节点
    """
    id: str = Field(..., description="节点唯一ID")
    name: str = Field(..., description="节点名称")
    tool: str = Field(..., description="使用的工具名称")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="工具输入参数")
    dependencies: List[str] = Field(default_factory=list, description="依赖的节点ID列表")
    description: Optional[str] = Field(None, description="节点描述")

    class Config:
        json_encoders = {
            # 确保中文字符正确编码
        }


class DAGPlan(BaseModel):
    """DAG执行计划

    定义完整的数据分析执行流程
    """
    id: str = Field(..., description="DAG唯一ID")
    name: str = Field(..., description="DAG名称")
    description: str = Field(..., description="DAG描述")
    nodes: List[DAGNode] = Field(..., description="所有节点")
    edges: List[Dict[str, str]] = Field(default_factory=list, description="节点之间的边")
    estimated_time: Optional[int] = Field(None, description="预估执行时间（秒）")

    def to_mermaid(self) -> str:
        """转换为Mermaid流程图格式

        Returns:
            Mermaid格式的流程图字符串
        """
        mermaid_lines = ["graph TD"]

        # 添加节点
        for node in self.nodes:
            label = f"{node.name}\\n({node.tool})"
            mermaid_lines.append(f'    {node.id}["{label}"]')

        # 添加边
        for edge in self.edges:
            mermaid_lines.append(f"    {edge['from']} --> {edge['to']}")

        return "\n".join(mermaid_lines)

    def topological_sort(self) -> List[DAGNode]:
        """拓扑排序，返回可执行的节点顺序

        Returns:
            按依赖关系排序的节点列表

        Raises:
            ValueError: 如果DAG包含循环依赖
        """
        # 计算入度
        in_degree = {node.id: 0 for node in self.nodes}
        graph = {node.id: [] for node in self.nodes}

        # 构建图和入度
        for edge in self.edges:
            graph[edge['from']].append(edge['to'])
            in_degree[edge['to']] += 1

        # 找到所有入度为0的节点
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            node = next(n for n in self.nodes if n.id == node_id)
            result.append(node)

            # 减少邻居节点的入度
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # 检查是否有循环依赖
        if len(result) != len(self.nodes):
            raise ValueError("DAG包含循环依赖，无法进行拓扑排序")

        return result

    def get_execution_order(self) -> List[List[str]]:
        """获取执行层级（可以并行执行的节点）

        Returns:
            二维列表，每个子列表包含可以并行执行的节点ID
        """
        sorted_nodes = self.topological_sort()
        levels = []
        node_level = {}
        executed_nodes = set()

        for node in sorted_nodes:
            # 找到所有依赖的层级
            dep_levels = []
            for dep in node.dependencies:
                if dep in node_level:
                    dep_levels.append(node_level[dep])

            # 当前节点层级 = 最大依赖层级 + 1
            current_level = max(dep_levels) + 1 if dep_levels else 0
            node_level[node.id] = current_level

            # 添加到对应层级
            while len(levels) <= current_level:
                levels.append([])
            levels[current_level].append(node.id)

            executed_nodes.add(node.id)

        return levels

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            DAG的字典表示
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [node.dict() for node in self.nodes],
            "edges": self.edges,
            "estimated_time": self.estimated_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DAGPlan':
        """从字典创建DAGPlan

        Args:
            data: DAG的字典表示

        Returns:
            DAGPlan实例
        """
        nodes = [DAGNode(**node_data) for node_data in data.get("nodes", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            nodes=nodes,
            edges=data.get("edges", []),
            estimated_time=data.get("estimated_time")
        )

    def get_node_by_id(self, node_id: str) -> Optional[DAGNode]:
        """根据ID获取节点

        Args:
            node_id: 节点ID

        Returns:
            DAGNode实例，如果未找到则返回None
        """
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
