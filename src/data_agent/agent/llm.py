"""
LLM 封装

支持所有 OpenAI API 兼容的模型（DeepSeek、智谱AI、OpenAI 等）。
支持 LLM Profile 配置，允许为不同子代理指定不同模型。
"""

import logging
from typing import Optional, List, Any

from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from ..config.settings import get_settings
from ..config.schema import LLMProfile

logger = logging.getLogger(__name__)


def create_llm(
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    streaming: bool = False,
    **kwargs
) -> ChatOpenAI:
    """
    创建 LLM 实例

    支持所有 OpenAI API 兼容的模型提供商：
    - DeepSeek: https://api.deepseek.com
    - 智谱 AI: https://open.bigmodel.cn/api/paas/v4/
    - OpenAI: https://api.openai.com/v1
    - 其他兼容接口...

    Args:
        model: 模型名称，默认使用配置中的模型
        temperature: 温度参数，控制输出随机性
        max_tokens: 最大输出token数
        streaming: 是否启用流式输出
        **kwargs: 其他ChatOpenAI参数

    Returns:
        ChatOpenAI实例
    """
    settings = get_settings()

    return ChatOpenAI(
        model=model or settings.model,
        openai_api_key=settings.api_key,
        openai_api_base=settings.base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
        **kwargs
    )


def create_llm_with_tools(
    tools: List[Any],
    model: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
) -> ChatOpenAI:
    """
    创建带有工具绑定的 LLM 实例

    Args:
        tools: 工具列表
        model: 模型名称
        temperature: 温度参数
        **kwargs: 其他参数

    Returns:
        带有工具绑定的ChatOpenAI实例
    """
    llm = create_llm(model=model, temperature=temperature, **kwargs)
    return llm.bind_tools(tools)


class ChatModel:
    """
    聊天模型封装类

    提供更高级的功能封装，如对话历史管理、错误重试等。
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
    ):
        """
        初始化聊天模型

        Args:
            model: 模型名称
            temperature: 温度参数
            max_retries: 最大重试次数
        """
        self.llm = create_llm(model=model, temperature=temperature)
        self.max_retries = max_retries
        self._conversation_history: List[BaseMessage] = []

    @property
    def model_name(self) -> str:
        """获取模型名称"""
        return self.llm.model_name

    def invoke(self, messages: List[BaseMessage], **kwargs) -> BaseMessage:
        """
        调用模型

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            模型响应消息
        """
        return self.llm.invoke(messages, **kwargs)

    async def ainvoke(self, messages: List[BaseMessage], **kwargs) -> BaseMessage:
        """
        异步调用模型

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            模型响应消息
        """
        return await self.llm.ainvoke(messages, **kwargs)

    def stream(self, messages: List[BaseMessage], **kwargs):
        """
        流式调用模型

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            模型响应片段
        """
        streaming_llm = create_llm(streaming=True)
        for chunk in streaming_llm.stream(messages, **kwargs):
            yield chunk

    async def astream(self, messages: List[BaseMessage], **kwargs):
        """
        异步流式调用模型

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            模型响应片段
        """
        streaming_llm = create_llm(streaming=True)
        async for chunk in streaming_llm.astream(messages, **kwargs):
            yield chunk

    def chat(self, user_message: str) -> str:
        """
        简单聊天接口，自动管理对话历史

        Args:
            user_message: 用户消息

        Returns:
            模型响应文本
        """
        from langchain_core.messages import HumanMessage, AIMessage

        self._conversation_history.append(HumanMessage(content=user_message))
        response = self.invoke(self._conversation_history)
        self._conversation_history.append(response)

        return response.content

    def clear_history(self):
        """清除对话历史"""
        self._conversation_history = []

    def bind_tools(self, tools: List[Any]) -> ChatOpenAI:
        """
        绑定工具

        Args:
            tools: 工具列表

        Returns:
            带有工具绑定的LLM
        """
        return self.llm.bind_tools(tools)


# 便捷函数
def get_llm() -> ChatOpenAI:
    """获取默认LLM实例"""
    return create_llm()


def get_streaming_llm() -> ChatOpenAI:
    """获取流式输出LLM实例"""
    return create_llm(streaming=True)


def create_llm_from_profile(profile: LLMProfile) -> ChatOpenAI:
    """
    根据 LLM Profile 创建实例

    Profile 中未指定的参数会使用全局配置。

    Args:
        profile: LLM Profile 配置对象

    Returns:
        ChatOpenAI 实例
    """
    settings = get_settings()

    return ChatOpenAI(
        model=profile.model,
        openai_api_key=profile.api_key or settings.api_key,
        openai_api_base=profile.base_url or settings.base_url,
        temperature=profile.temperature,
        max_tokens=profile.max_tokens,
    )


def create_llm_factory():
    """
    创建 LLM 工厂函数

    返回一个函数，根据 profile 名称创建 LLM 实例。
    用于子代理工厂的 llm_factory 参数。

    Returns:
        工厂函数: (profile_name: str) -> ChatOpenAI
    """
    from ..config.loader import get_agent_config

    def factory(profile_name: str) -> Optional[ChatOpenAI]:
        """根据 profile 名称创建 LLM"""
        config = get_agent_config()
        profile = config.get_llm_profile(profile_name)

        if profile:
            return create_llm_from_profile(profile)

        logger.warning(f"LLM Profile 不存在: {profile_name}，使用默认配置")
        return create_llm()

    return factory
