"""测试 LangChain ChatOpenAI 是否支持 reasoning_content"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.callbacks import BaseCallbackHandler
from typing import Any, Dict, List

# 自定义 callback 捕获所有信息
class DetailedCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.events = []

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """捕获新 token"""
        self.events.append({
            "type": "token",
            "content": token,
            "kwargs": kwargs  # 看看 kwargs 里有没有 reasoning_content
        })
        print(f"[Token] {token[:50]}... | kwargs keys: {list(kwargs.keys())}")

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        print(f"[LLM Start] kwargs keys: {list(kwargs.keys())}")

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        print(f"\n[LLM End]")
        print(f"  response type: {type(response)}")
        print(f"  response dir: {[x for x in dir(response) if not x.startswith('_')]}")

        # 尝试访问 reasoning_content
        if hasattr(response, 'generations'):
            for gen in response.generations:
                for g in gen:
                    print(f"\n  Generation type: {type(g)}")
                    print(f"  Generation dir: {[x for x in dir(g) if not x.startswith('_')]}")
                    if hasattr(g, 'message'):
                        msg = g.message
                        print(f"    Message type: {type(msg)}")
                        print(f"    Message dir: {[x for x in dir(msg) if not x.startswith('_')]}")
                        print(f"    Message dict: {msg.__dict__}")

# 测试
print("=" * 60)
print("测试 LangChain ChatOpenAI 对 reasoning_content 的支持")
print("=" * 60)

llm = ChatOpenAI(
    model="deepseek-reasoner",
    openai_api_key="sk-7c380b50fce04413a8ef674fb56dbf6c",
    openai_api_base="https://api.deepseek.com",
    streaming=True,
)

callback = DetailedCallbackHandler()

print("\n开始流式调用...\n")

response = llm.invoke(
    [HumanMessage(content="1+1等于几？")],
    config={"callbacks": [callback]}
)

print("\n" + "=" * 60)
print("最终响应：")
print("=" * 60)
print(f"Response type: {type(response)}")
print(f"Response content: {response.content[:200]}")

# 检查是否有 reasoning_content
if hasattr(response, 'response_metadata'):
    print(f"\nresponse_metadata: {response.response_metadata}")

if hasattr(response, 'additional_kwargs'):
    print(f"\nadditional_kwargs: {response.additional_kwargs}")

# 检查所有属性
print(f"\nResponse 所有属性:")
for attr in dir(response):
    if not attr.startswith('_'):
        try:
            value = getattr(response, attr)
            if not callable(value):
                print(f"  {attr}: {str(value)[:100]}")
        except:
            pass

print("\n" + "=" * 60)
print(f"捕获到的事件数: {len(callback.events)}")
print("=" * 60)

# 检查第一个事件
if callback.events:
    print(f"\n第一个事件: {callback.events[0]}")
