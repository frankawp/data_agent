"""
模式切换命令

实现各种模式的切换命令。
"""

from typing import List

from rich.console import Console
from rich.prompt import Confirm

from .base import Command
from .registry import get_registry
from ..config.modes import get_mode_manager, MODE_DEFINITIONS


class PlanCommand(Command):
    """Plan Mode 切换命令"""

    name = "plan"
    description = "切换计划模式"
    usage = "on|off|auto"

    def execute(self, args: List[str], console: Console) -> bool:
        manager = get_mode_manager()

        if not args:
            current = manager.get("plan")
            console.print(f"当前计划模式: [yellow]{current.value}[/yellow]")
            console.print()
            console.print("  [cyan]off[/cyan]  - 直接执行任务")
            console.print("  [cyan]on[/cyan]   - 先生成计划，确认后执行")
            console.print("  [cyan]auto[/cyan] - 复杂任务自动进入规划")
            return True

        value = args[0].lower()
        if value not in ["on", "off", "auto"]:
            console.print(f"[red]无效值: {value}[/red]")
            console.print("允许值: on, off, auto")
            return True

        if manager.set("plan", value):
            console.print(f"[green]计划模式已设置为: {value}[/green]")
        else:
            console.print("[red]设置失败[/red]")

        return True


class AutoCommand(Command):
    """Auto Execute 切换命令"""

    name = "auto"
    description = "切换自动执行模式"
    usage = "on|off"

    def execute(self, args: List[str], console: Console) -> bool:
        manager = get_mode_manager()

        if not args:
            current = manager.get("auto")
            status = "[green]ON[/green]" if current else "[red]OFF[/red]"
            console.print(f"自动执行: {status}")
            console.print()
            console.print("  [cyan]on[/cyan]  - 自动执行工具调用")
            console.print("  [cyan]off[/cyan] - 每次工具调用前需确认")
            return True

        value = args[0].lower()
        if value not in ["on", "off"]:
            console.print(f"[red]无效值: {value}[/red]")
            console.print("允许值: on, off")
            return True

        if manager.set("auto", value == "on"):
            status = "[green]ON[/green]" if value == "on" else "[red]OFF[/red]"
            console.print(f"自动执行已设置为: {status}")
        else:
            console.print("[red]设置失败[/red]")

        return True


class SafeCommand(Command):
    """Safe Mode 切换命令"""

    name = "safe"
    description = "切换安全模式"
    usage = "on|off"

    def execute(self, args: List[str], console: Console) -> bool:
        manager = get_mode_manager()

        if not args:
            current = manager.get("safe")
            status = "[green]ON[/green]" if current else "[red]OFF[/red]"
            console.print(f"安全模式: {status}")
            if current:
                console.print("  [dim]危险 SQL 操作（DROP/DELETE/UPDATE）将被阻止[/dim]")
            else:
                console.print("  [yellow]警告: 安全模式已关闭，请谨慎操作[/yellow]")
            return True

        value = args[0].lower()
        if value not in ["on", "off"]:
            console.print(f"[red]无效值: {value}[/red]")
            console.print("允许值: on, off")
            return True

        if value == "off":
            # 关闭安全模式需要二次确认
            console.print("[yellow]警告: 关闭安全模式将允许执行危险 SQL 操作！[/yellow]")
            if not Confirm.ask("确定关闭？", default=False):
                console.print("已取消")
                return True

        if manager.set("safe", value == "on"):
            status = "[green]ON[/green]" if value == "on" else "[red]OFF[/red]"
            console.print(f"安全模式已设置为: {status}")
        else:
            console.print("[red]设置失败[/red]")

        return True


class VerboseCommand(Command):
    """Verbose Mode 切换命令"""

    name = "verbose"
    aliases = ["v"]
    description = "切换详细输出模式"
    usage = "on|off"

    def execute(self, args: List[str], console: Console) -> bool:
        manager = get_mode_manager()

        if not args:
            current = manager.get("verbose")
            status = "[green]ON[/green]" if current else "[red]OFF[/red]"
            console.print(f"详细输出: {status}")
            return True

        value = args[0].lower()
        if value not in ["on", "off"]:
            console.print(f"[red]无效值: {value}[/red]")
            console.print("允许值: on, off")
            return True

        if manager.set("verbose", value == "on"):
            status = "[green]ON[/green]" if value == "on" else "[red]OFF[/red]"
            console.print(f"详细输出已设置为: {status}")
        else:
            console.print("[red]设置失败[/red]")

        return True


class PreviewCommand(Command):
    """Preview Limit 设置命令"""

    name = "preview"
    description = "设置数据预览行数"
    usage = "10|50|100|all"

    def execute(self, args: List[str], console: Console) -> bool:
        manager = get_mode_manager()

        if not args:
            current = manager.get("preview")
            console.print(f"当前预览行数: [yellow]{current.value}[/yellow]")
            console.print()
            console.print("可选值: 10, 50, 100, all")
            return True

        value = args[0].lower()
        if value not in ["10", "50", "100", "all"]:
            console.print(f"[red]无效值: {value}[/red]")
            console.print("允许值: 10, 50, 100, all")
            return True

        if manager.set("preview", value):
            console.print(f"[green]预览行数已设置为: {value}[/green]")
        else:
            console.print("[red]设置失败[/red]")

        return True


class ExportCommand(Command):
    """Export Mode 切换命令"""

    name = "export"
    description = "切换自动导出模式"
    usage = "on|off"

    def execute(self, args: List[str], console: Console) -> bool:
        manager = get_mode_manager()

        if not args:
            current = manager.get("export")
            status = "[green]ON[/green]" if current else "[red]OFF[/red]"
            console.print(f"自动导出: {status}")
            if current:
                console.print("  [dim]查询结果将自动保存到文件[/dim]")
            return True

        value = args[0].lower()
        if value not in ["on", "off"]:
            console.print(f"[red]无效值: {value}[/red]")
            console.print("允许值: on, off")
            return True

        if manager.set("export", value == "on"):
            status = "[green]ON[/green]" if value == "on" else "[red]OFF[/red]"
            console.print(f"自动导出已设置为: {status}")
        else:
            console.print("[red]设置失败[/red]")

        return True


class ModesCommand(Command):
    """显示所有模式状态"""

    name = "modes"
    aliases = ["status", "m"]
    description = "显示当前所有模式状态"

    def execute(self, args: List[str], console: Console) -> bool:
        manager = get_mode_manager()
        manager.display_modes(console)
        return True


class HelpCommand(Command):
    """帮助命令"""

    name = "help"
    aliases = ["h", "?"]
    description = "显示帮助信息"

    def execute(self, args: List[str], console: Console) -> bool:
        get_registry().show_help(console)
        return True


class ClearCommand(Command):
    """清除对话历史"""

    name = "clear"
    description = "清除对话历史"

    def execute(self, args: List[str], console: Console) -> bool:
        # 这个命令需要访问 agent，将在 main.py 中特殊处理
        # 这里只返回 False 表示需要特殊处理
        return False


class ResetCommand(Command):
    """重置所有模式"""

    name = "reset"
    description = "重置所有模式为默认值"

    def execute(self, args: List[str], console: Console) -> bool:
        if Confirm.ask("确定重置所有模式为默认值？", default=False):
            manager = get_mode_manager()
            manager.reset_to_defaults()
            console.print("[green]所有模式已重置为默认值[/green]")
            manager.display_modes(console)
        else:
            console.print("已取消")
        return True


def register_all_commands() -> None:
    """注册所有命令"""
    from .reload_command import ReloadCommand, ConfigCommand as NewConfigCommand

    registry = get_registry()

    # 模式命令
    registry.register(PlanCommand())
    registry.register(AutoCommand())
    registry.register(SafeCommand())
    registry.register(VerboseCommand())
    registry.register(PreviewCommand())
    registry.register(ExportCommand())
    registry.register(ModesCommand())
    registry.register(ResetCommand())

    # 系统命令
    registry.register(HelpCommand())
    registry.register(ClearCommand())

    # 配置命令（使用新的实现）
    registry.register(NewConfigCommand())
    registry.register(ReloadCommand())
