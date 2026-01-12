"""
数据库 API

提供数据库 Schema 查询接口。
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ...tools import list_tables, describe_table

router = APIRouter()


@router.get("/tables")
async def get_tables() -> Dict[str, Any]:
    """
    获取数据库中的所有表

    返回表列表，区分数据表和视图。
    """
    try:
        result = list_tables.invoke({})
        return {
            "success": True,
            "tables": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table_name}")
async def get_table_schema(table_name: str) -> Dict[str, Any]:
    """
    获取指定表的结构信息

    Args:
        table_name: 表名
    """
    try:
        result = describe_table.invoke({"table_name": table_name})
        return {
            "success": True,
            "table_name": table_name,
            "schema": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
