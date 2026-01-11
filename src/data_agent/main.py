"""
CLI 主入口

基于 rich 库的命令行界面，支持模式切换和斜杠命令。
"""

import os
import sys
import logging

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

from .agent.deep_agent import DataAgent
from .config.settings import get_settings
from .config.modes import get_mode_manager
from .commands import register_all_commands
from .ui import StepPager
from .cli import SyncCLI


def setup_langsmith():
    """
    配置 LangSmith 可观测性

    根据 settings 中的配置设置 LangChain 环境变量，
    启用后所有 LLM 调用将自动追踪到 LangSmith。
    """
    settings = get_settings()

    if settings.langsmith_enabled and settings.langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
        return True
    return False


# 初始化 LangSmith（必须在导入 LangChain 相关模块之前）
_langsmith_enabled = setup_langsmith()

# 配置日志
_settings = get_settings()
_log_level = getattr(logging, _settings.log_level.upper(), logging.WARNING)
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def print_welcome(console: Console):
    """打印欢迎信息"""
    welcome_text = """
# 数据分析 Agent

欢迎使用数据分析 Agent！我可以帮助您完成各种数据分析任务：

- **SQL查询**: 支持 MySQL、PostgreSQL
- **数据分析**: 使用 pandas、numpy、scipy
- **机器学习**: 使用 scikit-learn
- **图分析**: 使用 networkx

## 使用说明

1. 直接描述您的数据分析需求
2. 我会自动规划任务步骤
3. 执行分析并返回结果

## 常用命令

输入 `/help` 查看所有可用命令，或使用：

- `/modes` - 查看当前模式状态
- `/plan on|off|auto` - 切换计划模式
- `/safe on|off` - 切换安全模式
- `exit` - 退出程序
"""
    console.print(Panel(Markdown(welcome_text), title="Data Agent", border_style="blue"))


def print_config(console: Console):
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
    """主函数

    同步 CLI：
    - Ctrl+C 中断执行
    - 输入 :数字 查看历史步骤
    - 支持斜杠命令
    - 输入 exit 退出程序
    """
    console = Console()

    # 注册所有命令
    register_all_commands()
    mode_manager = get_mode_manager()

    # 打印欢迎信息
    print_welcome(console)

    # 验证配置
    if not validate_config(console):
        console.print("\n[yellow]警告: 配置不完整，部分功能可能不可用。[/yellow]")

    # 显示当前模式状态
    console.print()
    mode_manager.display_modes(console)

    # 创建步骤历史查看器
    step_pager = StepPager(console)

    # 创建 Agent
    try:
        agent = DataAgent(console=console)
        if _langsmith_enabled:
            settings = get_settings()
            console.print(f"[dim]LangSmith: 已启用 (项目: {settings.langsmith_project})[/dim]")
    except Exception as e:
        console.print(f"[red]Agent 初始化失败: {e}[/red]")
        return 1

    # 创建 CLI 并运行
    cli = SyncCLI(agent, console, step_pager)

    try:
        cli.run()
    except Exception as e:
        console.print(f"\n[red]程序异常: {e}[/red]")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
