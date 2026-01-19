"""
文件管理 API

支持 Excel/CSV 文件上传、列表、预览、删除功能。
用于 Dagster 数据处理管道的输入文件管理。
"""

import base64
import logging
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ...session import SessionManager, get_current_session as get_global_session, get_session_by_id

logger = logging.getLogger(__name__)

router = APIRouter()

# 允许上传的文件类型
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
# 最大文件大小：50MB
MAX_FILE_SIZE = 50 * 1024 * 1024


def get_current_session(session_id: str = None) -> SessionManager:
    """
    获取会话

    Args:
        session_id: 可选的会话 ID。如果提供，返回指定的会话；否则返回全局会话。

    Returns:
        SessionManager 实例
    """
    if session_id:
        session = get_session_by_id(session_id)
        if session:
            return session

    session = get_global_session()
    if session is None:
        session = SessionManager()
    return session


def is_allowed_file(filename: str) -> bool:
    """检查文件类型是否允许"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除潜在的路径遍历字符"""
    # 只保留文件名部分，移除路径
    filename = Path(filename).name
    # 替换可能的危险字符
    for char in ['..', '/', '\\', '\x00']:
        filename = filename.replace(char, '_')
    return filename


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = None
) -> Dict[str, Any]:
    """
    上传文件到 imports 目录

    支持格式：Excel (.xlsx, .xls), CSV (.csv)
    最大文件大小：50MB

    Args:
        file: 上传的文件
        session_id: 可选的会话 ID

    Returns:
        上传结果
    """
    session = get_current_session(session_id)

    # 检查文件类型
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。允许的类型: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 清理文件名
    safe_filename = sanitize_filename(file.filename)

    # 读取文件内容并检查大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大。最大允许 {MAX_FILE_SIZE // 1024 // 1024}MB"
        )

    # 保存文件
    file_path = session.import_dir / safe_filename
    try:
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"文件上传成功: {safe_filename} -> {file_path}")

        return {
            "success": True,
            "filename": safe_filename,
            "path": str(file_path),
            "size": len(content),
            "message": f"文件 {safe_filename} 上传成功",
        }
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")


@router.get("/imports")
async def list_imports(session_id: str = None) -> Dict[str, Any]:
    """
    列出 imports 目录中的所有文件

    Args:
        session_id: 可选的会话 ID

    Returns:
        文件列表
    """
    session = get_current_session(session_id)
    imports = session.list_imports()

    return {
        "session_id": session.session_id,
        "import_dir": str(session.import_dir),
        "files": [
            {
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size if f.exists() else 0,
                "modified": f.stat().st_mtime if f.exists() else 0,
                "type": f.suffix.lower().lstrip('.'),
            }
            for f in imports
        ],
    }


@router.get("/imports/{filename}/preview")
async def preview_import(
    filename: str,
    session_id: str = None,
    max_rows: int = 10
) -> Dict[str, Any]:
    """
    预览导入文件内容

    Args:
        filename: 文件名
        session_id: 可选的会话 ID
        max_rows: 最大预览行数（默认 10）

    Returns:
        文件预览内容
    """
    session = get_current_session(session_id)
    file_path = session.import_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")

    ext = file_path.suffix.lower()

    try:
        import pandas as pd

        if ext in [".xlsx", ".xls"]:
            # Excel 文件
            df = pd.read_excel(file_path, nrows=max_rows)
            total_rows = len(pd.read_excel(file_path, usecols=[0]))

            # 获取 sheet 名称
            xl = pd.ExcelFile(file_path)
            sheets = xl.sheet_names

            return {
                "type": "excel",
                "filename": filename,
                "sheets": sheets,
                "columns": list(df.columns),
                "data": df.to_dict(orient="records"),
                "preview_rows": len(df),
                "total_rows": total_rows,
            }

        elif ext == ".csv":
            # CSV 文件
            df = pd.read_csv(file_path, nrows=max_rows)

            # 估算总行数
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                total_rows = sum(1 for _ in f) - 1  # 减去表头

            return {
                "type": "csv",
                "filename": filename,
                "columns": list(df.columns),
                "data": df.to_dict(orient="records"),
                "preview_rows": len(df),
                "total_rows": total_rows,
            }

        else:
            raise HTTPException(status_code=400, detail=f"不支持预览的文件类型: {ext}")

    except Exception as e:
        logger.error(f"预览文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


@router.delete("/imports/{filename}")
async def delete_import(filename: str, session_id: str = None) -> Dict[str, Any]:
    """
    删除导入文件

    Args:
        filename: 文件名
        session_id: 可选的会话 ID

    Returns:
        删除结果
    """
    session = get_current_session(session_id)
    file_path = session.import_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")

    try:
        file_path.unlink()
        logger.info(f"文件已删除: {filename}")

        return {
            "success": True,
            "filename": filename,
            "message": f"文件 {filename} 已删除",
        }
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/imports/{filename}/download")
async def download_import(filename: str, session_id: str = None):
    """
    下载导入文件

    Args:
        filename: 文件名
        session_id: 可选的会话 ID
    """
    session = get_current_session(session_id)
    file_path = session.import_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
    )
