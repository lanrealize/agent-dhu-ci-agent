"""测试 Deepseek 官方 API 是否返回 thinking/reasoning_content"""

import os
import requests
import json

# 使用官方 Deepseek API
API_KEY = "sk-7c380b50fce04413a8ef674fb56dbf6c"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-reasoner"  # 推理模型，应该有 thinking

# 测试普通请求
print("=" * 60)
print("测试 1: 非流式请求")
print("=" * 60)

response = requests.post(
    f"{BASE_URL}/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "请简单介绍一下你自己"}
        ],
        "stream": False
    }
)

print(f"状态码: {response.status_code}")

# 保存到文件避免编码问题
with open("deepseek_response.json", "w", encoding="utf-8") as f:
    json.dump(response.json(), f, indent=2, ensure_ascii=False)

print("\n完整响应已保存到 deepseek_response.json")

# 检查是否有 reasoning_content
resp_json = response.json()
if "choices" in resp_json and len(resp_json["choices"]) > 0:
    message = resp_json["choices"][0].get("message", {})
    print("\n" + "=" * 60)
    print("message 字段包含的 keys:")
    print(list(message.keys()))

    if "reasoning_content" in message:
        print("\n✅ 找到 reasoning_content 字段！")
        print(f"内容: {message['reasoning_content'][:200]}...")
    else:
        print("\n❌ 未找到 reasoning_content 字段")

    if "content" in message:
        print("\n✅ 找到 content 字段")
        print(f"内容: {message['content'][:200]}...")

print("\n" + "=" * 60)
print("测试 2: 流式请求")
print("=" * 60)

response = requests.post(
    f"{BASE_URL}/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "1+1等于几？"}
        ],
        "stream": True
    },
    stream=True
)

print("流式响应片段（前 10 条）:")
count = 0
for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data_str = line_str[6:]
            if data_str.strip() == '[DONE]':
                break
            try:
                data = json.loads(data_str)
                count += 1
                if count <= 10:
                    print(f"\n片段 {count}:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))

                    # 检查 delta 中的字段
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        if delta:
                            print(f"  delta keys: {list(delta.keys())}")
            except json.JSONDecodeError:
                pass

print("\n" + "=" * 60)
print("测试完成")
