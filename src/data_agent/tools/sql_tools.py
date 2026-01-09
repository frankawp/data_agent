"""SQL工具集"""

from typing import Optional, Dict, Any
from langchain_core.tools import StructuredTool
from sqlalchemy import create_engine, text, inspect
import pandas as pd
import json


def execute_sql_query(
    database_url: str,
    query: str,
    query_type: str = "select"
) -> str:
    """执行SQL查询

    Args:
        database_url: 数据库连接URL (支持MySQL/PostgreSQL)
                     MySQL格式: mysql+pymysql://user:password@host:port/database
                     PostgreSQL格式: postgresql+psycopg2://user:password@host:port/database
        query: SQL查询语句
        query_type: 查询类型 (select/insert/update/delete/create/drop)

    Returns:
        查询结果的JSON字符串或执行信息

    Examples:
        >>> execute_sql_query(
        ...     "mysql+pymysql://user:pass@localhost:3306/mydb",
        ...     "SELECT * FROM users LIMIT 10"
        ... )
    """
    try:
        engine = create_engine(database_url)

        if query_type.lower() == "select":
            # SELECT查询，返回数据
            df = pd.read_sql(query, engine)
            return json.dumps({
                "success": True,
                "row_count": len(df),
                "data": df.to_dict(orient='records'),
                "columns": df.columns.tolist()
            }, ensure_ascii=False, indent=2)
        else:
            # INSERT/UPDATE/DELETE等操作
            with engine.connect() as conn:
                result = conn.execute(text(query))
                conn.commit()

                return json.dumps({
                    "success": True,
                    "row_count": result.rowcount if hasattr(result, 'rowcount') else 0,
                    "message": f"执行成功，影响 {result.rowcount if hasattr(result, 'rowcount') else 0} 行"
                }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "SQL执行失败"
        }, ensure_ascii=False, indent=2)


def get_database_schema(
    database_url: str,
    table_name: Optional[str] = None
) -> str:
    """获取数据库表结构

    Args:
        database_url: 数据库连接URL
        table_name: 表名（可选，如果为None则返回所有表）

    Returns:
        表结构信息的JSON字符串
    """
    try:
        engine = create_engine(database_url)
        inspector = inspect(engine)

        if table_name:
            # 获取单个表的结构
            columns = inspector.get_columns(table_name)
            result = {
                "table": table_name,
                "columns": [
                    {
                        "name": col['name'],
                        "type": str(col['type']),
                        "nullable": col.get('nullable', True),
                        "default": col.get('default')
                    }
                    for col in columns
                ]
            }
        else:
            # 获取所有表
            tables = inspector.get_table_names()
            result = {
                "tables": tables,
                "table_count": len(tables)
            }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


def list_tables(database_url: str) -> str:
    """列出数据库中的所有表

    Args:
        database_url: 数据库连接URL

    Returns:
        表列表的JSON字符串
    """
    try:
        engine = create_engine(database_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        return json.dumps({
            "success": True,
            "tables": tables,
            "count": len(tables)
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


# 创建LangChain工具
sql_query_tool = StructuredTool.from_function(
    func=execute_sql_query,
    name="sql_query",
    description="执行SQL查询。支持SELECT、INSERT、UPDATE、DELETE等操作。参数: database_url（数据库连接URL）, query（SQL语句）, query_type（查询类型，默认select）"
)

sql_schema_tool = StructuredTool.from_function(
    func=get_database_schema,
    name="sql_schema",
    description="获取数据库表结构信息。参数: database_url（数据库连接URL）, table_name（表名，可选）"
)

sql_tables_tool = StructuredTool.from_function(
    func=list_tables,
    name="sql_tables",
    description="列出数据库中的所有表。参数: database_url（数据库连接URL）"
)

# 导出所有工具
SQL_TOOLS = [sql_query_tool, sql_schema_tool, sql_tables_tool]
