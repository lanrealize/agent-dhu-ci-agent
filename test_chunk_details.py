"""深入检查 chunk 对象是否包含 reasoning_content"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.callbacks import BaseCallbackHandler
from typing import Any

class ChunkInspectorCallback(BaseCallbackHandler):
    def __init__(self):
        self.chunks = []

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        chunk = kwargs.get('chunk')
        if chunk:
            # 保存 chunk 对象
            self.chunks.append(chunk)

            # 检查 chunk 的所有属性
            print(f"\n[Chunk #{len(self.chunks)}]")
            print(f"  token: {token[:30]}...")
            print(f"  chunk type: {type(chunk)}")

            if hasattr(chunk, 'message'):
                msg = chunk.message
                print(f"  message type: {type(msg)}")
                print(f"  message.__dict__ keys: {list(msg.__dict__.keys())}")

                # 检查 additional_kwargs
                if hasattr(msg, 'additional_kwargs'):
                    print(f"  additional_kwargs: {msg.additional_kwargs}")

                # 检查 response_metadata
                if hasattr(msg, 'response_metadata'):
                    print(f"  response_metadata: {msg.response_metadata}")

                # 直接检查字典
                for key, value in msg.__dict__.items():
                    if 'reason' in key.lower() or 'thinking' in key.lower():
                        print(f"  ✅ Found: {key} = {str(value)[:100]}")

            # 只显示前 5 个 chunk
            if len(self.chunks) >= 5:
                return

llm = ChatOpenAI(
    model="deepseek-reasoner",
    openai_api_key="sk-7c380b50fce04413a8ef674fb56dbf6c",
    openai_api_base="https://api.deepseek.com",
    streaming=True,
)

callback = ChunkInspectorCallback()

print("开始检查 chunk 对象...\n")

response = llm.invoke(
    [HumanMessage(content="1+1等于几？")],
    config={"callbacks": [callback]}
)

print("\n" + "=" * 60)
print(f"总 chunk 数: {len(callback.chunks)}")
print("=" * 60)

# 检查最终 response
print("\n最终 response 检查:")
print(f"  response.__dict__ keys: {list(response.__dict__.keys())}")
for key, value in response.__dict__.items():
    if 'reason' in key.lower() or 'thinking' in key.lower():
        print(f"  ✅ Found in response: {key} = {str(value)[:100]}")

# 检查 usage_metadata
if hasattr(response, 'usage_metadata'):
    print(f"\nusage_metadata: {response.usage_metadata}")
