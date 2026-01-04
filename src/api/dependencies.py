"""FastAPI 依赖注入

定义 FastAPI 的依赖项。
"""

from sqlalchemy.orm import Session

from src.agent.devops_agent import DevOpsAgent
from src.models.database import get_db


def get_agent(db: Session = next(get_db())) -> DevOpsAgent:
    """获取 DevOps Agent 实例

    Args:
        db: 数据库会话

    Returns:
        DevOpsAgent: Agent 实例
    """
    return DevOpsAgent(db=db)
