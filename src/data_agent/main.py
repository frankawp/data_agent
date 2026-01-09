"""
CLI主入口

基于rich库的命令行界面。
"""

import sys
import logging
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner

from .agent.core import DataAgent
from .config.settings import get_settings
from .state.graph_state import create_initial_state, AgentPhase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def print_welcome(console: Console):
    """打印欢迎信息"""
    welcome_text = """
# 数据开发Agent

欢迎使用数据开发Agent！我可以帮助您完成各种数据分析任务：

- **SQL查询**: 支持MySQL、PostgreSQL、DuckDB
- **Python执行**: 在安全沙箱中运行代码
- **数据分析**: 使用pandas、numpy、scipy
- **机器学习**: 使用scikit-learn
- **图分析**: 使用networkx

## 使用说明

1. 直接描述您的数据分析需求
2. 我会与您确认需求细节
3. 生成执行计划供您确认
4. 执行并返回结果

## 常用命令

- `help` - 显示帮助
- `status` - 显示当前状态
- `clear` - 清除对话历史
- `exit` - 退出程序
"""
    console.print(Panel(Markdown(welcome_text), title="Data Agent", border_style="blue"))


def print_help(console: Console):
    """打印帮助信息"""
    help_table = Table(title="命令帮助")
    help_table.add_column("命令", style="cyan")
    help_table.add_column("说明", style="white")

    help_table.add_row("help", "显示帮助信息")
    help_table.add_row("status", "显示当前状态")
    help_table.add_row("clear", "清除对话历史")
    help_table.add_row("config", "显示配置信息")
    help_table.add_row("exit / quit / q", "退出程序")

    console.print(help_table)


def print_status(console: Console, state: dict):
    """打印当前状态"""
    status_table = Table(title="当前状态")
    status_table.add_column("项目", style="cyan")
    status_table.add_column("值", style="white")

    phase = state.get("current_phase", AgentPhase.CONVERSATION)
    if isinstance(phase, AgentPhase):
        phase = phase.value

    status_table.add_row("当前阶段", phase)
    status_table.add_row("消息数量", str(len(state.get("messages", []))))
    status_table.add_row("迭代次数", str(state.get("iteration_count", 0)))
    status_table.add_row("是否有计划", "是" if state.get("dag_plan") else "否")
    status_table.add_row("错误", state.get("error") or "无")

    console.print(status_table)


def print_config(console: Console):
    """打印配置信息"""
    settings = get_settings()

    config_table = Table(title="配置信息")
    config_table.add_column("配置项", style="cyan")
    config_table.add_column("值", style="white")

    config_table.add_row("模型", settings.zhipu_model)
    config_table.add_row("API地址", settings.zhipu_base_url)
    config_table.add_row("数据库类型", settings.get_db_type())
    config_table.add_row("沙箱启用", "是" if settings.sandbox_enabled else "否")
    config_table.add_row("DuckDB内存限制", settings.duckdb_memory_limit)
    config_table.add_row("最大迭代次数", str(settings.max_iterations))

    console.print(config_table)


def validate_config(console: Console) -> bool:
    """验证配置"""
    settings = get_settings()
    errors = settings.validate_config()

    if errors:
        console.print("[red]配置错误:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        console.print("\n请检查.env文件或环境变量配置。")
        return False

    return True


def main():
    """主函数"""
    console = Console()

    # 打印欢迎信息
    print_welcome(console)

    # 验证配置
    if not validate_config(console):
        console.print("\n[yellow]警告: 配置不完整，部分功能可能不可用。[/yellow]")

    # 创建Agent
    try:
        agent = DataAgent()
    except Exception as e:
        console.print(f"[red]Agent初始化失败: {e}[/red]")
        return 1

    # 初始化状态
    state = create_initial_state()

    console.print("\n[green]Agent已就绪，请输入您的需求...[/green]\n")

    # 主循环
    while True:
        try:
            # 获取用户输入
            user_input = Prompt.ask("[bold cyan]您[/bold cyan]")

            if not user_input.strip():
                continue

            # 处理命令
            cmd = user_input.strip().lower()

            if cmd in ["exit", "quit", "q", "退出"]:
                console.print("[yellow]再见！[/yellow]")
                break

            elif cmd == "help":
                print_help(console)
                continue

            elif cmd == "status":
                print_status(console, state)
                continue

            elif cmd == "config":
                print_config(console)
                continue

            elif cmd == "clear":
                state = create_initial_state()
                console.print("[green]对话历史已清除。[/green]")
                continue

            # 处理用户输入
            with console.status("[bold green]思考中...[/bold green]", spinner="dots"):
                try:
                    response, state = agent.chat(user_input, state)
                except Exception as e:
                    logger.error(f"处理失败: {e}")
                    console.print(f"[red]处理失败: {e}[/red]")
                    continue

            # 显示响应
            if response:
                console.print(Panel(
                    Markdown(response),
                    title="Agent",
                    border_style="green"
                ))

        except KeyboardInterrupt:
            console.print("\n[yellow]已中断。输入 'exit' 退出。[/yellow]")
            continue

        except EOFError:
            console.print("\n[yellow]再见！[/yellow]")
            break

        except Exception as e:
            logger.error(f"未知错误: {e}")
            console.print(f"[red]发生错误: {e}[/red]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
