"""数据Agent的CLI入口"""

import asyncio
import os
import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.table import Table

from .agent.core import DataAgent
from .agent.executor import DAGExecutor
from .dag.models import DAGPlan
from .dag.visualizer import DAGVisualizer


class DataAgentCLI:
    """数据Agent的CLI界面"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "glm-4",
        db_connection: Optional[str] = None,
        provider: str = "zhipu",
        base_url: Optional[str] = None
    ):
        """初始化CLI

        Args:
            api_key: API密钥
            model_name: 模型名称
            db_connection: 数据库连接字符串
            provider: LLM提供商（anthropic或zhipu）
            base_url: API基础URL（仅用于智谱AI）
        """
        self.console = Console()
        self.agent = DataAgent(
            api_key=api_key,
            model_name=model_name,
            db_connection=db_connection,
            provider=provider,
            base_url=base_url
        )
        self.state = None
        self.running = True

    def print_welcome(self):
        """打印欢迎信息"""
        welcome_text = """
# 🤖 数据开发Agent

基于LangChain DeepAgents框架的数据分析助手

## 功能特性
- 多轮交互，理解您的数据分析需求
- 自动生成DAG执行计划
- 支持SQL、Python、pandas、scikit-learn、networkx等工具
- 数据库查询和分析

## 使用说明
- 直接描述您的数据分析需求
- 输入 'exit' 或 'quit' 退出
- 输入 'help' 查看帮助信息
"""
        md = Markdown(welcome_text)
        self.console.print(md)

    def print_help(self):
        """打印帮助信息"""
        help_table = Table(title="命令列表")
        help_table.add_column("命令", style="cyan", no_wrap=True)
        help_table.add_column("说明")

        help_table.add_row("exit / quit", "退出程序")
        help_table.add_row("help", "显示帮助信息")
        help_table.add_row("clear", "清空屏幕")
        help_table.add_row("status", "查看当前状态")
        help_table.add_row("任何其他文本", "与Agent对话")

        self.console.print(help_table)

    async def run(self):
        """运行主循环"""
        self.print_welcome()

        while self.running:
            try:
                # 获取用户输入
                user_input = Prompt.ask(
                    "\n[bold cyan]您[/bold cyan]",
                    console=self.console,
                    default="",
                    show_default=False
                )

                if not user_input.strip():
                    continue

                # 处理命令
                await self.process_input(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]检测到中断信号，正在退出...[/yellow]")
                break
            except Exception as e:
                self.console.print(f"\n[red]错误: {str(e)}[/red]\n")

    async def process_input(self, user_input: str):
        """处理用户输入

        Args:
            user_input: 用户输入
        """
        # 处理特殊命令
        command = user_input.strip().lower()

        if command in ['exit', 'quit', '退出', 'q']:
            self.running = False
            self.console.print("[green]再见！👋[/green]")
            return

        if command in ['help', 'h', '帮助']:
            self.print_help()
            return

        if command in ['clear', 'cls', '清屏']:
            os.system('cls' if os.name == 'nt' else 'clear')
            return

        if command in ['status', '状态']:
            if self.state:
                summary = self.agent.get_state_summary(self.state)
                self.console.print(Panel(summary, title="[bold]当前状态[/bold]"))
            else:
                self.console.print("[yellow]尚未开始对话[/yellow]")
            return

        # 与Agent对话
        await self.chat_with_agent(user_input)

    async def chat_with_agent(self, user_input: str):
        """与Agent对话

        Args:
            user_input: 用户输入
        """
        # 调用Agent
        self.state = await self.agent.chat(user_input, self.state)

        # 显示AI响应
        self.display_ai_response()

        # 如果生成了DAG，等待确认
        if self.state.get("current_phase") == "confirmation":
            await self.handle_dag_confirmation()

        # 如果需要执行DAG
        elif self.state.get("current_phase") == "execution" and self.state.get("dag_confirmed"):
            await self.execute_dag()

    def display_ai_response(self):
        """显示AI响应"""
        if not self.state or not self.state.get("messages"):
            return

        # 获取最后的AI消息
        ai_messages = [
            msg for msg in self.state["messages"]
            if msg.__class__.__name__ == 'AIMessage'
        ]

        if ai_messages:
            last_message = ai_messages[-1].content

            # 如果包含Mermaid代码，用语法高亮显示
            if "```mermaid" in last_message:
                parts = last_message.split("```")
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        self.console.print(part)
                    else:
                        lang = part.split('\n', 1)[0] if '\n' in part else ''
                        code = part.split('\n', 1)[1] if '\n' in part else part
                        if lang.strip() == 'mermaid':
                            syntax = Syntax(code, "mermaid", theme="monokai", line_numbers=False)
                            self.console.print(syntax)
                        else:
                            self.console.print(f"```{part}```")
            else:
                # 普通消息显示在面板中
                self.console.print(Panel(
                    last_message,
                    title="[bold green]Agent[/bold green]",
                    border_style="green"
                ))

    async def handle_dag_confirmation(self):
        """处理DAG确认"""
        dag_plan_dict = self.state.get("dag_plan")
        if not dag_plan_dict:
            return

        # 显示DAG
        dag = DAGPlan.from_dict(dag_plan_dict)
        visualizer = DAGVisualizer()

        # 使用用户友好的格式显示
        dag_text = visualizer.to_execution_plan(dag)
        self.console.print(Panel(dag_text, title="[bold yellow]执行计划[/bold yellow]", border_style="yellow"))

        # 显示Mermaid图
        mermaid = dag.to_mermaid()
        syntax = Syntax(mermaid, "mermaid", theme="monokai", line_numbers=False)
        self.console.print(Panel(syntax, title="[bold]流程图[/bold]", border_style="blue"))

        # 等待用户确认
        while True:
            confirm = Prompt.ask(
                "\n[bold yellow]是否执行此计划？[/bold yellow] ([green]y[/green]/[red]n[/red]/[blue]m[/blue])",
                choices=["y", "n", "m"],
                default="y",
                console=self.console
            )

            if confirm == "y":
                # 确认执行
                self.state = await self.agent.confirm_dag(True, self.state)
                break
            elif confirm == "n":
                # 拒绝执行
                self.state = await self.agent.confirm_dag(False, self.state)
                self.console.print("[yellow]已取消，请重新描述需求[/yellow]")
                break
            else:
                self.console.print("[yellow]修改功能尚未实现，请选择 y 或 n[/yellow]")

    async def execute_dag(self):
        """执行DAG"""
        dag_plan_dict = self.state.get("dag_plan")
        if not dag_plan_dict:
            return

        dag = DAGPlan.from_dict(dag_plan_dict)

        # 创建执行器
        executor = DAGExecutor(db_connection=self.state.get("db_connection"))

        # 创建进度回调
        async def progress_callback(current, total, node):
            self.console.print(f"[cyan]执行进度: {current}/{total} - {node.name}[/cyan]")

        # 执行DAG
        self.console.print("\n[green]开始执行DAG...[/green]\n")

        results = await executor.execute_dag(dag, progress_callback)

        # 显示执行结果
        self.display_execution_results(results)

        # 更新状态
        self.state["execution_results"] = results
        self.state["current_phase"] = "interaction"
        self.state["dag_confirmed"] = False

    def display_execution_results(self, results):
        """显示执行结果

        Args:
            results: 执行结果列表
        """
        self.console.print("\n[bold]执行结果:[/bold]\n")

        for i, result in enumerate(results, 1):
            node_name = result.get("node_name", f"节点{i}")
            success = result.get("success", False)

            if success:
                self.console.print(f"[green]✓[/green] {node_name}: [green]成功[/green]")

                # 显示结果详情
                result_data = result.get("result", {})
                if isinstance(result_data, dict):
                    if "output" in result_data:
                        self.console.print(f"  输出: {result_data['output'][:200]}...")
                    elif "data" in result_data:
                        data = result_data["data"]
                        if isinstance(data, list) and len(data) > 0:
                            self.console.print(f"  数据行数: {len(data)}")
                    elif "statistics" in result_data:
                        self.console.print(f"  统计信息已生成")
            else:
                error = result.get("error", "未知错误")
                self.console.print(f"[red]✗[/red] {node_name}: [red]失败[/red]")
                self.console.print(f"  错误: {error}")

        # 检查是否全部成功
        all_success = all(r.get("success", False) for r in results)
        if all_success:
            self.console.print("\n[bold green]✓ 所有任务执行完成！[/bold green]\n")
        else:
            self.console.print("\n[bold red]✗ 部分任务执行失败[/bold red]\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="数据开发Agent")
    parser.add_argument(
        "--api-key",
        help="API密钥（Anthropic或智谱AI）"
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "zhipu"],
        default="anthropic",
        help="LLM提供商（默认: anthropic）"
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5-20250929" if os.environ.get("ANTHROPIC_API_KEY") else "glm-4",
        help="模型名称（默认: claude-sonnet-4-5-20250929 或 glm-4）"
    )
    parser.add_argument(
        "--base-url",
        default="https://open.bigmodel.cn/api/paas/v4",
        help="API基础URL（仅用于智谱AI）"
    )
    parser.add_argument(
        "--db",
        help="数据库连接字符串（例如: mysql+pymysql://user:pass@localhost:3306/db）"
    )

    args = parser.parse_args()

    # 确定API密钥
    if args.provider == "zhipu":
        api_key = args.api_key or os.environ.get("ZHIPUAI_API_KEY")
        if not api_key:
            print("错误: 使用智谱AI时必须提供--api-key参数或设置ZHIPUAI_API_KEY环境变量")
            sys.exit(1)
    else:
        api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("错误: 使用Anthropic时必须提供--api-key参数或设置ANTHROPIC_API_KEY环境变量")
            sys.exit(1)

    # 创建CLI实例
    cli = DataAgentCLI(
        api_key=api_key,
        model_name=args.model,
        db_connection=args.db,
        provider=args.provider,
        base_url=args.base_url if args.provider == "zhipu" else None
    )

    # 运行CLI
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
