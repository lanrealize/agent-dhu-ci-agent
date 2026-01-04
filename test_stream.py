#!/usr/bin/env python
"""测试流式对话接口"""

import requests
import json

# 测试流式接口
url = "http://127.0.0.1:8005/api/v1/chat/stream"
data = {
    "message": "分析一下 mobile-app 项目的整体健康状况",
    "session_id": None
}

print("=== 开始流式对话测试 ===\n")

try:
    response = requests.post(
        url,
        json=data,
        stream=True,  # 启用流式
        headers={"Content-Type": "application/json"}
    )

    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data_str = line[6:]  # 移除 'data: ' 前缀
                try:
                    event = json.loads(data_str)
                    event_type = event.get('type', '')

                    if event_type == 'start':
                        print(f"\n🚀 开始处理 (Session: {event.get('session_id', 'N/A')[:8]}...)")

                    elif event_type == 'thinking':
                        print(f"\n💭 {event.get('content', '')}")

                    elif event_type == 'tool_start':
                        print(f"\n🔧 调用工具: {event.get('tool', '')}")
                        print(f"   输入: {event.get('input', '')[:100]}...")

                    elif event_type == 'tool_end':
                        print(f"✅ 工具返回: {event.get('output', '')[:100]}...")

                    elif event_type == 'token':
                        print(event.get('content', ''), end='', flush=True)

                    elif event_type == 'done':
                        print(f"\n\n✨ 完成!")
                        print(f"\nSession ID: {event.get('session_id', 'N/A')}")

                    elif event_type == 'error':
                        print(f"\n❌ 错误: {event.get('error', '')}")

                except json.JSONDecodeError:
                    pass

except requests.RequestException as e:
    print(f"❌ 请求失败: {e}")

print("\n\n=== 测试结束 ===")
