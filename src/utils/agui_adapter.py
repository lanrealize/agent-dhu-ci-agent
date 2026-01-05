"""AG-UI 协议适配器

将内部事件格式转换为 AG-UI 标准协议格式。
参考：https://tdesign.tencent.com/chat
"""

import uuid
from typing import Dict, Any, Optional, List
from enum import Enum
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AGUIEventType(str, Enum):
    """AG-UI 协议事件类型"""
    # 生命周期事件
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    RUN_ERROR = "RUN_ERROR"

    # 思考过程事件
    THINKING_START = "THINKING_START"
    THINKING_END = "THINKING_END"
    THINKING_TEXT_MESSAGE_START = "THINKING_TEXT_MESSAGE_START"
    THINKING_TEXT_MESSAGE_CONTENT = "THINKING_TEXT_MESSAGE_CONTENT"
    THINKING_TEXT_MESSAGE_END = "THINKING_TEXT_MESSAGE_END"

    # 文本消息事件
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"

    # 工具调用事件
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
    TOOL_CALL_END = "TOOL_CALL_END"
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"


class AGUIAdapter:
    """AG-UI 协议适配器

    将我们的内部事件格式转换为符合 AG-UI 协议的事件流。
    支持流式逐字输出、思考过程展示、工具调用等。
    """

    def __init__(self, session_id: Optional[str] = None, debug: bool = False):
        """初始化适配器

        Args:
            session_id: 会话 ID，用作 runId
            debug: 是否启用调试日志
        """
        self.run_id = session_id or str(uuid.uuid4())
        self.message_id = f"msg_{uuid.uuid4().hex[:8]}"
        self.thinking_id = f"thinking_{uuid.uuid4().hex[:8]}"
        self.tool_call_id = f"tool_{uuid.uuid4().hex[:8]}"
        self.debug = debug

        # 状态追踪
        self.run_started = False
        self.message_started = False
        self.thinking_started = False
        self.thinking_text_started = False
        self.tool_call_started = False

        # 当前工具调用信息
        self.current_tool: Optional[str] = None

        # Agent ReAct 阶段追踪
        self.current_stage = None  # None, "thought", "action", "action_input", "observation", "final_answer"
        self.line_buffer = ""  # 用于检测行标记
        self.pending_tokens = []  # 等待确认的 token 缓冲

    def convert_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """转换内部事件为 AG-UI 事件

        Args:
            event: 内部事件字典，格式如 {"type": "token", "content": "..."}

        Returns:
            AG-UI 事件列表（可能包含多个事件，如 START + CONTENT）
        """
        event_type = event.get("type")

        # 会话开始
        if event_type == "start":
            return self._handle_start(event)

        # Reasoning 思考过程（Deepseek）
        elif event_type == "reasoning_token":
            return self._handle_reasoning_token(event)

        # 正式回答内容
        elif event_type == "token":
            return self._handle_answer_token(event)

        # 工具调用
        elif event_type == "action":
            return self._handle_action(event)

        elif event_type == "tool_start":
            return self._handle_tool_start(event)

        elif event_type == "tool_end":
            return self._handle_tool_end(event)

        # 会话结束
        elif event_type in ("done", "final"):
            return self._handle_finish(event)

        # 错误
        elif event_type == "error":
            return self._handle_error(event)

        # 其他事件（如 thinking）暂不处理
        else:
            return []

    def _handle_start(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理会话开始"""
        if self.run_started:
            return []

        self.run_started = True
        return [{
            "type": AGUIEventType.RUN_STARTED,
            "runId": self.run_id
        }]

    def _handle_reasoning_token(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理 Reasoning 思考过程 token（Deepseek 特有）

        返回 THINKING_* 系列事件
        """
        events = []

        # 第一次 reasoning token，发送 THINKING_START 和 TEXT_MESSAGE_START
        if not self.thinking_started:
            self.thinking_started = True
            events.append({
                "type": AGUIEventType.THINKING_START,
                "thinkingId": self.thinking_id
            })
            events.append({
                "type": AGUIEventType.THINKING_TEXT_MESSAGE_START,
                "thinkingId": self.thinking_id
            })
            self.thinking_text_started = True

        # 发送思考内容（delta 逐字传输）
        content = event.get("content", "")
        if content:
            events.append({
                "type": AGUIEventType.THINKING_TEXT_MESSAGE_CONTENT,
                "thinkingId": self.thinking_id,
                "delta": content
            })

        return events

    def _detect_and_handle_react_markers(self, token: str) -> tuple[List[str], Optional[str]]:
        """检测 ReAct 格式标记，返回要发送的 tokens 和阶段切换信息

        Args:
            token: 当前 token

        Returns:
            (tokens_to_send, stage_info):
                - tokens_to_send: 要发送的 token 列表（可能包含之前缓存的）
                - stage_info: 阶段切换信息 ("thought", "final_answer", None)
        """
        self.line_buffer += token

        # 🔥 调试日志
        if self.debug:
            logger.debug(f"[ReAct] Token: {repr(token)}, Stage: {self.current_stage}, "
                        f"Buffer: {repr(self.line_buffer[-50:])}, Pending: {len(self.pending_tokens)}")

        # 限制缓冲区大小
        if len(self.line_buffer) > 100:
            self.line_buffer = self.line_buffer[-100:]

        # 检测标记（按照长度降序，优先匹配长标记）
        markers = {
            "Action Input:": "action_input",
            "Final Answer:": "final_answer",
            "Observation:": "observation",
            "Thought:": "thought",
            "Action:": "action",
        }

        # 检查是否匹配到完整标记
        for marker, stage in markers.items():
            if marker in self.line_buffer:
                # 找到标记，清空 pending_tokens（不发送）
                if self.debug:
                    logger.debug(f"[ReAct] 🎯 Detected marker: {marker} -> {stage}, "
                                f"Discarding {len(self.pending_tokens)} pending tokens")
                self.pending_tokens.clear()

                # 从缓冲区中移除标记及之前的内容
                marker_pos = self.line_buffer.find(marker)
                self.line_buffer = self.line_buffer[marker_pos + len(marker):]

                # 切换阶段
                old_stage = self.current_stage
                self.current_stage = stage
                if self.debug:
                    logger.debug(f"[ReAct] Stage transition: {old_stage} -> {stage}")

                # 只有 Thought 和 Final Answer 需要通知上层开启新消息
                if stage in ["thought", "final_answer"]:
                    return ([], stage)
                else:
                    # Action/Observation 不开启消息，直接返回
                    return ([], None)

        # 检测换行符
        if '\n' in token or '\r' in token:
            self.line_buffer = ""

        # 检查 line_buffer 是否以可能的标记关键词结尾（需要等待下一个 token 确认）
        marker_prefixes = ["Thought", "Action", "Observation", "Final"]
        buffer_ends_with_prefix = any(
            self.line_buffer.rstrip().endswith(prefix) for prefix in marker_prefixes
        )

        if buffer_ends_with_prefix:
            # 可能是标记的开始，缓存当前 token，等待确认
            if self.debug:
                logger.debug(f"[ReAct] ⏸️ Buffering token (possible marker prefix)")
            self.pending_tokens.append(token)
            return ([], None)

        # 没有检测到标记前缀，发送之前缓存的 tokens + 当前 token
        tokens_to_send = []
        if len(self.pending_tokens) > 0:
            tokens_to_send.extend(self.pending_tokens)
            if self.debug:
                logger.debug(f"[ReAct] ✅ Releasing {len(self.pending_tokens)} pending tokens")
            self.pending_tokens.clear()
        tokens_to_send.append(token)

        # 根据当前阶段决定是否发送
        if self.current_stage in ["thought", "final_answer"]:
            # Thought 或 Final Answer 内容，发送
            if self.debug and len(tokens_to_send) > 0:
                logger.debug(f"[ReAct] 📤 Sending {len(tokens_to_send)} tokens in stage {self.current_stage}")
            return (tokens_to_send, None)
        elif self.current_stage in ["action", "action_input", "observation"]:
            # Action/Observation 内容，不发送
            if self.debug:
                logger.debug(f"[ReAct] 🚫 Discarding token in stage {self.current_stage}")
            return ([], None)
        else:
            # 初始阶段（第一个 Thought 之前），不发送
            if self.debug:
                logger.debug(f"[ReAct] 🚫 Discarding token (before first Thought)")
            return ([], None)

    def _handle_answer_token(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理正式回答 token（来自 content 流，包含 ReAct 格式）

        返回 TEXT_MESSAGE_* 系列事件
        """
        events = []
        content = event.get("content", "")

        # 🔥 检测 ReAct 标记和阶段切换
        tokens_to_send, stage_info = self._detect_and_handle_react_markers(content)

        # 如果检测到新的 Thought 或 Final Answer 阶段
        if stage_info in ["thought", "final_answer"]:
            # 先结束之前的 THINKING（如果有）
            if self.thinking_started:
                if self.thinking_text_started:
                    events.append({
                        "type": AGUIEventType.THINKING_TEXT_MESSAGE_END,
                        "thinkingId": self.thinking_id
                    })
                    self.thinking_text_started = False
                events.append({
                    "type": AGUIEventType.THINKING_END,
                    "thinkingId": self.thinking_id
                })
                self.thinking_started = False

            # 结束上一个 MESSAGE（如果有）
            if self.message_started:
                events.append({
                    "type": AGUIEventType.TEXT_MESSAGE_END,
                    "messageId": self.message_id
                })
                self.message_started = False

            # 生成新的 MESSAGE ID
            self.message_id = f"msg_{uuid.uuid4().hex[:8]}"

            # 开启新的 MESSAGE
            events.append({
                "type": AGUIEventType.TEXT_MESSAGE_START,
                "messageId": self.message_id,
                "role": "assistant"
            })
            self.message_started = True

            return events

        # 如果有需要发送的内容
        if len(tokens_to_send) > 0:
            # 确保消息已经开启（如果还没开启，开启一个）
            if not self.message_started:
                # 先结束 THINKING（如果有）
                if self.thinking_started:
                    if self.thinking_text_started:
                        events.append({
                            "type": AGUIEventType.THINKING_TEXT_MESSAGE_END,
                            "thinkingId": self.thinking_id
                        })
                        self.thinking_text_started = False
                    events.append({
                        "type": AGUIEventType.THINKING_END,
                        "thinkingId": self.thinking_id
                    })
                    self.thinking_started = False

                # 开启新消息
                self.message_id = f"msg_{uuid.uuid4().hex[:8]}"
                events.append({
                    "type": AGUIEventType.TEXT_MESSAGE_START,
                    "messageId": self.message_id,
                    "role": "assistant"
                })
                self.message_started = True

            # 发送所有 tokens
            for token in tokens_to_send:
                events.append({
                    "type": AGUIEventType.TEXT_MESSAGE_CONTENT,
                    "messageId": self.message_id,
                    "delta": token
                })

        return events

    def _handle_action(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理 Agent action 决策

        这个事件包含工具名称和思考过程
        """
        # action 事件暂时不单独处理，等待 tool_start
        self.current_tool = event.get("action")
        return []

    def _handle_tool_start(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理工具调用开始"""
        events = []

        # 如果之前有 thinking，先结束它
        if self.thinking_started:
            if self.thinking_text_started:
                events.append({
                    "type": AGUIEventType.THINKING_TEXT_MESSAGE_END,
                    "thinkingId": self.thinking_id
                })
                self.thinking_text_started = False

            events.append({
                "type": AGUIEventType.THINKING_END,
                "thinkingId": self.thinking_id
            })
            self.thinking_started = False

        # 🔥 如果消息已开始，先关闭它（工具调用表示当前思考已结束）
        if self.message_started:
            events.append({
                "type": AGUIEventType.TEXT_MESSAGE_END,
                "messageId": self.message_id
            })
            self.message_started = False

        # 生成新的 tool_call_id
        self.tool_call_id = f"tool_{uuid.uuid4().hex[:8]}"
        self.tool_call_started = True

        tool_name = event.get("tool", "unknown")
        tool_input = event.get("input", "")

        # 发送 TOOL_CALL_START
        events.append({
            "type": AGUIEventType.TOOL_CALL_START,
            "toolCallId": self.tool_call_id,
            "toolCallName": tool_name
        })

        # 发送 TOOL_CALL_ARGS（可以流式传输 JSON）
        if tool_input:
            events.append({
                "type": AGUIEventType.TOOL_CALL_ARGS,
                "toolCallId": self.tool_call_id,
                "delta": tool_input
            })

        return events

    def _handle_tool_end(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理工具调用结束"""
        if not self.tool_call_started:
            return []

        events = []

        # 发送 TOOL_CALL_END
        events.append({
            "type": AGUIEventType.TOOL_CALL_END,
            "toolCallId": self.tool_call_id
        })

        # 发送工具执行结果
        output = event.get("output", "")
        if output:
            events.append({
                "type": AGUIEventType.TOOL_CALL_RESULT,
                "toolCallId": self.tool_call_id,
                "content": output
            })

        self.tool_call_started = False
        return events

    def _handle_finish(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理会话结束"""
        events = []

        # 结束所有未完成的事件
        if self.thinking_started:
            if self.thinking_text_started:
                events.append({
                    "type": AGUIEventType.THINKING_TEXT_MESSAGE_END,
                    "thinkingId": self.thinking_id
                })
                self.thinking_text_started = False
            events.append({
                "type": AGUIEventType.THINKING_END,
                "thinkingId": self.thinking_id
            })
            self.thinking_started = False

        if self.message_started:
            events.append({
                "type": AGUIEventType.TEXT_MESSAGE_END,
                "messageId": self.message_id
            })
            self.message_started = False

        # 只在第一次结束时发送 RUN_FINISHED
        if self.run_started:
            events.append({
                "type": AGUIEventType.RUN_FINISHED,
                "runId": self.run_id,
                "sessionId": event.get("session_id")  # 保留原始 session_id
            })
            self.run_started = False

        return events

    def _handle_error(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理错误"""
        return [{
            "type": AGUIEventType.RUN_ERROR,
            "runId": self.run_id,
            "error": event.get("error", "Unknown error")
        }]
