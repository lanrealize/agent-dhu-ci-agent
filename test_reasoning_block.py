"""深入研究 ReasoningContentBlock 和 content_blocks"""

from langchain_core.messages import AIMessage
from langchain_core.messages.content import ReasoningContentBlock
import inspect

print("=" * 60)
print("ReasoningContentBlock 研究")
print("=" * 60)

# 查看 ReasoningContentBlock 的定义
print(f"\nReasoningContentBlock 定义在: {inspect.getfile(ReasoningContentBlock)}")
print(f"\n类定义:")
print(inspect.getsource(ReasoningContentBlock))

# 查看其字段
if hasattr(ReasoningContentBlock, 'model_fields'):
    print("\n模型字段:")
    for field_name, field in ReasoningContentBlock.model_fields.items():
        print(f"  {field_name}: {field}")

# 测试创建
print("\n" + "=" * 60)
print("测试: 创建带 reasoning content 的消息")
print("=" * 60)

try:
    reasoning_block = ReasoningContentBlock(
        text="这是推理过程"
    )

    msg = AIMessage(
        content="最终答案",
        content_blocks=[
            reasoning_block,
            {"type": "text", "text": "最终答案"}
        ]
    )

    print("成功创建消息！")
    print(f"\nmsg.content: {msg.content}")
    print(f"\nmsg.content_blocks: {msg.content_blocks}")
    print(f"\n完整结构:")
    import json
    print(json.dumps(msg.__dict__, indent=2, ensure_ascii=False, default=str))

except Exception as e:
    print(f"失败: {e}")
    import traceback
    traceback.print_exc()

# 测试从 API 响应读取
print("\n" + "=" * 60)
print("测试: 从实际 API 响应读取 content_blocks")
print("=" * 60)

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

llm = ChatOpenAI(
    model="deepseek-reasoner",
    openai_api_key="sk-7c380b50fce04413a8ef674fb56dbf6c",
    openai_api_base="https://api.deepseek.com",
)

response = llm.invoke([HumanMessage(content="1+1等于几？")])

print(f"response.content_blocks: {response.content_blocks}")

if response.content_blocks:
    print("\n解析 content_blocks:")
    for i, block in enumerate(response.content_blocks):
        print(f"\n  Block {i}:")
        print(f"    type: {type(block)}")
        if hasattr(block, '__dict__'):
            print(f"    data: {block.__dict__}")
        else:
            print(f"    data: {block}")
