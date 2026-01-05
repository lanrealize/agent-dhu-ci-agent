"""AG-UI 协议适配器

将内部事件格式转换为 AG-UI 标准协议格式。
参考：https://tdesign.tencent.com/chat
"""

import uuid
from typing import Dict, Any, Optional, List
from enum import Enum


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

    def __init__(self, session_id: Optional[str] = None):
        """初始化适配器

        Args:
            session_id: 会话 ID，用作 runId
        """
        self.run_id = session_id or str(uuid.uuid4())
        self.message_id = f"msg_{uuid.uuid4().hex[:8]}"
        self.thinking_id = f"thinking_{uuid.uuid4().hex[:8]}"
        self.tool_call_id = f"tool_{uuid.uuid4().hex[:8]}"

        # 状态追踪
        self.run_started = False
        self.message_started = False
        self.thinking_started = False
        self.thinking_text_started = False
        self.tool_call_started = False

        # 当前工具调用信息
        self.current_tool: Optional[str] = None

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

    def _handle_answer_token(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理正式回答 token

        返回 TEXT_MESSAGE_* 系列事件
        """
        events = []
        content = event.get("content", "")

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

        # 第一次回答 token，发送 MESSAGE_START
        if not self.message_started:
            self.message_started = True
            events.append({
                "type": AGUIEventType.TEXT_MESSAGE_START,
                "messageId": self.message_id,
                "role": "assistant"
            })

        # 发送回答内容（delta 逐字传输）
        if content:
            events.append({
                "type": AGUIEventType.TEXT_MESSAGE_CONTENT,
                "messageId": self.message_id,
                "delta": content
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

        # 如果消息已开始，先暂停（稍后在 tool_end 后继续）
        # 注意：不发送 MESSAGE_END，因为工具调用后还会继续回答

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
