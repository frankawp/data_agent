"""
同步 CLI

简洁的命令行界面：
- Ctrl+C 中断执行
- :数字 查看历史步骤
- exit 退出程序
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table

from ..agent.deep_agent import DataAgent
from ..config.settings import get_settings
from ..commands import get_registry, register_all_commands
from ..ui import StepPager, format_tool_result, format_tool_args_display


def _print_config(console: Console) -> None:
    """打印配置信息"""
    settings = get_settings()

    config_table = Table(title="配置信息")
    config_table.add_column("配置项", style="cyan")
    config_table.add_column("值", style="white")

    config_table.add_row("模型", settings.model)
    config_table.add_row("API地址", settings.base_url)
    config_table.add_row("数据库类型", settings.get_db_type())
    config_table.add_row("沙箱启用", "是" if settings.sandbox_enabled else "否")
    config_table.add_row("最大迭代次数", str(settings.max_iterations))

    console.print(config_table)


class SyncCLI:
    """
    同步 CLI

    支持：
    - Ctrl+C 中断执行
    - :数字 查看历史步骤
    - 斜杠命令
    - exit 退出程序
    """

    def __init__(
        self,
        agent: DataAgent,
        console: Console,
        step_pager: Optional[StepPager] = None,
    ):
        self.agent = agent
        self.console = console
        self.step_pager = step_pager or StepPager(console)

        # 命令注册表
        register_all_commands()
        self.registry = get_registry()

        # 执行状态
        self.is_running = False
        self.should_cancel = False
        self.step_count = 0

    def run(self):
        """运行 CLI 主循环"""
        self._print_welcome()

        while True:
            try:
                # 获取用户输入
                user_input = self.console.input("[bold green]您: [/bold green]").strip()

                if not user_input:
                    continue

                # 处理命令
                if self._handle_command(user_input):
                    continue

                # 处理用户输入
                self._process_input(user_input)

            except KeyboardInterrupt:
                if self.is_running:
                    self.should_cancel = True
                    self.console.print("\n[yellow]⏹ 执行已中断[/yellow]")
                else:
                    self.console.print("\n[dim]提示: 输入 exit 退出程序[/dim]")
                continue
            except EOFError:
                self.console.print("\n[yellow]再见！[/yellow]")
                break

    def _print_welcome(self):
        """打印欢迎信息"""
        self.console.print()
        self.console.print("[bold green]Agent 已就绪[/bold green]")
        self.console.print(f"[dim]会话 ID: {self.agent.session_id}[/dim]")
        self.console.print(f"[dim]导出目录: {self.agent.export_dir}[/dim]")
        self.console.print("[dim]快捷键: Ctrl+C 中断执行，输入 exit 退出[/dim]")
        self.console.print()

    def _handle_command(self, user_input: str) -> bool:
        """处理命令，返回 True 表示已处理"""
        cmd = user_input.lower()

        # 退出命令
        if cmd in ("exit", "quit", "q", "退出"):
            self.console.print("[yellow]再见！[/yellow]")
            raise EOFError()

        # 步骤查看命令 :数字
        if user_input.startswith(":"):
            step_str = user_input[1:]
            if step_str.isdigit():
                self._show_step_detail(int(step_str))
            else:
                self.console.print("[yellow]用法: :步骤号（如 :12）[/yellow]")
            return True

        # 斜杠命令
        if user_input.startswith("/"):
            if cmd == "/clear":
                self.agent.clear_history()
                self.step_pager.clear_history()
                self.step_count = 0
                self.console.print("[green]对话历史已清除。[/green]")
            elif cmd == "/config":
                _print_config(self.console)
            elif cmd == "/steps":
                self._list_steps()
            else:
                self.registry.execute(user_input, self.console)
            return True

        # 旧式命令（向后兼容）
        if cmd == "help":
            self.registry.show_help(self.console)
            return True
        elif cmd == "config":
            _print_config(self.console)
            return True
        elif cmd == "clear":
            self.agent.clear_history()
            self.step_pager.clear_history()
            self.step_count = 0
            self.console.print("[green]对话历史已清除。[/green]")
            return True

        return False

    def _show_step_detail(self, step_num: int):
        """显示步骤详情"""
        step = self.step_pager.get_step(step_num)
        if not step:
            self.console.print(f"[red]步骤 {step_num} 不存在[/red]")
            return

        self.console.print()
        self.console.print(f"[bold cyan]{'─' * 20} Step {step.step_num}: {step.tool_name} {'─' * 20}[/bold cyan]")

        # 显示代码/参数
        if step.tool_name == "execute_python_safe" and "code" in step.tool_args:
            self.console.print("[bold yellow]代码:[/bold yellow]")
            syntax = Syntax(step.tool_args["code"], "python", theme="monokai", line_numbers=True)
            self.console.print(syntax)
        elif step.tool_name == "execute_sql" and "query" in step.tool_args:
            self.console.print("[bold yellow]SQL:[/bold yellow]")
            syntax = Syntax(step.tool_args["query"], "sql", theme="monokai", line_numbers=True)
            self.console.print(syntax)
        else:
            self.console.print("[bold yellow]参数:[/bold yellow]")
            for key, value in step.tool_args.items():
                val_str = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
                self.console.print(f"  {key}: {val_str}")

        if step.result:
            self.console.print()
            self.console.print("[bold yellow]执行结果:[/bold yellow]")
            for line in step.result.split("\n"):
                self.console.print(f"  {line}")

        self.console.print(f"[bold cyan]{'─' * 60}[/bold cyan]")
        self.console.print()

    def _list_steps(self):
        """列出所有步骤"""
        latest = self.step_pager.get_latest_step_num()
        if latest == 0:
            self.console.print("[dim]暂无步骤历史[/dim]")
            return

        table = Table(title="步骤历史", show_header=True)
        table.add_column("步骤", style="cyan", width=6)
        table.add_column("工具", style="yellow")
        table.add_column("时间", style="dim")

        for num in range(1, latest + 1):
            step = self.step_pager.get_step(num)
            if step:
                table.add_row(str(num), step.tool_name, step.timestamp.strftime("%H:%M:%S"))

        self.console.print(table)
        self.console.print("[dim]输入 :步骤号 查看详情（如 :5）[/dim]")

    def _process_input(self, user_input: str):
        """处理用户输入"""
        self.console.print()
        self.is_running = True
        self.should_cancel = False
        self.step_count = 0

        # 当前步骤参数
        current_tool_args = [{}]

        def on_thinking(content: str):
            from ..config.modes import get_mode_manager
            if get_mode_manager().get("verbose"):
                truncated = content[:200] + "..." if len(content) > 200 else content
                self.console.print(f"[dim]{truncated}[/dim]")

        def on_tool_call(tool_name: str, tool_args: dict):
            if self.should_cancel:
                raise InterruptedError("用户中断")

            self.step_count += 1
            current_tool_args[0] = tool_args

            self.console.print(
                f"  [bold cyan]Step {self.step_count}[/bold cyan]  "
                f"[bold yellow]{tool_name}[/bold yellow]"
            )
            format_tool_args_display(tool_name, tool_args, self.console)

        def on_tool_result(tool_name: str, result: str):
            if self.should_cancel:
                raise InterruptedError("用户中断")

            self.step_pager.add_step(self.step_count, tool_name, current_tool_args[0], result)
            format_tool_result(tool_name, result, self.console, step_num=self.step_count)
            self.console.print()

        try:
            self.console.print("[bold blue]思考中...[/bold blue]")
            self.console.print()

            response = self.agent.chat_stream(
                user_input,
                on_thinking=on_thinking,
                on_tool_call=on_tool_call,
                on_tool_result=on_tool_result,
                should_cancel=lambda: self.should_cancel,
            )

            if response:
                self.console.print(Panel(
                    Markdown(response),
                    title="Agent 回复",
                    border_style="green"
                ))

            if self.step_count > 0:
                self.console.print(
                    f"[dim]本次执行了 {self.step_count} 个步骤，"
                    f"输入 :1-:{self.step_count} 查看详情[/dim]"
                )

        except KeyboardInterrupt:
            self.should_cancel = True
            self.console.print("\n[yellow]⏹ 执行已中断[/yellow]")

        except InterruptedError:
            self.console.print("[yellow]⏹ 执行已中断[/yellow]")

        except Exception as e:
            self.console.print(f"[red]处理失败: {e}[/red]")

        finally:
            self.is_running = False
            self.console.print()
