"""流式对话接口路由（基于 Callbacks）"""

from datetime import datetime
from typing import AsyncGenerator, Any, Dict, List
import asyncio
import json
import re
from queue import Queue

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.callbacks import BaseCallbackHandler

from src.agent.devops_agent import DevOpsAgent
from src.models.schemas import ChatRequest, AGUIRunAgentInput
from src.utils.logger import get_logger
from src.utils.agui_adapter import AGUIAdapter

logger = get_logger(__name__)
router = APIRouter(tags=["对话"])


def clean_model_output(text: str) -> str:
    """清理模型输出中的特殊标签

    移除 XML 标签（<think>, </think>）和其他可能影响 UI 显示的标记

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    if not text:
        return text

    # 移除 <think> 和 </think> 标签
    text = re.sub(r'</?think>', '', text, flags=re.IGNORECASE)

    # 移除其他常见的 XML 标签（如果需要）
    # text = re.sub(r'<[^>]+>', '', text)

    return text


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
        """LLM 生成新 token - 实现逐字显示

        🔥 支持 reasoning_content：
        - 如果 chunk 中包含 reasoning_content，发送 reasoning_token 事件
        - 如果包含 content，发送普通 token 事件
        """
        # 获取 chunk 对象
        chunk = kwargs.get('chunk')

        # 🔥 检查是否有 reasoning content
        if chunk:
            # chunk 是 ChatGenerationChunk，message 是 AIMessageChunk
            if hasattr(chunk, 'message'):
                msg = chunk.message
                # 检查 additional_kwargs 中的 reasoning_content
                if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                    reasoning = msg.additional_kwargs.get('reasoning_content')
                    if reasoning:
                        # 🔥 清理 reasoning content 中的 XML 标签
                        cleaned_reasoning = clean_model_output(reasoning)
                        # 发送 reasoning token 事件
                        self.queue.put({
                            "type": "reasoning_token",
                            "content": cleaned_reasoning
                        })
                        return  # reasoning token 不需要再发送普通 token

        # 🔥 清理普通 token 中的 XML 标签
        cleaned_token = clean_model_output(token)
        # 发送普通 content token
        self.queue.put({
            "type": "token",
            "content": cleaned_token
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
    """使用回调的流式返回（AG-UI 协议）"""
    queue = Queue()

    try:
        # 创建 AG-UI 适配器
        adapter = AGUIAdapter(session_id=session_id)

        # 发送会话开始事件
        start_events = adapter.convert_event({"type": "start", "session_id": session_id or "new"})
        for event in start_events:
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

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

                # 🔥 通过 AG-UI 适配器转换事件
                agui_events = adapter.convert_event(event)

                # 发送转换后的事件（可能是多个）
                for agui_event in agui_events:
                    yield f"data: {json.dumps(agui_event, ensure_ascii=False)}\n\n"

    except Exception as e:
        logger.error(f"流式响应错误: {str(e)}")
        # 发送错误事件
        error_events = adapter.convert_event({"type": "error", "error": str(e)})
        for event in error_events:
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式对话接口（AG-UI 协议）- 简化格式

    符合 AG-UI 协议标准的流式 SSE 接口，支持 TDesign Chat 组件直接集成。

    AG-UI 事件类型：
    - RUN_STARTED/FINISHED/ERROR: 会话生命周期
    - THINKING_*: 思考过程（Deepseek Reasoning）
    - TEXT_MESSAGE_*: 正式回答内容
    - TOOL_CALL_*: 工具调用过程

    前端集成示例（Vue3 + TDesign Chat）：
    ```vue
    <template>
      <t-chatbot :chat-service-config="chatServiceConfig" />
    </template>

    <script setup>
    const chatServiceConfig = {
      endpoint: '/api/v1/chat/stream',
      protocol: 'agui',  // 启用 AG-UI 协议
      stream: true,
    };
    </script>
    ```

    或使用原生 EventSource：
    ```javascript
    const eventSource = new EventSource('/api/v1/chat/stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.type, data);
    };
    ```

    或使用 curl 测试：
    ```bash
    curl -N -X POST http://localhost:8000/api/v1/chat/stream \\
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


@router.post("/agent/run")
async def agent_run(request: AGUIRunAgentInput):
    """AG-UI 协议标准端点 (RunAgentInput)

    完全符合 AG-UI 协议标准的接口，接收 RunAgentInput 格式请求。

    请求格式：
    ```json
    {
      "threadId": "thread-123",
      "runId": "run-456",
      "messages": [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮你的？"},
        {"role": "user", "content": "请帮我检查Navigation项目的代码覆盖率"}
      ],
      "tools": [...],
      "state": {...},
      "context": {...}
    }
    ```

    返回：AG-UI 标准事件流 (SSE)

    前端集成示例（TDesign Chat）：
    ```vue
    <script setup>
    const chatServiceConfig = {
      endpoint: '/api/v1/agent/run',
      protocol: 'agui',
      stream: true,
    };
    </script>
    ```
    """
    # 🔥 打印成功解析的请求数据
    logger.info("=" * 80)
    logger.info("[SUCCESS] /agent/run request parsed")
    logger.info(f"  threadId: {request.threadId}")
    logger.info(f"  runId: {request.runId}")
    logger.info(f"  messages count: {len(request.messages)}")
    for i, msg in enumerate(request.messages):
        logger.info(f"    [{i}] role={msg.role}, content={msg.content[:50]}...")
    logger.info("=" * 80)

    agent = DevOpsAgent()

    # 提取最后一条用户消息
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    if not user_messages:
        # 如果没有用户消息，返回错误
        logger.warning("请求中没有用户消息")
        async def error_stream():
            yield f"data: {json.dumps({'type': 'RUN_ERROR', 'error': 'No user message found'}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    # 获取最后一条用户消息
    last_user_message = user_messages[-1].content
    logger.info(f"提取的用户消息: {last_user_message}")

    # 使用 threadId 作为 session_id
    session_id = request.threadId or request.runId

    return StreamingResponse(
        stream_with_callback(agent, last_user_message, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
