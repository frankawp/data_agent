"""
多 Agent 数据分析实现

使用 DeepAgents 框架的 subagents 功能，实现多 Agent 协作的数据分析。
主 Agent 作为协调者，将任务分配给专业的子代理处理。

支持配置化：
1. 从 YAML 配置文件加载子代理定义
2. 支持 LLM Profile 为不同子代理指定不同模型
3. 无配置时回退到默认硬编码配置
"""

import logging
from typing import Optional

from deepagents import create_deep_agent
from langgraph.graph.state import CompiledStateGraph

from .backend import create_session_backend
from .llm import create_llm, create_llm_factory
from .middleware import SubAgentToolMonitor, SubAgentCallbackHolder
from .factory import get_subagent_factory
from ..config.loader import get_config_loader

logger = logging.getLogger(__name__)


# 注意：协调者提示词已迁移到 config/prompts/coordinator.md
# 当配置文件不存在时，factory.get_coordinator_prompt() 会返回 None，需要有默认值
DEFAULT_COORDINATOR_PROMPT = "你是一个数据分析任务的协调者，负责将用户任务分配给合适的子代理并汇总结果。"


def create_multi_agent(
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    callback_holder: Optional[SubAgentCallbackHolder] = None,
) -> CompiledStateGraph:
    """
    创建多 Agent 数据分析器

    使用 DeepAgents 的 subagents 功能，主 Agent 可以将任务委托给专业子代理。

    配置优先级：
    1. 函数参数（model, system_prompt）
    2. YAML 配置文件
    3. 硬编码默认值

    Args:
        model: 模型名称，默认使用配置中的模型
        system_prompt: 自定义协调者提示，默认使用配置或内置提示
        callback_holder: 子代理回调持有者，支持动态更新回调函数

    Returns:
        CompiledStateGraph: 编译后的多 Agent 图
    """
    # 获取配置加载器和子代理工厂
    config_loader = get_config_loader()
    factory = get_subagent_factory()

    # 检查是否有自定义配置
    has_config = config_loader.has_subagents_config()
    if has_config:
        logger.info("使用 YAML 配置创建多 Agent 系统")
    else:
        logger.info("使用默认配置创建多 Agent 系统")

    # 初始化 LLM
    llm = create_llm(model=model) if model else create_llm()

    # 创建 LLM 工厂函数（用于为子代理创建专用 LLM）
    llm_factory = create_llm_factory() if has_config else None

    # 从工厂获取子代理配置
    subagents_raw = factory.create_all_subagents(llm_factory=llm_factory)

    # 为子代理添加工具监听中间件
    def add_monitor(config: dict) -> dict:
        """为子代理配置添加监听中间件"""
        if callback_holder is None:
            return config

        # 创建监听中间件（使用 callback_holder 支持动态回调）
        monitor = SubAgentToolMonitor(
            subagent_name=config["name"],
            callback_holder=callback_holder,
        )

        # 合并已有的中间件
        existing_middleware = config.get("middleware", [])
        return {
            **config,
            "middleware": [monitor] + list(existing_middleware),
        }

    # 为所有子代理添加监听中间件
    subagents = [add_monitor(config) for config in subagents_raw]

    # 获取协调者提示词
    # 优先级：函数参数 > 配置文件 > 默认提示
    if system_prompt:
        coordinator_prompt = system_prompt
    else:
        config_prompt = factory.get_coordinator_prompt()
        coordinator_prompt = config_prompt if config_prompt else DEFAULT_COORDINATOR_PROMPT

    # 创建多 Agent，传入会话后端
    agent = create_deep_agent(
        model=llm,
        system_prompt=coordinator_prompt,
        subagents=subagents,
        backend=create_session_backend,  # 使用会话后端工厂函数
    )

    return agent
