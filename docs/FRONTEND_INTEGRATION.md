# TDesign Chat 前端集成指南

## 概述

后端已实现 AG-UI 协议支持，可以直接与 TDesign Chat 组件无缝集成。

## 快速开始

### 1. 安装 TDesign Chat

```bash
npm install @tdesign-vue-next/chat
# 或
pnpm add @tdesign-vue-next/chat
```

### 2. 最简单的集成（零配置）

```vue
<template>
  <t-chatbot :chat-service-config="chatServiceConfig" />
</template>

<script setup>
const chatServiceConfig = {
  endpoint: 'http://localhost:8007/api/v1/chat/stream',
  protocol: 'agui',  // ✅ 启用 AG-UI 协议
  stream: true,
};
</script>
```

**就这么简单！TDesign Chat 会自动：**
- ✅ 显示思考过程（THINKING_*）
- ✅ 逐字流式展示回答（delta）
- ✅ 展示工具调用（TOOL_CALL_*）
- ✅ 管理会话状态（RUN_*）

---

## 事件流说明

### 完整的 AG-UI 事件流示例

```
1. RUN_STARTED → 会话开始
   {"type": "RUN_STARTED", "runId": "001c79f3-..."}

2. TEXT_MESSAGE_START → 消息开始
   {"type": "TEXT_MESSAGE_START", "messageId": "msg_f819cbd8", "role": "assistant"}

3. THINKING_* → 思考过程（Deepseek Reasoning）
   {"type": "THINKING_START", "thinkingId": "thinking_4a6a7d78"}
   {"type": "THINKING_TEXT_MESSAGE_START", "thinkingId": "thinking_4a6a7d78"}
   {"type": "THINKING_TEXT_MESSAGE_CONTENT", "thinkingId": "thinking_4a6a7d78", "delta": "用户"}
   {"type": "THINKING_TEXT_MESSAGE_CONTENT", "thinkingId": "thinking_4a6a7d78", "delta": "问"}
   ...
   {"type": "THINKING_TEXT_MESSAGE_END", "thinkingId": "thinking_4a6a7d78"}
   {"type": "THINKING_END", "thinkingId": "thinking_4a6a7d78"}

4. TEXT_MESSAGE_CONTENT → 正式回答（逐字流式）
   {"type": "TEXT_MESSAGE_CONTENT", "messageId": "msg_f819cbd8", "delta": "当"}
   {"type": "TEXT_MESSAGE_CONTENT", "messageId": "msg_f819cbd8", "delta": "前"}
   {"type": "TEXT_MESSAGE_CONTENT", "messageId": "msg_f819cbd8", "delta": "项"}
   ...

5. TOOL_CALL_* → 工具调用
   {"type": "TOOL_CALL_START", "toolCallId": "tool_001", "toolCallName": "test_coverage"}
   {"type": "TOOL_CALL_ARGS", "toolCallId": "tool_001", "delta": "{\"project_name\":\"default\"}"}
   {"type": "TOOL_CALL_END", "toolCallId": "tool_001"}
   {"type": "TOOL_CALL_RESULT", "toolCallId": "tool_001", "content": "总覆盖率75%..."}

6. TEXT_MESSAGE_END → 消息结束
   {"type": "TEXT_MESSAGE_END", "messageId": "msg_f819cbd8"}

7. RUN_FINISHED → 会话结束
   {"type": "RUN_FINISHED", "runId": "001c79f3-...", "sessionId": "cf98a961-..."}
```

---

## 高级配置

### 1. 自定义事件处理

```vue
<script setup>
const chatServiceConfig = {
  endpoint: 'http://localhost:8007/api/v1/chat/stream',
  protocol: 'agui',
  stream: true,

  // 可选：自定义事件处理（返回 null 使用内置处理）
  onMessage: (chunk) => {
    console.log('收到事件:', chunk);

    // 使用 TDesign Chat 内置的 AG-UI 解析
    return null;
  },
};
</script>
```

### 2. 自定义工具组件渲染

```vue
<script setup>
import { useAgentToolcall } from '@tdesign-vue-next/chat';

// 注册自定义工具组件
const { registerTool } = useAgentToolcall();

registerTool('test_coverage', {
  component: TestCoverageCard,  // 自定义组件
  props: (toolCall) => ({
    data: JSON.parse(toolCall.args),
    result: toolCall.result
  })
});
</script>
```

### 3. 订阅 Agent 状态

```vue
<script setup>
import { useAgentState } from '@tdesign-vue-next/chat';

const { state, subscribe } = useAgentState();

// 订阅状态变化
subscribe((newState) => {
  console.log('Agent 状态更新:', newState);
});
</script>
```

---

## 测试接口

### 使用 curl 测试

```bash
curl -N -X POST http://localhost:8007/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "查询项目测试覆盖率", "session_id": null}'
```

### 使用原生 JavaScript

```javascript
const eventSource = new EventSource('http://localhost:8007/api/v1/chat/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'THINKING_TEXT_MESSAGE_CONTENT':
      console.log('思考:', data.delta);
      break;
    case 'TEXT_MESSAGE_CONTENT':
      console.log('回答:', data.delta);
      break;
    case 'TOOL_CALL_START':
      console.log('调用工具:', data.toolCallName);
      break;
  }
};
```

---

## UI 展示效果

### 思考过程（THINKING）
- **标题**: "🧠 深度思考" 或自定义
- **样式**: 灰色、小字体、可折叠
- **内容**: Deepseek Reasoner 的内部推理过程

### 正式回答（TEXT_MESSAGE）
- **样式**: 正常字体、Markdown 渲染
- **效果**: 逐字流式打字机效果

### 工具调用（TOOL_CALL）
- **标题**: "🔧 调用工具: test_coverage"
- **参数**: JSON 格式显示
- **结果**: 可自定义渲染组件

---

## 常见问题

### Q: 如何区分思考过程和正式回答？

A: AG-UI 协议已经明确区分：
- `THINKING_TEXT_MESSAGE_CONTENT` → 思考过程（可折叠、灰色）
- `TEXT_MESSAGE_CONTENT` → 正式回答（主要展示区）

### Q: 流式效果能逐字显示吗？

A: 能！每个 `delta` 字段都是一个字或词，TDesign Chat 会自动逐字追加。

### Q: 如何自定义工具调用的显示？

A: 使用 `useAgentToolcall` Hook 注册自定义组件：

```javascript
registerTool('test_coverage', {
  component: MyCustomCard,
  props: (toolCall) => ({ ...toolCall })
});
```

### Q: 如何保存对话历史？

A: 后端返回的 `sessionId` 可用于恢复会话：

```javascript
const chatServiceConfig = {
  endpoint: '/api/v1/chat/stream',
  protocol: 'agui',
  sessionId: savedSessionId,  // 传入已有会话 ID
};
```

---

## 完整示例项目结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.vue      # 聊天界面
│   │   └── tools/
│   │       ├── TestCoverageCard.vue  # 测试覆盖率工具卡片
│   │       └── JenkinsBuildCard.vue  # Jenkins 构建卡片
│   ├── composables/
│   │   └── useChatConfig.js       # 聊天配置
│   └── App.vue
└── package.json
```

### ChatInterface.vue 示例

```vue
<template>
  <div class="chat-container">
    <t-chatbot
      :chat-service-config="chatConfig"
      :messages="messages"
      @message-send="handleSend"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAgentToolcall } from '@tdesign-vue-next/chat';
import TestCoverageCard from './tools/TestCoverageCard.vue';

// 注册工具组件
const { registerTool } = useAgentToolcall();
registerTool('test_coverage', {
  component: TestCoverageCard
});

const chatConfig = {
  endpoint: 'http://localhost:8007/api/v1/chat/stream',
  protocol: 'agui',
  stream: true,
};

const messages = ref([]);

const handleSend = (message) => {
  console.log('发送消息:', message);
};
</script>

<style scoped>
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
```

---

## 下一步

1. **创建前端项目**：使用 Vue3 + TDesign Chat
2. **安装依赖**：`npm install @tdesign-vue-next/chat`
3. **复制配置**：使用上面的 chatServiceConfig
4. **启动测试**：访问 http://localhost:3000
5. **自定义工具组件**：根据业务需求定制展示

---

## 参考资源

- [TDesign Chat 官方文档](https://tdesign.tencent.com/chat)
- [AG-UI 协议规范](https://tdesign.tencent.com/chat/getting-started)
- [Vue3 文档](https://vuejs.org/)
