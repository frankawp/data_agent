"""智谱AI的LangChain兼容包装器"""

from typing import Any, List, Optional, Sequence
from pydantic import Field, PrivateAttr
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks.manager import CallbackManagerForLLMRun


class ChatZhipuAI(BaseChatModel):
    """智谱AI的LangChain兼容包装器

    支持智谱AI的GLM-4系列模型
    """

    api_key: str = Field(...)
    model: str = Field(default="glm-4")
    base_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4")
    temperature: float = Field(default=0.7)

    # 使用PrivateAttr来存储不需要验证的属性
    _client: Any = PrivateAttr(default=None)

    class Config:
        """Pydantic配置"""
        arbitrary_types_allowed = True

    def __init__(self, api_key: str, model: str = "glm-4", base_url: str = None, **kwargs):
        """初始化智谱AI

        Args:
            api_key: API密钥
            model: 模型名称（如 glm-4, glm-4-plus等）
            base_url: API基础URL
            **kwargs: 其他参数
        """
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://open.bigmodel.cn/api/paas/v4",
            **kwargs
        )

        # 导入zhipuai SDK
        try:
            from zhipuai import ZhipuAI
            self._client = ZhipuAI(api_key=api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError("请安装zhipuai包: pip install zhipuai")

    @property
    def client(self):
        """获取client属性"""
        return self._client

    @property
    def _llm_type(self) -> str:
        return "zhipu_ai"

    def _format_messages(self, messages: Sequence[BaseMessage]) -> List[dict]:
        """将LangChain消息格式转换为智谱AI格式

        Args:
            messages: LangChain消息列表

        Returns:
            智谱AI消息列表
        """
        formatted = []

        for message in messages:
            if isinstance(message, HumanMessage):
                formatted.append({
                    "role": "user",
                    "content": message.content
                })
            elif isinstance(message, AIMessage):
                formatted.append({
                    "role": "assistant",
                    "content": message.content
                })
            elif isinstance(message, SystemMessage):
                formatted.append({
                    "role": "system",
                    "content": message.content
                })

        return formatted

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """生成文本（同步版本）

        Args:
            messages: 消息列表
            stop: 停止序列
            run_manager: 回调管理器
            **kwargs: 其他参数

        Returns:
            ChatResult
        """
        # 格式化消息
        formatted_messages = self._format_messages(messages)

        # 调用智谱AI API
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=self.temperature,
                **kwargs
            )

            # 提取响应内容
            content = response.choices[0].message.content

            # 创建ChatGeneration
            generation = ChatGeneration(message=AIMessage(content=content))

            return ChatResult(generations=[generation])

        except Exception as e:
            # 返回错误消息
            error_generation = ChatGeneration(
                message=AIMessage(content=f"智谱AI调用失败: {str(e)}")
            )
            return ChatResult(generations=[error_generation])

    async def ainvoke(
        self,
        messages: Sequence[BaseMessage],
        **kwargs: Any
    ) -> AIMessage:
        """异步调用智谱AI

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            AIMessage
        """
        # 格式化消息
        formatted_messages = self._format_messages(messages)

        # 调用智谱AI API
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=self.temperature,
                **kwargs
            )

            # 提取响应内容
            content = response.choices[0].message.content

            return AIMessage(content=content)

        except Exception as e:
            # 返回错误消息
            return AIMessage(content=f"智谱AI调用失败: {str(e)}")

    def invoke(self, messages: Sequence[BaseMessage], **kwargs):
        """同步调用

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            AIMessage
        """
        result = self._generate(list(messages), **kwargs)
        return result.generations[0].message
