"""
沙箱模块测试用例

测试 MicroSandbox 安全沙箱和会话管理功能。
"""

import asyncio
import pytest
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


class TestSandboxImport:
    """测试沙箱模块导入"""

    def test_import_sandbox(self):
        """测试沙箱模块导入"""
        from data_agent.sandbox import DataAgentSandbox, ExecutionResult, execute_python_sync
        assert DataAgentSandbox is not None
        assert ExecutionResult is not None
        assert execute_python_sync is not None


class TestExecutionResult:
    """测试 ExecutionResult 数据类"""

    def test_execution_result_success(self):
        """测试成功的执行结果"""
        from data_agent.sandbox import ExecutionResult

        result = ExecutionResult(
            success=True,
            output="Hello World",
            execution_time=0.1
        )
        assert result.success is True
        assert result.output == "Hello World"
        assert result.error is None
        assert result.execution_time == 0.1

    def test_execution_result_failure(self):
        """测试失败的执行结果"""
        from data_agent.sandbox import ExecutionResult

        result = ExecutionResult(
            success=False,
            output="",
            error="SyntaxError: invalid syntax",
            execution_time=0.05
        )
        assert result.success is False
        assert result.error == "SyntaxError: invalid syntax"


class TestDataAgentSandbox:
    """测试 DataAgentSandbox 类"""

    def test_sandbox_creation(self):
        """测试沙箱创建"""
        from data_agent.sandbox import DataAgentSandbox

        sandbox = DataAgentSandbox(name="test_sandbox", timeout=10)
        assert sandbox.name == "test_sandbox"
        assert sandbox.timeout == 10

    def test_sandbox_default_name(self):
        """测试沙箱默认名称"""
        from data_agent.sandbox import DataAgentSandbox
        from data_agent.session import SessionManager

        # 创建会话
        session = SessionManager()
        sandbox = DataAgentSandbox()
        assert sandbox.name == session.get_sandbox_name()

    @pytest.mark.asyncio
    async def test_sandbox_local_execution(self):
        """测试本地执行模式"""
        from data_agent.sandbox import DataAgentSandbox

        # 禁用 MicroSandbox 使用本地执行
        with patch('data_agent.sandbox.microsandbox.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                sandbox_enabled=False,
                sandbox_server_url=None,
                sandbox_api_key=None
            )

            sandbox = DataAgentSandbox(timeout=10)
            result = await sandbox.execute("print('Hello')")

            assert result.success is True
            assert "Hello" in result.output

    @pytest.mark.asyncio
    async def test_sandbox_local_execution_math(self):
        """测试本地执行数学计算"""
        from data_agent.sandbox import DataAgentSandbox

        with patch('data_agent.sandbox.microsandbox.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                sandbox_enabled=False,
                sandbox_server_url=None,
                sandbox_api_key=None
            )

            sandbox = DataAgentSandbox(timeout=10)
            result = await sandbox.execute("print(sum(range(10)))")

            assert result.success is True
            assert "45" in result.output

    @pytest.mark.asyncio
    async def test_sandbox_local_execution_error(self):
        """测试本地执行错误处理"""
        from data_agent.sandbox import DataAgentSandbox

        with patch('data_agent.sandbox.microsandbox.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                sandbox_enabled=False,
                sandbox_server_url=None,
                sandbox_api_key=None
            )

            sandbox = DataAgentSandbox(timeout=10)
            result = await sandbox.execute("raise ValueError('test error')")

            assert result.success is False
            assert "test error" in result.error

    @pytest.mark.asyncio
    async def test_sandbox_with_data(self):
        """测试带数据执行"""
        from data_agent.sandbox import DataAgentSandbox

        with patch('data_agent.sandbox.microsandbox.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                sandbox_enabled=False,
                sandbox_server_url=None,
                sandbox_api_key=None
            )

            sandbox = DataAgentSandbox(timeout=10)
            result = await sandbox.execute_with_data(
                "print(len(data))",
                {"data": [1, 2, 3]}
            )

            assert result.success is True
            assert "3" in result.output


class TestExecutePythonSync:
    """测试同步执行函数"""

    def test_execute_python_sync(self):
        """测试同步执行 Python 代码"""
        from data_agent.sandbox import execute_python_sync

        with patch('data_agent.sandbox.microsandbox.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                sandbox_enabled=False,
                sandbox_server_url=None,
                sandbox_api_key=None
            )

            result = execute_python_sync("print('sync test')")
            assert result.success is True
            assert "sync test" in result.output


class TestSessionManager:
    """测试会话管理器"""

    def test_session_creation(self):
        """测试会话创建"""
        from data_agent.session import SessionManager

        session = SessionManager()
        assert session.session_id is not None
        assert session.session_id.startswith("session_")

    def test_session_custom_id(self):
        """测试自定义会话 ID"""
        from data_agent.session import SessionManager

        session = SessionManager(session_id="custom_session")
        assert session.session_id == "custom_session"

    def test_session_dirs_created(self):
        """测试会话目录创建"""
        from data_agent.session import SessionManager

        session = SessionManager()
        assert session.session_dir.exists()
        assert session.export_dir.exists()
        assert session.workspace_dir.exists()

        # 清理
        shutil.rmtree(session.session_dir)

    def test_session_sandbox_name(self):
        """测试沙箱名称生成"""
        from data_agent.session import SessionManager

        session = SessionManager()
        sandbox_name = session.get_sandbox_name()
        assert sandbox_name.startswith("sandbox_session_")

        # 清理
        shutil.rmtree(session.session_dir)

    def test_session_export_path(self):
        """测试导出路径获取"""
        from data_agent.session import SessionManager

        session = SessionManager()
        export_path = session.get_export_path("test.csv")
        assert export_path == session.export_dir / "test.csv"

        # 清理
        shutil.rmtree(session.session_dir)

    def test_session_generate_filename(self):
        """测试文件名生成"""
        from data_agent.session import SessionManager

        session = SessionManager()
        filename = session.generate_export_filename("result", "csv")
        assert filename.startswith("result_")
        assert filename.endswith(".csv")

        # 清理
        shutil.rmtree(session.session_dir)

    def test_session_list_exports(self):
        """测试导出文件列表"""
        from data_agent.session import SessionManager

        session = SessionManager()

        # 创建测试文件
        test_file = session.export_dir / "test.txt"
        test_file.write_text("test")

        exports = session.list_exports()
        assert len(exports) >= 1
        assert test_file in exports

        # 清理
        shutil.rmtree(session.session_dir)

    def test_session_cleanup(self):
        """测试会话清理"""
        from data_agent.session import SessionManager

        session = SessionManager()
        session_dir = session.session_dir
        assert session_dir.exists()

        session.cleanup()
        assert not session_dir.exists()

    def test_session_context_manager(self):
        """测试上下文管理器"""
        from data_agent.session import SessionManager

        with SessionManager() as session:
            assert session.session_id is not None
            session_dir = session.session_dir
            assert session_dir.exists()

        # 上下文退出后目录仍然存在（不自动清理）
        assert session_dir.exists()
        # 手动清理
        shutil.rmtree(session_dir)


class TestGetCurrentSession:
    """测试获取当前会话"""

    def test_get_current_session(self):
        """测试获取当前会话"""
        from data_agent.session import SessionManager, get_current_session

        session = SessionManager()
        current = get_current_session()
        assert current is session

        # 清理
        shutil.rmtree(session.session_dir)


class TestSandboxSessionIntegration:
    """测试沙箱与会话的集成"""

    def test_sandbox_uses_session_export_dir(self):
        """测试沙箱使用会话导出目录"""
        from data_agent.sandbox import DataAgentSandbox
        from data_agent.session import SessionManager

        session = SessionManager()
        sandbox = DataAgentSandbox()

        assert sandbox.export_dir == session.export_dir
        assert sandbox.workspace_dir == session.workspace_dir

        # 清理
        shutil.rmtree(session.session_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
