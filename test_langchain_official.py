"""调研 LangChain 对 reasoning content 的官方支持

参考：
1. OpenAI o1 模型的 reasoning_content 支持
2. LangChain 的 ChatOpenAI 参数
3. AIMessage 的字段
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import json

# 测试 1: 检查 AIMessage 是否有 reasoning_content 字段
print("=" * 60)
print("测试 1: 检查最终 AIMessage 结构")
print("=" * 60)

llm = ChatOpenAI(
    model="deepseek-reasoner",
    openai_api_key="sk-7c380b50fce04413a8ef674fb56dbf6c",
    openai_api_base="https://api.deepseek.com",
    streaming=False,  # 先测试非流式
)

response = llm.invoke([HumanMessage(content="1+1等于几？")])

print(f"\n类型: {type(response)}")
print(f"\n所有属性:")
for attr in dir(response):
    if not attr.startswith('_'):
        try:
            value = getattr(response, attr)
            if not callable(value):
                print(f"  {attr}: {str(value)[:100] if value else value}")
        except:
            pass

# 检查是否有隐藏的 reasoning_content
print(f"\n完整 __dict__:")
print(json.dumps(response.__dict__, indent=2, ensure_ascii=False, default=str))

# 测试 2: 检查是否需要特殊参数
print("\n" + "=" * 60)
print("测试 2: 尝试不同的初始化参数")
print("=" * 60)

# 尝试添加 model_kwargs
llm2 = ChatOpenAI(
    model="deepseek-reasoner",
    openai_api_key="sk-7c380b50fce04413a8ef674fb56dbf6c",
    openai_api_base="https://api.deepseek.com",
    model_kwargs={
        "include_reasoning": True,  # 尝试
    }
)

response2 = llm2.invoke([HumanMessage(content="1+1等于几？")])
print(f"model_kwargs 测试:")
print(f"  additional_kwargs: {response2.additional_kwargs}")

# 测试 3: 检查 response_metadata 中的详细信息
print("\n" + "=" * 60)
print("测试 3: response_metadata 详细检查")
print("=" * 60)

if hasattr(response, 'response_metadata'):
    print(json.dumps(response.response_metadata, indent=2, ensure_ascii=False, default=str))

# 测试 4: 检查完整的 generation_info
print("\n" + "=" * 60)
print("测试 4: 使用 generate 方法获取更多信息")
print("=" * 60)

result = llm.generate([[HumanMessage(content="1+1等于几？")]])

print(f"LLMResult 类型: {type(result)}")
print(f"LLMResult.generations: {len(result.generations)}")
if result.generations:
    gen = result.generations[0][0]
    print(f"\nGeneration 类型: {type(gen)}")
    print(f"Generation.generation_info:")
    if hasattr(gen, 'generation_info'):
        print(json.dumps(gen.generation_info, indent=2, ensure_ascii=False, default=str))

    print(f"\nGeneration.message.__dict__:")
    if hasattr(gen, 'message'):
        print(json.dumps(gen.message.__dict__, indent=2, ensure_ascii=False, default=str))

if hasattr(result, 'llm_output'):
    print(f"\nLLMResult.llm_output:")
    print(json.dumps(result.llm_output, indent=2, ensure_ascii=False, default=str))
