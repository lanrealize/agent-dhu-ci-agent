"""测试 LLM 流式输出是否工作"""

from src.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.callbacks import StreamingStdOutCallbackHandler

# 创建启用流式的 LLM
llm = ChatOpenAI(
    model=settings.deepseek_model,
    openai_api_key=settings.deepseek_api_key,
    openai_api_base=settings.deepseek_base_url,
    temperature=0.7,
    streaming=True,  # 启用流式
    callbacks=[StreamingStdOutCallbackHandler()]  # 直接输出到控制台
)

print("测试 LLM 流式输出...")
print("="*80)
print("如果流式工作，你应该看到文字一个一个蹦出来：\n")

# 测试
messages = [HumanMessage(content="请用一句话介绍你自己")]
response = llm.invoke(messages)

print("\n\n" + "="*80)
print("✓ 测试完成")
