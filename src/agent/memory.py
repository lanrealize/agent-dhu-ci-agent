"""对话记忆管理

管理 Agent 的对话历史和上下文。
"""

from typing import List, Optional

from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import BaseMessage
from sqlalchemy.orm import Session

from src.models.orm import Conversation
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PersistentConversationMemory:
    """持久化对话记忆

    将对话历史保存到数据库，支持跨会话恢复。
    """

    def __init__(self, session_id: str, db: Session):
        """初始化对话记忆

        Args:
            session_id: 会话 ID
            db: 数据库会话
        """
        self.session_id = session_id
        self.db = db
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )

        # 从数据库加载历史对话
        self._load_history()

    def _load_history(self) -> None:
        """从数据库加载历史对话"""
        try:
            conversations = (
                self.db.query(Conversation)
                .filter(Conversation.session_id == self.session_id)
                .order_by(Conversation.timestamp)
                .all()
            )

            for conv in conversations:
                self.memory.chat_memory.add_user_message(conv.user_message)
                self.memory.chat_memory.add_ai_message(conv.agent_response)

            logger.info(
                f"从数据库加载了 {len(conversations)} 条历史对话，会话 ID: {self.session_id}"
            )
        except Exception as e:
            logger.error(f"加载历史对话失败: {str(e)}")

    def save_conversation(self, user_message: str, agent_response: str) -> None:
        """保存对话到数据库

        Args:
            user_message: 用户消息
            agent_response: Agent 响应
        """
        try:
            conversation = Conversation(
                session_id=self.session_id,
                user_message=user_message,
                agent_response=agent_response,
            )
            self.db.add(conversation)
            self.db.commit()
            logger.info(f"保存对话成功，会话 ID: {self.session_id}")
        except Exception as e:
            logger.error(f"保存对话失败: {str(e)}")
            self.db.rollback()

    def add_message(self, user_message: str, agent_response: str) -> None:
        """添加对话消息

        Args:
            user_message: 用户消息
            agent_response: Agent 响应
        """
        # 添加到内存
        self.memory.chat_memory.add_user_message(user_message)
        self.memory.chat_memory.add_ai_message(agent_response)

        # 保存到数据库
        self.save_conversation(user_message, agent_response)

    def get_messages(self) -> List[BaseMessage]:
        """获取所有消息

        Returns:
            List[BaseMessage]: 消息列表
        """
        return self.memory.chat_memory.messages

    def clear(self) -> None:
        """清空对话记忆"""
        self.memory.clear()
        logger.info(f"清空对话记忆，会话 ID: {self.session_id}")
