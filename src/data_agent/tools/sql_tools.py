"""
SQL 工具

支持 MySQL、PostgreSQL 数据库查询。
"""

import logging

import pandas as pd
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


@tool
def execute_sql(query: str, database: str = "default") -> str:
    """
    执行SQL查询（MySQL/PostgreSQL）

    在配置的数据库上执行SQL查询，返回查询结果。
    仅支持SELECT查询，不允许修改数据。

    Args:
        query: SQL查询语句
        database: 数据库标识（默认使用配置中的数据库）

    Returns:
        查询结果的字符串表示
    """
    settings = get_settings()

    # 安全检查：只允许SELECT查询
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        return "错误：只允许执行SELECT查询"

    # 检查危险关键字
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT"]
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return f"错误：查询包含不允许的关键字 {keyword}"

    try:
        engine = create_engine(settings.db_connection)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

            if df.empty:
                return "查询结果为空"

            # 限制返回行数
            if len(df) > 1000:
                df = df.head(1000)
                return f"查询结果（显示前1000行，共{len(df)}行）:\n{df.to_string()}"

            return f"查询结果:\n{df.to_string()}"

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
