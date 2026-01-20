"""
数据库 API

提供数据库 Schema 查询和连接配置接口。
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from ...tools import list_tables, describe_table
from ...session import SessionManager, get_current_session as get_global_session, set_current_session, get_session_by_id

logger = logging.getLogger(__name__)

router = APIRouter()


class DatabaseConfig(BaseModel):
    """数据库连接配置"""
    host: str
    port: int
    user: str
    password: str
    database: str


def _get_session(session_id: Optional[str] = None) -> SessionManager:
    """获取会话实例"""
    if session_id:
        session = get_session_by_id(session_id)
        if session:
            return session

    session = get_global_session()
    if session is None:
        session = SessionManager()
    return session


@router.get("/tables")
async def get_tables(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    获取数据库中的所有表

    返回表列表。如果会话未配置数据库，返回空列表。

    Args:
        session_id: 会话 ID
    """
    session = _get_session(session_id)

    # 检查会话是否已配置数据库
    if not session.get_db_config():
        return {
            "success": True,
            "tables": "",
            "configured": False,
            "message": "未配置数据库连接",
        }

    # 设置为当前会话，以便工具使用
    set_current_session(session)

    try:
        result = list_tables.invoke({})
        return {
            "success": True,
            "tables": result,
            "configured": True,
        }
    except Exception as e:
        logger.error(f"获取表列表失败: {e}")
        return {
            "success": False,
            "tables": "",
            "configured": True,
            "error": str(e),
        }


@router.get("/tables/{table_name}")
async def get_table_schema(table_name: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    获取指定表的结构信息

    Args:
        table_name: 表名
        session_id: 会话 ID
    """
    session = _get_session(session_id)

    # 检查会话是否已配置数据库
    if not session.get_db_config():
        raise HTTPException(status_code=400, detail="未配置数据库连接")

    # 设置为当前会话，以便工具使用
    set_current_session(session)

    try:
        result = describe_table.invoke({"table_name": table_name})
        return {
            "success": True,
            "table_name": table_name,
            "schema": result,
        }
    except Exception as e:
        logger.error(f"获取表结构失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def set_database_config(config: DatabaseConfig, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    设置会话的数据库连接配置

    Args:
        config: 数据库配置
        session_id: 会话 ID
    """
    session = _get_session(session_id)

    try:
        session.set_db_config(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
        )

        return {
            "success": True,
            "session_id": session.session_id,
            "config": session.get_db_config(),
            "message": "数据库配置已保存",
        }
    except Exception as e:
        logger.error(f"设置数据库配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_database_config(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    获取会话的数据库连接配置状态

    Args:
        session_id: 会话 ID
    """
    session = _get_session(session_id)
    config = session.get_db_config()

    return {
        "success": True,
        "session_id": session.session_id,
        "configured": config is not None,
        "config": config,
    }


@router.delete("/config")
async def clear_database_config(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    清除会话的数据库连接配置

    Args:
        session_id: 会话 ID
    """
    session = _get_session(session_id)
    session.clear_db_config()

    return {
        "success": True,
        "session_id": session.session_id,
        "message": "数据库配置已清除",
    }


@router.post("/test")
async def test_database_connection(config: DatabaseConfig) -> Dict[str, Any]:
    """
    测试数据库连接

    Args:
        config: 数据库配置
    """
    from urllib.parse import quote_plus

    try:
        # 构建连接字符串
        password = quote_plus(config.password)
        conn_str = f"mysql+pymysql://{config.user}:{password}@{config.host}:{config.port}/{config.database}"

        # 测试连接
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        return {
            "success": True,
            "message": "连接成功",
        }
    except SQLAlchemyError as e:
        logger.warning(f"数据库连接测试失败: {e}")
        return {
            "success": False,
            "message": f"连接失败: {str(e)}",
        }
    except Exception as e:
        logger.error(f"测试连接异常: {e}")
        return {
            "success": False,
            "message": f"连接异常: {str(e)}",
        }
