"""DAG可视化工具"""

from typing import Dict, Any
from .models import DAGPlan


class DAGVisualizer:
    """DAG可视化工具类

    提供多种格式的DAG可视化输出
    """

    @staticmethod
    def to_mermaid(dag: DAGPlan) -> str:
        """生成Mermaid格式的流程图

        Args:
            dag: DAG计划实例

        Returns:
            Mermaid格式的字符串
        """
        return dag.to_mermaid()

    @staticmethod
    def to_ascii(dag: DAGPlan) -> str:
        """生成ASCII艺术图

        Args:
            dag: DAG计划实例

        Returns:
            ASCII格式的文本图
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"DAG: {dag.name}")
        lines.append("=" * 60)
        lines.append(f"\n描述: {dag.description}\n")

        # 获取执行顺序
        sorted_nodes = dag.topological_sort()

        lines.append("执行步骤:")
        lines.append("-" * 60)

        for i, node in enumerate(sorted_nodes, 1):
            deps = ", ".join(node.dependencies) if node.dependencies else "无"
            lines.append(f"\n{i}. {node.name}")
            lines.append(f"   工具: {node.tool}")
            lines.append(f"   依赖: {deps}")
            if node.description:
                lines.append(f"   说明: {node.description}")

        # 添加预估时间
        if dag.estimated_time:
            lines.append(f"\n预估执行时间: {dag.estimated_time} 秒")

        return "\n".join(lines)

    @staticmethod
    def to_markdown(dag: DAGPlan) -> str:
        """生成Markdown格式的文档

        Args:
            dag: DAG计划实例

        Returns:
            Markdown格式的文档
        """
        md = f"""# {dag.name}

## 描述
{dag.description}

## 执行计划

"""
        sorted_nodes = dag.topological_sort()

        for i, node in enumerate(sorted_nodes, 1):
            md += f"\n### 步骤 {i}: {node.name}\n\n"
            md += f"- **工具**: {node.tool}\n"
            if node.dependencies:
                md += f"- **依赖**: {', '.join(node.dependencies)}\n"
            if node.description:
                md += f"- **说明**: {node.description}\n"
            if node.inputs:
                import json
                md += f"- **参数**: \n```json\n{json.dumps(node.inputs, indent=2, ensure_ascii=False)}\n```\n"

        if dag.estimated_time:
            md += f"\n**预估执行时间**: {dag.estimated_time} 秒\n"

        md += "\n## 流程图\n\n"
        md += "```mermaid\n"
        md += dag.to_mermaid()
        md += "\n```\n"

        return md

    @staticmethod
    def to_execution_plan(dag: DAGPlan) -> str:
        """生成执行计划文本（用户友好的格式）

        Args:
            dag: DAG计划实例

        Returns:
            格式化的执行计划文本
        """
        lines = []
        lines.append("╔" + "═" * 58 + "╗")
        lines.append("║" + " " * 58 + "║")
        lines.append(f"║{' ' * ((58 - len(dag.name)) // 2)}{dag.name}{' ' * (58 - ((58 - len(dag.name)) // 2) - len(dag.name))}║")
        lines.append("║" + " " * 58 + "║")
        lines.append("╚" + "═" * 58 + "╝")
        lines.append(f"\n📋 {dag.description}\n")

        # 获取执行层级
        levels = dag.get_execution_order()

        lines.append("执行计划:")
        lines.append("─" * 60)

        for level_num, level_nodes in enumerate(levels, 1):
            lines.append(f"\n阶段 {level_num}:")
            for node_id in level_nodes:
                node = dag.get_node_by_id(node_id)
                if node:
                    deps = f" (依赖: {', '.join(node.dependencies)})" if node.dependencies else ""
                    lines.append(f"  • {node.name} - 使用 {node.tool} 工具{deps}")

        if dag.estimated_time:
            lines.append(f"\n⏱️  预计耗时: {dag.estimated_time} 秒")

        return "\n".join(lines)

    @staticmethod
    def print_dag(dag: DAGPlan, format: str = "ascii") -> None:
        """打印DAG（默认使用ASCII格式）

        Args:
            dag: DAG计划实例
            format: 输出格式 (ascii/mermaid/markdown/plan)
        """
        if format == "ascii":
            print(DAGVisualizer.to_ascii(dag))
        elif format == "mermaid":
            print(DAGVisualizer.to_mermaid(dag))
        elif format == "markdown":
            print(DAGVisualizer.to_markdown(dag))
        elif format == "plan":
            print(DAGVisualizer.to_execution_plan(dag))
        else:
            raise ValueError(f"不支持的格式: {format}")
