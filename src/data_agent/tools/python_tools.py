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

        # 数学计算
        execute_python_safe('''
        result = sum(range(100))
        print(f"1到99的和是: {result}")
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
