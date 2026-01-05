"""Pydantic 数据模型

定义 API 请求和响应的数据结构。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ========== 对话相关 ==========


class Message(BaseModel):
    """AG-UI 消息格式"""
    role: str = Field(..., description="消息角色 (user/assistant/system)")
    content: str = Field(..., description="消息内容")


class AGUIRunAgentInput(BaseModel):
    """AG-UI 协议标准请求格式 (RunAgentInput)

    符合 AG-UI 协议：https://docs.ag-ui.com/sdk/python/core/types#runagentinput
    """
    threadId: Optional[str] = Field(None, description="对话线程 ID")
    runId: Optional[str] = Field(None, description="运行 ID")
    messages: List[Message] = Field(..., description="消息历史")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="可用工具")
    state: Optional[Dict[str, Any]] = Field(None, description="状态数据")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class ChatRequest(BaseModel):
    """对话请求（简化格式，向后兼容）"""

    message: str = Field(..., description="用户消息", min_length=1)
    session_id: Optional[str] = Field(None, description="会话 ID")


class ChatResponse(BaseModel):
    """对话响应"""

    response: str = Field(..., description="Agent 响应")
    session_id: str = Field(..., description="会话 ID")
    timestamp: datetime = Field(..., description="响应时间")


# ========== 分析相关 ==========


class AnalysisRequest(BaseModel):
    """分析请求"""

    project_name: str = Field(..., description="项目名称", min_length=1)
    metrics: Optional[List[str]] = Field(
        None, description="指定要分析的指标列表，不指定则分析全部"
    )


class AnalysisResponse(BaseModel):
    """分析响应"""

    project_name: str = Field(..., description="项目名称")
    metrics: Dict[str, Any] = Field(..., description="指标数据")
    analysis: str = Field(..., description="分析结果")
    timestamp: datetime = Field(..., description="分析时间")


# ========== 报告相关 ==========


class ReportRequest(BaseModel):
    """报告生成请求"""

    project_name: str = Field(..., description="项目名称", min_length=1)
    report_type: str = Field(default="daily", description="报告类型 (daily/weekly/monthly)")


class ReportResponse(BaseModel):
    """报告响应"""

    report_id: int = Field(..., description="报告 ID")
    project_name: str = Field(..., description="项目名称")
    report_type: str = Field(..., description="报告类型")
    summary: str = Field(..., description="报告摘要")
    content: str = Field(..., description="报告内容")
    created_at: datetime = Field(..., description="创建时间")


# ========== 趋势相关 ==========


class TrendRequest(BaseModel):
    """趋势查询请求"""

    project: str = Field(..., description="项目名称")
    metric: str = Field(..., description="指标类型")
    days: int = Field(default=30, description="查询天数", ge=1, le=365)


class TrendDataPoint(BaseModel):
    """趋势数据点"""

    timestamp: datetime = Field(..., description="时间戳")
    value: float = Field(..., description="指标值")


class TrendResponse(BaseModel):
    """趋势响应"""

    project: str = Field(..., description="项目名称")
    metric: str = Field(..., description="指标类型")
    data: List[TrendDataPoint] = Field(..., description="趋势数据")
    trend_analysis: str = Field(..., description="趋势分析")


# ========== 健康检查 ==========


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    timestamp: datetime = Field(..., description="检查时间")


# ========== Tool 响应 ==========


class ToolResponse(BaseModel):
    """Tool 调用响应"""

    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误信息")
