"""数据分析工具（pandas、numpy、scipy）"""

import json
import pandas as pd
import numpy as np
from scipy import stats
from typing import Optional, Dict, Any, List
from langchain_core.tools import StructuredTool


def analyze_data(
    operation: str,
    data: str,
    params: Optional[str] = None
) -> str:
    """执行数据分析操作

    Args:
        operation: 分析类型
                  - descriptive: 描述性统计
                  - correlation: 相关性分析
                  - distribution: 分布分析
                  - outlier_detection: 异常值检测
                  - missing_values: 缺失值分析
                  - groupby_stats: 分组统计
        data: 数据（JSON格式字符串或文件路径）
        params: 额外参数（JSON格式字符串）

    Returns:
        分析结果（JSON格式）
    """
    try:
        # 解析参数
        params_dict = json.loads(params) if params else {}

        # 读取数据
        if data.startswith('{') or data.startswith('['):
            # JSON格式数据
            df = pd.read_json(data)
        else:
            # 假设是CSV文件路径
            df = pd.read_csv(data)

        result = {
            "success": True,
            "operation": operation
        }

        if operation == "descriptive":
            # 描述性统计
            desc = df.describe(include='all')
            result["statistics"] = json.loads(desc.to_json())

            # 添加基本统计信息
            result["info"] = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }

        elif operation == "correlation":
            # 相关性分析（仅数值列）
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) < 2:
                result["warning"] = "数值列少于2列，无法计算相关性"
            else:
                corr_matrix = numeric_df.corr()
                result["correlation_matrix"] = json.loads(corr_matrix.to_json())

        elif operation == "distribution":
            # 分布分析
            column = params_dict.get('column')
            if not column:
                return json.dumps({
                    "success": False,
                    "error": "请指定column参数"
                }, ensure_ascii=False)

            if column not in df.columns:
                return json.dumps({
                    "success": False,
                    "error": f"列 {column} 不存在"
                }, ensure_ascii=False)

            series = df[column]
            result["column"] = column

            if pd.api.types.is_numeric_dtype(series):
                # 数值型数据
                result["distribution"] = {
                    "mean": float(series.mean()),
                    "median": float(series.median()),
                    "std": float(series.std()),
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "q25": float(series.quantile(0.25)),
                    "q75": float(series.quantile(0.75)),
                    "skewness": float(series.skew()),
                    "kurtosis": float(series.kurtosis())
                }
            else:
                # 分类型数据
                value_counts = series.value_counts()
                result["distribution"] = {
                    "unique_values": int(series.nunique()),
                    "most_common": json.loads(value_counts.head(10).to_json())
                }

        elif operation == "outlier_detection":
            # 异常值检测（使用IQR方法）
            column = params_dict.get('column')
            if not column:
                return json.dumps({
                    "success": False,
                    "error": "请指定column参数"
                }, ensure_ascii=False)

            if column not in df.columns:
                return json.dumps({
                    "success": False,
                    "error": f"列 {column} 不存在"
                }, ensure_ascii=False)

            series = df[column].dropna()
            if not pd.api.types.is_numeric_dtype(series):
                return json.dumps({
                    "success": False,
                    "error": f"列 {column} 不是数值类型"
                }, ensure_ascii=False)

            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = series[(series < lower_bound) | (series > upper_bound)]

            result["outlier_detection"] = {
                "column": column,
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "outlier_count": len(outliers),
                "outlier_percentage": float(len(outliers) / len(series) * 100),
                "outlier_values": outliers.tolist()[:100]  # 限制返回数量
            }

        elif operation == "missing_values":
            # 缺失值分析
            missing = df.isnull().sum()
            missing_pct = (missing / len(df)) * 100

            missing_info = []
            for col in df.columns:
                if missing[col] > 0:
                    missing_info.append({
                        "column": col,
                        "missing_count": int(missing[col]),
                        "missing_percentage": float(missing_pct[col])
                    })

            result["missing_values"] = {
                "total_missing": int(missing.sum()),
                "columns_with_missing": len(missing_info),
                "details": sorted(missing_info, key=lambda x: x['missing_count'], reverse=True)
            }

        elif operation == "groupby_stats":
            # 分组统计
            groupby_col = params_dict.get('groupby_column')
            agg_col = params_dict.get('agg_column')
            agg_func = params_dict.get('agg_func', 'mean')

            if not groupby_col or not agg_col:
                return json.dumps({
                    "success": False,
                    "error": "请指定groupby_column和agg_column参数"
                }, ensure_ascii=False)

            grouped = df.groupby(groupby_col)[agg_col].agg(agg_func)
            result["groupby_stats"] = {
                "groupby_column": groupby_col,
                "agg_column": agg_col,
                "agg_func": agg_func,
                "results": json.loads(grouped.to_json())
            }

        else:
            result["error"] = f"未知的操作类型: {operation}"

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


def transform_data(
    operation: str,
    data: str,
    params: Optional[str] = None
) -> str:
    """数据转换操作

    Args:
        operation: 转换类型
                  - filter: 过滤数据
                  - sort: 排序
                  - drop_columns: 删除列
                  - rename_columns: 重命名列
                  - fill_missing: 填充缺失值
                  - drop_duplicates: 删除重复值
        data: 输入数据（JSON格式）
        params: 操作参数（JSON格式）

    Returns:
        转换后的数据（JSON格式）
    """
    try:
        params_dict = json.loads(params) if params else {}

        # 读取数据
        if data.startswith('{') or data.startswith('['):
            df = pd.read_json(data)
        else:
            df = pd.read_csv(data)

        if operation == "filter":
            # 过滤数据
            column = params_dict.get('column')
            operator = params_dict.get('operator', '==')
            value = params_dict.get('value')

            if not column:
                return json.dumps({"success": False, "error": "请指定column参数"}, ensure_ascii=False)

            if operator == '==':
                df = df[df[column] == value]
            elif operator == '!=':
                df = df[df[column] != value]
            elif operator == '>':
                df = df[df[column] > value]
            elif operator == '<':
                df = df[df[column] < value]
            elif operator == '>=':
                df = df[df[column] >= value]
            elif operator == '<=':
                df = df[df[column] <= value]
            elif operator == 'in':
                df = df[df[column].isin(value)]

        elif operation == "sort":
            # 排序
            column = params_dict.get('column')
            ascending = params_dict.get('ascending', True)

            if not column:
                return json.dumps({"success": False, "error": "请指定column参数"}, ensure_ascii=False)

            df = df.sort_values(by=column, ascending=ascending)

        elif operation == "drop_columns":
            # 删除列
            columns = params_dict.get('columns', [])
            df = df.drop(columns=columns, errors='ignore')

        elif operation == "rename_columns":
            # 重命名列
            rename_map = params_dict.get('rename_map', {})
            df = df.rename(columns=rename_map)

        elif operation == "fill_missing":
            # 填充缺失值
            column = params_dict.get('column')
            method = params_dict.get('method', 'mean')  # mean, median, mode, forward, backward, value
            value = params_dict.get('value')

            if column:
                if method == 'mean':
                    df[column].fillna(df[column].mean(), inplace=True)
                elif method == 'median':
                    df[column].fillna(df[column].median(), inplace=True)
                elif method == 'mode':
                    df[column].fillna(df[column].mode()[0], inplace=True)
                elif method == 'forward':
                    df[column].fillna(method='ffill', inplace=True)
                elif method == 'backward':
                    df[column].fillna(method='bfill', inplace=True)
                elif method == 'value' and value is not None:
                    df[column].fillna(value, inplace=True)
            else:
                # 对所有列填充
                if method == 'forward':
                    df.fillna(method='ffill', inplace=True)
                elif method == 'backward':
                    df.fillna(method='bfill', inplace=True)

        elif operation == "drop_duplicates":
            # 删除重复值
            subset = params_dict.get('subset')
            df = df.drop_duplicates(subset=subset, keep='first')

        return json.dumps({
            "success": True,
            "row_count": len(df),
            "data": df.to_dict(orient='records')
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


# 创建LangChain工具
data_analyze_tool = StructuredTool.from_function(
    func=analyze_data,
    name="data_analyze",
    description="执行数据分析操作。支持描述性统计、相关性分析、分布分析、异常值检测、缺失值分析、分组统计。参数: operation（操作类型）, data（数据JSON）, params（参数JSON）"
)

data_transform_tool = StructuredTool.from_function(
    func=transform_data,
    name="data_transform",
    description="执行数据转换操作。支持过滤、排序、删除列、重命名列、填充缺失值、删除重复值。参数: operation（操作类型）, data（数据JSON）, params（参数JSON）"
)

# 导出所有工具
DATA_TOOLS = [data_analyze_tool, data_transform_tool]
