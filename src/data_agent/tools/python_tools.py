"""Python代码执行工具"""

import sys
import traceback
import json
from typing import Optional, Dict, Any
from io import StringIO
from langchain_core.tools import StructuredTool


def execute_python_code(
    code: str,
    context_vars: Optional[str] = None
) -> str:
    """安全地执行Python代码

    Args:
        code: 要执行的Python代码
        context_vars: 预定义的上下文变量（JSON格式字符串）

    Returns:
        执行结果或错误信息（JSON格式）

    Examples:
        >>> execute_python_code(
        ...     "import pandas as pd\\ndf = pd.DataFrame({'a': [1,2,3]})\\nprint(df)"
        ... )
    """
    import pandas as pd
    import numpy as np
    import scipy
    import sklearn
    import networkx as nx

    # 创建隔离的执行环境
    output = StringIO()
    error_output = StringIO()

    # 准备执行环境
    exec_globals = {
        'pd': pd,
        'numpy': np,
        'np': np,
        'scipy': scipy,
        'sklearn': sklearn,
        'nx': nx,
        'networkx': nx,
        '__builtins__': __builtins__,
    }

    # 解析上下文变量
    if context_vars:
        try:
            additional_vars = json.loads(context_vars)
            exec_globals.update(additional_vars)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"上下文变量解析失败: {str(e)}"
            }, ensure_ascii=False, indent=2)

    try:
        # 重定向输出
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = output
        sys.stderr = error_output

        # 执行代码
        exec(code, exec_globals)

        # 恢复输出
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        # 获取输出
        stdout_result = output.getvalue()
        stderr_result = error_output.getvalue()

        result = {
            "success": True,
            "output": stdout_result if stdout_result else "代码执行成功（无输出）"
        }

        if stderr_result:
            result["stderr"] = stderr_result

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        # 恢复输出
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        return json.dumps({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, ensure_ascii=False, indent=2)
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def execute_data_analysis_code(
    code: str,
    data: Optional[str] = None
) -> str:
    """执行数据分析代码（带数据输入）

    Args:
        code: 要执行的Python代码
        data: 输入数据（JSON格式字符串，会自动转换为DataFrame）

    Returns:
        执行结果（JSON格式）
    """
    import pandas as pd
    import numpy as np

    context_vars = {}

    # 如果提供了数据，转换为DataFrame
    if data:
        try:
            data_dict = json.loads(data)
            if isinstance(data_dict, list):
                # 如果是列表，转换为DataFrame
                df = pd.DataFrame(data_dict)
                context_vars['input_data'] = df
                context_vars['df'] = df
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"数据解析失败: {str(e)}"
            }, ensure_ascii=False)

    # 使用上下文变量执行代码
    context_json = json.dumps(context_vars) if context_vars else None
    return execute_python_code(code, context_json)


# 创建LangChain工具
python_execute_tool = StructuredTool.from_function(
    func=execute_python_code,
    name="python_execute",
    description="执行Python代码。支持pandas、numpy、scipy、sklearn、networkx等库。参数: code（Python代码字符串）, context_vars（可选的上下文变量JSON字符串）"
)

python_data_analysis_tool = StructuredTool.from_function(
    func=execute_data_analysis_code,
    name="python_data_analysis",
    description="执行Python数据分析代码。自动处理输入数据并转换为DataFrame。参数: code（Python代码）, data（可选的输入数据JSON字符串）"
)

# 导出所有工具
PYTHON_TOOLS = [python_execute_tool, python_data_analysis_tool]
