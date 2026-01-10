"""
数据分析工具

使用pandas、numpy、scipy进行数据分析和统计。
"""

import json
import logging
from typing import List, Optional, Any

import numpy as np
import pandas as pd
from langchain_core.tools import tool
from scipy import stats

logger = logging.getLogger(__name__)


@tool
def analyze_dataframe(data_json: str, operations: str) -> str:
    """
    使用pandas分析DataFrame数据

    Args:
        data_json: JSON格式的数据
        operations: 要执行的操作（逗号分隔），支持:
                   - describe: 描述性统计
                   - info: 数据信息
                   - head: 前5行
                   - tail: 后5行
                   - shape: 数据形状
                   - dtypes: 数据类型
                   - missing: 缺失值统计
                   - unique: 唯一值统计

    Returns:
        分析结果

    示例:
        analyze_dataframe(
            data_json='[{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]',
            operations="describe,shape,missing"
        )
    """
    try:
        data = json.loads(data_json)
        df = pd.DataFrame(data)
    except Exception as e:
        return f"数据解析错误: {str(e)}"

    ops = [op.strip().lower() for op in operations.split(",")]
    results = []

    for op in ops:
        if op == "describe":
            results.append(f"描述性统计:\n{df.describe().to_string()}")
        elif op == "info":
            import io
            buffer = io.StringIO()
            df.info(buf=buffer)
            results.append(f"数据信息:\n{buffer.getvalue()}")
        elif op == "head":
            results.append(f"前5行:\n{df.head().to_string()}")
        elif op == "tail":
            results.append(f"后5行:\n{df.tail().to_string()}")
        elif op == "shape":
            results.append(f"数据形状: {df.shape[0]}行 x {df.shape[1]}列")
        elif op == "dtypes":
            results.append(f"数据类型:\n{df.dtypes.to_string()}")
        elif op == "missing":
            missing = df.isnull().sum()
            results.append(f"缺失值统计:\n{missing.to_string()}")
        elif op == "unique":
            unique_counts = df.nunique()
            results.append(f"唯一值统计:\n{unique_counts.to_string()}")
        else:
            results.append(f"未知操作: {op}")

    return "\n\n".join(results)


@tool
def statistical_analysis(data_json: str, method: str, column: Optional[str] = None) -> str:
    """
    使用scipy进行统计分析

    Args:
        data_json: JSON格式的数据
        method: 统计方法，支持:
                - describe: 描述性统计
                - normality: 正态性检验
                - correlation: 相关性分析
                - ttest: t检验
                - anova: 方差分析
        column: 指定分析的列（某些方法需要）

    Returns:
        统计分析结果

    示例:
        statistical_analysis(
            data_json='[{"value": 1}, {"value": 2}, {"value": 3}]',
            method="describe",
            column="value"
        )
    """
    try:
        data = json.loads(data_json)
        df = pd.DataFrame(data)
    except Exception as e:
        return f"数据解析错误: {str(e)}"

    method = method.lower()

    try:
        if method == "describe":
            if column:
                result = df[column].describe()
                return f"列 '{column}' 的描述性统计:\n{result.to_string()}"
            else:
                return f"描述性统计:\n{df.describe().to_string()}"

        elif method == "normality":
            if not column:
                return "正态性检验需要指定column参数"
            values = df[column].dropna().values
            stat, p_value = stats.shapiro(values)
            result = f"Shapiro-Wilk正态性检验:\n"
            result += f"统计量: {stat:.4f}\n"
            result += f"P值: {p_value:.4f}\n"
            result += f"结论: {'数据服从正态分布' if p_value > 0.05 else '数据不服从正态分布'} (α=0.05)"
            return result

        elif method == "correlation":
            numeric_df = df.select_dtypes(include=[np.number])
            corr_matrix = numeric_df.corr()
            return f"相关性矩阵:\n{corr_matrix.to_string()}"

        elif method == "ttest":
            if not column:
                return "t检验需要指定column参数"
            values = df[column].dropna().values
            # 单样本t检验（检验均值是否为0）
            stat, p_value = stats.ttest_1samp(values, 0)
            result = f"单样本t检验 (H0: μ=0):\n"
            result += f"t统计量: {stat:.4f}\n"
            result += f"P值: {p_value:.4f}\n"
            result += f"结论: {'拒绝H0' if p_value < 0.05 else '不能拒绝H0'} (α=0.05)"
            return result

        elif method == "anova":
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) < 2:
                return "方差分析需要至少2个数值列"
            groups = [df[col].dropna().values for col in numeric_cols]
            stat, p_value = stats.f_oneway(*groups)
            result = f"单因素方差分析:\n"
            result += f"F统计量: {stat:.4f}\n"
            result += f"P值: {p_value:.4f}\n"
            result += f"结论: {'组间存在显著差异' if p_value < 0.05 else '组间无显著差异'} (α=0.05)"
            return result

        else:
            return f"未知的统计方法: {method}"

    except Exception as e:
        logger.error(f"统计分析错误: {e}")
        return f"统计分析失败: {str(e)}"


@tool
def pivot_table(data_json: str, index: str, columns: str, values: str, aggfunc: str = "sum") -> str:
    """
    创建数据透视表

    Args:
        data_json: JSON格式的数据
        index: 行索引列
        columns: 列标签列
        values: 值列
        aggfunc: 聚合函数（sum, mean, count, min, max）

    Returns:
        透视表结果
    """
    try:
        data = json.loads(data_json)
        df = pd.DataFrame(data)

        pivot = pd.pivot_table(
            df,
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc
        )

        return f"数据透视表:\n{pivot.to_string()}"

    except Exception as e:
        logger.error(f"透视表创建错误: {e}")
        return f"创建透视表失败: {str(e)}"


@tool
def group_by_analysis(data_json: str, group_columns: str, agg_column: str, agg_func: str = "sum") -> str:
    """
    分组聚合分析

    Args:
        data_json: JSON格式的数据
        group_columns: 分组列（逗号分隔）
        agg_column: 聚合列
        agg_func: 聚合函数（sum, mean, count, min, max, std）

    Returns:
        分组聚合结果
    """
    try:
        data = json.loads(data_json)
        df = pd.DataFrame(data)

        group_cols = [col.strip() for col in group_columns.split(",")]

        agg_funcs = {
            "sum": "sum",
            "mean": "mean",
            "count": "count",
            "min": "min",
            "max": "max",
            "std": "std"
        }

        if agg_func.lower() not in agg_funcs:
            return f"不支持的聚合函数: {agg_func}"

        result = df.groupby(group_cols)[agg_column].agg(agg_funcs[agg_func.lower()])
        return f"分组聚合结果 ({agg_func}):\n{result.to_string()}"

    except Exception as e:
        logger.error(f"分组聚合错误: {e}")
        return f"分组聚合失败: {str(e)}"
