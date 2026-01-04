# 流式对话接口使用指南

## 概述

为了解决 Agent 处理时间长、用户需要等待的问题，我们实现了**流式对话接口**。用户可以实时看到 Agent 的思考过程和工具调用情况，大大提升用户体验。

## 接口对比

### 普通接口（阻塞式）
- **端点**: `POST /api/v1/chat`
- **特点**: 等待所有处理完成后一次性返回
- **问题**: 复杂查询可能需要 2+ 分钟，用户干等
- **适用**: 简单查询、后台任务

### 流式接口（推荐）
- **端点**: `POST /api/v1/chat/stream`
- **特点**: 实时返回处理进度和结果
- **优势**: 用户能看到 Agent 在做什么，不会焦虑
- **适用**: 所有用户交互场景

## 事件类型

流式接口使用 Server-Sent Events (SSE) 格式，返回以下事件类型：

| 事件类型 | 说明 | 示例数据 |
|---------|------|---------|
| `start` | 开始处理请求 | `{"type": "start", "session_id": "xxx"}` |
| `thinking` | Agent 思考中 | `{"type": "thinking", "content": "正在思考..."}` |
| `action` | Agent 决定的行动 | `{"type": "action", "action": "test_coverage", "thought": "需要查询..."}` |
| `tool_start` | 开始调用工具 | `{"type": "tool_start", "tool": "test_coverage", "input": "{...}"}` |
| `tool_end` | 工具调用完成 | `{"type": "tool_end", "output": "{...}"}` |
| `done` | Agent 完成思考 | `{"type": "done", "response": "答案"}` |
| `final` | 最终响应 | `{"type": "final", "response": "...", "session_id": "xxx"}` |
| `error` | 发生错误 | `{"type": "error", "error": "错误信息"}` |

## 使用方法

### 1. curl 测试

```bash
curl -N -X POST http://localhost:8006/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "查询 my-project 的测试覆盖率",
    "session_id": null
  }'
```

**关键参数**:
- `-N`: 禁用缓冲，立即显示输出
- `--no-buffer`: 某些 curl 版本需要此参数

### 2. Python 客户端

```python
import requests
import json

url = "http://localhost:8006/api/v1/chat/stream"
data = {
    "message": "分析项目健康状况",
    "session_id": None
}

response = requests.post(url, json=data, stream=True)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            event = json.loads(line_str[6:])
            print(f"[{event['type']}]", event)
```

### 3. JavaScript (前端)

#### 方式A: EventSource (仅 GET)

```javascript
// 注意: EventSource 只支持 GET 请求
// 需要后端提供 GET 版本或使用 fetch
```

#### 方式B: Fetch API (推荐)

```javascript
const response = await fetch('/api/v1/chat/stream', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: '查询项目状态',
    session_id: null
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));

      switch(event.type) {
        case 'start':
          console.log('开始处理:', event.session_id);
          break;
        case 'thinking':
          showThinking(event.content);
          break;
        case 'tool_start':
          showToolCall(event.tool, event.input);
          break;
        case 'tool_end':
          hideToolCall();
          break;
        case 'final':
          displayFinalAnswer(event.response);
          break;
      }
    }
  }
}
```

### 4. React 示例

```jsx
import { useState, useEffect } from 'react';

function ChatStream() {
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState('');

  const sendMessage = async (message) => {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message, session_id: null})
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const event = JSON.parse(line.slice(6));

          if (event.type === 'thinking') {
            setStatus('Agent思考中...');
          } else if (event.type === 'tool_start') {
            setStatus(`调用工具: ${event.tool}`);
          } else if (event.type === 'final') {
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: event.response
            }]);
            setStatus('');
          }
        }
      }
    }
  };

  return (
    <div>
      <div className="status">{status}</div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>{msg.content}</div>
        ))}
      </div>
    </div>
  );
}
```

## UI 设计建议

### 实时状态显示

```
┌─────────────────────────────────────┐
│ 💭 Agent思考中...                    │
│                                     │
│ 🔧 正在调用: test_coverage          │
│    ⏳ 查询测试覆盖率数据...         │
└─────────────────────────────────────┘
```

### 工具调用可视化

```
执行过程:
├─ ✅ test_coverage (已完成)
├─ ✅ test_cases (已完成)
├─ 🔄 jenkins (进行中...)
└─ ⏳ artifactory (等待中)
```

### 打字机效果

对于 `done` 和 `final` 事件中的文本，可以实现打字机效果：

```javascript
function typeWriter(text, element, delay = 30) {
  let i = 0;
  const timer = setInterval(() => {
    if (i < text.length) {
      element.textContent += text.charAt(i);
      i++;
    } else {
      clearInterval(timer);
    }
  }, delay);
}
```

## 性能数据

### 测试对比

| 场景 | 普通接口 | 流式接口 | 改善 |
|-----|---------|---------|------|
| 简单查询 | 8秒 | 首个响应 1秒 | ⭐⭐⭐⭐⭐ |
| 综合分析 | 120秒 | 首个响应 1秒 | ⭐⭐⭐⭐⭐ |
| 用户感知 | 焦虑等待 | 实时反馈 | ⭐⭐⭐⭐⭐ |

### 实际案例

**测试3（5个工具调用）**:
- **普通接口**: 用户等待 2+ 分钟，不知道在做什么
- **流式接口**:
  - 0s: 看到"开始处理"
  - 1s: 看到"正在思考"
  - 5s: 看到"调用 test_coverage 工具"
  - 8s: 看到"调用 test_cases 工具"
  - ...实时进度
  - 120s: 收到完整答案

用户体验提升：**从焦虑等待到放心观看**

## 最佳实践

### 1. 前端实现

- ✅ 显示实时状态（思考/工具调用）
- ✅ 展示工具调用列表和进度
- ✅ 支持取消请求
- ✅ 错误处理和重试

### 2. 错误处理

```javascript
try {
  // 流式请求
} catch (error) {
  if (error.name === 'AbortError') {
    console.log('用户取消');
  } else {
    console.error('请求失败:', error);
    // 降级到普通接口
  }
}
```

### 3. 超时控制

```python
response = requests.post(
    url,
    json=data,
    stream=True,
    timeout=(5, 300)  # (连接超时, 读取超时)
)
```

## 故障排查

### 问题1: 没有实时输出

**原因**: 可能被反向代理缓冲

**解决**:
```nginx
# nginx 配置
proxy_buffering off;
proxy_cache off;
```

### 问题2: 连接中断

**原因**: 超时设置过短

**解决**: 增加超时时间或实现心跳

### 问题3: 解析错误

**原因**: SSE 格式不正确

**解决**: 确保每个事件以 `data: ` 开头，以 `\n\n` 结尾

## 下一步优化

1. **LLM 流式输出**: 当前 LLM 回复是一次性的，可以改为逐token流式
2. **心跳机制**: 长时间无事件时发送心跳保持连接
3. **进度百分比**: 估算总步骤数，显示进度百分比
4. **可取消**: 支持用户中途取消请求
5. **重连机制**: 连接断开后自动重连

## 总结

流式接口将 **2分钟的焦虑等待** 变成了 **2分钟的实时互动**，大幅提升用户体验！

**推荐**: 所有生产环境都使用流式接口 `/api/v1/chat/stream`
