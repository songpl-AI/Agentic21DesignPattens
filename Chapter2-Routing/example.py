import os
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableBranch

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

def booking_handler(request:str)->str:
    """
    模拟预订Agent处理请求。

    Args:
        request (str): The booking request.

    Returns:
        str: The booking response.
    """
    print("\n---将请求委托给预订Agent处理程序---")
    return f"预订Agent处理了请求: {request}。结果：模拟的预订操作。"

def info_handler(request:str)->str:
    """
    模拟信息Agent处理请求。

    Args:
        request (str): The information request.

    Returns:
        str: The information response.
    """
    print("\n---将请求委托给信息Agent处理程序---")
    return f"信息Agent处理了请求: {request}。结果：模拟的信息检索结果。"

def unclear_handler(request:str)->str:
    """
    模拟不清晰Agent处理请求。

    Args:
        request (str): The unclear request.

    Returns:
        str: The unclear response.
    """
    print("\n---将请求委托给不清晰Agent处理程序---")
    return f"路由无法将请求委托给其他Agent: {request}。请重新说明您的请求。"

coordinator_router_prompt = ChatPromptTemplate.from_messages([
    ("system", """分析用户请求，确定应该由哪个专业处理程序来处理它。
    -如果请求与预订航班或酒店相关，输出"booker"。
    -对于所有其他一般性信息查询，输出"info"。
    -如果请求不清晰或无法理解，输出"unclear"。
    只输出一个单词，“booker”、“info”或“unclear”。
    """),
    ("user", "{request}"),
])

if llm :
    coordinator_router_chain = coordinator_router_prompt | llm | StrOutputParser()

# 基于子Agent进行路由处理
# 使用 RunnableBranch 根据路由器链的输出结果来决定路由路径。
# 为 RunnableBranch 定义不同的路由分支：
# 说明：为避免出现 x["request"]["request"] 的双层访问混淆，这里将并行映射中的“保留原始输入”键统一为 raw。
branches = {
    "booker": RunnablePassthrough.assign(output=lambda x: booking_handler(x["raw"]["request"])),
    "info": RunnablePassthrough.assign(output=lambda x: info_handler(x["raw"]["request"])),
    "unclear": RunnablePassthrough.assign(output=lambda x: unclear_handler(x["raw"]["request"]))
}

#创建RunnableBranch类型。该类型会接收路由器链的处理结果，然后将原始输入数据传递给对应的分支。
delegation_branch = RunnableBranch(
    # 路由条件按顺序匹配，第一个命中的分支会被执行；增加 lower() 提升健壮性但不改变现有逻辑
    (lambda x: x["decision"].strip().lower() == "booker", branches["booker"]),
    (lambda x: x["decision"].strip().lower() == "info", branches["info"]),
    branches["unclear"]  # 用于处理 “unclear” 类型的输出，或任何其他无法明确分类的输出
)

# 将路由器链和委托分支合并为一个可执行的整体
# 路由器链的输出结果会与原始数据一起被传递给委托分支。
# 说明：并行映射中使用 raw 键原样保存“原始输入”，以提升可读性和维护性。
coordinator_agent = {
    "decision": coordinator_router_chain,
    "raw": RunnablePassthrough(),
} | delegation_branch | (lambda x: x["output"])

def main():
    """
    示例主函数：
    - 展示基于 LCEL 的路由协调器如何将不同意图请求路由到对应的处理器。
    - 依赖 DeepSeek 模型输出路由决策，最终只返回处理器产生的字符串结果。

    注意：
    - 输入结构为 {"request": 文本}；内部并行映射会将该原始输入保存在 raw 键。
    - 该重构仅提升可读性（如将并行键名更改为 raw、规范化匹配），不改变外部接口和逻辑。
    """
    if not llm:
        print("请先配置DeepSeek API密钥和基础URL。")
        return

    print("正在处理预订请求")
    request_a = "我想预订一个航班到纽约"
    response_a = coordinator_agent.invoke({"request": request_a})
    print(response_a)

    print("正在处理信息请求")
    request_b = "纽约的天气怎么样"
    response_b = coordinator_agent.invoke({"request": request_b})
    print(response_b)

    print("正在处理不清晰请求")
    request_c = "你好"
    response_c = coordinator_agent.invoke({"request": request_c})
    print(response_c)

if __name__ == "__main__":
    main()
