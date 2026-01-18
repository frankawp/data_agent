"""
子代理工厂

根据配置动态创建子代理配置字典，供 DeepAgents 框架使用。
支持：
1. 从 YAML 配置创建子代理
2. 回退到默认硬编码配置
3. 自动生成协调者提示词
"""

import logging
from typing import Any, Dict, List, Optional

from ..config.loader import get_agent_config
from ..config.schema import AgentSystemConfig, SubAgentConfig
from ..tools.registry import get_tool_registry

logger = logging.getLogger(__name__)


def _get_default_subagent_configs() -> List[Dict[str, Any]]:
    """
    获取默认的硬编码子代理配置

    用于向后兼容：当没有 YAML 配置时，使用这些默认配置。

    Returns:
        子代理配置字典列表
    """
    from .subagents import (
        DATA_COLLECTOR_CONFIG,
        DATA_ANALYZER_CONFIG,
        REPORT_WRITER_CONFIG,
    )

    return [
        DATA_COLLECTOR_CONFIG,
        DATA_ANALYZER_CONFIG,
        REPORT_WRITER_CONFIG,
    ]


class SubAgentFactory:
    """
    子代理工厂

    根据配置文件动态创建子代理配置。

    使用示例:
        factory = get_subagent_factory()

        # 获取所有子代理配置
        subagents = factory.create_all_subagents()

        # 获取协调者提示词
        prompt = factory.get_coordinator_prompt()
    """

    def __init__(self):
        self._registry = get_tool_registry()

    def create_subagent_config(
        self,
        name: str,
        config: SubAgentConfig,
        llm_factory: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        根据配置创建单个子代理配置字典

        Args:
            name: 子代理名称
            config: 子代理配置对象
            llm_factory: LLM 创建工厂函数，接收 profile 名称返回 LLM

        Returns:
            DeepAgents 格式的子代理配置字典
        """
        # 获取工具列表
        tools = self._registry.get_many(config.tools)

        if not tools:
            logger.warning(f"子代理 {name} 没有可用的工具")

        # 构建配置字典
        subagent_config = {
            "name": name,
            "description": config.description,
            "system_prompt": config.system_prompt or "",
            "tools": tools,
        }

        # 如果有 LLM 工厂函数且指定了非默认 profile，创建专用 LLM
        if llm_factory and config.llm != "default":
            try:
                llm = llm_factory(config.llm)
                if llm:
                    subagent_config["model"] = llm
            except Exception as e:
                logger.warning(f"为子代理 {name} 创建 LLM 失败: {e}")

        return subagent_config

    def create_all_subagents(
        self,
        llm_factory: Optional[callable] = None,
    ) -> List[Dict[str, Any]]:
        """
        创建所有配置的子代理

        Args:
            llm_factory: LLM 创建工厂函数

        Returns:
            子代理配置字典列表
        """
        config = get_agent_config()

        # 如果没有配置子代理，使用默认配置
        if not config.subagents:
            logger.info("使用默认子代理配置")
            return _get_default_subagent_configs()

        # 应用工具配置
        self._registry.apply_config(config.tools)

        # 创建所有子代理
        subagents = []
        for name, subagent_config in config.subagents.items():
            subagent = self.create_subagent_config(
                name=name,
                config=subagent_config,
                llm_factory=llm_factory,
            )
            subagents.append(subagent)
            logger.debug(f"已创建子代理配置: {name}")

        return subagents

    def get_coordinator_prompt(self) -> Optional[str]:
        """
        获取协调者提示词

        优先级：
        1. 配置文件中的 system_prompt
        2. 配置文件中的 prompt_file 加载的内容
        3. 如果 use_default_prompt 为 True，返回 None（使用默认）
        4. 自动生成的提示词

        Returns:
            协调者提示词，None 表示使用默认
        """
        config = get_agent_config()
        coord = config.coordinator

        # 如果有配置的提示词
        if coord.system_prompt:
            return coord.system_prompt

        # 如果使用默认提示词
        if coord.use_default_prompt:
            return None

        # 自动生成协调者提示词
        return self._generate_coordinator_prompt(config)

    def _generate_coordinator_prompt(self, config: AgentSystemConfig) -> str:
        """根据子代理配置自动生成协调者提示词"""
        subagent_docs = []
        for name, subagent in config.subagents.items():
            subagent_docs.append(f"### {name}\n- 功能：{subagent.description}")

        subagents_section = "\n\n".join(subagent_docs) if subagent_docs else "无配置的子代理"

        return f"""你是一个数据分析任务的协调者。

## 职责
1. 理解用户的数据分析需求
2. 将任务分配给合适的专业子代理
3. 汇总各子代理的结果
4. 向用户提供清晰的最终答案

## 可用子代理

{subagents_section}

## 使用 task() 工具调用子代理
- `agent_name`: 子代理名称
- `task`: 详细的任务描述，包含所有必要的上下文

## 重要提示
- 复杂任务请使用子代理
- 简单问题可以直接回答
- 将前一个子代理的关键结果包含在下一个任务描述中
"""


# 全局单例
_factory: Optional[SubAgentFactory] = None


def get_subagent_factory() -> SubAgentFactory:
    """获取子代理工厂单例"""
    global _factory
    if _factory is None:
        _factory = SubAgentFactory()
    return _factory


def create_subagents_from_config(
    llm_factory: Optional[callable] = None,
) -> List[Dict[str, Any]]:
    """
    便捷函数：从配置创建所有子代理

    Args:
        llm_factory: LLM 创建工厂函数

    Returns:
        子代理配置字典列表
    """
    return get_subagent_factory().create_all_subagents(llm_factory)


def get_coordinator_prompt_from_config() -> Optional[str]:
    """
    便捷函数：从配置获取协调者提示词

    Returns:
        协调者提示词，None 表示使用默认
    """
    return get_subagent_factory().get_coordinator_prompt()
