
import os
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv

load_dotenv()

llm = LLM(
    model="openai/gpt-oss-20b:free",
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-v1-"
)

# Agent
planner_writer_agent = Agent(
    role="文章策划和撰写专家",
    goal="根据指定主题指定详细的写作计划，并撰写出简洁、引人入胜的摘要。",
    backstory="""你是一名经验丰富的技术写作专家及内容策略师。你的优势在于能够在写作前制定出清晰、可执行的计划，
    从而确保最终生成的摘要既具有信息价值，又易于理解。
    """,
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

# Task
topic = "强化学习在人工智能领域的重要性"
high_level_task = Task(
    description=f"""
    1.为关于"{topic}"的摘要制定一份详细的写作计划，内容需以项目符号列表的形式呈现。
    2.根据指定的计划撰写摘要，字数控制在200字左右。
    """,
     expected_output=(  
        "最终报告应包含两个部分：\n\n"  
        "### 写作计划\n"  
        "- 以项目符号列表的形式列出摘要的主要内容。\n\n"  
        "### 摘要\n"  
        "- 写出一篇结构清晰、内容简洁的摘要。"  
    ),  
    agent=planner_writer_agent,
)


crew = Crew(
    agents=[planner_writer_agent],
    tasks=[high_level_task],
    process=Process.sequential,
)

result = crew.kickoff()
print(result)

