"""
输出格式化函数

提供各种工具结果的格式化显示功能。
"""

import json
import re

from rich.console import Console
from rich.table import Table
from rich.padding import Padding
from rich.syntax import Syntax


def format_todos_result(result: str, console: Console) -> None:
    """格式化 write_todos 结果"""
    try:
        match = re.search(r'\[.*\]', result, re.DOTALL)
        if match:
            json_str = match.group()
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
        console.print(f"    [dim]{result[:200]}...[/dim]" if len(result) > 200 else f"    [dim]{result}[/dim]")


def format_sql_result(result: str, console: Console, max_rows: int = 15, step_num: int = 0) -> None:
    """格式化 SQL 查询结果为表格"""
    lines = result.strip().split("\n")

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

    try:
        header_line = None
        data_rows = []

        for line in data_lines:
            line = line.strip()
            if not line:
                continue

            if re.match(r'^\d+\s+', line):
                parts = re.split(r'\s{2,}', line.strip())
                if parts:
                    data_rows.append(parts[1:] if len(parts) > 1 else parts)
            elif header_line is None and line:
                header_line = line

        if header_line:
            headers = re.split(r'\s{2,}', header_line.strip())
            total_rows = len(data_rows)
            console.print(f"    [bold blue]SQL 查询结果 ({total_rows} 行):[/bold blue]")

            table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
            for header in headers:
                table.add_column(header)

            shown_rows = 0
            for row in data_rows:
                if shown_rows >= max_rows:
                    break
                while len(row) < len(headers):
                    row.append("")
                table.add_row(*row[:len(headers)])
                shown_rows += 1

            console.print(Padding(table, (0, 0, 0, 4)))

            if len(data_rows) > max_rows:
                hint = f"，输入 :{step_num} 查看完整内容" if step_num > 0 else ""
                console.print(f"    [dim]... 还有 {len(data_rows) - max_rows} 行未显示{hint}[/dim]")
            return

    except Exception:
        pass

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

    views = [t for t in tables if t.endswith(("_list", "_info", "v_"))]
    regular = [t for t in tables if t not in views]

    if regular:
        console.print(f"    [bold]数据表 ({len(regular)}):[/bold]")
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

    try:
        data_start = 0
        for i, line in enumerate(lines):
            if "Field" in line and "Type" in line:
                data_start = i
                break

        if data_start < len(lines):
            table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
            table.add_column("字段", style="cyan")
            table.add_column("类型", style="yellow")
            table.add_column("可空")
            table.add_column("键")

            for line in lines[data_start + 1:]:
                if re.match(r'^\d+\s+', line.strip()):
                    parts = re.split(r'\s{2,}', line.strip())
                    if len(parts) >= 3:
                        field = parts[1] if len(parts) > 1 else ""
                        dtype = parts[2] if len(parts) > 2 else ""
                        nullable = parts[3] if len(parts) > 3 else ""
                        key = parts[4] if len(parts) > 4 else ""
                        table.add_row(field, dtype, nullable, key)

            console.print(Padding(table, (0, 0, 0, 4)))
            return

    except Exception:
        pass

    preview = result[:500] + "..." if len(result) > 500 else result
    console.print(f"    [dim]{preview}[/dim]")


def format_default_result(result: str, console: Console, max_length: int = 500) -> None:
    """默认结果格式化"""
    result = result.strip()
    if len(result) > max_length:
        console.print(f"    [dim]{result[:max_length]}...[/dim]")
    else:
        for line in result.split("\n")[:20]:
            console.print(f"    [dim]{line}[/dim]")
        if result.count("\n") > 20:
            console.print(f"    [dim]... 还有更多内容[/dim]")


def format_python_result(result: str, console: Console, step_num: int = 0) -> None:
    """格式化 Python 执行结果"""
    result = result.strip()
    lines = result.split("\n")

    console.print("    [bold green]Python 执行结果:[/bold green]")

    max_lines = 20
    for line in lines[:max_lines]:
        console.print(f"    {line}")

    if len(lines) > max_lines:
        hint = f"，输入 :{step_num} 查看完整内容" if step_num > 0 else ""
        console.print(f"    [dim]... 还有 {len(lines) - max_lines} 行{hint}[/dim]")


def format_tool_result(tool_name: str, result: str, console: Console, step_num: int = 0) -> None:
    """根据工具类型格式化结果"""
    if tool_name == "write_todos":
        format_todos_result(result, console)
        return

    if tool_name == "execute_sql":
        format_sql_result(result, console, step_num=step_num)
        return

    if tool_name == "execute_python_safe":
        format_python_result(result, console, step_num=step_num)
        return

    if tool_name == "list_tables":
        console.print("    [bold blue]数据库表列表:[/bold blue]")
        format_table_list(result, console)
        return

    if tool_name == "describe_table":
        console.print("    [bold blue]表结构信息:[/bold blue]")
        format_describe_result(result, console)
        return

    if tool_name == "get_database_schema":
        console.print("    [bold blue]数据库结构:[/bold blue]")
        format_default_result(result, console)
        return

    format_default_result(result, console)


def format_sql_query(query: str, console: Console) -> None:
    """格式化显示 SQL 查询"""
    query = query.strip()
    syntax = Syntax(query, "sql", theme="monokai", line_numbers=False, word_wrap=True)
    console.print(Padding(syntax, (0, 0, 0, 4)))


def format_tool_args_display(tool_name: str, args: dict, console: Console) -> None:
    """格式化显示工具参数"""
    if not args:
        return

    if "query" in args and tool_name == "execute_sql":
        format_sql_query(args["query"], console)
        other_args = {k: v for k, v in args.items() if k != "query"}
        if other_args:
            for key, value in other_args.items():
                console.print(f"    [dim]{key}:[/dim] {value}")
        return

    if tool_name == "write_todos" and "todos" in args:
        todos = args["todos"]
        if isinstance(todos, list):
            console.print("    [dim]更新任务列表...[/dim]")
            return

    for key, value in args.items():
        value_str = str(value)
        if len(value_str) > 100:
            value_str = value_str[:100] + "..."
        console.print(f"    [dim]{key}:[/dim] {value_str}")
