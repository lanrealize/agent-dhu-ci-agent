#!/usr/bin/env python
"""MongoDB 数据库初始化脚本

用于初始化 MongoDB 数据库、创建索引、测试连接。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.models.mongodb import MongoDBManager
from src.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """主函数"""
    print("=" * 60)
    print("MongoDB 数据库初始化")
    print("=" * 60)

    print(f"\n连接信息:")
    print(f"  MongoDB URL: {settings.mongodb_url}")
    print(f"  数据库名称: {settings.mongodb_database}")
    print(f"  集合列表:")
    print(f"    - conversations (对话历史)")
    print(f"    - analysis_records (分析记录)")
    print(f"    - reports (报告)")

    try:
        # 测试连接
        print(f"\n正在连接 MongoDB...")
        client = MongoDBManager.get_client()

        # 测试连接
        client.admin.command('ping')
        print("✓ MongoDB 连接成功")

        # 获取数据库
        db = MongoDBManager.get_database()
        print(f"✓ 数据库 '{settings.mongodb_database}' 已连接")

        # 列出现有集合
        existing_collections = db.list_collection_names()
        print(f"\n现有集合: {existing_collections if existing_collections else '(无)'}")

        # 创建索引
        print(f"\n正在创建索引...")
        MongoDBManager.init_indexes()
        print("✓ 索引创建完成")

        # 显示索引信息
        print(f"\n索引信息:")
        for coll_name in ["conversations", "analysis_records", "reports"]:
            collection = db[coll_name]
            indexes = list(collection.list_indexes())
            print(f"\n  {coll_name}:")
            for idx in indexes:
                print(f"    - {idx['name']}: {idx.get('key', {})}")

        # 统计数据
        print(f"\n数据统计:")
        print(f"  conversations: {db.conversations.count_documents({})} 条记录")
        print(f"  analysis_records: {db.analysis_records.count_documents({})} 条记录")
        print(f"  reports: {db.reports.count_documents({})} 条记录")

        print("\n" + "=" * 60)
        print("✓ 数据库初始化完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        logger.error(f"数据库初始化失败: {str(e)}")
        return 1

    finally:
        MongoDBManager.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
