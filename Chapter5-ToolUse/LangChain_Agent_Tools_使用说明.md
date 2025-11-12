# LangChain Agents 与 Tools 使用指南（最新版）

> 本文档系统性总结新版 LangChain Agents 与 Tools 的用法、注意事项与最佳实践，并结合当前仓库示例给出对齐方案与常见坑位修复建议。

**重要链接**
- Agents 文档: https://docs.langchain.com/oss/python/langchain/agents
- Tools 文档: https://docs.langchain.com/oss/python/langchain/tools

---

## 核心概念
- Agent 是“模型 + 工具”的智能体架构，遵循 ReAct（推理 + 行动）循环：模型思考 → 选择/并行调用工具 → 根据工具观察继续推理 → 直到输出最终答案或达到迭代上限。
- `create_agent` 提供生产可用的 Agent 实现，简化创建与运行（支持字符串模型标识或模型实例）。
- Tool 是可调用的动作封装（函数 + 输入模式），通过 `@tool` 装饰器即可把函数暴露为工具，Agent 在循环中按需调用。

## 快速开始

### 安装与依赖
- 需要 `langchain>=最新稳定版` 与相应模型 Provider 包（如 `langchain_openai`、`langchain_deepseek` 等）。
- Python 3.10+ 建议。

### 定义工具
```python
from langchain.tools import tool

@tool
def search_information(query: str) -> str:
    """提供关于特定主题的事实信息。明确工具用途与输入类型。"""
    # 这里写具体逻辑，如调用 Web/API/DB
    return f"Results for: {query}"
```
- 要点：
  - 必须使用类型注解（定义输入 schema）。
  - docstring 用于指导模型何时使用该工具与输入格式。
  - 可用 `@tool("custom_name", description="...")` 自定义名称和描述。

### 创建 Agent
```python
from langchain.agents import create_agent

# 传入字符串模型（或模型实例）
agent = create_agent(
    model="gpt-4o",            # 或者 ChatOpenAI/ChatDeepSeek 实例
    tools=[search_information],
    system_prompt="You are a helpful assistant."
)
```

### 运行与输入/输出约定
```python
# 标准输入：messages 数组（兼容多轮）
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "What is the capital of France?"}
    ]
})

# 标准输出：包含消息序列，从最后一条 AI 消息中取最终内容
final_msg = result["messages"][-1]
print(final_msg.content)
```
- 不再使用旧版 `{"input": "..."}` 与 `response["output"]`；新版统一使用 `messages` 结构。
- 支持流式：
```python
for step in agent.stream(
    {"messages": [{"role": "user", "content": "..."}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()
```

## Tools 进阶用法
- 自定义名称与描述：
```python
@tool("web_search", description="Search the web for information.")
def search(query: str) -> str:
    return f"Results for: {query}"
```
- 复杂输入：可用 Pydantic/JSON Schema 设计结构化入参（参见 Tools 文档）。
- ToolRuntime（高级）：
  - 工具可访问运行态信息：`state`、`context`、`store`、`stream writer`、`config`、`tool_call_id`。
  - 支持读写对话/自定义状态、持久化存储、流式输出等增强能力。
  - 可返回 `Command` 更新图状态（如清理历史消息或更新用户偏好）。

## 中间件（Middleware）
- `wrap_model_call`：按会话复杂度动态选择模型（成本/能力路由）。
```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    # 根据消息数量等策略切换模型
    request.model = (advanced_model if len(request.state["messages"]) > 10 else basic_model)
    return handler(request)
```
- `wrap_tool_call`：统一工具异常处理并返回结构化 `ToolMessage`，便于模型恢复与继续推理。

## 最佳实践
- 工具职责单一：每个工具只做一件事，便于模型正确选择与组合。
- 明确 docstring：告诉模型何时、如何调用工具、输入要求与输出格式。
- 输入输出稳定：保持函数签名与返回结构稳定，避免歧义。
- 控制随机性：推理与工具使用场景建议低温度（如 `temperature=0`），提升可重复性。
- 错误可恢复：给出“可理解”的错误消息与重试策略（中间件/工具内部校验）。
- 可观测性：使用 `agent.stream` 观察 ReAct 步骤与工具调用，利于调试与优化。
- 复杂编排：当需要更强可控性与持久化，建议迁移到 LangGraph（Agent 内部已基于它）。

## 常见坑位与修复
- KeyError: `'output'`
  - 新版 Agent 返回消息序列而非旧版 `output` 字段；应改为读取 `result["messages"][-1].content`。
- 旧版 API 混用：
  - `create_tool_calling_agent`/`AgentExecutor` 属于较旧接口；新版推荐 `create_agent` + 消息式输入输出。
  - `initialize_agent` 不再建议作为主路径；建议升级到 `create_agent`。
- 工具类型不匹配：
  - 传入必须是 `@tool` 生成的工具或兼容 `BaseTool`，避免直接传入普通函数列表。

## 安全与性能建议
- 输入校验：严格检查工具输入参数合法性，防注入、防越权、避免异常崩溃。
- 超时与重试：在模型/工具层面配置 `timeout` 与重试策略，提升鲁棒性。
- 日志与追踪：结合 LangSmith/可观测性工具记录关键步骤，定位性能瓶颈与错误来源。

## 代码示例（整合仓库用法）
```python
import asyncio
import nest_asyncio
from langchain.tools import tool
from langchain.agents import create_agent

# 1) 定义工具（职责单一 + 明确 docstring + 类型注解）
@tool("search_information", description="提供关于特定主题的事实信息。")
def search_information(query: str) -> str:
    """输入查询关键词，返回简要事实信息。"""
    return f"Results for: {query}"

# 2) 创建 Agent（字符串模型或模型实例）
agent = create_agent(
    model="gpt-4o",  # 或者替换为 ChatDeepSeek/ChatOpenAI 实例
    tools=[search_information],
    system_prompt="You are a helpful assistant. Be concise and accurate."
)

# 3) 异步调用：传入 messages，取最后一条 AI 消息内容
async def run_agent_with_tool(query: str):
    """传入用户消息，返回最终 AI 输出。"""
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": query}]
    })
    final_msg = result["messages"][-1]
    return final_msg.content

async def main():
    answers = await asyncio.gather(
        run_agent_with_tool("What is the capital of France?"),
        run_agent_with_tool("What's the weather like in London?"),
        run_agent_with_tool("Tell me something about dogs."),
    )
    for a in answers:
        print(a)

nest_asyncio.apply()
asyncio.run(main())
```

## 与本仓库示例的对齐
- 工具定义：`Chapter5-ToolUse/example_LangChain.py:21-35`
- Agent 创建：`Chapter5-ToolUse/example_LangChain.py:37-45`
- 结果解析（消息式）：`Chapter5-ToolUse/example_LangChain.py:49-57`

---

## 参考链接（再次列出）
- Agents 文档（新版入口）：https://docs.langchain.com/oss/python/langchain/agents
- Tools 文档（工具进阶与 ToolRuntime）：https://docs.langchain.com/oss/python/langchain/tools