# CrewAI 新手教程：关键组件、使用方法与最佳实践

> 适用对象：第一次接触 CrewAI 的开发者，或希望从“程序式（Python 代码）”与“配置式（YAML）”两种方式快速上手并构建可维护的多智能体工作流的团队。

## 目录

- 什么是 CrewAI
- 安装与环境准备
- 快速开始（程序式）
- 关键组件与概念
- 使用 YAML 进行配置化开发
- 项目结构与组织建议
- 运行、调试与日志
- 最佳实践
- 常见问题与排查
- 与本仓库示例代码的对照与改进建议

---

## 什么是 CrewAI

CrewAI 是一个用于编排多智能体（Agents）的 Python 框架，提供“智能体（Agent）—任务（Task）—编队（Crew）—流程（Process）”的核心抽象，帮助你将复杂的工作拆分为可协作的子任务，共同完成研究、写作、分析、自动化等工作。

官方快速开始提供基于 CLI 的工程脚手架方式，同时框架也支持直接在 Python 代码中以库的形式使用。

---

## 安装与环境准备

- 环境要求：`Python >= 3.10`
- 建议使用虚拟环境（`venv` 或 `conda`）隔离依赖

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -U pip
pip install crewai python-dotenv
```

密钥与模型配置建议通过环境变量管理（不在代码中硬编码）。创建 `.env`：

```bash
OPENAI_API_KEY="你的OpenAI密钥"
OPENROUTER_API_KEY="你的OpenRouter密钥"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
```

---

## 快速开始（程序式）

最小可运行示例（单智能体，顺序流程）：

```python
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv()

llm = LLM(
    model=os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
)

agent = Agent(
    role="技术写作专家",
    goal="根据主题制定写作要点并生成简洁摘要",
    backstory="经验丰富的内容策略师，强调结构化、可读性与信息密度",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

topic = "强化学习在人工智能领域的重要性"
task = Task(
    description=(
        f"1.为关于\"{topic}\"的摘要制定项目符号写作计划。\n"
        "2.根据计划撰写约200字摘要。"
    ),
    expected_output=(
        "最终报告应包含两个部分：\n\n"
        "### 写作计划\n"
        "- 以项目符号列表形式列出摘要主要内容。\n\n"
        "### 摘要\n"
        "- 写出结构清晰、内容简洁的摘要。"
    ),
    agent=agent
)

crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)

if __name__ == "__main__":
    result = crew.kickoff()
    print(result)
```

要点：

- 使用 `.env` 管理密钥与模型配置，避免硬编码。
- `Agent` 承担角色与目标，`Task` 描述输入与预期产出，`Crew` 编排整体流程。
- `Process.sequential` 指定顺序执行；复杂场景可扩展为层级或并行流程。

---

## 关键组件与概念

- `LLM`：封装具体模型与服务端点，用于为智能体提供语言能力。
- `Agent`：具备角色、目标、背景与工具的执行体，负责完成分配的任务。
- `Task`：一段明确的工作描述，含输入与期望输出，用于驱动 Agent 行动。
- `Crew`：由多个 Agent 与多个 Task 构成的编队，定义整体协作关系与执行流程。
- `Process`：流程控制。常见为顺序流程（`sequential`），也可拓展为层级或并行编排。
- `Tools`：Agent 可调用的外部能力，例如网页搜索、数据库查询、代码执行等。

设计建议：

- 每个 Task 只做一件清晰的事，产出可验证、可复用。
- Agent 的角色与目标应与 Task 的语言风格一致，避免冲突。
- `expected_output` 尽量结构化，便于后续程序消费与评估。

---

## 使用 YAML 进行配置化开发

很多团队偏好将 “Agent/Task 的声明” 与 “Python 运行逻辑” 分离。常见做法是使用 `agents.yaml` 与 `tasks.yaml` 并保持命名一致性，以便配置与代码自动关联。

示例 `agents.yaml`：

```yaml
email_summarizer:
  role: "Email Summarizer"
  goal: "Summarize emails into a concise and clear summary"
  backstory: "Create a 5-bullet summary of the report"
  llm: "provider/model-id"
```

示例 `tasks.yaml`：

```yaml
email_summarizer_task:
  description: "Summarize the email into a 5 bullet point summary"
  expected_output: "A 5 bullet point summary of the email"
  agent: "email_summarizer"
  context:
    - "reporting_task"
    - "research_task"
```

加载 YAML 的桥接代码（示例）：

```python
import os, yaml
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv()

llm = LLM(
    model=os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
)

with open("agents.yaml", "r", encoding="utf-8") as f:
    agents_cfg = yaml.safe_load(f)
with open("tasks.yaml", "r", encoding="utf-8") as f:
    tasks_cfg = yaml.safe_load(f)

agents = {}
for name, cfg in agents_cfg.items():
    agents[name] = Agent(
        role=cfg.get("role"),
        goal=cfg.get("goal"),
        backstory=cfg.get("backstory"),
        llm=llm,
        verbose=True
    )

tasks = []
for name, cfg in tasks_cfg.items():
    tasks.append(Task(
        description=cfg.get("description"),
        expected_output=cfg.get("expected_output"),
        agent=agents[cfg.get("agent")]
    ))

crew = Crew(agents=list(agents.values()), tasks=tasks, process=Process.sequential)
result = crew.kickoff()
print(result)
```

命名一致性非常关键：YAML 中 `agent` 字段应准确对应到代码中的 Agent 标识，否则任务无法正确关联。

---

## 项目结构与组织建议

推荐的最小结构：

```text
project/
  ├─ src/
  │   ├─ agents.py
  │   ├─ tasks.py
  │   └─ run.py
  ├─ configs/
  │   ├─ agents.yaml
  │   └─ tasks.yaml
  ├─ .env
  └─ pyproject.toml 或 requirements.txt
```

- 模块化拆分：将 Agent、Task 的定义与运行入口分开，便于维护与测试。
- 配置集中：把模型、阈值、提示词模板等放在配置，代码只做装配与控制。
- 明确边界：工具调用、外部 I/O 尽量通过接口抽象，降低耦合。

---

## 运行、调试与日志

- 调试时开启 `verbose=True`，便于观察每个步骤的输入输出。
- 使用 Python 标准库 `logging` 输出关键事件与错误信息，结合结构化日志定位问题。
- 对 `crew.kickoff()` 外层加异常捕获与重试策略，防止网络波动导致整体失败。

示例：

```python
import logging

logging.basicConfig(level=logging.INFO)

try:
    result = crew.kickoff()
    logging.info("Crew run completed")
    print(result)
except Exception as e:
    logging.exception("Crew run failed: %s", e)
```

---

## 最佳实践

- 安全与合规：密钥仅通过环境变量加载；避免提交到版本库。
- 结构化输出：`expected_output` 使用小标题、项目符号或 JSON，使结果可解析。
- 任务原子化：每个 Task 聚焦单一目标，便于组合与复用。
- 命名一致性：YAML 与代码中的 Agent/Task 名称保持一致，减少绑定错误。
- 资源策略：根据场景选择合适模型与温度，控制成本与延迟。
- 观测与重试：为关键步骤添加日志、超时与重试，提高稳定性。
- 可测试性：将组装逻辑封装为函数，便于编写单元测试与集成测试。

---

## 常见问题与排查

- 密钥未设置或无效：检查 `.env` 与环境变量，确认服务端点与模型名称正确。
- 命名不一致：YAML 中 `agent` 的值找不到对应 Agent，任务无法执行。
- 模型不可用：不同提供商的模型命名可能不同，需确认当前账户可用。
- 网络或速率限制：为远端调用设置重试与指数退避，避免瞬时失败。

---

## 与本仓库示例代码的对照与改进建议

- 路径 `Chapter6-Planning/example_CrewAI.py:8-12` 使用了硬编码的 `api_key`。建议改为从环境变量读取，避免敏感信息泄露。
- `Chapter6-Planning/example_CrewAI.py:15-24` 定义了中文 Agent；可补充更细的目标与结构化 `expected_output`，提升可重复性。
- `Chapter6-Planning/example_CrewAI.py:27-41` 的 Task 描述较清晰；可将主题与字数等参数外置到配置或命令行。
- `Chapter6-Planning/example_CrewAI.py:44-50` 使用 `Process.sequential`；如需多智能体协作，可扩展为更复杂流程并增加工具调用。

示例改进片段（环境变量读取）：

```python
llm = LLM(
    model=os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini"),
    base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
)
```

---

## 进一步学习与部署

- 官方快速开始文档提供完整的 CLI 工程化流程与示例。
- 生产部署可考虑使用官方提供的 AMP 平台与 CLI，简化上线流程。

---

## 结语

通过本文档，你可以选择“程序式”或“配置式”两种路径上手 CrewAI。在小型项目中，程序式更灵活；在团队协作与多环境部署中，配置式更规范。按“任务原子化、结构化输出、命名一致、环境变量管理”的四项原则落实到代码与配置，即可获得清晰、可维护、可扩展的多智能体工作流。