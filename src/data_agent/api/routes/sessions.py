"""
会话管理 API

提供会话信息查询接口。
"""

from typing import Any, Dict, List
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...session import SessionManager, get_current_session as get_global_session, get_session_by_id

router = APIRouter()


def get_current_session(session_id: str = None) -> SessionManager:
    """
    获取会话

    Args:
        session_id: 可选的会话 ID。如果提供，返回指定的会话；否则返回全局会话。

    Returns:
        SessionManager 实例
    """
    # 如果提供了 session_id，尝试获取指定会话
    if session_id:
        session = get_session_by_id(session_id)
        if session:
            return session

    # 回退到全局会话
    session = get_global_session()
    if session is None:
        # 创建新会话（这会自动设置为全局会话）
        session = SessionManager()
    return session


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
async def get_exports(session_id: str = None) -> Dict[str, Any]:
    """
    获取指定会话的导出文件列表

    Args:
        session_id: 可选的会话 ID。如果提供，返回指定会话的导出文件；否则返回全局会话的导出文件。
    """
    session = get_current_session(session_id)
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


@router.get("/exports/{filename}/preview")
async def preview_export(filename: str, session_id: str = None) -> Dict[str, Any]:
    """
    预览导出文件内容

    根据文件类型返回不同格式的预览：
    - CSV: 返回前 10 行数据
    - SQL/Python/JSON: 返回前 50 行代码
    - 图片: 返回 base64 编码
    - 其他: 返回文本内容

    Args:
        filename: 文件名
        session_id: 可选的会话 ID
    """
    session = get_current_session(session_id)
    file_path = session.export_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")

    ext = file_path.suffix.lower()

    try:
        if ext == ".csv":
            # CSV 返回前 10 行
            import pandas as pd
            df = pd.read_csv(file_path, nrows=10)
            return {"content": df.to_string(), "type": "table"}

        elif ext in [".sql", ".py", ".json", ".txt", ".md"]:
            # 代码/文本文件返回前 50 行
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[:50]
            content = "".join(lines)
            if len(lines) == 50:
                content += "\n... (更多内容请下载查看)"
            return {"content": content, "type": "code"}

        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".svg"]:
            # 图片返回 base64
            import base64
            with open(file_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            mime_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
            }
            mime = mime_types.get(ext, "image/png")
            return {"content": f"data:{mime};base64,{b64}", "type": "image"}

        elif ext in [".pkl", ".joblib"]:
            # 模型文件返回元信息
            return {
                "content": f"模型文件: {filename}\n大小: {file_path.stat().st_size} 字节\n\n(二进制文件，无法预览)",
                "type": "text",
            }

        else:
            # 其他文件尝试作为文本读取
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read(4096)  # 最多读取 4KB
                if len(content) == 4096:
                    content += "\n... (内容已截断)"
                return {"content": content, "type": "text"}
            except UnicodeDecodeError:
                return {
                    "content": f"二进制文件: {filename}\n大小: {file_path.stat().st_size} 字节\n\n(无法预览)",
                    "type": "text",
                }

    except Exception as e:
        return {"content": f"预览失败: {str(e)}", "type": "text"}


@router.get("/exports/{filename}/download")
async def download_export(filename: str, session_id: str = None):
    """
    下载导出文件

    Args:
        filename: 文件名
        session_id: 可选的会话 ID
    """
    session = get_current_session(session_id)
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
    # 创建新会话（会自动设置为全局会话）
    new_session = SessionManager()

    return {
        "success": True,
        "session_id": new_session.session_id,
        "export_dir": str(new_session.export_dir),
        "message": "新会话已创建",
    }
