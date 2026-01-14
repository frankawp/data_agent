"""
MicroSandbox安全沙箱封装

提供安全的Python代码执行环境，支持会话隔离。
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from types import ModuleType

from ..config.settings import get_settings
from ..session import get_current_session

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """代码执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0


class DataAgentSandbox:
    """
    数据分析Agent的安全沙箱

    使用MicroSandbox提供硬件级别的代码隔离执行环境。
    支持会话隔离，每个会话使用独立的沙箱实例。
    """

    def __init__(
        self,
        name: Optional[str] = None,
        memory: Optional[int] = None,
        cpus: int = 2,
        timeout: Optional[int] = None,
        session_id: Optional[str] = None,
    ):
        """
        初始化沙箱

        Args:
            name: 沙箱名称，不提供则从当前会话生成
            memory: 内存限制（MB），不提供则使用配置值
            cpus: CPU核心数
            timeout: 执行超时时间（秒），不提供则使用配置值
            session_id: 会话 ID，用于隔离
        """
        # 获取当前会话
        session = get_current_session()
        self.settings = get_settings()

        # 确定沙箱名称（优先使用会话名称）
        if name:
            self.name = name
        elif session:
            self.name = session.get_sandbox_name()
        else:
            self.name = f"sandbox_{session_id}" if session_id else "data_agent"

        # 优先使用参数，否则使用 settings 配置
        self.memory = memory if memory is not None else self.settings.sandbox_memory
        self.cpus = cpus
        self.timeout = timeout if timeout is not None else self.settings.sandbox_timeout
        self._sandbox = None
        self._session = session

        # 设置导出目录（用于 volume 挂载）
        if session:
            self.export_dir = session.export_dir
            self.workspace_dir = session.workspace_dir
        else:
            self.export_dir = Path.home() / ".data_agent" / "exports"
            self.workspace_dir = Path.home() / ".data_agent" / "workspace"
            self.export_dir.mkdir(parents=True, exist_ok=True)
            self.workspace_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, code: str) -> ExecutionResult:
        """
        在沙箱中执行Python代码

        Args:
            code: Python代码

        Returns:
            ExecutionResult: 执行结果
        """
        import time
        start_time = time.time()

        # 检查配置是否禁用沙箱
        if not self.settings.sandbox_enabled:
            return await self._execute_local(code, start_time)

        # 检查会话中沙箱是否已标记为不可用（避免重复尝试连接）
        if self._session and not self._session.is_sandbox_available():
            return await self._execute_local(code, start_time)

        try:
            from microsandbox import PythonSandbox

            logger.debug(f"创建沙箱: {self.name}, 导出目录: {self.export_dir}")

            # 使用 async with 语法创建和管理沙箱
            # 沙箱名称使用会话唯一名称，实现会话隔离
            async with PythonSandbox.create(
                name=self.name,
                server_url=self.settings.sandbox_server_url or None,
                api_key=self.settings.sandbox_api_key or None,
            ) as sandbox:
                # 执行代码
                exec_result = await asyncio.wait_for(
                    sandbox.run(code),
                    timeout=self.timeout
                )
                output = await exec_result.output()

                return ExecutionResult(
                    success=True,
                    output=output,
                    execution_time=time.time() - start_time
                )

        except ImportError:
            logger.warning("MicroSandbox未安装，将使用本地执行模式")
            # 标记沙箱为不可用，后续不再重试
            if self._session:
                self._session.mark_sandbox_unavailable("MicroSandbox 未安装")
            return await self._execute_local(code, start_time)
        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                output="",
                error=f"执行超时（{self.timeout}秒）",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            logger.warning(f"MicroSandbox执行失败: {e}，将使用本地执行模式")
            # 标记沙箱为不可用，后续不再重试
            if self._session:
                self._session.mark_sandbox_unavailable(str(e))
            return await self._execute_local(code, start_time)

    async def _execute_local(self, code: str, start_time: float) -> ExecutionResult:
        """
        本地执行Python代码（作为回退方案）

        Args:
            code: Python代码
            start_time: 开始时间

        Returns:
            ExecutionResult: 执行结果
        """
        import time
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # 创建受限的全局命名空间
        restricted_globals = {
            "__builtins__": {
                "__import__": __import__,  # 支持 import 语句
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "bool": bool,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "isinstance": isinstance,
                "type": type,
                "hasattr": hasattr,
                "getattr": getattr,
                "setattr": setattr,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
                "AttributeError": AttributeError,
                "RuntimeError": RuntimeError,
                "StopIteration": StopIteration,
            },
            "__name__": "__main__",
        }

        # 注入导出目录变量，让代码知道文件应该保存到哪里
        restricted_globals["EXPORT_DIR"] = str(self.export_dir)

        # 预加载 os 模块（用于路径操作）
        import os
        restricted_globals["os"] = os

        # 从会话中注入已保存的变量（变量持久化）
        if self._session:
            session_context = self._session.get_execution_context()
            restricted_globals.update(session_context)
            logger.debug(f"注入会话变量: {list(session_context.keys())}")

        # 预加载常用数据分析库
        try:
            import pandas as pd
            import numpy as np
            restricted_globals["pd"] = pd
            restricted_globals["pandas"] = pd
            restricted_globals["np"] = np
            restricted_globals["numpy"] = np
        except ImportError:
            pass

        try:
            import scipy
            from scipy import stats
            restricted_globals["scipy"] = scipy
            restricted_globals["stats"] = stats
        except ImportError:
            pass

        try:
            import sklearn
            from sklearn import cluster, preprocessing, model_selection
            restricted_globals["sklearn"] = sklearn
        except ImportError:
            pass

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, restricted_globals)

            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()

            # 提取并保存用户变量到会话（变量持久化）
            if self._session:
                self._save_user_variables(restricted_globals)

            return ExecutionResult(
                success=True,
                output=output,
                error=error if error else None,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=str(e),
                execution_time=time.time() - start_time
            )

    def _save_user_variables(self, namespace: Dict[str, Any]) -> None:
        """
        从执行命名空间中提取用户变量并保存到会话

        Args:
            namespace: 代码执行后的命名空间
        """
        # 需要排除的系统变量和预加载模块
        excluded_names = {
            # 内置变量
            "__builtins__", "__name__", "__doc__", "__package__",
            "__loader__", "__spec__", "__annotations__", "__cached__",
            # 预加载模块
            "pd", "pandas", "np", "numpy", "os", "scipy", "stats", "sklearn",
            # 注入变量
            "EXPORT_DIR",
        }

        # 允许保存的类型
        allowed_types = (
            int, float, str, bool, list, dict, tuple, set,
        )

        # 尝试添加 pandas/numpy 类型
        try:
            import pandas as pd
            import numpy as np
            allowed_types = allowed_types + (pd.DataFrame, pd.Series, np.ndarray)
        except ImportError:
            pass

        user_variables = {}
        for name, value in namespace.items():
            # 跳过私有变量
            if name.startswith("_"):
                continue
            # 跳过系统变量
            if name in excluded_names:
                continue
            # 跳过模块类型
            if isinstance(value, ModuleType):
                continue
            # 跳过函数和类
            if callable(value) and not isinstance(value, type):
                continue
            # 只保存允许的类型
            if isinstance(value, allowed_types):
                user_variables[name] = value

        if user_variables and self._session:
            self._session.update_execution_context(user_variables)
            logger.debug(f"保存用户变量: {list(user_variables.keys())}")

    async def execute_with_data(
        self,
        code: str,
        data: Dict[str, Any]
    ) -> ExecutionResult:
        """
        执行代码并传入数据

        Args:
            code: Python代码
            data: 数据字典，将作为变量注入代码环境

        Returns:
            ExecutionResult: 执行结果
        """
        # 构建数据注入代码
        data_setup = []
        for name, value in data.items():
            if isinstance(value, str):
                data_setup.append(f'{name} = """{value}"""')
            else:
                import json
                data_setup.append(f'{name} = {json.dumps(value)}')

        full_code = "\n".join(data_setup) + "\n" + code
        return await self.execute(full_code)

    def get_export_path(self, filename: str) -> Path:
        """
        获取导出文件的完整路径

        Args:
            filename: 文件名

        Returns:
            完整的文件路径
        """
        return self.export_dir / filename

    async def close(self):
        """关闭沙箱"""
        if self._sandbox is not None:
            try:
                await self._sandbox.stop()
            except Exception as e:
                logger.warning(f"关闭沙箱时出错: {e}")
            finally:
                self._sandbox = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()


# 同步版本的沙箱执行函数
def execute_python_sync(code: str, timeout: int = 30) -> ExecutionResult:
    """
    同步执行Python代码

    Args:
        code: Python代码
        timeout: 超时时间

    Returns:
        ExecutionResult: 执行结果
    """
    sandbox = DataAgentSandbox(timeout=timeout)

    # 使用 asyncio.run() 自动管理事件循环的生命周期
    # 这会创建新的事件循环，执行协程，然后正确关闭循环
    return asyncio.run(sandbox.execute(code))
