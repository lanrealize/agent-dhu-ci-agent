"""直接测试 OpenAI SDK 是否返回 reasoning_content"""

import openai

client = openai.OpenAI(
    api_key="sk-7c380b50fce04413a8ef674fb56dbf6c",
    base_url="https://api.deepseek.com"
)

print("=" * 60)
print("测试 OpenAI SDK 流式响应")
print("=" * 60)

stream = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[{"role": "user", "content": "1+1等于几？"}],
    stream=True
)

chunk_count = 0
for chunk in stream:
    chunk_count += 1
    if chunk_count <= 100:  # 增加到 100 个 chunk
        print(f"\nChunk {chunk_count}:")
        print(f"  chunk type: {type(chunk)}")
        print(f"  chunk: {chunk}")

        if chunk.choices:
            delta = chunk.choices[0].delta
            print(f"  delta: {delta}")
            print(f"  delta.__dict__: {delta.__dict__ if hasattr(delta, '__dict__') else 'N/A'}")

            # 检查是否有 reasoning_content
            if hasattr(delta, 'reasoning_content'):
                rc = delta.reasoning_content
                print(f"  [OK] reasoning_content: {rc if rc else '(empty)'}")
            else:
                print(f"  [NO] reasoning_content")

            # 检查 content
            if hasattr(delta, 'content'):
                c = delta.content
                print(f"  [OK] content: {c if c else '(empty)'}")

print(f"\n总共 {chunk_count} 个 chunks")
