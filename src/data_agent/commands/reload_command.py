"""
配置重载命令

手动重载 Agent 配置文件。
"""

from typing import List

from rich.console import Console

from .base import Command


class ReloadCommand(Command):
    """配置重载命令"""

    name = "reload"
    aliases = ["r"]
    description = "重新加载 Agent 配置文件"
    usage = ""

    def execute(self, args: List[str], console: Console) -> bool:
        """执行配置重载"""
        from ..config.loader import reload_agent_config, get_config_loader
        from ..tools.registry import get_tool_registry

        try:
            # 重新加载配置
            config = reload_agent_config()

            # 重置并重新应用工具配置
            registry = get_tool_registry()
            registry.reset()
            registry.apply_config(config.tools)

            # 获取配置路径
            loader = get_config_loader()
            config_path = loader.config_path

            console.print("[green]✓[/green] 配置已重新加载")

            if config_path:
                console.print(f"  配置文件: [cyan]{config_path}[/cyan]")

            # 显示加载的子代理
            if config.subagents:
                subagent_names = list(config.subagents.keys())
                console.print(f"  子代理: [cyan]{', '.join(subagent_names)}[/cyan]")
            else:
                console.print("  子代理: [dim]使用默认配置[/dim]")

            # 显示 LLM profiles
            profile_names = list(config.llm.profiles.keys())
            if profile_names:
                console.print(f"  LLM Profiles: [cyan]{', '.join(profile_names)}[/cyan]")

            console.print()
            console.print("[dim]注意: 重载配置不会影响当前会话的 Agent 实例。[/dim]")
            console.print("[dim]新配置将在下次创建 Agent 时生效。[/dim]")

            return True

        except Exception as e:
            console.print(f"[red]配置重载失败: {e}[/red]")
            return True


class ConfigCommand(Command):
    """显示当前配置命令"""

    name = "config"
    aliases = ["cfg"]
    description = "显示当前 Agent 配置信息"
    usage = ""

    def execute(self, args: List[str], console: Console) -> bool:
        """显示配置信息"""
        from rich.table import Table
        from rich.panel import Panel

        from ..config.loader import get_config_loader
        from ..config.settings import get_settings

        loader = get_config_loader()
        config = loader.config
        settings = get_settings()

        # 基础配置表格
        basic_table = Table(show_header=False, box=None, padding=(0, 2))
        basic_table.add_column("Key", style="cyan")
        basic_table.add_column("Value", style="white")

        basic_table.add_row("配置文件", str(loader.config_path) if loader.config_path else "无")
        basic_table.add_row("配置版本", config.version)
        basic_table.add_row("热重载", "启用" if config.hot_reload.enabled else "禁用")

        console.print(Panel(basic_table, title="基础配置", border_style="blue"))

        # LLM 配置表格
        llm_table = Table(show_header=True, header_style="bold")
        llm_table.add_column("Profile", style="cyan")
        llm_table.add_column("Model", style="white")
        llm_table.add_column("Temperature", style="white")

        # 默认配置
        default_llm = config.llm.default
        llm_table.add_row(
            "default",
            default_llm.model or settings.model,
            str(default_llm.temperature),
        )

        # 其他 profiles
        for name, profile in config.llm.profiles.items():
            llm_table.add_row(
                name,
                profile.model,
                str(profile.temperature),
            )

        console.print(Panel(llm_table, title="LLM Profiles", border_style="green"))

        # 子代理配置表格
        if config.subagents:
            subagent_table = Table(show_header=True, header_style="bold")
            subagent_table.add_column("名称", style="cyan")
            subagent_table.add_column("LLM", style="white")
            subagent_table.add_column("工具数量", style="white")
            subagent_table.add_column("描述", style="dim", max_width=40)

            for name, subagent in config.subagents.items():
                subagent_table.add_row(
                    name,
                    subagent.llm,
                    str(len(subagent.tools)),
                    subagent.description[:40] + "..." if len(subagent.description) > 40 else subagent.description,
                )

            console.print(Panel(subagent_table, title="子代理配置", border_style="yellow"))
        else:
            console.print("[dim]未配置子代理，使用默认配置[/dim]")

        # 工具配置
        tools = config.tools.builtin
        tool_status = []
        if tools.sql_tools:
            tool_status.append("[green]SQL[/green]")
        else:
            tool_status.append("[red]SQL[/red]")

        if tools.python_tools:
            tool_status.append("[green]Python[/green]")
        else:
            tool_status.append("[red]Python[/red]")

        if tools.ml_tools:
            tool_status.append("[green]ML[/green]")
        else:
            tool_status.append("[red]ML[/red]")

        if tools.graph_tools:
            tool_status.append("[green]Graph[/green]")
        else:
            tool_status.append("[red]Graph[/red]")

        console.print(f"\n工具组: {' | '.join(tool_status)}")

        return True
