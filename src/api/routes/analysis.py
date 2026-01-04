"""分析和报告路由"""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Query

from src.agent.devops_agent import DevOpsAgent
from src.models.mongodb import get_analysis_records_collection
from src.models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    ReportRequest,
    ReportResponse,
    TrendDataPoint,
    TrendResponse,
)

router = APIRouter(prefix="/analysis", tags=["分析与报告"])


@router.post("/project", response_model=AnalysisResponse)
async def analyze_project(request: AnalysisRequest) -> AnalysisResponse:
    """分析项目整体状况

    对指定项目进行全面分析，包括代码质量、测试情况、构建状态等。

    Args:
        request: 分析请求

    Returns:
        AnalysisResponse: 分析结果
    """
    # 创建 Agent
    agent = DevOpsAgent()

    # 执行项目分析
    result = agent.analyze_project(request.project_name)

    return AnalysisResponse(
        project_name=request.project_name,
        metrics={},  # 这里可以添加具体的指标数据
        analysis=result["response"],
        timestamp=datetime.now(),
    )


@router.post("/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest) -> ReportResponse:
    """生成项目报告

    生成指定类型的项目健康报告。

    Args:
        request: 报告请求

    Returns:
        ReportResponse: 报告内容
    """
    # 创建 Agent
    agent = DevOpsAgent()

    # 生成报告提示
    report_prompt = f"请为项目 {request.project_name} 生成一份{request.report_type}报告，包括关键指标、问题分析和改进建议。"

    # 执行分析
    result = agent.chat(report_prompt)

    # Mock 报告 ID（实际应保存到数据库）
    report_id = 1

    return ReportResponse(
        report_id=report_id,
        project_name=request.project_name,
        report_type=request.report_type,
        summary="项目整体健康状况良好",
        content=result["response"],
        created_at=datetime.now(),
    )


@router.get("/trend", response_model=TrendResponse)
async def get_trend(
    project: str = Query(..., description="项目名称"),
    metric: str = Query(..., description="指标类型"),
    days: int = Query(30, description="查询天数", ge=1, le=365),
) -> TrendResponse:
    """查询指标趋势

    查询指定项目和指标的历史趋势数据。

    Args:
        project: 项目名称
        metric: 指标类型
        days: 查询天数

    Returns:
        TrendResponse: 趋势数据
    """
    # 计算查询起始时间
    start_date = datetime.now() - timedelta(days=days)

    # 从 MongoDB 查询历史记录
    collection = get_analysis_records_collection()
    records = list(
        collection.find(
            {
                "project_name": project,
                "metric_type": metric,
                "timestamp": {"$gte": start_date},
            }
        ).sort("timestamp", 1)  # 按时间升序排序
    )

    # 转换为数据点列表
    data_points = [
        TrendDataPoint(
            timestamp=record["timestamp"],
            value=record["metric_value"],
        )
        for record in records
    ]

    # Mock 趋势分析（实际可以使用 Agent 进行分析）
    if len(data_points) > 0:
        first_value = data_points[0].value
        last_value = data_points[-1].value
        change = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
        trend_analysis = f"在过去 {days} 天内，{metric} 指标变化了 {change:.1f}%"
    else:
        trend_analysis = "暂无历史数据"

    return TrendResponse(
        project=project,
        metric=metric,
        data=data_points,
        trend_analysis=trend_analysis,
    )
