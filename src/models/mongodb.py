"""MongoDB 数据库连接

管理 MongoDB 连接和集合访问。
"""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MongoDBManager:
    """MongoDB 连接管理器（同步版本）"""

    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    @classmethod
    def get_client(cls) -> MongoClient:
        """获取 MongoDB 客户端"""
        if cls._client is None:
            logger.info(f"连接 MongoDB: {settings.mongodb_url}")
            # 设置短超时，避免在 MongoDB 不可用时长时间阻塞
            cls._client = MongoClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=2000,  # 连接超时 2 秒（默认 30 秒）
                connectTimeoutMS=2000,          # 连接建立超时 2 秒
                socketTimeoutMS=2000,           # 读写超时 2 秒
            )
        return cls._client

    @classmethod
    def get_database(cls) -> Database:
        """获取数据库"""
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[settings.mongodb_database]
            logger.info(f"使用数据库: {settings.mongodb_database}")
        return cls._db

    @classmethod
    def close(cls):
        """关闭连接"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("MongoDB 连接已关闭")

    @classmethod
    def init_indexes(cls):
        """初始化索引"""
        db = cls.get_database()

        # conversations 集合索引
        conversations = db.conversations
        conversations.create_index("session_id", unique=True)
        conversations.create_index([("updated_at", DESCENDING)])
        conversations.create_index([("user_id", ASCENDING), ("updated_at", DESCENDING)])

        # analysis_records 集合索引
        analysis_records = db.analysis_records
        analysis_records.create_index([("project_name", ASCENDING), ("metric_type", ASCENDING)])
        analysis_records.create_index([("timestamp", DESCENDING)])

        # reports 集合索引
        reports = db.reports
        reports.create_index([("project_name", ASCENDING), ("created_at", DESCENDING)])

        logger.info("MongoDB 索引创建完成")


class AsyncMongoDBManager:
    """MongoDB 连接管理器（异步版本）"""

    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """获取异步 MongoDB 客户端"""
        if cls._client is None:
            logger.info(f"连接 MongoDB (异步): {settings.mongodb_url}")
            cls._client = AsyncIOMotorClient(settings.mongodb_url)
        return cls._client

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """获取异步数据库"""
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[settings.mongodb_database]
            logger.info(f"使用数据库 (异步): {settings.mongodb_database}")
        return cls._db

    @classmethod
    def close(cls):
        """关闭连接"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("MongoDB 异步连接已关闭")


# 便捷函数
def get_db() -> Database:
    """获取数据库实例（同步）"""
    return MongoDBManager.get_database()


def get_async_db() -> AsyncIOMotorDatabase:
    """获取数据库实例（异步）"""
    return AsyncMongoDBManager.get_database()


# 集合访问函数
def get_conversations_collection():
    """获取 conversations 集合"""
    return get_db().conversations


def get_analysis_records_collection():
    """获取 analysis_records 集合"""
    return get_db().analysis_records


def get_reports_collection():
    """获取 reports 集合"""
    return get_db().reports
