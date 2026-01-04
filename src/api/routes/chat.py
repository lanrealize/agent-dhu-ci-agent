"""对话接口路由"""

from datetime import datetime

from fastapi import APIRouter

from src.agent.devops_agent import DevOpsAgent
from src.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["对话"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """对话接口

    与 Agent 进行对话式交互，查询项目信息。

    Args:
        request: 对话请求

    Returns:
        ChatResponse: Agent 响应
    """
    # 创建 Agent（不再需要 db 参数）
    agent = DevOpsAgent()

    # 执行对话
    result = agent.chat(
        message=request.message,
        session_id=request.session_id,
    )

    return ChatResponse(
        response=result["response"],
        session_id=result["session_id"],
        timestamp=datetime.now(),
    )
