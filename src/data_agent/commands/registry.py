"""
命令注册表

管理所有命令的注册和执行。
"""

from typing import Dict, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .base import Command


class CommandRegistry:
    """命令注册表（单例）"""

    _instance: Optional["CommandRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._commands: Dict[str, Command] = {}
            cls._instance._aliases: Dict[str, str] = {}
        return cls._instance

    def register(self, command: Command) -> None:
        """注册命令"""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._aliases[alias] = command.name

    def get(self, name: str) -> Optional[Command]:
        """获取命令"""
        # 先检查别名
        if name in self._aliases:
            name = self._aliases[name]
        return self._commands.get(name)

    def execute(self, input_str: str, console: Console) -> bool:
        """
        解析并执行命令

        Args:
            input_str: 用户输入（以 / 开头）
            console: Rich Console 实例

        Returns:
            是否成功处理
        """
        if not input_str.startswith("/"):
            return False

        parts = input_str[1:].split()
        if not parts:
            return False

        cmd_name = parts[0].lower()
        args = parts[1:]

        command = self.get(cmd_name)
        if command:
            return command.execute(args, console)

        console.print(f"[red]未知命令: /{cmd_name}[/red]")
        console.print("输入 [cyan]/help[/cyan] 查看可用命令")
        return True  # 已处理（虽然是错误）

    def show_help(self, console: Console) -> None:
        """显示所有命令帮助"""
        table = Table(
            title="可用命令",
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("命令", style="cyan", width=22)
        table.add_column("说明", style="white")

        for name in sorted(self._commands.keys()):
            cmd = self._commands[name]
            usage = f"/{name} {cmd.usage}" if cmd.usage else f"/{name}"
            table.add_row(usage, cmd.description)

        console.print(Panel(table, border_style="blue"))

    def list_commands(self) -> Dict[str, Command]:
        """获取所有命令"""
        return self._commands.copy()


def get_registry() -> CommandRegistry:
    """获取命令注册表单例"""
    return CommandRegistry()
