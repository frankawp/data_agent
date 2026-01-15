"""
会话管理器

管理每个分析会话的生命周期、目录和资源。
"""

import logging
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 全局会话实例
_current_session: Optional["SessionManager"] = None

# 会话注册表：session_id -> SessionManager
_session_registry: Dict[str, "SessionManager"] = {}


def get_current_session() -> Optional["SessionManager"]:
    """获取当前会话实例"""
    return _current_session


def get_session_by_id(session_id: str) -> Optional["SessionManager"]:
    """
    根据 session_id 获取会话实例

    Args:
        session_id: 会话 ID

    Returns:
        SessionManager 实例，如果不存在则返回 None
    """
    return _session_registry.get(session_id)


class SessionManager:
    """
    会话管理器

    每个分析会话拥有独立的：
    - 会话 ID
    - 导出目录
    - 沙箱实例名称

    自动清理超过 7 天的旧会话。
    """

    # 会话保留天数
    RETENTION_DAYS = 7

    # 基础目录
    BASE_DIR = Path.home() / ".data_agent"
    SESSIONS_DIR = BASE_DIR / "sessions"

    def __init__(self, session_id: Optional[str] = None):
        """
        初始化会话管理器

        Args:
            session_id: 可选的会话 ID，不提供则自动生成
        """
        self.session_id = session_id or self._generate_session_id()
        self.session_dir = self.SESSIONS_DIR / self.session_id
        self.export_dir = self.session_dir / "exports"
        self.workspace_dir = self.session_dir / "workspace"

        # 沙箱可用状态（会话级别）
        self._sandbox_unavailable = False
        self._sandbox_error: Optional[str] = None

        # Python 执行上下文（变量持久化）
        self._execution_context: Dict[str, Any] = {}

        # 创建会话目录
        self._create_session_dirs()

        # 清理旧会话
        self._cleanup_old_sessions()

        # 设置为当前会话
        global _current_session
        _current_session = self

        # 注册到会话注册表
        global _session_registry
        _session_registry[self.session_id] = self

        logger.info(f"会话已创建: {self.session_id}")
        logger.debug(f"导出目录: {self.export_dir}")

    def _generate_session_id(self) -> str:
        """
        生成唯一会话 ID

        格式: session_YYYYMMDD_HHMMSS_xxxxxx
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        return f"session_{timestamp}_{unique_id}"

    def _create_session_dirs(self) -> None:
        """创建会话所需的目录"""
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _cleanup_old_sessions(self) -> None:
        """
        清理超过保留期限的旧会话

        默认清理 7 天前的会话目录。
        """
        if not self.SESSIONS_DIR.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=self.RETENTION_DAYS)
        cleaned_count = 0

        for session_path in self.SESSIONS_DIR.iterdir():
            if not session_path.is_dir():
                continue

            # 跳过当前会话
            if session_path.name == self.session_id:
                continue

            # 尝试从目录名解析时间戳
            try:
                # 格式: session_YYYYMMDD_HHMMSS_xxxxxx
                parts = session_path.name.split("_")
                if len(parts) >= 3 and parts[0] == "session":
                    date_str = parts[1]  # YYYYMMDD
                    session_date = datetime.strptime(date_str, "%Y%m%d")

                    if session_date < cutoff_date:
                        shutil.rmtree(session_path)
                        cleaned_count += 1
                        logger.debug(f"已清理旧会话: {session_path.name}")
            except (ValueError, IndexError) as e:
                logger.warning(f"无法解析会话目录名称: {session_path.name}, 错误: {e}")
                continue

        if cleaned_count > 0:
            logger.info(f"已清理 {cleaned_count} 个旧会话")

    def get_sandbox_name(self) -> str:
        """
        获取此会话的沙箱名称

        Returns:
            唯一的沙箱名称
        """
        return f"sandbox_{self.session_id}"

    def mark_sandbox_unavailable(self, error: str) -> None:
        """
        标记沙箱在本会话中不可用

        一旦标记，后续执行将直接使用本地模式，不再尝试连接沙箱。

        Args:
            error: 错误信息
        """
        self._sandbox_unavailable = True
        self._sandbox_error = error
        logger.info(f"沙箱已标记为不可用，后续将使用本地执行模式。原因: {error}")

    def is_sandbox_available(self) -> bool:
        """
        检查沙箱是否可用

        Returns:
            True 表示可用（可以尝试连接），False 表示不可用
        """
        return not self._sandbox_unavailable

    def get_sandbox_error(self) -> Optional[str]:
        """
        获取沙箱不可用的错误信息

        Returns:
            错误信息，如果沙箱可用则返回 None
        """
        return self._sandbox_error

    def get_execution_context(self) -> Dict[str, Any]:
        """
        获取 Python 执行上下文

        Returns:
            包含已保存变量的字典
        """
        return self._execution_context

    def update_execution_context(self, variables: Dict[str, Any]) -> None:
        """
        更新 Python 执行上下文

        Args:
            variables: 要保存的变量字典
        """
        self._execution_context.update(variables)

    def clear_execution_context(self) -> None:
        """清空 Python 执行上下文"""
        self._execution_context.clear()

    def get_export_path(self, filename: str) -> Path:
        """
        获取导出文件的完整路径

        Args:
            filename: 文件名

        Returns:
            完整的文件路径
        """
        return self.export_dir / filename

    def generate_export_filename(self, prefix: str = "result", ext: str = "csv") -> str:
        """
        生成导出文件名

        Args:
            prefix: 文件名前缀
            ext: 文件扩展名

        Returns:
            带时间戳的文件名
        """
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{prefix}_{timestamp}.{ext}"

    def list_exports(self) -> list[Path]:
        """
        列出当前会话的所有导出文件

        Returns:
            导出文件路径列表
        """
        if not self.export_dir.exists():
            return []
        return sorted(self.export_dir.iterdir())

    def cleanup(self) -> None:
        """
        清理当前会话

        删除会话目录及所有内容。
        """
        global _current_session, _session_registry

        if self.session_dir.exists():
            shutil.rmtree(self.session_dir)
            logger.info(f"会话已清理: {self.session_id}")

        if _current_session is self:
            _current_session = None

        # 从注册表移除
        if self.session_id in _session_registry:
            del _session_registry[self.session_id]

    def __enter__(self) -> "SessionManager":
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器退出"""
        # 退出时不自动清理，保留导出文件
        global _current_session
        if _current_session is self:
            _current_session = None

    def __repr__(self) -> str:
        return f"SessionManager(session_id='{self.session_id}')"
