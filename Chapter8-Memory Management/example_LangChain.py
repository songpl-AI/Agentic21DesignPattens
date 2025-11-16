
from langchain.messages import AIMessage, SystemMessage, HumanMessage

from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv

load_dotenv()

llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

messages = [
    HumanMessage("你好"),
    AIMessage("你好！有什么我可以帮助你的吗？"),
    HumanMessage("我想知道关于LangChain的更多信息"),
    AIMessage("当然！LangChain是一个用于构建智能对话式应用的框架。它提供了丰富的功能，包括内存管理、工具调用、模型集成等。你可以在LangChain的官方文档中找到更多详细信息。")
]

print(llm.invoke(messages))




