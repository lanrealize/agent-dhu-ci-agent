"""MongoDB 对话记忆管理

使用 MongoDB 存储和管理对话历史。
"""

from datetime import datetime
from typing import List, Optional

from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.models.mongodb import get_conversations_collection
from src.models.mongodb_models import (
    ConversationDocument,
    ConversationTurn,
    AgentStep,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MongoDBConversationMemory:
    """MongoDB 持久化对话记忆

    将对话历史保存到 MongoDB，支持跨会话恢复。
    当 MongoDB 不可用时，自动降级为纯内存模式。
    """

    def __init__(self, session_id: str):
        """初始化对话记忆

        Args:
            session_id: 会话 ID
        """
        self.session_id = session_id
        self.mongodb_available = True  # MongoDB 可用性标记

        try:
            self.collection = get_conversations_collection()

            # 🔥 立即测试连接，避免后续操作卡住
            # 使用快速ping测试，而不是等到find_one时才发现连接失败
            from src.models.mongodb import MongoDBManager
            MongoDBManager.get_client().admin.command('ping')

        except Exception as e:
            logger.warning(f"MongoDB 不可用，降级为纯内存模式: {str(e)}")
            self.mongodb_available = False
            self.collection = None

        # 创建 LangChain Memory 对象
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )

        # 从数据库加载或创建会话（如果 MongoDB 可用）
        if self.mongodb_available:
            self._load_or_create_session()
        else:
            logger.info(f"创建纯内存会话: {self.session_id}")

    def _load_or_create_session(self) -> None:
        """从数据库加载或创建新会话"""
        if not self.mongodb_available:
            return

        try:
            # 查询现有会话
            doc = self.collection.find_one({"session_id": self.session_id})

            if doc:
                # 加载现有会话
                conv_doc = ConversationDocument(**doc)
                self._load_history(conv_doc)
                logger.info(
                    f"加载现有会话: {self.session_id}, "
                    f"包含 {len(conv_doc.turns)} 轮对话"
                )
            else:
                # 创建新会话
                new_doc = ConversationDocument(
                    session_id=self.session_id,
                    turns=[],
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                self.collection.insert_one(new_doc.dict())
                logger.info(f"创建新会话: {self.session_id}")

        except Exception as e:
            logger.error(f"加载或创建会话失败，降级为纯内存模式: {str(e)}")
            self.mongodb_available = False

    def _load_history(self, conv_doc: ConversationDocument) -> None:
        """从会话文档加载历史对话到 Memory

        只加载最终的用户问题和 Agent 回复（不包含中间步骤）

        Args:
            conv_doc: 会话文档
        """
        for turn in conv_doc.turns:
            # 只加载最终的 Q&A（节省 token）
            self.memory.chat_memory.add_user_message(turn.user_input)
            self.memory.chat_memory.add_ai_message(turn.final_response)

        logger.info(f"加载了 {len(conv_doc.turns)} 轮对话到 Memory")

    def add_turn(
        self,
        user_input: str,
        final_response: str,
        agent_steps: Optional[List[AgentStep]] = None,
        total_tokens: Optional[int] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        """添加新的对话轮次

        Args:
            user_input: 用户输入
            final_response: 最终回复
            agent_steps: Agent 执行步骤（完整信息，用于前端展示）
            total_tokens: 总 token 消耗
            duration_ms: 总耗时（毫秒）
        """
        # 先添加到 LangChain Memory（即使 MongoDB 不可用也要保持内存中的对话）
        self.memory.chat_memory.add_user_message(user_input)
        self.memory.chat_memory.add_ai_message(final_response)

        # 如果 MongoDB 可用，持久化到数据库
        if not self.mongodb_available:
            logger.debug(f"MongoDB 不可用，跳过持久化")
            return

        try:
            # 获取当前 turn_id
            doc = self.collection.find_one({"session_id": self.session_id})
            if not doc:
                logger.warning(f"会话不存在: {self.session_id}, 跳过持久化")
                return

            turn_id = len(doc.get("turns", [])) + 1

            # 创建新的 Turn
            new_turn = ConversationTurn(
                turn_id=turn_id,
                user_input=user_input,
                agent_steps=agent_steps or [],
                final_response=final_response,
                total_tokens=total_tokens,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
            )

            # 更新数据库（追加到 turns 数组）
            self.collection.update_one(
                {"session_id": self.session_id},
                {
                    "$push": {"turns": new_turn.dict()},
                    "$set": {"updated_at": datetime.now()},
                },
            )

            logger.info(
                f"保存对话轮次 {turn_id} 成功，会话 ID: {self.session_id}, "
                f"包含 {len(agent_steps or [])} 个执行步骤"
            )

        except Exception as e:
            logger.error(f"保存对话轮次失败: {str(e)}")

    def get_messages(self) -> List[BaseMessage]:
        """获取所有消息（用于发送给 LLM）

        Returns:
            List[BaseMessage]: 消息列表（只包含最终 Q&A）
        """
        return self.memory.chat_memory.messages

    def get_full_conversation(self) -> Optional[ConversationDocument]:
        """获取完整的对话文档（包含所有 agent steps）

        用于前端展示完整的推理过程。

        Returns:
            Optional[ConversationDocument]: 对话文档
        """
        try:
            doc = self.collection.find_one({"session_id": self.session_id})
            if doc:
                return ConversationDocument(**doc)
            return None
        except Exception as e:
            logger.error(f"获取完整对话失败: {str(e)}")
            return None

    def clear(self) -> None:
        """清空对话记忆（只清空 Memory，不删除数据库记录）"""
        self.memory.clear()
        logger.info(f"清空对话记忆，会话 ID: {self.session_id}")

    def delete_session(self) -> None:
        """删除整个会话（从数据库删除）"""
        try:
            self.collection.delete_one({"session_id": self.session_id})
            self.memory.clear()
            logger.info(f"删除会话: {self.session_id}")
        except Exception as e:
            logger.error(f"删除会话失败: {str(e)}")
            raise
