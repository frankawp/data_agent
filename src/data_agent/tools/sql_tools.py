"""
SQL和DuckDB工具

支持MySQL、PostgreSQL数据库查询，以及使用DuckDB进行高性能分析。
"""

import logging
from typing import Optional, Any, Dict

import duckdb
import pandas as pd
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class DuckDBEngine:
    """
    DuckDB数据分析引擎

    用于处理大数据量的分析查询。
    """

    def __init__(self, memory_limit: str = "4GB", threads: int = 4):
        """
        初始化DuckDB引擎

        Args:
            memory_limit: 内存限制
            threads: 线程数
        """
        self.conn = duckdb.connect(":memory:")
        self.conn.execute(f"SET memory_limit='{memory_limit}'")
        self.conn.execute(f"SET threads={threads}")
        self._registered_tables: Dict[str, Any] = {}

    def register_dataframe(self, name: str, df: pd.DataFrame):
        """
        注册DataFrame为虚拟表

        Args:
            name: 表名
            df: DataFrame
        """
        self._registered_tables[name] = df
        self.conn.register(name, df)

    def query(self, sql: str) -> pd.DataFrame:
        """
        执行SQL查询

        Args:
            sql: SQL语句

        Returns:
            查询结果DataFrame
        """
        return self.conn.execute(sql).df()

    def query_file(self, file_path: str, sql: str) -> pd.DataFrame:
        """
        查询文件数据

        Args:
            file_path: 文件路径（支持CSV、Parquet、JSON）
            sql: SQL查询语句

        Returns:
            查询结果DataFrame
        """
        # 根据文件扩展名选择读取函数
        if file_path.endswith(".parquet"):
            full_sql = sql.replace("__TABLE__", f"read_parquet('{file_path}')")
        elif file_path.endswith(".csv"):
            full_sql = sql.replace("__TABLE__", f"read_csv_auto('{file_path}')")
        elif file_path.endswith(".json"):
            full_sql = sql.replace("__TABLE__", f"read_json_auto('{file_path}')")
        else:
            full_sql = sql

        return self.conn.execute(full_sql).df()

    def close(self):
        """关闭连接"""
        self.conn.close()


# 全局DuckDB引擎实例
_duckdb_engine: Optional[DuckDBEngine] = None


def get_duckdb_engine() -> DuckDBEngine:
    """获取DuckDB引擎单例"""
    global _duckdb_engine
    if _duckdb_engine is None:
        settings = get_settings()
        _duckdb_engine = DuckDBEngine(
            memory_limit=settings.duckdb_memory_limit,
            threads=settings.duckdb_threads
        )
    return _duckdb_engine


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
def query_with_duckdb(sql: str) -> str:
    """
    使用DuckDB执行高性能SQL分析查询

    DuckDB是一个嵌入式分析数据库，可以直接查询pandas DataFrame，
    性能比传统pandas操作快10-100倍，适合大数据量分析。

    Args:
        sql: SQL查询语句

    Returns:
        查询结果的字符串表示

    示例:
        # 查询已注册的DataFrame
        query_with_duckdb("SELECT * FROM my_table WHERE amount > 1000")

        # 聚合查询
        query_with_duckdb("SELECT category, SUM(amount) FROM sales GROUP BY category")
    """
    try:
        result = duckdb.sql(sql).df()

        if result.empty:
            return "查询结果为空"

        # 限制返回行数
        if len(result) > 1000:
            result = result.head(1000)
            return f"查询结果（显示前1000行）:\n{result.to_string()}"

        return f"查询结果:\n{result.to_string()}"

    except Exception as e:
        logger.error(f"DuckDB查询错误: {e}")
        return f"查询失败: {str(e)}"


@tool
def query_parquet(file_path: str, sql_condition: str = "1=1") -> str:
    """
    直接查询Parquet文件

    无需将数据加载到内存，直接对Parquet文件执行SQL查询，
    适合处理超大文件。

    Args:
        file_path: Parquet文件路径
        sql_condition: WHERE条件（默认返回所有数据）

    Returns:
        查询结果的字符串表示

    示例:
        # 查询所有数据
        query_parquet("data/sales.parquet")

        # 带条件查询
        query_parquet("data/sales.parquet", "amount > 1000 AND region = 'East'")
    """
    try:
        sql = f"SELECT * FROM read_parquet('{file_path}') WHERE {sql_condition} LIMIT 1000"
        result = duckdb.sql(sql).df()

        if result.empty:
            return "查询结果为空"

        return f"查询结果:\n{result.to_string()}"

    except Exception as e:
        logger.error(f"Parquet查询错误: {e}")
        return f"查询失败: {str(e)}"


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
