"""检查 LangChain AIMessage 类是否支持 reasoning_content"""

from langchain_core.messages import AIMessage, AIMessageChunk
import inspect

print("=" * 60)
print("AIMessage 类定义检查")
print("=" * 60)

# 查看 AIMessage 的源码位置
print(f"\nAIMessage 定义在: {inspect.getfile(AIMessage)}")

# 查看 __init__ 签名
print(f"\n__init__ 签名:")
print(inspect.signature(AIMessage.__init__))

# 查看所有字段
print(f"\n模型字段:")
if hasattr(AIMessage, 'model_fields'):
    for field_name, field in AIMessage.model_fields.items():
        print(f"  {field_name}: {field}")

# 检查是否有 reasoning 相关字段
print(f"\n查找 reasoning 相关:")
for attr in dir(AIMessage):
    if 'reason' in attr.lower():
        print(f"  找到: {attr}")

# 测试创建带 reasoning_content 的消息
print("\n" + "=" * 60)
print("测试: 尝试创建带 reasoning_content 的 AIMessage")
print("=" * 60)

try:
    # 尝试 1: 直接作为参数
    msg1 = AIMessage(
        content="最终答案",
        reasoning_content="推理过程"
    )
    print("✅ 方式 1 成功: 直接作为参数")
    print(f"  msg1.__dict__: {msg1.__dict__}")
except Exception as e:
    print(f"❌ 方式 1 失败: {e}")

try:
    # 尝试 2: 通过 additional_kwargs
    msg2 = AIMessage(
        content="最终答案",
        additional_kwargs={"reasoning_content": "推理过程"}
    )
    print("\n✅ 方式 2 成功: 通过 additional_kwargs")
    print(f"  msg2.additional_kwargs: {msg2.additional_kwargs}")
except Exception as e:
    print(f"\n❌ 方式 2 失败: {e}")

try:
    # 尝试 3: 通过 response_metadata
    msg3 = AIMessage(
        content="最终答案",
        response_metadata={"reasoning_content": "推理过程"}
    )
    print("\n✅ 方式 3 成功: 通过 response_metadata")
    print(f"  msg3.response_metadata: {msg3.response_metadata}")
except Exception as e:
    print(f"\n❌ 方式 3 失败: {e}")

# 检查 AIMessageChunk（流式消息）
print("\n" + "=" * 60)
print("AIMessageChunk 类定义检查")
print("=" * 60)

print(f"\nAIMessageChunk 定义在: {inspect.getfile(AIMessageChunk)}")

if hasattr(AIMessageChunk, 'model_fields'):
    print(f"\n模型字段:")
    for field_name in AIMessageChunk.model_fields.keys():
        print(f"  {field_name}")

# 查看是否支持 model_extra='allow'
print(f"\nmodel_config:")
if hasattr(AIMessage, 'model_config'):
    print(f"  {AIMessage.model_config}")

print("\n" + "=" * 60)
print("结论:")
print("=" * 60)
