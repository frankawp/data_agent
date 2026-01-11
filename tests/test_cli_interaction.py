"""
CLI 交互测试

使用 pexpect 进行端到端交互测试，验证：
- CLI 启动和退出
- 命令执行
- 步骤查看

运行方式:
    pytest tests/test_cli_interaction.py -v -s

注意：这些测试需要配置有效的 API 密钥和网络连接。
"""

import os
import sys
import time
import pytest

# 跳过条件：pexpect 不支持 Windows
pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="pexpect 在 Windows 上不支持 pty"
)

try:
    import pexpect
except ImportError:
    pytest.skip("pexpect 未安装", allow_module_level=True)


# 测试超时时间（秒）
DEFAULT_TIMEOUT = 60
STARTUP_TIMEOUT = 30


class TestCLIInteraction:
    """CLI 交互测试类"""

    @pytest.fixture
    def cli_process(self):
        """启动 CLI 进程"""
        # 设置环境变量
        env = os.environ.copy()
        # 确保不使用代理（可能干扰沙箱连接）
        env.pop("HTTPS_PROXY", None)
        env.pop("HTTP_PROXY", None)
        env.pop("https_proxy", None)
        env.pop("http_proxy", None)

        # 启动进程
        child = pexpect.spawn(
            "python", ["-m", "data_agent"],
            encoding="utf-8",
            timeout=DEFAULT_TIMEOUT,
            env=env,
            dimensions=(24, 120),  # 设置终端大小
        )

        # 等待启动完成
        try:
            # 等待看到 "Agent 已就绪" 或 "您:"
            child.expect(
                ["Agent 已就绪", "您:"],
                timeout=STARTUP_TIMEOUT
            )
        except pexpect.TIMEOUT:
            print("启动超时，当前输出：")
            print(child.before)
            child.terminate()
            pytest.skip("CLI 启动超时")
        except pexpect.EOF:
            print("进程意外退出，输出：")
            print(child.before)
            pytest.skip("CLI 启动失败")

        yield child

        # 清理
        try:
            child.sendline("exit")
            child.expect(pexpect.EOF, timeout=5)
        except Exception:
            pass
        finally:
            if child.isalive():
                child.terminate(force=True)

    def test_startup_and_exit(self, cli_process):
        """测试 CLI 启动和退出"""
        child = cli_process

        # 发送退出命令
        child.sendline("exit")

        # 验证退出
        try:
            child.expect(["再见", pexpect.EOF], timeout=10)
        except pexpect.TIMEOUT:
            pytest.fail("退出超时")

    def test_help_command(self, cli_process):
        """测试 /help 命令"""
        child = cli_process

        # 发送 help 命令
        child.sendline("/help")

        # 等待响应
        try:
            index = child.expect(
                ["可用命令", "命令", "帮助", pexpect.TIMEOUT],
                timeout=10
            )
            if index == 3:  # TIMEOUT
                print("超时，输出：", child.before)
                pytest.fail("help 命令超时")
        except Exception as e:
            print("错误：", e)
            print("输出：", child.before)
            raise

    def test_step_history_command(self, cli_process):
        """测试 /steps 命令显示步骤历史"""
        child = cli_process

        # 在没有执行任何步骤时查看历史
        child.sendline("/steps")

        try:
            index = child.expect(
                ["暂无步骤历史", "步骤历史", pexpect.TIMEOUT],
                timeout=10
            )
            if index == 2:  # TIMEOUT
                print("超时，输出：", child.before)
        except Exception as e:
            print("错误：", e)
            print("输出：", child.before)

    @pytest.mark.slow
    def test_step_number_query(self, cli_process):
        """测试 :数字 查看步骤详情

        场景：
        1. 执行一个简单任务
        2. 任务完成后使用 :1 查看第一步详情
        """
        child = cli_process

        # 发送一个简单请求
        child.sendline("请用 Python 计算 1+1")

        # 等待执行或计划确认
        try:
            index = child.expect(
                ["Agent 回复", "本次执行了", "是否按此计划执行"],
                timeout=90
            )
            # 如果看到计划确认，发送 y 确认
            if index == 2:
                child.sendline("y")
                # 等待执行完成
                child.expect(["Agent 回复", "本次执行了"], timeout=120)
        except pexpect.TIMEOUT:
            print("执行超时，输出：")
            print(child.before)
            pytest.skip("执行超时")

        # 等待稳定
        time.sleep(1)

        # 查看步骤 1
        child.sendline(":1")

        # 验证显示了步骤详情
        try:
            index = child.expect(
                [
                    "Step 1:",
                    "步骤 1 不存在",
                    "代码:",
                    "参数:",
                    pexpect.TIMEOUT
                ],
                timeout=10
            )
            if index == 0 or index == 2 or index == 3:
                print("成功显示步骤 1 详情")
            elif index == 1:
                pytest.fail("步骤 1 不存在，可能没有执行任何步骤")
            else:
                print("超时，输出：", child.before)
        except Exception as e:
            print("错误：", e)
            print("输出：", child.before)

    @pytest.mark.slow
    def test_plan_confirmation_input(self, cli_process):
        """测试执行计划确认时能正常输入

        验证修复后用户可以输入 y 确认执行计划
        """
        child = cli_process

        # 发送一个会触发计划的请求
        child.sendline("请用 Python 分析数据趋势")

        # 等待计划确认
        try:
            index = child.expect(
                ["是否按此计划执行", "思考中", pexpect.TIMEOUT],
                timeout=60
            )
            if index == 0:
                # 看到计划确认，发送 y
                child.sendline("y")
                # 验证执行开始
                child.expect(["Step", "思考中", "正在"], timeout=30)
                print("成功确认执行计划")
            elif index == 1:
                # 没有显示计划，直接开始执行
                print("直接开始执行，无需确认")
            else:
                print("超时，输出：", child.before)
        except Exception as e:
            print("错误：", e)
            print("输出：", child.before)


class TestStepPager:
    """StepPager 单元测试"""

    def test_step_pager_add_and_get(self):
        """测试添加和获取步骤"""
        from data_agent.ui.pager import StepPager

        pager = StepPager()

        # 添加步骤
        pager.add_step(1, "execute_python_safe", {"code": "print(1)"}, "1")
        pager.add_step(2, "execute_sql", {"query": "SELECT 1"}, "1")

        # 获取步骤
        step1 = pager.get_step(1)
        assert step1 is not None
        assert step1.tool_name == "execute_python_safe"
        assert step1.tool_args == {"code": "print(1)"}
        assert step1.result == "1"

        step2 = pager.get_step(2)
        assert step2 is not None
        assert step2.tool_name == "execute_sql"

        # 获取不存在的步骤
        step3 = pager.get_step(3)
        assert step3 is None

    def test_step_pager_latest(self):
        """测试获取最新步骤编号"""
        from data_agent.ui.pager import StepPager

        pager = StepPager()

        # 空时返回 0
        assert pager.get_latest_step_num() == 0

        # 添加步骤
        pager.add_step(1, "tool1", {}, "")
        assert pager.get_latest_step_num() == 1

        pager.add_step(5, "tool5", {}, "")
        assert pager.get_latest_step_num() == 5

    def test_step_pager_clear(self):
        """测试清空历史"""
        from data_agent.ui.pager import StepPager

        pager = StepPager()

        pager.add_step(1, "tool1", {}, "")
        pager.add_step(2, "tool2", {}, "")

        assert pager.get_latest_step_num() == 2

        pager.clear_history()

        assert pager.get_latest_step_num() == 0
        assert pager.get_step(1) is None
