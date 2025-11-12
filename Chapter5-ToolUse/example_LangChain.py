import asyncio
import nest_asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from langchain.tools import tool

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

@tool
def search_information(query: str) -> str:
    """该工具提供关于特定主题的事实信息。你可以利用它来查找诸如“法国的首都是设么？”或伦敦的天气如何？”之类问题的答案。"""
    print(f"\n--- 🛠 Tool Called: search_information with query:'{query}' ---")
    simulated_results = {"weather in london": "The weather in London is currently cloudy with a temperature of 15°C.",
                        "capital of france": "The capital of France is Paris.",
                        "population of earth": "The estimated population of Earth is around 8 billion people.",
                        "tallest mountain": "Mount Everest is the tallest mountain above sea level.",
                        "default": f"Simulated search result for '{query}': No specific information found, but the topic seems interesting."
        }
    result = simulated_results.get(query.lower(), simulated_results["default"])
    print(f"--- TOOL RESULT: {result} ---")
    return result

tools = [search_information]

if llm:
    agent_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    agent = create_agent(llm, tools, system_prompt="You are a helpful assistant. Be concise and accurate.")
else:
    agent_executor = None

async def run_agent_with_tool(query: str):
    """Invokes the agent with new API contract and prints final AI message content."""
    print(f"\n--- 🏃 Running Agent with Query: '{query}' ---")
    try:
        response = await agent.ainvoke({
            "messages": [{"role": "user", "content": query}]
        })
        print("\n--- ✅ Final Agent Response ---")
        if isinstance(response, dict) and "messages" in response:
            messages = response.get("messages", [])
            final = messages[-1] if messages else None
            content = getattr(final, "content", None) if final is not None else None
            print(content if content is not None else str(response))
        else:
            print(str(response))
    except Exception as e:
        print(f"\n🛑 An error occurred during agent execution: {e}")

async def main():
    """Runs all agent queries concurrently."""
    tasks = [
        run_agent_with_tool("What is the capital of France?"),
        run_agent_with_tool("What's the weather like in London?"),
        run_agent_with_tool("Tell me something about dogs.") # Should trigger the default tool response
    ]
    await asyncio.gather(*tasks)

nest_asyncio.apply()
asyncio.run(main())
