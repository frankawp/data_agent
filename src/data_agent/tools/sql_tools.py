"""
SQL 工具

支持 MySQL、PostgreSQL 数据库查询。
支持 Safe Mode 和 Preview Limit 模式控制。
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from ..config.settings import get_settings
from ..config.modes import get_mode_manager
from ..session import get_current_session

logger = logging.getLogger(__name__)


def _get_export_dir() -> Path:
    """获取导出目录，优先使用当前会话目录"""
    session = get_current_session()
    if session:
        return session.export_dir
    # 回退到默认目录
    export_dir = Path.home() / ".data_agent" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def _auto_export(df: pd.DataFrame, query: str) -> str:
    """自动导出查询结果到文件（使用会话目录）"""
    export_dir = _get_export_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"query_result_{timestamp}.csv"
    filepath = export_dir / filename

    df.to_csv(filepath, index=False, encoding="utf-8")
    return str(filepath)


@tool
def execute_sql(query: str, database: str = "default") -> str:
    """
    执行SQL查询（MySQL/PostgreSQL）

    在配置的数据库上执行SQL查询，返回查询结果。
    支持 Safe Mode 和 Preview Limit 模式控制。

    Args:
        query: SQL查询语句
        database: 数据库标识（默认使用配置中的数据库）

    Returns:
        查询结果的字符串表示
    """
    settings = get_settings()
    mode_manager = get_mode_manager()

    # 获取模式设置
    safe_mode = mode_manager.get("safe")
    preview_limit = mode_manager.get("preview")
    export_mode = mode_manager.get("export")

    query_upper = query.strip().upper()

    # 安全模式检查
    if safe_mode:
        # 严格模式：只允许 SELECT
        if not query_upper.startswith("SELECT"):
            return "错误：安全模式下只允许执行 SELECT 查询。使用 /safe off 关闭安全模式。"

        # 检查所有危险关键字
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT"]
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return f"错误：安全模式下不允许使用 {keyword}。使用 /safe off 关闭安全模式。"
    else:
        # 非安全模式：仍然阻止最危险的操作
        critical_keywords = ["DROP", "TRUNCATE", "GRANT"]
        for keyword in critical_keywords:
            if keyword in query_upper:
                return f"错误：不允许执行 {keyword} 操作（此操作在任何模式下都被禁止）"

    try:
        engine = create_engine(settings.db_connection)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

            if df.empty:
                return "查询结果为空"

            total_rows = len(df)
            result_parts = []

            # 应用预览限制
            limit = preview_limit.to_int()
            if limit and total_rows > limit:
                df_display = df.head(limit)
                result_parts.append(f"查询结果（显示前 {limit} 行，共 {total_rows} 行）:")
            else:
                df_display = df
                result_parts.append(f"查询结果（共 {total_rows} 行）:")

            result_parts.append(df_display.to_string())

            # 自动导出
            if export_mode:
                export_path = _auto_export(df, query)
                result_parts.append(f"\n[已导出至: {export_path}]")

            return "\n".join(result_parts)

    except SQLAlchemyError as e:
        logger.error(f"SQL执行错误: {e}")
        return f"SQL执行错误: {str(e)}"
    except Exception as e:
        logger.error(f"未知错误: {e}")
        return f"执行失败: {str(e)}"


@tool
def describe_table(table_name: str) -> str:
    """
    获取数据库表结构信息

    Args:
        table_name: 表名

    Returns:
        表结构描述
    """
    settings = get_settings()

    try:
        engine = create_engine(settings.db_connection)
        db_type = settings.get_db_type()

        if db_type == "mysql":
            query = f"DESCRIBE {table_name}"
        elif db_type == "postgresql":
            query = f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
            """
        else:
            return f"不支持的数据库类型: {db_type}"

        with engine.connect() as conn:
            result = conn.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return f"表 {table_name} 的结构:\n{df.to_string()}"

    except Exception as e:
        logger.error(f"获取表结构失败: {e}")
        return f"获取表结构失败: {str(e)}"


@tool
def list_tables() -> str:
    """
    列出数据库中的所有表

    Returns:
        表名列表
    """
    settings = get_settings()

    try:
        engine = create_engine(settings.db_connection)
        db_type = settings.get_db_type()

        if db_type == "mysql":
            query = "SHOW TABLES"
        elif db_type == "postgresql":
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """
        else:
            return f"不支持的数据库类型: {db_type}"

        with engine.connect() as conn:
            result = conn.execute(text(query))
            tables = [row[0] for row in result.fetchall()]
            return f"数据库中的表:\n" + "\n".join(f"- {t}" for t in tables)

    except Exception as e:
        logger.error(f"列出表失败: {e}")
        return f"列出表失败: {str(e)}"
