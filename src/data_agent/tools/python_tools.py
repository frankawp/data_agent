"""
Python执行工具

在安全沙箱中执行Python代码。
"""

import asyncio
import logging
from typing import Optional

from langchain_core.tools import tool

from ..sandbox.microsandbox import DataAgentSandbox, execute_python_sync

logger = logging.getLogger(__name__)


@tool
def execute_python_safe(code: str, timeout: int = 30) -> str:
    """
    在安全沙箱中执行Python代码

    代码将在隔离的环境中执行，可以使用pandas、numpy、scipy等
    数据分析库。执行结果通过print输出。

    **重要**：如需保存文件，必须使用预定义的 EXPORT_DIR 变量作为保存目录。
    这样文件才能被正确导出，用户才能下载。

    Args:
        code: Python代码
        timeout: 执行超时时间（秒），默认30秒

    Returns:
        代码执行输出

    示例:
        # 数据处理
        execute_python_safe('''
        import pandas as pd
        import numpy as np

        data = {'name': ['Alice', 'Bob'], 'age': [25, 30]}
        df = pd.DataFrame(data)
        print(df.describe())
        ''')

        # 保存文件到导出目录（重要：必须使用 EXPORT_DIR）
        execute_python_safe('''
        import pandas as pd
        import os

        df = pd.DataFrame({'x': [1,2,3], 'y': [4,5,6]})
        # EXPORT_DIR 是预定义的导出目录路径
        filepath = os.path.join(EXPORT_DIR, 'result.csv')
        df.to_csv(filepath, index=False)
        print(f"文件已保存到: {filepath}")
        ''')

        # 保存图表
        execute_python_safe('''
        import matplotlib.pyplot as plt
        import os

        plt.figure()
        plt.plot([1,2,3], [4,5,6])
        filepath = os.path.join(EXPORT_DIR, 'chart.png')
        plt.savefig(filepath)
        print(f"图表已保存到: {filepath}")
        ''')
    """
    result = execute_python_sync(code, timeout=timeout)

    if result.success:
        output = result.output
        if result.error:
            output += f"\n警告: {result.error}"
        return output if output else "代码执行成功，无输出"
    else:
        return f"执行失败: {result.error}"


@tool
async def execute_python_async(code: str, timeout: int = 30) -> str:
    """
    异步执行Python代码

    与execute_python_safe相同，但支持异步执行。

    Args:
        code: Python代码
        timeout: 执行超时时间（秒）

    Returns:
        代码执行输出
    """
    async with DataAgentSandbox(timeout=timeout) as sandbox:
        result = await sandbox.execute(code)

        if result.success:
            output = result.output
            if result.error:
                output += f"\n警告: {result.error}"
            return output if output else "代码执行成功，无输出"
        else:
            return f"执行失败: {result.error}"


@tool
def execute_python_with_data(code: str, data_json: str) -> str:
    """
    执行Python代码并传入JSON数据

    数据将作为名为'data'的变量注入代码环境。

    Args:
        code: Python代码
        data_json: JSON格式的数据

    Returns:
        代码执行输出

    示例:
        execute_python_with_data(
            code='''
            import pandas as pd
            df = pd.DataFrame(data)
            print(df.head())
            ''',
            data_json='[{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]'
        )
    """
    import json

    try:
        data = json.loads(data_json)
    except json.JSONDecodeError as e:
        return f"JSON解析错误: {str(e)}"

    # 构建完整代码
    full_code = f"import json\ndata = json.loads('''{data_json}''')\n{code}"

    result = execute_python_sync(full_code)

    if result.success:
        return result.output if result.output else "代码执行成功，无输出"
    else:
        return f"执行失败: {result.error}"


@tool
def validate_python_code(code: str) -> str:
    """
    验证Python代码语法

    检查代码是否有语法错误，但不执行代码。

    Args:
        code: Python代码

    Returns:
        验证结果
    """
    import ast

    try:
        ast.parse(code)
        return "代码语法正确"
    except SyntaxError as e:
        return f"语法错误 (行 {e.lineno}): {e.msg}"


def get_safe_builtins() -> dict:
    """
    获取安全的内置函数列表

    Returns:
        允许在沙箱中使用的内置函数
    """
    return {
        # 基本类型
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "set": set,
        "frozenset": frozenset,
        "bytes": bytes,
        "bytearray": bytearray,

        # 常用函数
        "len": len,
        "range": range,
        "print": print,
        "type": type,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "hasattr": hasattr,
        "getattr": getattr,
        "setattr": setattr,
        "delattr": delattr,
        "callable": callable,

        # 数学函数
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "divmod": divmod,

        # 序列操作
        "sorted": sorted,
        "reversed": reversed,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "all": all,
        "any": any,

        # 字符串
        "chr": chr,
        "ord": ord,
        "format": format,
        "repr": repr,

        # 其他
        "id": id,
        "hash": hash,
        "iter": iter,
        "next": next,
        "slice": slice,

        # 异常
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "KeyError": KeyError,
        "IndexError": IndexError,
        "AttributeError": AttributeError,
        "RuntimeError": RuntimeError,
        "StopIteration": StopIteration,
    }


@tool
def list_variables() -> str:
    """
    列出当前会话中保存的所有 Python 变量

    显示变量名、类型和简要信息。这些变量可以在后续的
    execute_python_safe 调用中直接使用。

    Returns:
        变量列表信息
    """
    from ..session import get_current_session

    session = get_current_session()
    if not session:
        return "当前没有活动会话"

    context = session.get_execution_context()
    if not context:
        return "当前会话没有保存的变量"

    lines = ["当前会话保存的变量:"]
    for name, value in context.items():
        type_name = type(value).__name__
        # 获取简要描述
        if hasattr(value, "shape"):  # DataFrame 或 ndarray
            info = f"shape={value.shape}"
        elif isinstance(value, (list, dict, set, tuple)):
            info = f"len={len(value)}"
        elif isinstance(value, str) and len(value) > 50:
            info = f'"{value[:50]}..."'
        else:
            info = repr(value) if len(repr(value)) < 50 else f"{repr(value)[:50]}..."
        lines.append(f"  - {name} ({type_name}): {info}")

    return "\n".join(lines)


@tool
def clear_variables() -> str:
    """
    清空当前会话中保存的所有 Python 变量

    清空后，之前保存的变量将无法在后续执行中使用。

    Returns:
        操作结果
    """
    from ..session import get_current_session

    session = get_current_session()
    if not session:
        return "当前没有活动会话"

    context = session.get_execution_context()
    count = len(context)

    session.clear_execution_context()

    if count > 0:
        return f"已清空 {count} 个变量"
    else:
        return "没有需要清空的变量"


@tool
def export_dataframe(data_json: str, filename: str, file_format: str = "csv") -> str:
    """
    将数据导出为文件，自动保存到用户可下载的导出目录

    这是保存数据分析结果的推荐方式。文件将保存到会话导出目录，
    用户可以在"导出文件"面板中查看和下载。

    Args:
        data_json: JSON 格式的数据（数组或对象）
        filename: 文件名（不含路径），如 "result.csv"
        file_format: 文件格式，支持 "csv", "json", "excel"，默认 "csv"

    Returns:
        导出结果信息

    示例:
        # 导出为 CSV
        export_dataframe(
            data_json='[{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]',
            filename="users.csv"
        )

        # 导出为 JSON
        export_dataframe(
            data_json='{"total": 100, "items": [1, 2, 3]}',
            filename="report.json",
            file_format="json"
        )
    """
    import json
    from pathlib import Path

    from ..session import get_current_session

    # 获取导出目录
    session = get_current_session()
    if session:
        export_dir = session.export_dir
    else:
        export_dir = Path.home() / ".data_agent" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

    # 清理文件名（移除路径字符）
    safe_filename = filename.replace("/", "_").replace("\\", "_")
    filepath = export_dir / safe_filename

    try:
        data = json.loads(data_json)
    except json.JSONDecodeError as e:
        return f"JSON 解析错误: {e}"

    try:
        if file_format == "json":
            # 保存为 JSON
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif file_format in ("csv", "excel"):
            # 使用 pandas 保存
            import pandas as pd

            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # 尝试转换为 DataFrame
                if all(isinstance(v, list) for v in data.values()):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([data])
            else:
                return f"数据格式不支持: {type(data)}"

            if file_format == "csv":
                df.to_csv(filepath, index=False, encoding="utf-8-sig")
            else:
                df.to_excel(filepath, index=False)
        else:
            return f"不支持的文件格式: {file_format}"

        return f"文件已导出: {safe_filename}\n路径: {filepath}"

    except Exception as e:
        return f"导出失败: {e}"


@tool
def export_text(content: str, filename: str) -> str:
    """
    将文本内容导出为文件

    适用于导出 SQL 脚本、Python 代码、报告文本等。

    Args:
        content: 要保存的文本内容
        filename: 文件名（不含路径），如 "report.txt"

    Returns:
        导出结果信息

    示例:
        # 导出 SQL 脚本
        export_text(
            content="SELECT * FROM users WHERE age > 18;",
            filename="query.sql"
        )

        # 导出分析报告
        export_text(
            content="## 数据分析报告\\n\\n总用户数: 1000\\n活跃用户: 800",
            filename="report.md"
        )
    """
    from pathlib import Path

    from ..session import get_current_session

    # 获取导出目录
    session = get_current_session()
    if session:
        export_dir = session.export_dir
    else:
        export_dir = Path.home() / ".data_agent" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

    # 清理文件名
    safe_filename = filename.replace("/", "_").replace("\\", "_")
    filepath = export_dir / safe_filename

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"文件已导出: {safe_filename}\n路径: {filepath}"
    except Exception as e:
        return f"导出失败: {e}"


@tool
def list_exports() -> str:
    """
    列出当前会话的所有导出文件

    显示文件名、大小和修改时间。

    Returns:
        导出文件列表
    """
    from datetime import datetime
    from pathlib import Path

    from ..session import get_current_session

    session = get_current_session()
    if session:
        export_dir = session.export_dir
    else:
        export_dir = Path.home() / ".data_agent" / "exports"

    if not export_dir.exists():
        return "导出目录不存在"

    files = list(export_dir.iterdir())
    if not files:
        return "当前没有导出文件"

    lines = [f"导出目录: {export_dir}", ""]
    for f in sorted(files):
        if f.is_file():
            size = f.stat().st_size
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            size_str = (
                f"{size} B"
                if size < 1024
                else f"{size / 1024:.1f} KB"
                if size < 1024 * 1024
                else f"{size / 1024 / 1024:.1f} MB"
            )
            lines.append(f"  - {f.name} ({size_str}) {mtime.strftime('%H:%M:%S')}")

    return "\n".join(lines)
