"""
会话管理 API

提供会话信息查询接口。
"""

from typing import Any, Dict, List
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...session import SessionManager

router = APIRouter()

# 当前会话管理器（由 copilot 模块创建时设置）
_current_session: SessionManager = None


def set_current_session(session: SessionManager):
    """设置当前会话"""
    global _current_session
    _current_session = session


def get_current_session() -> SessionManager:
    """获取当前会话，如果不存在则创建"""
    global _current_session
    if _current_session is None:
        _current_session = SessionManager()
    return _current_session


@router.get("")
@router.get("/")
async def get_session_info() -> Dict[str, Any]:
    """
    获取当前会话信息
    """
    session = get_current_session()
    return {
        "session_id": session.session_id,
        "export_dir": str(session.export_dir),
        "workspace_dir": str(session.workspace_dir),
    }


@router.get("/exports")
async def get_exports() -> Dict[str, Any]:
    """
    获取当前会话的导出文件列表
    """
    session = get_current_session()
    exports = session.list_exports()

    return {
        "session_id": session.session_id,
        "export_dir": str(session.export_dir),
        "files": [
            {
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size if f.exists() else 0,
                "modified": f.stat().st_mtime if f.exists() else 0,
            }
            for f in exports
        ],
    }


@router.get("/exports/{filename}")
async def download_export(filename: str):
    """
    下载导出文件

    Args:
        filename: 文件名
    """
    session = get_current_session()
    file_path = session.export_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("/new")
async def create_new_session() -> Dict[str, Any]:
    """
    创建新会话

    注意：这会创建一个全新的会话，之前的会话数据仍然保留。
    """
    global _current_session
    _current_session = SessionManager()

    return {
        "success": True,
        "session_id": _current_session.session_id,
        "export_dir": str(_current_session.export_dir),
        "message": "新会话已创建",
    }
