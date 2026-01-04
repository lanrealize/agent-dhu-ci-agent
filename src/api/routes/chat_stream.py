"""流式对话接口路由（基于 Callbacks）"""

from datetime import datetime
from typing import AsyncGenerator, Any, Dict, List
import asyncio
import json
from queue import Queue

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.callbacks import BaseCallbackHandler

from src.agent.devops_agent import DevOpsAgent
from src.models.schemas import ChatRequest
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["对话"])


class StreamingCallbackHandler(BaseCallbackHandler):
    """流式回调处理器

    捕获 Agent 执行过程中的各种事件并放入队列。
    """

    def __init__(self, queue: Queue):
        self.queue = queue

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """LLM 开始"""
        self.queue.put({"type": "thinking", "content": "正在思考..."})

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """LLM 生成新 token - 🔥 关键：实现逐字显示"""
        self.queue.put({
            "type": "token",
            "content": token
        })

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """工具调用开始"""
        tool_name = serialized.get("name", "unknown")
        self.queue.put({
            "type": "tool_start",
            "tool": tool_name,
            "input": input_str[:200]
        })

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """工具调用结束"""
        self.queue.put({
            "type": "tool_end",
            "output": output[:200]
        })

    def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        """Agent 行动"""
        self.queue.put({
            "type": "action",
            "action": action.tool,
            "thought": action.log[:300] if hasattr(action, 'log') else ""
        })

    def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        """Agent 完成"""
        output = finish.return_values.get("output", "") if hasattr(finish, 'return_values') else ""
        self.queue.put({
            "type": "done",
            "response": output
        })


async def stream_with_callback(agent: DevOpsAgent, message: str, session_id: str) -> AsyncGenerator[str, None]:
    """使用回调的流式返回"""
    queue = Queue()

    try:
        # 发送开始事件
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id or 'new'}, ensure_ascii=False)}\n\n"

        # 创建回调处理器
        callback = StreamingCallbackHandler(queue)

        # 在后台线程中运行 Agent
        def run_agent():
            try:
                executor, sid, memory = agent.create_executor(session_id)

                # 添加回调
                result = executor.invoke(
                    {"input": message},
                    config={"callbacks": [callback]}
                )

                # 放入最终结果
                queue.put({
                    "type": "final",
                    "response": result.get("output", ""),
                    "session_id": sid
                })

            except Exception as e:
                queue.put({"type": "error", "error": str(e)})
            finally:
                queue.put(None)  # 结束标记

        # 启动后台线程
        import threading
        thread = threading.Thread(target=run_agent)
        thread.start()

        # 从队列读取并流式发送
        while True:
            await asyncio.sleep(0.1)  # 避免CPU占用过高

            while not queue.empty():
                event = queue.get()

                if event is None:  # 结束标记
                    return

                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    except Exception as e:
        logger.error(f"流式响应错误: {str(e)}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式对话接口（基于 Callbacks）

    返回 Server-Sent Events (SSE) 流，实时显示 Agent 执行过程。

    事件类型：
    - start: 开始处理，包含 session_id
    - thinking: Agent 思考中
    - action: Agent 决定采取的行动
    - tool_start: 开始调用工具
    - tool_end: 工具调用完成
    - final: 最终响应（包含完整答案和 session_id）
    - error: 发生错误

    使用示例：
    ```javascript
    const eventSource = new EventSource('/api/v1/chat/stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.type, data);
    };
    ```

    或使用 curl 测试：
    ```bash
    curl -N -X POST http://localhost:8005/api/v1/chat/stream \\
      -H "Content-Type: application/json" \\
      -d '{"message": "查询项目状态", "session_id": null}'
    ```
    """
    agent = DevOpsAgent()

    return StreamingResponse(
        stream_with_callback(agent, request.message, request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
