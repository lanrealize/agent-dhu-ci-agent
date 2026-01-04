"""健康检查路由"""

from datetime import datetime

from fastapi import APIRouter

from src.models.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["健康检查"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """健康检查接口

    Returns:
        HealthResponse: 服务状态
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.now(),
    )
