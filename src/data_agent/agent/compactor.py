"""
对话历史压缩模块

当对话历史 token 使用率超过阈值时，将旧消息摘要为简短的上下文总结。
"""

from typing import List, Union, Dict, Any

import tiktoken
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)


COMPACT_PROMPT = """请将以下对话历史压缩为简洁的摘要，保留关键信息：
- 用户的主要问题和意图
- 已执行的重要操作和结果
- 重要的数据发现或结论

对话历史：
{conversation}

请用 2-3 句话总结上述对话的核心内容，使用中文回答："""


class ConversationCompactor:
    """对话历史压缩器（基于 token 百分比）"""

    def __init__(self, llm):
        """
        初始化压缩器

        Args:
            llm: LLM 实例，用于生成摘要
        """
        self.llm = llm
        # 使用 cl100k_base 编码（适用于大多数现代模型）
        self._encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, messages: List) -> int:
        """
        计算消息列表的 token 数量

        Args:
            messages: 消息列表

        Returns:
            总 token 数
        """
        total = 0
        for msg in messages:
            content = self._get_message_content(msg)
            if content:
                total += len(self._encoder.encode(content))
            # 每条消息额外开销（role, formatting）
            total += 4
        return total

    def _count_single_message(self, msg) -> int:
        """计算单条消息的 token 数"""
        content = self._get_message_content(msg)
        if content:
            return len(self._encoder.encode(content)) + 4
        return 4

    def should_compact(
        self,
        messages: List,
        max_tokens: int,
        threshold: float = 0.8
    ) -> bool:
        """
        判断是否需要压缩

        Args:
            messages: 消息列表
            max_tokens: 模型最大上下文 tokens
            threshold: 触发阈值 (0.0-1.0)

        Returns:
            bool: 是否需要压缩
        """
        if max_tokens <= 0:
            return False
        current_tokens = self.count_tokens(messages)
        usage_ratio = current_tokens / max_tokens
        return usage_ratio >= threshold

    def compact(
        self,
        messages: List,
        max_tokens: int,
        keep_ratio: float = 0.1
    ) -> List:
        """
        压缩对话历史

        Args:
            messages: 完整消息列表
            max_tokens: 模型最大上下文 tokens
            keep_ratio: 保留最近消息的 token 比例

        Returns:
            压缩后的消息列表: [SystemMessage(摘要)] + [最近消息]
        """
        # 计算要保留的 token 数
        keep_tokens = int(max_tokens * keep_ratio)

        # 从后往前累计，找到保留的分界点
        recent_messages = []
        recent_tokens = 0
        for msg in reversed(messages):
            msg_tokens = self._count_single_message(msg)
            if recent_tokens + msg_tokens > keep_tokens:
                break
            recent_messages.insert(0, msg)
            recent_tokens += msg_tokens

        # 确保从 HumanMessage 开始
        recent_messages = self._ensure_start_with_human(recent_messages)

        # 需要压缩的旧消息
        old_count = len(messages) - len(recent_messages)
        old_messages = messages[:old_count]

        if not old_messages:
            return messages

        # 生成摘要
        summary = self._generate_summary(old_messages)

        return [
            SystemMessage(content=f"[对话历史摘要]\n{summary}")
        ] + recent_messages

    def _ensure_start_with_human(self, messages: List) -> List:
        """确保消息列表从 HumanMessage 开始"""
        for i, msg in enumerate(messages):
            if self._is_human_message(msg):
                return messages[i:]
        return messages

    def _is_human_message(self, msg) -> bool:
        """判断是否为用户消息"""
        if isinstance(msg, HumanMessage):
            return True
        if isinstance(msg, dict):
            return msg.get("role") == "user"
        return False

    def _generate_summary(self, messages: List) -> str:
        """
        调用 LLM 生成摘要

        Args:
            messages: 需要压缩的消息列表

        Returns:
            摘要文本
        """
        # 格式化对话历史
        conversation_text = self._format_messages(messages)

        # 调用 LLM
        prompt = COMPACT_PROMPT.format(conversation=conversation_text)
        response = self.llm.invoke([HumanMessage(content=prompt)])

        return response.content

    def _format_messages(self, messages: List) -> str:
        """
        格式化消息为文本

        Args:
            messages: 消息列表

        Returns:
            格式化的文本
        """
        lines = []
        for msg in messages:
            content = self._get_message_content(msg)
            role = self._get_message_role(msg)

            if content:
                # 截断过长的内容
                truncated = content[:200] + "..." if len(content) > 200 else content
                lines.append(f"{role}: {truncated}")

        return "\n".join(lines)

    def _get_message_content(self, msg) -> str:
        """获取消息内容"""
        if isinstance(msg, BaseMessage):
            return msg.content if msg.content else ""
        if isinstance(msg, dict):
            return msg.get("content", "")
        return ""

    def _get_message_role(self, msg) -> str:
        """获取消息角色"""
        if isinstance(msg, HumanMessage):
            return "用户"
        if isinstance(msg, AIMessage):
            return "助手"
        if isinstance(msg, ToolMessage):
            return "工具"
        if isinstance(msg, SystemMessage):
            return "系统"
        if isinstance(msg, dict):
            role_map = {"user": "用户", "assistant": "助手", "system": "系统", "tool": "工具"}
            return role_map.get(msg.get("role", ""), "未知")
        return "未知"
