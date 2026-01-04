"""ORM 数据模型

定义数据库表结构。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, Float
from sqlalchemy.sql import func

from src.models.database import Base


class Conversation(Base):
    """对话历史表"""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=False, comment="会话 ID")
    user_message = Column(Text, nullable=False, comment="用户消息")
    agent_response = Column(Text, nullable=False, comment="Agent 响应")
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="时间戳",
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, session_id={self.session_id})>"


class AnalysisRecord(Base):
    """分析记录表"""

    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_name = Column(String(128), index=True, nullable=False, comment="项目名称")
    metric_type = Column(String(64), index=True, nullable=False, comment="指标类型")
    metric_value = Column(Float, nullable=False, comment="指标值")
    metric_data = Column(Text, nullable=True, comment="指标详细数据 (JSON)")
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="时间戳",
    )

    def __repr__(self) -> str:
        return f"<AnalysisRecord(id={self.id}, project={self.project_name}, metric={self.metric_type})>"


class Report(Base):
    """报告表"""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_name = Column(String(128), index=True, nullable=False, comment="项目名称")
    report_type = Column(String(32), index=True, nullable=False, comment="报告类型")
    content = Column(Text, nullable=False, comment="报告内容")
    summary = Column(Text, nullable=True, comment="报告摘要")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="创建时间",
    )

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, project={self.project_name}, type={self.report_type})>"
