from ast import Nonlocal
import os
import asyncio
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableParallel, RunnableBranch

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

summarize_chain: Runnable = (
    ChatPromptTemplate.from_messages([
        ("system", "Summarize the following topic concisely:"),
        ("user", "{topic}")
    ])
    | llm
    | StrOutputParser()
)

question_chain: Runnable = (
    ChatPromptTemplate.from_messages([
        ("system", "Generate three interesting questions about the following topic:"),
        ("user", "{topic}")
    ])
    | llm
    | StrOutputParser()
)

term_chain: Runnable = (
    ChatPromptTemplate.from_messages([
        ("system", "Identify 5-10 key terms from the following topic, separated by commas:"),
        ("user", "{topic}")
    ])
    | llm
    | StrOutputParser()
)

# --- Build the Parallel + Synthesis Chain ---
# 1.定义需要并行执行的任务模块。这些任务的结果会与原始主题一起被传递到下一步处理
map_chain = RunnableParallel(
    {
        "summary": summarize_chain,
        "questions": question_chain,
        "key_terms": term_chain,
        "topic": RunnablePassthrough(),
    }
)

# 2.定义最终的合成提示语，用于将并行处理的结果整合在一起
synthesis_prompt = ChatPromptTemplate.from_messages([
    ("system", """Based on the following information:
                Summary: {summary}
                Related Questions: {questions}
                Key Terms: {key_terms}
                Synthesize a comprehensive answer."""),
    ("user", "Original topic: {topic}")
])

# 3.将并行处理和合成提示语连接起来
full_parallel_chain = map_chain | synthesis_prompt | llm | StrOutputParser()

# 运行并行处理链
async def run_parallel_example(topic: str) -> None:
    """
    Asynchronously invokes the parallel processing chain with a
    specific topic
    and prints the synthesized result.
    Args:
    topic: The input topic to be processed by the LangChain
    chains.
    """
    if not llm:
        print("Error: LLM is not initialized.")
        return
    
    print(f"Processing topic: {topic}")
    try:
        result = await full_parallel_chain.ainvoke({"topic": topic})
        print(f"Synthesized answer: {result}")
    except Exception as e:
        print(f"Error processing topic {topic}: {e}")

if __name__ == "__main__":
    test_topic = "The history of space exploration"
    asyncio.run(run_parallel_example(test_topic))
