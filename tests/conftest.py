"""Pytest 配置文件"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.models.database import Base


@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库

    每个测试函数使用独立的内存数据库。
    """
    # 创建内存数据库
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    # 创建会话
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def sample_project_name():
    """示例项目名称"""
    return "test-project"
