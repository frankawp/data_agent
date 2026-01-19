"""
DeepAgents 后端配置

使用 CompositeBackend 将虚拟路径映射到实际会话目录：
- /exports/ → 会话导出目录（持久化）
- /workspace/ → 会话工作目录（持久化）
- /imports/ → 会话导入目录（用户上传的文件）
- /dagster/ → 会话 Dagster 目录（DAG 代码文件）
- 其他路径 → StateBackend（临时虚拟文件系统）
"""

from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.backends.protocol import BackendProtocol

from ..session import get_current_session


def create_session_backend(runtime) -> BackendProtocol:
    """
    创建与会话关联的后端

    根据当前会话动态创建 CompositeBackend：
    - /exports/ 路由到会话的 export_dir（FilesystemBackend）
    - /workspace/ 路由到会话的 workspace_dir（FilesystemBackend）
    - /imports/ 路由到会话的 import_dir（FilesystemBackend）
    - 其他路径使用默认的 StateBackend

    Args:
        runtime: DeepAgents runtime 对象

    Returns:
        配置好路由的 CompositeBackend 实例
    """
    session = get_current_session()

    if session is None:
        # 如果没有会话，使用默认的 StateBackend
        return StateBackend(runtime)

    # 创建文件系统后端，映射到会话目录
    exports_backend = FilesystemBackend(
        root_dir=session.export_dir,
        virtual_mode=True,  # 使用虚拟路径模式（/xxx.csv 而非绝对路径）
    )

    workspace_backend = FilesystemBackend(
        root_dir=session.workspace_dir,
        virtual_mode=True,
    )

    imports_backend = FilesystemBackend(
        root_dir=session.import_dir,
        virtual_mode=True,
    )

    dagster_backend = FilesystemBackend(
        root_dir=session.dagster_dir,
        virtual_mode=True,
    )

    # 创建组合后端
    return CompositeBackend(
        default=StateBackend(runtime),
        routes={
            "/exports/": exports_backend,
            "/workspace/": workspace_backend,
            "/imports/": imports_backend,
            "/dagster/": dagster_backend,
        },
    )
