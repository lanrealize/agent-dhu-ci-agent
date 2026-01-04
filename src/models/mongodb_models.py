"""MongoDB 数据模型

定义 MongoDB 的文档结构（使用 Pydantic）。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    """Agent 执行的单个步骤"""

    step_number: int = Field(..., description="步骤编号")
    thought: str = Field(..., description="LLM 的思考过程")
    action: Optional[str] = Field(None, description="工具名称")
    action_input: Optional[Dict[str, Any]] = Field(None, description="工具输入参数")
    observation: Optional[str] = Field(None, description="工具返回结果")
    duration_ms: Optional[int] = Field(None, description="执行耗时（毫秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ConversationMessage(BaseModel):
    """单条消息"""

    role: str = Field(..., description="角色 (user/assistant)")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ConversationTurn(BaseModel):
    """单次用户输入的完整记录"""

    turn_id: int = Field(..., description="对话轮次 ID")
    user_input: str = Field(..., description="用户输入")
    agent_steps: List[AgentStep] = Field(default_factory=list, description="Agent 执行步骤")
    final_response: str = Field(..., description="最终回复")
    total_tokens: Optional[int] = Field(None, description="总 token 消耗")
    duration_ms: Optional[int] = Field(None, description="总耗时（毫秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ConversationDocument(BaseModel):
    """对话文档（MongoDB 文档结构）"""

    session_id: str = Field(..., description="会话 ID")
    user_id: Optional[str] = Field(None, description="用户 ID")
    title: Optional[str] = Field(None, description="对话标题")

    # 所有对话轮次
    turns: List[ConversationTurn] = Field(default_factory=list, description="对话轮次列表")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisRecordDocument(BaseModel):
    """分析记录文档"""

    project_name: str = Field(..., description="项目名称")
    metric_type: str = Field(..., description="指标类型")
    metric_value: float = Field(..., description="指标值")
    metric_data: Optional[Dict[str, Any]] = Field(None, description="详细数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReportDocument(BaseModel):
    """报告文档"""

    project_name: str = Field(..., description="项目名称")
    report_type: str = Field(..., description="报告类型")
    content: str = Field(..., description="报告内容")
    summary: Optional[str] = Field(None, description="报告摘要")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
