"""测试官方 Deepseek API 流式输出中的 reasoning_content"""

import requests
import json

API_KEY = "sk-7c380b50fce04413a8ef674fb56dbf6c"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-reasoner"

print("=" * 60)
print("测试流式输出中的 reasoning_content")
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
            {"role": "user", "content": "1+1等于几？请思考后回答。"}
        ],
        "stream": True
    },
    stream=True
)

print("\n流式响应片段：\n")

reasoning_chunks = []
content_chunks = []
chunk_count = 0

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data_str = line_str[6:]
            if data_str.strip() == '[DONE]':
                print("\n[DONE]")
                break

            try:
                data = json.loads(data_str)
                chunk_count += 1

                if "choices" in data and len(data["choices"]) > 0:
                    delta = data["choices"][0].get("delta", {})

                    # 检查 delta 中的字段
                    if delta:
                        print(f"\n[Chunk {chunk_count}]")
                        print(f"  delta keys: {list(delta.keys())}")

                        # 检查 reasoning_content
                        if "reasoning_content" in delta and delta["reasoning_content"]:
                            reasoning_chunks.append(delta["reasoning_content"])
                            print(f"  reasoning_content: {delta['reasoning_content'][:50]}...")

                        # 检查 content
                        if "content" in delta and delta["content"]:
                            content_chunks.append(delta["content"])
                            print(f"  content: {delta['content'][:50]}...")

                        # 其他字段
                        if "role" in delta:
                            print(f"  role: {delta['role']}")

                # 只显示前 20 个 chunk
                if chunk_count >= 20:
                    print("\n... (后续 chunk 省略)")
                    break

            except json.JSONDecodeError as e:
                print(f"JSON 解析错误: {e}")

print("\n" + "=" * 60)
print("汇总：")
print("=" * 60)
print(f"总 chunk 数: {chunk_count}")
print(f"reasoning_content chunk 数: {len(reasoning_chunks)}")
print(f"content chunk 数: {len(content_chunks)}")

if reasoning_chunks:
    print("\n完整 reasoning_content:")
    print("".join(reasoning_chunks))

if content_chunks:
    print("\n完整 content:")
    print("".join(content_chunks))
