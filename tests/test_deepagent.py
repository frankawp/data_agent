"""
DeepAgent 测试用例

测试基于 DeepAgent 框架重构后的数据分析功能。
"""

import pytest
from unittest.mock import patch, MagicMock


class TestDataAgentImport:
    """测试模块导入"""

    def test_import_data_agent(self):
        """测试 DataAgent 类导入"""
        from data_agent.agent import DataAgent
        assert DataAgent is not None

    def test_import_create_data_agent(self):
        """测试 create_data_agent 函数导入"""
        from data_agent.agent import create_data_agent
        assert create_data_agent is not None

    def test_import_version(self):
        """测试版本号"""
        from data_agent import __version__
        assert __version__ == "0.2.0"


class TestToolsImport:
    """测试工具导入"""

    def test_import_sql_tools(self):
        """测试 SQL 工具导入"""
        from data_agent.tools import (
            execute_sql,
            list_tables,
            describe_table,
        )
        assert execute_sql is not None
        assert list_tables is not None
        assert describe_table is not None

    def test_import_data_tools(self):
        """测试数据分析工具导入"""
        from data_agent.tools import (
            analyze_dataframe,
            statistical_analysis,
        )
        assert analyze_dataframe is not None

    def test_import_ml_tools(self):
        """测试机器学习工具导入"""
        from data_agent.tools import train_model, predict, evaluate_model
        assert train_model is not None

    def test_import_graph_tools(self):
        """测试图分析工具导入"""
        from data_agent.tools import create_graph, graph_analysis
        assert create_graph is not None


class TestSQLTools:
    """测试 SQL 工具功能"""

    def test_list_tables(self):
        """测试列出表"""
        from data_agent.tools import list_tables

        result = list_tables.invoke({})
        assert "customer" in result
        assert "film" in result

    def test_describe_table(self):
        """测试描述表结构"""
        from data_agent.tools import describe_table

        result = describe_table.invoke({"table_name": "customer"})
        assert "customer_id" in result
        assert "first_name" in result

    def test_execute_sql_select(self):
        """测试执行 SELECT 查询"""
        from data_agent.tools import execute_sql

        result = execute_sql.invoke({"query": "SELECT COUNT(*) as cnt FROM customer"})
        assert "599" in result

    def test_execute_sql_blocks_dangerous(self):
        """测试阻止危险 SQL"""
        from data_agent.tools import execute_sql

        result = execute_sql.invoke({"query": "DROP TABLE customer"})
        assert "错误" in result or "不允许" in result or "仅支持" in result


class TestDataAgentCreation:
    """测试 DataAgent 创建"""

    def test_create_data_agent(self):
        """测试创建 DataAgent 函数"""
        from data_agent.agent import create_data_agent

        agent = create_data_agent()
        assert agent is not None
        # 验证是 CompiledStateGraph 类型
        assert hasattr(agent, "invoke")

    def test_data_agent_class(self):
        """测试 DataAgent 类实例化"""
        from data_agent.agent import DataAgent

        agent = DataAgent()
        assert agent is not None
        assert hasattr(agent, "chat")
        assert hasattr(agent, "clear_history")
        assert hasattr(agent, "invoke")

    def test_data_agent_clear_history(self):
        """测试清除历史"""
        from data_agent.agent import DataAgent

        agent = DataAgent()
        agent._messages = [{"role": "user", "content": "test"}]
        agent.clear_history()
        assert agent._messages == []


class TestConfigImport:
    """测试配置导入"""

    def test_import_settings(self):
        """测试 Settings 导入"""
        from data_agent.config import get_settings

        settings = get_settings()
        assert settings is not None
        assert hasattr(settings, "zhipu_model")
        assert hasattr(settings, "zhipu_api_key")

    def test_import_prompts(self):
        """测试提示模板导入"""
        from data_agent.config import SYSTEM_PROMPTS

        assert "main" in SYSTEM_PROMPTS
        assert "sql" in SYSTEM_PROMPTS
        assert "ml" in SYSTEM_PROMPTS


class TestMainEntry:
    """测试主入口"""

    def test_import_main(self):
        """测试 main 模块导入"""
        from data_agent.main import main
        assert main is not None

    def test_import_helpers(self):
        """测试辅助函数导入"""
        from data_agent.main import print_welcome, print_help, print_config
        assert print_welcome is not None
        assert print_help is not None
        assert print_config is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
