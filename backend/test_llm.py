"""LLM 连通性测试脚本 — 验证 API Key 和模型是否可用。"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY", "")
if not api_key or api_key == "your_api_key_here":
    print("❌ GOOGLE_API_KEY 未设置或仍为占位符")
    print("   请在 backend/.env 中填入真实的 API Key")
    sys.exit(1)

print(f"✅ API Key 已加载（前8位: {api_key[:8]}...）")
print(f"   模型: gemini-3-flash-preview")
print(f"   Base URL: https://new-api.lingowhale.com/")
print()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=api_key,
    base_url="https://new-api.lingowhale.com/",
    temperature=0,
)

print("🔄 发送测试请求...")
try:
    response = llm.invoke([HumanMessage(content="请回复'连接成功'四个字")])
    print(f"✅ LLM 响应: {response.content}")
    print()
    print("🎉 LLM 连通性测试通过！可以启动演示了。")
except Exception as e:
    print(f"❌ LLM 调用失败: {e}")
    sys.exit(1)
