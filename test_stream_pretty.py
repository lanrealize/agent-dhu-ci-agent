#!/usr/bin/env python
"""流式对话测试脚本 - 带美化输出"""

import requests
import json
import time

def test_streaming_chat():
    """测试流式对话接口"""
    url = "http://127.0.0.1:8006/api/v1/chat/stream"

    # 测试案例
    test_cases = [
        {"message": "请查询 my-project 的测试覆盖率", "name": "简单查询"},
        {"message": "分析一下 mobile-app 项目的整体健康状况", "name": "综合分析"},
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"测试 {i}: {test_case['name']}")
        print(f"问题: {test_case['message']}")
        print('='*80)

        data = {
            "message": test_case['message'],
            "session_id": None
        }

        start_time = time.time()
        session_id = None

        try:
            response = requests.post(
                url,
                json=data,
                stream=True,
                headers={"Content-Type": "application/json"},
                timeout=180
            )

            print()
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        try:
                            event = json.loads(data_str)
                            event_type = event.get('type', '')

                            if event_type == 'start':
                                session_id = event.get('session_id', 'N/A')
                                print(f"🚀 开始处理")
                                print(f"   Session: {session_id}")

                            elif event_type == 'thinking':
                                print(f"\n💭 Agent思考中...")

                            elif event_type == 'action':
                                print(f"\n🎯 决定行动:")
                                print(f"   工具: {event.get('action', 'unknown')}")
                                thought = event.get('thought', '')[:150]
                                print(f"   思考: {thought}...")

                            elif event_type == 'tool_start':
                                print(f"\n🔧 调用工具: {event.get('tool', 'unknown')}")

                            elif event_type == 'tool_end':
                                print(f"   ✅ 工具完成")

                            elif event_type == 'done':
                                print(f"\n\n📝 Agent回答:")
                                print("-" * 80)

                            elif event_type == 'final':
                                response_text = event.get('response', '')
                                print(response_text)
                                print("-" * 80)
                                session_id = event.get('session_id', session_id)

                            elif event_type == 'error':
                                print(f"\n❌ 错误: {event.get('error', '')}")

                        except json.JSONDecodeError:
                            pass

            elapsed = time.time() - start_time
            print(f"\n⏱️  总耗时: {elapsed:.2f}秒")
            print(f"📌 Session ID: {session_id}")

        except requests.RequestException as e:
            print(f"\n❌ 请求失败: {e}")

        # 分隔测试用例
        if i < len(test_cases):
            print("\n" + "="*80)
            print("等待3秒后继续下一个测试...")
            print("="*80)
            time.sleep(3)


if __name__ == "__main__":
    print("流式对话接口测试")
    print("="*80)
    test_streaming_chat()
    print("\n\n✨ 测试完成！")
