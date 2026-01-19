"""
Dagster 数据处理工具

提供预设的数据操作 ops 和 DAG 生成/执行功能。
用于 data-processor SubAgent 构建数据处理管道。
"""

import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

from ..session import get_current_session, get_session_by_id

logger = logging.getLogger(__name__)

# 预设操作定义
PRESET_OPS = {
    # 文件 I/O
    "read_excel": {
        "category": "文件读取",
        "description": "读取 Excel 文件 (.xlsx, .xls)",
        "params": ["file_path", "sheet_name"],
        "example": 'read_excel(file_path="data.xlsx", sheet_name=0)',
    },
    "read_csv": {
        "category": "文件读取",
        "description": "读取 CSV 文件",
        "params": ["file_path", "encoding"],
        "example": 'read_csv(file_path="data.csv", encoding="utf-8")',
    },
    "write_excel": {
        "category": "文件写入",
        "description": "写入 Excel 文件",
        "params": ["df", "file_path", "sheet_name"],
        "example": 'write_excel(df, file_path="output.xlsx")',
    },
    "write_csv": {
        "category": "文件写入",
        "description": "写入 CSV 文件",
        "params": ["df", "file_path", "encoding"],
        "example": 'write_csv(df, file_path="output.csv")',
    },
    # 数据选择
    "select_columns": {
        "category": "数据选择",
        "description": "选择指定的列",
        "params": ["df", "columns"],
        "example": 'select_columns(df, columns=["A", "B", "C"])',
    },
    "filter_rows": {
        "category": "数据过滤",
        "description": "按条件过滤行",
        "params": ["df", "condition"],
        "example": 'filter_rows(df, condition="col_a > 10")',
    },
    "rename_columns": {
        "category": "数据转换",
        "description": "重命名列",
        "params": ["df", "mapping"],
        "example": 'rename_columns(df, mapping={"old_name": "new_name"})',
    },
    # 数据清洗
    "fill_missing": {
        "category": "数据清洗",
        "description": "填充缺失值",
        "params": ["df", "value", "method", "columns"],
        "example": 'fill_missing(df, value=0) 或 fill_missing(df, method="ffill")',
    },
    "drop_duplicates": {
        "category": "数据清洗",
        "description": "删除重复行",
        "params": ["df", "subset", "keep"],
        "example": 'drop_duplicates(df, subset=["col_a"], keep="first")',
    },
    "drop_na": {
        "category": "数据清洗",
        "description": "删除包含空值的行",
        "params": ["df", "subset", "how"],
        "example": 'drop_na(df, subset=["col_a"], how="any")',
    },
    # 排序
    "sort_data": {
        "category": "数据排序",
        "description": "按列排序",
        "params": ["df", "by", "ascending"],
        "example": 'sort_data(df, by=["col_a"], ascending=True)',
    },
    # 聚合
    "aggregate": {
        "category": "数据聚合",
        "description": "分组聚合",
        "params": ["df", "group_by", "agg_dict"],
        "example": 'aggregate(df, group_by=["group"], agg_dict={"value": "sum"})',
    },
    "pivot_table": {
        "category": "数据透视",
        "description": "创建数据透视表",
        "params": ["df", "index", "columns", "values", "aggfunc"],
        "example": 'pivot_table(df, index="date", columns="group", values="amount", aggfunc="sum")',
    },
    # 合并
    "merge_dataframes": {
        "category": "数据合并",
        "description": "合并两个 DataFrame",
        "params": ["df1", "df2", "on", "how"],
        "example": 'merge_dataframes(df1, df2, on="key", how="left")',
    },
    "concat_dataframes": {
        "category": "数据合并",
        "description": "纵向拼接多个 DataFrame",
        "params": ["dfs", "axis"],
        "example": "concat_dataframes([df1, df2], axis=0)",
    },
    # 复杂计算
    "python_transform": {
        "category": "自定义计算",
        "description": "执行自定义 Python 代码进行数据转换。代码中可使用 df, pd, np，必须将结果赋值给 result 变量。",
        "params": ["df", "code"],
        "example": """python_transform(df, code='''
# 计算新列
result = df.copy()
result['new_col'] = result['col_a'] * 2
''')""",
    },
}


@tool
def list_preset_ops() -> Dict[str, Any]:
    """
    列出所有可用的预设数据操作

    返回按类别分组的操作列表，包括描述、参数和示例。
    """
    # 按类别分组
    by_category: Dict[str, List[Dict]] = {}
    for op_name, op_info in PRESET_OPS.items():
        category = op_info["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(
            {
                "name": op_name,
                "description": op_info["description"],
                "params": op_info["params"],
                "example": op_info["example"],
            }
        )

    return {
        "total_ops": len(PRESET_OPS),
        "categories": list(by_category.keys()),
        "ops_by_category": by_category,
    }


@tool
def list_import_files(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    列出当前会话 imports 目录中的所有可用文件

    Args:
        session_id: 可选的会话 ID

    Returns:
        包含文件列表的字典
    """
    session = None
    if session_id:
        session = get_session_by_id(session_id)
    if not session:
        session = get_current_session()

    if not session:
        return {"error": "没有活动会话", "files": []}

    import_files = session.list_imports()

    files_info = []
    for f in import_files:
        try:
            stat = f.stat()
            # 使用虚拟路径而不是绝对路径，与 CompositeBackend 路由匹配
            virtual_path = f"/imports/{f.name}"
            files_info.append(
                {
                    "name": f.name,
                    "path": virtual_path,  # 虚拟路径，便于 AI 使用
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": f.suffix.lower().lstrip("."),
                }
            )
        except Exception as e:
            logger.warning(f"获取文件信息失败: {f}, 错误: {e}")

    return {
        "session_id": session.session_id,
        "import_dir": "/imports/",  # 虚拟路径
        "files": files_info,
        "total": len(files_info),
        "note": "使用 generate_dag_code 处理文件，只需提供文件名（如 'data.xlsx'），无需完整路径",
    }


def _generate_op_code(op_name: str, params: Dict[str, Any]) -> str:
    """
    生成单个 op 的代码

    Args:
        op_name: 操作名称
        params: 操作参数

    Returns:
        生成的 Python 代码片段
    """
    if op_name == "read_excel":
        file_path = params.get("file_path", "")
        sheet_name = params.get("sheet_name", 0)
        return f'pd.read_excel("{file_path}", sheet_name={repr(sheet_name)})'

    elif op_name == "read_csv":
        file_path = params.get("file_path", "")
        encoding = params.get("encoding", "utf-8")
        return f'pd.read_csv("{file_path}", encoding="{encoding}")'

    elif op_name == "write_excel":
        file_path = params.get("file_path", "output.xlsx")
        sheet_name = params.get("sheet_name", "Sheet1")
        return f'df.to_excel("{file_path}", sheet_name="{sheet_name}", index=False)'

    elif op_name == "write_csv":
        file_path = params.get("file_path", "output.csv")
        encoding = params.get("encoding", "utf-8")
        return f'df.to_csv("{file_path}", encoding="{encoding}", index=False)'

    elif op_name == "select_columns":
        columns = params.get("columns", [])
        return f"df[{repr(columns)}]"

    elif op_name == "filter_rows":
        condition = params.get("condition", "")
        return f"df.query('{condition}')"

    elif op_name == "rename_columns":
        mapping = params.get("mapping", {})
        return f"df.rename(columns={repr(mapping)})"

    elif op_name == "fill_missing":
        value = params.get("value")
        method = params.get("method")
        columns = params.get("columns")
        if method:
            if columns:
                return f"df.fillna(method='{method}', subset={repr(columns)})"
            return f"df.fillna(method='{method}')"
        if columns:
            return f"df[{repr(columns)}].fillna({repr(value)})"
        return f"df.fillna({repr(value)})"

    elif op_name == "drop_duplicates":
        subset = params.get("subset")
        keep = params.get("keep", "first")
        if subset:
            return f"df.drop_duplicates(subset={repr(subset)}, keep='{keep}')"
        return f"df.drop_duplicates(keep='{keep}')"

    elif op_name == "drop_na":
        subset = params.get("subset")
        how = params.get("how", "any")
        if subset:
            return f"df.dropna(subset={repr(subset)}, how='{how}')"
        return f"df.dropna(how='{how}')"

    elif op_name == "sort_data":
        by = params.get("by", [])
        ascending = params.get("ascending", True)
        return f"df.sort_values(by={repr(by)}, ascending={ascending})"

    elif op_name == "aggregate":
        group_by = params.get("group_by", [])
        agg_dict = params.get("agg_dict", {})
        return f"df.groupby({repr(group_by)}).agg({repr(agg_dict)}).reset_index()"

    elif op_name == "pivot_table":
        index = params.get("index")
        columns = params.get("columns")
        values = params.get("values")
        aggfunc = params.get("aggfunc", "mean")
        return f"pd.pivot_table(df, index={repr(index)}, columns={repr(columns)}, values={repr(values)}, aggfunc='{aggfunc}')"

    elif op_name == "merge_dataframes":
        on = params.get("on")
        how = params.get("how", "left")
        return f"pd.merge(df1, df2, on={repr(on)}, how='{how}')"

    elif op_name == "concat_dataframes":
        axis = params.get("axis", 0)
        return f"pd.concat(dfs, axis={axis})"

    elif op_name == "python_transform":
        code = params.get("code", "")
        # 转义代码中的三引号
        escaped_code = code.replace('"""', '\\"\\"\\"')
        return f'_python_transform(df, """{escaped_code}""")'

    return f"# 未知操作: {op_name}"


@tool
def generate_dag_code(
    description: str,
    input_files: List[str],
    output_file: str,
    operations: List[Dict[str, Any]],
    input_source: str = "imports",
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    根据操作列表生成 Dagster DAG 代码

    Args:
        description: DAG 的描述
        input_files: 输入文件列表（文件名）
        output_file: 输出文件名（相对于 exports 目录）
        operations: 操作列表，每个操作包含 {"op": "操作名", "params": {...}}
        input_source: 输入来源目录，'imports' 或 'exports'（默认 'imports'）
        session_id: 可选的会话 ID

    Returns:
        包含生成代码和作业信息的字典
    """
    session = None
    if session_id:
        session = get_session_by_id(session_id)
    if not session:
        session = get_current_session()

    if not session:
        return {"error": "没有活动会话"}

    # 生成唯一的作业名称
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_id = f"job_{timestamp}_{uuid.uuid4().hex[:6]}"
    job_file = session.dagster_jobs_dir / f"{job_id}.py"

    # 构建导入路径
    import_dir = str(session.import_dir)
    export_dir = str(session.export_dir)

    # 生成代码
    code_lines = [
        '"""',
        f"Dagster Job: {job_id}",
        f"描述: {description}",
        f"生成时间: {datetime.now().isoformat()}",
        '"""',
        "",
        "import pandas as pd",
        "import numpy as np",
        "from pathlib import Path",
        "",
        f'IMPORT_DIR = Path("{import_dir}")',
        f'EXPORT_DIR = Path("{export_dir}")',
        "",
        "",
        "def _python_transform(df, code):",
        '    """执行自定义 Python 代码"""',
        '    local_vars = {"df": df, "pd": pd, "np": np, "result": None}',
        '    exec(code, {"pd": pd, "np": np}, local_vars)',
        '    return local_vars.get("result", df)',
        "",
        "",
        "def run_job():",
        f'    """',
        f"    {description}",
        "",
        f"    输入文件: {', '.join(input_files)}",
        f"    输出文件: {output_file}",
        '    """',
    ]

    # 根据 input_source 选择输入目录
    input_dir_var = "EXPORT_DIR" if input_source == "exports" else "IMPORT_DIR"

    # 生成读取输入文件的代码
    for i, input_file in enumerate(input_files):
        file_path = f'{input_dir_var} / "{input_file}"'
        ext = Path(input_file).suffix.lower()
        if ext in [".xlsx", ".xls"]:
            code_lines.append(f"    df{i if i > 0 else ''} = pd.read_excel({file_path})")
        else:
            code_lines.append(f"    df{i if i > 0 else ''} = pd.read_csv({file_path})")

    code_lines.append("")

    # 生成操作代码
    # 过滤掉与输入文件重复的读取操作（因为已经自动生成了读取代码）
    input_file_names = {Path(f).name for f in input_files}

    for i, op in enumerate(operations):
        op_name = op.get("op") or op.get("op_name") or ""
        # 规范化操作名：去除空格，转小写
        op_name_normalized = op_name.strip().lower() if op_name else ""
        params = op.get("params", {})
        comment = op.get("comment", "")

        # 跳过所有 read_excel/read_csv 操作（因为输入文件已经在上面自动读取了）
        # 使用规范化后的操作名进行匹配，处理大小写和空格问题
        if op_name_normalized in ["read_excel", "read_csv", "readexcel", "readcsv"]:
            logger.info(f"跳过读取操作: {op_name}（输入文件已自动读取）")
            continue

        if comment:
            code_lines.append(f"    # {comment}")

        if op_name_normalized == "python_transform":
            # 特殊处理 python_transform
            code = params.get("code", "")
            code_lines.append("    # 自定义 Python 代码")
            code_lines.append(f'    code = """{code}"""')
            code_lines.append("    df = _python_transform(df, code)")
        else:
            # 使用原始 op_name（带正确大小写）进行代码生成
            op_code = _generate_op_code(op_name.strip() if op_name else "", params)
            code_lines.append(f"    df = {op_code}")

        code_lines.append("")

    # 生成输出代码
    output_path = f'EXPORT_DIR / "{output_file}"'
    ext = Path(output_file).suffix.lower()
    if ext in [".xlsx", ".xls"]:
        code_lines.append(f"    df.to_excel({output_path}, index=False)")
    else:
        code_lines.append(f"    df.to_csv({output_path}, index=False)")

    code_lines.append(f'    print(f"结果已保存到: {{{output_path}}}")')
    code_lines.append(f"    return df")
    code_lines.append("")
    code_lines.append("")
    code_lines.append('if __name__ == "__main__":')
    code_lines.append("    result = run_job()")
    code_lines.append('    print(f"处理完成，结果行数: {len(result)}")')

    code = "\n".join(code_lines)

    # 保存代码文件
    try:
        job_file.write_text(code, encoding="utf-8")
        logger.info(f"DAG 代码已生成: {job_file}")
    except Exception as e:
        logger.error(f"保存 DAG 代码失败: {e}")
        return {"error": f"保存代码失败: {str(e)}"}

    # 生成操作描述
    ops_description = []
    for i, op in enumerate(operations, 1):
        op_name = op.get("op")
        comment = op.get("comment", PRESET_OPS.get(op_name, {}).get("description", ""))
        ops_description.append(f"{i}. {op_name}: {comment}")

    # 返回虚拟路径供 AI 读取（通过 /dagster/ 路由）
    virtual_job_file = f"/dagster/jobs/{job_id}.py"

    return {
        "success": True,
        "job_id": job_id,
        "job_file": virtual_job_file,  # 使用虚拟路径
        "job_file_absolute": str(job_file),  # 保留绝对路径供调试
        "description": description,
        "input_source": input_source,  # 输入来源目录
        "input_files": input_files,
        "output_file": output_file,
        "operations_count": len(operations),
        "operations_description": ops_description,
        "code_preview": code[:2000] + ("..." if len(code) > 2000 else ""),
        "full_code": code,
        "message": f"DAG 代码已生成，等待确认执行。作业 ID: {job_id}",
    }


def _get_venv_python() -> str:
    """
    获取虚拟环境的 Python 可执行文件路径

    优先使用项目虚拟环境的 Python，确保依赖可用
    """
    # 方法1: 检查当前项目的 .venv
    project_root = Path(__file__).parent.parent.parent.parent  # 回到项目根目录
    venv_python = project_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)

    # 方法2: 检查 VIRTUAL_ENV 环境变量
    virtual_env = os.environ.get("VIRTUAL_ENV")
    if virtual_env:
        venv_python = Path(virtual_env) / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)

    # 方法3: 回退到 sys.executable
    return sys.executable


@tool
def execute_dag_job(job_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    执行指定的 DAG 作业

    Args:
        job_id: 作业 ID（由 generate_dag_code 返回）
        session_id: 可选的会话 ID

    Returns:
        执行结果
    """
    session = None
    if session_id:
        session = get_session_by_id(session_id)
    if not session:
        session = get_current_session()

    if not session:
        return {"error": "没有活动会话"}

    job_file = session.dagster_jobs_dir / f"{job_id}.py"

    if not job_file.exists():
        return {"error": f"作业文件不存在: {job_id}"}

    # 获取正确的 Python 路径
    python_executable = _get_venv_python()
    logger.info(f"使用 Python 执行 DAG: {python_executable}")

    try:
        # 使用虚拟环境的 Python 执行脚本
        result = subprocess.run(
            [python_executable, str(job_file)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 分钟超时
            cwd=str(session.session_dir),
        )

        if result.returncode == 0:
            logger.info(f"作业执行成功: {job_id}")
            return {
                "success": True,
                "job_id": job_id,
                "output": result.stdout,
                "message": "作业执行成功",
            }
        else:
            logger.error(f"作业执行失败: {job_id}, 错误: {result.stderr}")
            return {
                "success": False,
                "job_id": job_id,
                "error": result.stderr,
                "output": result.stdout,
                "message": "作业执行失败",
            }

    except subprocess.TimeoutExpired:
        logger.error(f"作业执行超时: {job_id}")
        return {
            "success": False,
            "job_id": job_id,
            "error": "执行超时（超过 5 分钟）",
            "message": "作业执行超时",
        }
    except Exception as e:
        logger.error(f"执行作业时出错: {job_id}, 错误: {e}")
        return {
            "success": False,
            "job_id": job_id,
            "error": str(e),
            "message": "执行作业时发生错误",
        }


@tool
def list_dag_jobs(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    列出当前会话的所有 DAG 作业文件

    Args:
        session_id: 可选的会话 ID

    Returns:
        作业列表
    """
    session = None
    if session_id:
        session = get_session_by_id(session_id)
    if not session:
        session = get_current_session()

    if not session:
        return {"error": "没有活动会话", "jobs": []}

    job_files = session.list_dagster_jobs()

    jobs_info = []
    for f in job_files:
        try:
            stat = f.stat()
            # 尝试读取描述（从文件开头的 docstring）
            content = f.read_text(encoding="utf-8")
            description = ""
            if '"""' in content:
                start = content.find('"""') + 3
                end = content.find('"""', start)
                if end > start:
                    doc = content[start:end].strip()
                    lines = doc.split("\n")
                    if len(lines) > 1:
                        description = lines[1].replace("描述:", "").strip()

            jobs_info.append(
                {
                    "job_id": f.stem,
                    "file": str(f),
                    "description": description,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size": stat.st_size,
                }
            )
        except Exception as e:
            logger.warning(f"获取作业信息失败: {f}, 错误: {e}")

    return {
        "session_id": session.session_id,
        "jobs_dir": str(session.dagster_jobs_dir),
        "jobs": jobs_info,
        "total": len(jobs_info),
    }


# 导出工具列表
__all__ = [
    "list_preset_ops",
    "list_import_files",
    "generate_dag_code",
    "execute_dag_job",
    "list_dag_jobs",
    "PRESET_OPS",
]
