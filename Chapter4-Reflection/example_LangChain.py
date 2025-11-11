from ast import Nonlocal
import os
import asyncio
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableParallel, RunnableBranch
from langchain_core.messages import SystemMessage, HumanMessage

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

def run_reflection_loop():
    """
    这个示例展示了一个多步骤的人工智能反馈循环机制，通过该机制可以逐步优化Python函数的性能。
    """
    task_prompt = """
        你的任务是创建一个名字为‘calculate_factorial’的Python函数。
        这个函数需要完成以下功能：
        1.接收一个整数n作为输入。
        2.计算它的阶乘n!
        3.为该函数添加清晰的文档说明
        4.处理特殊情况：0的阶乘为1
        5.处理无效输入：如果输入的是负数，应排除ValueError异常
    """
    #--反思循环
    max_interations = 3
    current_code = ""
    message_history = [HumanMessage(content=task_prompt)]

    for i in range(max_interations):
        if i == 0:
            response = llm.invoke(message_history)
            current_code = response.content
        else:
            message_history.append(HumanMessage(content=f"请根据之前的反馈意见优化代码。"))
            response = llm.invoke(message_history)
            current_code = response.content
        print("\n--- 生成代码第{}轮 ---\n".format(i+1) + current_code)
        message_history.append(response)

        # 反思阶段
        reflector_prompt = [
            SystemMessage(content="""你是一名资深软件工程师，也是Python方面的专家。你的职责是对代码进行细致的审查，根据任务要求对提供的Python代码进行严格评估。
                你需要找出其中的错误、代码风格问题、未考虑到的边界情况以及需要改进的地方。如果代码完美无缺且完全符合要求，请回复‘CODE_IS_PERFECT’；否则，请列出你
                的批评意见。"""),
            HumanMessage(content=f"原始任务：\n{task_prompt}\n\n 需要审查的到吗：\n{current_code}")
        ]

        critique_response = llm.invoke(reflector_prompt)
        critique = critique_response.content

        # 结束条件
        if "CODE_IS_PERFECT" in critique:
            print("\n--- 代码完美无缺，结束循环 ---\n")
            break
        else:
            message_history.append(HumanMessage(content=f"对之前代码的审核意见：\n{critique}"))

        print("\n--- 经过审核后的代码 ---\n")
        print(current_code)


if __name__ == "__main__":
    run_reflection_loop()
