"""
DAG可视化

将DAG计划转换为Mermaid图表格式。
"""

from typing import Optional
from .models import DAGPlan, NodeStatus


class DAGVisualizer:
    """
    DAG可视化器

    将DAG计划转换为Mermaid格式，支持在CLI中展示。
    """

    # 节点状态对应的样式
    STATUS_STYLES = {
        NodeStatus.PENDING: "fill:#f9f9f9,stroke:#333",
        NodeStatus.RUNNING: "fill:#fff3cd,stroke:#856404",
        NodeStatus.COMPLETED: "fill:#d4edda,stroke:#155724",
        NodeStatus.FAILED: "fill:#f8d7da,stroke:#721c24",
        NodeStatus.SKIPPED: "fill:#e2e3e5,stroke:#383d41",
    }

    # 状态图标
    STATUS_ICONS = {
        NodeStatus.PENDING: "○",
        NodeStatus.RUNNING: "◐",
        NodeStatus.COMPLETED: "✓",
        NodeStatus.FAILED: "✗",
        NodeStatus.SKIPPED: "⊘",
    }

    def to_mermaid(self, dag: DAGPlan, show_status: bool = True) -> str:
        """
        将DAG转换为Mermaid格式

        Args:
            dag: DAG计划
            show_status: 是否显示节点状态

        Returns:
            Mermaid格式的图表字符串
        """
        lines = ["graph TD"]

        # 添加节点
        for node in dag.nodes:
            label = self._get_node_label(node, show_status)
            lines.append(f'    {node.id}["{label}"]')

        # 添加边
        for node in dag.nodes:
            for dep in node.dependencies:
                lines.append(f"    {dep} --> {node.id}")

        # 添加样式
        if show_status:
            for status, style in self.STATUS_STYLES.items():
                nodes_with_status = [n.id for n in dag.nodes if n.status == status]
                if nodes_with_status:
                    for node_id in nodes_with_status:
                        lines.append(f"    style {node_id} {style}")

        return "\n".join(lines)

    def _get_node_label(self, node, show_status: bool) -> str:
        """获取节点标签"""
        if show_status:
            icon = self.STATUS_ICONS.get(node.status, "")
            return f"{icon} {node.name}"
        return node.name

    def to_ascii(self, dag: DAGPlan) -> str:
        """
        将DAG转换为ASCII格式

        简单的文本表示，适合CLI显示。

        Args:
            dag: DAG计划

        Returns:
            ASCII格式的图表字符串
        """
        lines = []
        lines.append(f"╔{'═' * 50}╗")
        lines.append(f"║ {dag.name:^48} ║")
        lines.append(f"╠{'═' * 50}╣")

        # 拓扑排序获取执行顺序
        try:
            sorted_nodes = dag.topological_sort()
        except ValueError:
            sorted_nodes = dag.nodes

        for i, node in enumerate(sorted_nodes):
            icon = self.STATUS_ICONS.get(node.status, "○")
            status_text = node.status.value

            # 节点信息
            node_line = f"║ {icon} [{node.id}] {node.name}"
            node_line = f"{node_line:<48} ║"
            lines.append(node_line)

            # 工具和参数
            tool_line = f"║   工具: {node.tool}"
            tool_line = f"{tool_line:<48} ║"
            lines.append(tool_line)

            # 依赖
            if node.dependencies:
                deps = ", ".join(node.dependencies)
                dep_line = f"║   依赖: {deps}"
                dep_line = f"{dep_line:<48} ║"
                lines.append(dep_line)

            # 状态
            status_line = f"║   状态: {status_text}"
            status_line = f"{status_line:<48} ║"
            lines.append(status_line)

            # 分隔线
            if i < len(sorted_nodes) - 1:
                lines.append(f"╟{'─' * 50}╢")

        lines.append(f"╚{'═' * 50}╝")

        return "\n".join(lines)

    def to_rich_panel(self, dag: DAGPlan) -> str:
        """
        生成适合rich库显示的格式

        Args:
            dag: DAG计划

        Returns:
            富文本格式字符串
        """
        from rich.table import Table
        from rich.panel import Panel
        from io import StringIO
        from rich.console import Console

        table = Table(title=dag.name, show_header=True, header_style="bold")
        table.add_column("ID", style="cyan")
        table.add_column("名称", style="white")
        table.add_column("工具", style="green")
        table.add_column("依赖", style="yellow")
        table.add_column("状态", style="magenta")

        # 状态颜色映射
        status_colors = {
            NodeStatus.PENDING: "white",
            NodeStatus.RUNNING: "yellow",
            NodeStatus.COMPLETED: "green",
            NodeStatus.FAILED: "red",
            NodeStatus.SKIPPED: "dim",
        }

        try:
            sorted_nodes = dag.topological_sort()
        except ValueError:
            sorted_nodes = dag.nodes

        for node in sorted_nodes:
            deps = ", ".join(node.dependencies) if node.dependencies else "-"
            status_color = status_colors.get(node.status, "white")
            icon = self.STATUS_ICONS.get(node.status, "○")

            table.add_row(
                node.id,
                node.name,
                node.tool,
                deps,
                f"[{status_color}]{icon} {node.status.value}[/{status_color}]"
            )

        # 渲染到字符串
        console = Console(file=StringIO(), force_terminal=True)
        console.print(table)
        return console.file.getvalue()

    def print_progress(self, dag: DAGPlan):
        """
        打印执行进度

        Args:
            dag: DAG计划
        """
        from rich.console import Console
        from rich.progress import Progress, TaskID

        console = Console()
        progress = dag.get_progress()
        total = len(dag.nodes)
        completed = progress["completed"]
        failed = progress["failed"]
        running = progress["running"]

        # 进度条
        pct = (completed / total * 100) if total > 0 else 0

        console.print(f"\n[bold]执行进度[/bold]: {completed}/{total} ({pct:.0f}%)")
        console.print(f"  ✓ 完成: {completed}  ◐ 运行中: {running}  ✗ 失败: {failed}")

        # 显示失败的任务
        if failed > 0:
            console.print("\n[red]失败的任务:[/red]")
            for node in dag.nodes:
                if node.status == NodeStatus.FAILED:
                    console.print(f"  - {node.name}: {node.error}")


def visualize_dag(dag: DAGPlan, format: str = "ascii") -> str:
    """
    便捷函数：可视化DAG

    Args:
        dag: DAG计划
        format: 输出格式 (mermaid, ascii, rich)

    Returns:
        可视化结果字符串
    """
    viz = DAGVisualizer()

    if format == "mermaid":
        return viz.to_mermaid(dag)
    elif format == "rich":
        return viz.to_rich_panel(dag)
    else:
        return viz.to_ascii(dag)
