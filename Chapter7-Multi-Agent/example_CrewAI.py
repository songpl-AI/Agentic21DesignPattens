
import os
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv

load_dotenv()

llm = LLM(
    model="openai/gpt-oss-20b:free",
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-v1-346c"
)

def main():
    # 定义Agent
    researcher = Agent(
        role="高级研究分析师",
        goal="发现并总结人工智能领域的最新发展趋势。",
        backstory="""你是一名经验丰富的研究专家，擅长识别关键趋势并整合相关信息。""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    writer = Agent(
        role="技术内容撰稿人",
        goal="根据研究结果撰写一篇通俗易懂的博客文章。",
        backstory="""你是一名专业的作家，擅长将复杂的信息以清晰、有吸引力的方式传达。""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


    # 定义任务

    research_task = Task(
        description="""研究2024-2025年人工智能领域的三大新兴趋势，重点关注其实际应用及潜在影响。""",
        expected_output="""一个详细的报告，包括每个趋势的定义、实际应用案例、潜在影响及未来发展方向。""",
        agent=researcher,
    )

    write_task = Task(
        description="""根据研究结果撰写一篇 500 字的博客文章。文章需通俗易懂，适合普通读者阅读。""",
        expected_output="""一篇专业、有吸引力的博客文章，长度在500左右。""",
        agent=writer,
        context=[research_task],
    )

    # 定义Crew
    blog_creation_crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        llm=llm,
        verbose=True,
    )

    # 运行Crew
    result = blog_creation_crew.kickoff()
    print(result)

if __name__ == "__main__":
    main()

