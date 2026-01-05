"""LangChain reasoning content 支持补丁

此补丁修复 LangChain 在流式输出时忽略 reasoning_content 字段的问题。

原理：
- Deepseek-reasoner 模型在流式响应中返回 reasoning_content 字段
- LangChain 的 _convert_delta_to_message_chunk 函数只提取了 content，忽略了 reasoning_content
- 此补丁在运行时替换该函数，添加对 reasoning_content 的支持

使用方法：
    from src.utils.langchain_patch import apply_reasoning_patch
    apply_reasoning_patch()  # 在应用启动时调用一次
"""

from typing import Any, Mapping
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.messages.base import BaseMessageChunk
from langchain_openai.chat_models import base as langchain_base

from src.utils.logger import get_logger

logger = get_logger(__name__)

# 保存原始函数引用
_original_convert_delta = langchain_base._convert_delta_to_message_chunk


def _convert_delta_with_reasoning(
    _dict: Mapping[str, Any],
    default_class: type[BaseMessageChunk]
) -> BaseMessageChunk:
    """扩展版本的 delta 转换函数，支持 reasoning_content

    Args:
        _dict: OpenAI API 返回的 delta 字典
        default_class: 默认消息类

    Returns:
        BaseMessageChunk: 包含 reasoning_content 的消息块
    """
    # 调用原始转换函数
    message_chunk = _original_convert_delta(_dict, default_class)

    # 🔥 添加 reasoning_content 支持
    if isinstance(message_chunk, AIMessageChunk):
        # 检查是否有 reasoning_content 字段
        if reasoning_content := _dict.get("reasoning_content"):
            # 将 reasoning_content 添加到 additional_kwargs
            # 这样在 callback 中就可以访问到
            message_chunk.additional_kwargs["reasoning_content"] = reasoning_content

    return message_chunk


def apply_reasoning_patch():
    """应用 reasoning content 补丁

    此函数应在应用启动时调用一次，它会替换 LangChain 的
    _convert_delta_to_message_chunk 函数为支持 reasoning_content 的版本。

    Example:
        >>> from src.utils.langchain_patch import apply_reasoning_patch
        >>> apply_reasoning_patch()
        >>> # 现在所有 LangChain 的流式调用都会包含 reasoning_content
    """
    # Monkey patch: 替换函数
    langchain_base._convert_delta_to_message_chunk = _convert_delta_with_reasoning

    logger.info("[OK] LangChain reasoning content patch applied")
    logger.info("   Streaming responses will now include reasoning_content field")


def remove_reasoning_patch():
    """移除 reasoning content 补丁（恢复原始行为）

    如果需要恢复 LangChain 的原始行为，可以调用此函数。
    """
    langchain_base._convert_delta_to_message_chunk = _original_convert_delta
    logger.info("LangChain reasoning content 补丁已移除")
