"""
CLI主入口

基于rich库的命令行界面，支持模式切换和斜杠命令。
"""

import sys
import logging
import json
import re

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.spinner import Spinner
from rich.padding import Padding
from rich.syntax import Syntax

from .agent.deep_agent import DataAgent
from .config.settings import get_settings
from .config.modes import get_mode_manager
from .commands import get_registry, register_all_commands

# 配置日志 - 默认只显示警告级别，减少噪音
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# 禁用 httpx 的详细日志
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


def print_help(console: Console):
    """打印帮助信息"""
    help_table = Table(title="命令帮助")
    help_table.add_column("命令", style="cyan")
    help_table.add_column("说明", style="white")

    help_table.add_row("help", "显示帮助信息")
    help_table.add_row("clear", "清除对话历史")
    help_table.add_row("config", "显示配置信息")
    help_table.add_row("exit / quit / q", "退出程序")

    console.print(help_table)


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


# ==================== 输出格式化函数 ====================

def format_todos_result(result: str, console: Console) -> None:
    """格式化 write_todos 结果"""
    # 尝试解析 JSON 格式的 todos
    try:
        # 从结果中提取 JSON 列表
        match = re.search(r'\[.*\]', result, re.DOTALL)
        if match:
            json_str = match.group()
            # 将单引号转换为双引号以兼容 Python 格式
            json_str = json_str.replace("'", '"')
            todos = json.loads(json_str)
        else:
            console.print(f"    [dim]{result[:200]}...[/dim]" if len(result) > 200 else f"    [dim]{result}[/dim]")
            return

        console.print("    [bold]任务进度:[/bold]")
        for todo in todos:
            content = todo.get("content", "")
            status = todo.get("status", "pending")

            if status == "completed":
                console.print(f"    [green]✓[/green] [dim]{content}[/dim]")
            elif status == "in_progress":
                console.print(f"    [yellow]→[/yellow] [bold]{content}[/bold]")
            else:
                console.print(f"    [dim]○[/dim] {content}")

    except (json.JSONDecodeError, TypeError):
        # 如果解析失败，显示原始结果
        console.print(f"    [dim]{result[:200]}...[/dim]" if len(result) > 200 else f"    [dim]{result}[/dim]")


def format_sql_result(result: str, console: Console, max_rows: int = 15) -> None:
    """格式化 SQL 查询结果为表格"""
    lines = result.strip().split("\n")

    # 跳过前缀（如 "查询结果:"）
    data_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith(("查询结果", "Query result")):
            data_start = i + 1
            break

    if data_start >= len(lines):
        console.print(f"    [dim]{result[:300]}[/dim]")
        return

    data_lines = lines[data_start:]
    if not data_lines:
        console.print(f"    [dim]{result[:300]}[/dim]")
        return

    # 解析表格数据
    try:
        # 尝试解析 DataFrame 格式的输出
        # 格式通常是: "   col1  col2  col3" (header) 然后 "0  val1  val2  val3" (rows)
        header_line = None
        data_rows = []

        for line in data_lines:
            line = line.strip()
            if not line:
                continue

            # 检测是否是带索引的数据行（以数字开头）
            if re.match(r'^\d+\s+', line):
                # 移除索引列
                parts = re.split(r'\s{2,}', line.strip())
                if parts:
                    data_rows.append(parts[1:] if len(parts) > 1 else parts)
            elif header_line is None and line:
                # 第一行非空行作为表头
                header_line = line

        if header_line:
            # 解析表头
            headers = re.split(r'\s{2,}', header_line.strip())

            # 创建 Rich Table
            table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))

            for header in headers:
                table.add_column(header)

            # 添加数据行（限制行数）
            shown_rows = 0
            for row in data_rows:
                if shown_rows >= max_rows:
                    break
                # 确保列数匹配
                while len(row) < len(headers):
                    row.append("")
                table.add_row(*row[:len(headers)])
                shown_rows += 1

            console.print(Padding(table, (0, 0, 0, 4)))

            if len(data_rows) > max_rows:
                console.print(f"    [dim]... 还有 {len(data_rows) - max_rows} 行未显示[/dim]")

            return

    except Exception:
        pass

    # 如果解析失败，显示原始结果
    preview = result[:500] + "..." if len(result) > 500 else result
    console.print(f"    [dim]{preview}[/dim]")


def format_table_list(result: str, console: Console) -> None:
    """格式化表列表"""
    lines = result.strip().split("\n")

    tables = []
    for line in lines:
        line = line.strip()
        if line.startswith("-"):
            table_name = line[1:].strip()
            tables.append(table_name)
        elif line and not line.startswith(("数据库", "Database")):
            tables.append(line)

    if not tables:
        console.print(f"    [dim]{result}[/dim]")
        return

    # 分类显示
    views = [t for t in tables if t.endswith(("_list", "_info", "v_"))]
    regular = [t for t in tables if t not in views]

    if regular:
        console.print(f"    [bold]数据表 ({len(regular)}):[/bold]")
        # 每行显示多个表名
        for i in range(0, len(regular), 4):
            row = regular[i:i+4]
            console.print("    " + "  ".join(f"[cyan]{t}[/cyan]" for t in row))

    if views:
        console.print(f"    [bold]视图 ({len(views)}):[/bold]")
        for i in range(0, len(views), 4):
            row = views[i:i+4]
            console.print("    " + "  ".join(f"[dim cyan]{t}[/dim cyan]" for t in row))


def format_describe_result(result: str, console: Console) -> None:
    """格式化表结构描述"""
    lines = result.strip().split("\n")

    # 解析列信息
    try:
        # 跳过标题行（如 "表 xxx 的结构:"）
        data_start = 0
        for i, line in enumerate(lines):
            if "Field" in line and "Type" in line:
                data_start = i
                break

        if data_start < len(lines):
            # 创建表格
            table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
            table.add_column("字段", style="cyan")
            table.add_column("类型", style="yellow")
            table.add_column("可空")
            table.add_column("键")

            for line in lines[data_start + 1:]:
                # DataFrame 格式: "0  field_name  type  null  key  default  extra"
                if re.match(r'^\d+\s+', line.strip()):
                    parts = re.split(r'\s{2,}', line.strip())
                    if len(parts) >= 3:
                        # 跳过索引列
                        field = parts[1] if len(parts) > 1 else ""
                        dtype = parts[2] if len(parts) > 2 else ""
                        nullable = parts[3] if len(parts) > 3 else ""
                        key = parts[4] if len(parts) > 4 else ""
                        table.add_row(field, dtype, nullable, key)

            console.print(Padding(table, (0, 0, 0, 4)))
            return

    except Exception:
        pass

    # 回退到默认显示
    preview = result[:500] + "..." if len(result) > 500 else result
    console.print(f"    [dim]{preview}[/dim]")


def format_default_result(result: str, console: Console, max_length: int = 500) -> None:
    """默认结果格式化"""
    result = result.strip()
    if len(result) > max_length:
        console.print(f"    [dim]{result[:max_length]}...[/dim]")
    else:
        # 多行结果缩进显示
        for line in result.split("\n")[:20]:  # 最多显示20行
            console.print(f"    [dim]{line}[/dim]")
        if result.count("\n") > 20:
            console.print(f"    [dim]... 还有更多内容[/dim]")


def format_tool_result(tool_name: str, result: str, console: Console) -> None:
    """根据工具类型格式化结果"""
    # write_todos 结果
    if tool_name == "write_todos":
        format_todos_result(result, console)
        return

    # SQL 查询结果
    if tool_name == "execute_sql":
        format_sql_result(result, console)
        return

    # 表列表
    if tool_name == "list_tables":
        format_table_list(result, console)
        return

    # 表结构
    if tool_name == "describe_table":
        format_describe_result(result, console)
        return

    # 默认格式
    format_default_result(result, console)


def format_sql_query(query: str, console: Console) -> None:
    """格式化显示 SQL 查询"""
    # 清理查询
    query = query.strip()

    # 使用 Syntax 高亮显示
    syntax = Syntax(query, "sql", theme="monokai", line_numbers=False, word_wrap=True)
    console.print(Padding(syntax, (0, 0, 0, 4)))


def format_tool_args_display(tool_name: str, args: dict, console: Console) -> None:
    """格式化显示工具参数"""
    if not args:
        return

    # SQL 查询特殊处理
    if "query" in args and tool_name == "execute_sql":
        format_sql_query(args["query"], console)
        # 显示其他参数
        other_args = {k: v for k, v in args.items() if k != "query"}
        if other_args:
            for key, value in other_args.items():
                console.print(f"    [dim]{key}:[/dim] {value}")
        return

    # todos 参数特殊处理
    if tool_name == "write_todos" and "todos" in args:
        todos = args["todos"]
        if isinstance(todos, list):
            console.print("    [dim]更新任务列表...[/dim]")
            return

    # 默认参数显示
    for key, value in args.items():
        value_str = str(value)
        if len(value_str) > 100:
            value_str = value_str[:100] + "..."
        console.print(f"    [dim]{key}:[/dim] {value_str}")


# ==================== 主函数 ====================

def main():
    """主函数"""
    console = Console()

    # 注册所有命令
    register_all_commands()
    registry = get_registry()
    mode_manager = get_mode_manager()

    # 打印欢迎信息
    print_welcome(console)

    # 验证配置
    if not validate_config(console):
        console.print("\n[yellow]警告: 配置不完整，部分功能可能不可用。[/yellow]")

    # 显示当前模式状态
    console.print()
    mode_manager.display_modes(console)

    # 创建 Agent
    agent = None
    try:
        agent = DataAgent(console=console)
        console.print("\n[green]Agent 已就绪，请输入您的需求...[/green]\n")
    except Exception as e:
        console.print(f"[red]Agent 初始化失败: {e}[/red]")
        return 1

    # 主循环
    while True:
        try:
            # 获取用户输入
            user_input = Prompt.ask("[bold cyan]您[/bold cyan]")

            if not user_input.strip():
                continue

            # 处理斜杠命令
            if user_input.strip().startswith("/"):
                cmd_input = user_input.strip()

                # 特殊处理需要访问 agent 的命令
                if cmd_input.lower() == "/clear":
                    agent.clear_history()
                    console.print("[green]对话历史已清除。[/green]")
                    continue
                elif cmd_input.lower() == "/config":
                    print_config(console)
                    continue

                # 使用命令注册表处理其他命令
                registry.execute(cmd_input, console)
                continue

            # 处理退出命令（保持向后兼容）
            cmd = user_input.strip().lower()
            if cmd in ["exit", "quit", "q", "退出"]:
                console.print("[yellow]再见！[/yellow]")
                break

            # 处理旧式命令（保持向后兼容）
            if cmd == "help":
                registry.show_help(console)
                continue
            elif cmd == "config":
                print_config(console)
                continue
            elif cmd == "clear":
                agent.clear_history()
                console.print("[green]对话历史已清除。[/green]")
                continue

            # 处理用户输入 - 显示思考过程
            console.print()  # 空行
            step_count = [0]  # 使用列表以便在闭包中修改

            def on_thinking(content: str):
                """显示思考内容（verbose 模式下）"""
                # verbose 模式的判断在 DataAgent 中处理
                console.print(f"[dim]{content[:200]}...[/dim]" if len(content) > 200 else f"[dim]{content}[/dim]")

            def on_tool_call(tool_name: str, tool_args: dict):
                """显示工具调用"""
                step_count[0] += 1
                console.print(
                    f"  [bold cyan]Step {step_count[0]}[/bold cyan]  "
                    f"[bold yellow]{tool_name}[/bold yellow]"
                )
                format_tool_args_display(tool_name, tool_args, console)

            def on_tool_result(tool_name: str, result: str):
                """显示工具结果"""
                format_tool_result(tool_name, result, console)
                console.print()  # 空行分隔

            try:
                console.print("[bold blue]思考中...[/bold blue]")
                console.print()

                response = agent.chat_stream(
                    user_input,
                    on_thinking=on_thinking,
                    on_tool_call=on_tool_call,
                    on_tool_result=on_tool_result,
                )

            except Exception as e:
                logger.error(f"处理失败: {e}")
                console.print(f"[red]处理失败: {e}[/red]")
                continue

            # 显示最终响应
            if response:
                console.print(Panel(
                    Markdown(response),
                    title="Agent 回复",
                    border_style="green"
                ))
            console.print()  # 空行

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
