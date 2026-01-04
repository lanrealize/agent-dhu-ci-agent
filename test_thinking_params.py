"""测试不同参数是否能获取 thinking"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
MODEL = os.getenv("DEEPSEEK_MODEL")

# 测试各种可能的参数组合
test_cases = [
    {
        "name": "标准请求",
        "params": {}
    },
    {
        "name": "启用 reasoning (类似 o1)",
        "params": {"reasoning": True}
    },
    {
        "name": "启用 thinking",
        "params": {"thinking": True}
    },
    {
        "name": "启用 include_reasoning",
        "params": {"include_reasoning": True}
    },
    {
        "name": "设置 response_format",
        "params": {"response_format": {"type": "json_object"}}
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{'=' * 60}")
    print(f"测试 {i}: {test['name']}")
    print(f"{'=' * 60}")

    try:
        request_body = {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": "1+1等于几？请思考后回答。"}
            ],
            **test['params']
        }

        print(f"请求参数: {json.dumps(test['params'], ensure_ascii=False)}")

        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json=request_body,
            timeout=10
        )

        if response.status_code == 200:
            resp_json = response.json()
            message = resp_json["choices"][0]["message"]

            print(f"message keys: {list(message.keys())}")

            # 检查各种可能的 thinking 字段
            thinking_fields = ["reasoning_content", "thinking", "reasoning", "thought"]
            found = False
            for field in thinking_fields:
                if field in message:
                    print(f"  找到 {field}: {message[field][:100]}...")
                    found = True

            if not found:
                print("  未找到任何 thinking 相关字段")
                print(f"  content 前 100 字符: {message.get('content', '')[:100]}...")
        else:
            print(f"  错误: {response.status_code}")
            print(f"  {response.text[:200]}")

    except Exception as e:
        print(f"  异常: {str(e)}")

print(f"\n{'=' * 60}")
print("测试完成")
print(f"{'=' * 60}")
