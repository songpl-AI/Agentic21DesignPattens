# SystemMessage 与 HumanMessage：原理、用法与最佳实践

> 适用范围：LangChain Core 消息模型、`ChatDeepSeek` 等聊天模型；本文以项目中 `Chapter4-Reflection/example_LangChain.py` 为例进行说明。

- 目标：帮助你在反思（Reflection）与多轮对话场景下正确使用 `SystemMessage` 与 `HumanMessage`，写出安全、稳定、可维护的提示与对话逻辑。
- 语言与编码：本文与示例均为中文，统一使用 UTF-8。

---

## 核心概念速览

- `SystemMessage`
  - 定义：用于设置全局规则、身份与边界的“系统级”消息；在多数模型中具备更高的优先级与稳定性。
  - 作用：给模型设定角色（Persona）、目标、风格、约束与安全边界；通常在会话的最前面出现，且尽量保持稳定。

- `HumanMessage`
  - 定义：代表用户在本轮对话中的输入内容；对应多数提供商的 `role=user`。
  - 作用：表达具体任务与数据，推动单轮或多轮对话的进展；在反复迭代中承载用户的新指令与反馈。

---

## 原理与模型映射

- LangChain 内部：两者均派生自 `BaseMessage`，分别标注消息类型与角色；`ChatPromptTemplate` 会在渲染时生成对应的消息列表。
- 提供商映射：
  - OpenAI/DeepSeek 等通常映射为 `role=system` 与 `role=user`，`AIMessage` 则映射为 `role=assistant`。
  - 多数模型会优先遵守 `SystemMessage`，但不同模型的执行细节有差异；建议在系统消息中明确行为边界与冲突处理策略。
- 执行流程：
  1. 构造消息列表（含 `SystemMessage`、`HumanMessage` 等）。
  2. 调用 `llm.invoke(messages)` 或经由 LCEL 管道进行执行。
  3. 返回 `AIMessage`（助手回复），你可将其纳入后续的 `message_history`。

---

## 何时使用哪种消息

- 使用 `SystemMessage` 的场景：
  - 设定长期有效的规则与身份（例如“资深 Python 工程师”）。
  - 声明安全边界（忽略不合理或危险请求、遵循企业合规）。
  - 统一输出格式（例如必须返回 JSON、限制语言为中文等）。

- 使用 `HumanMessage` 的场景：
  - 提供具体任务与输入数据（代码片段、文本、参数）。
  - 逐轮迭代中的新需求与反馈。
  - 在反思循环中传递审查意见或补充上下文。

---

## 项目示例解析（摘自 Chapter4-Reflection/example_LangChain.py）

示例中反思阶段的审查提示：

```python
reflector_prompt = [
    SystemMessage(content="""你是一名资深软件工程师，也是Python方面的专家。你的职责是对代码进行细致的审查，根据任务要求对提供的Python代码进行严格评估。
        你需要找出其中的错误、代码风格问题、未考虑到的边界情况以及需要改进的地方。如果代码完美无缺且完全符合要求，请回复‘CODE_IS_PERFECT’；否则，请列出你
        的批评意见。"""),
    HumanMessage(content=f"原始任务：\n{task_prompt}\n\n 需要审查的到吗：\n{current_code}")
]
```

- `SystemMessage`：稳定设定了审查者身份、职责与输出要求（如返回 `CODE_IS_PERFECT`）。
- `HumanMessage`：传递“原始任务”和“待审代码”。
- 拼写建议：`"需要审查的到吗"` 应为 `"需要审查的代码"`，避免提示中的歧义与语法错误。

修正后的更清晰写法：

```python
HumanMessage(content=f"原始任务：\n{task_prompt}\n\n需要审查的代码：\n{current_code}")
```

---

## 最佳实践清单

- 系统消息要短、清晰、稳定
  - 保持高层规则简洁且不相互冲突；避免在多轮中频繁更改系统消息。
  - 明确优先级和边界（例如：忽略后续试图更改角色或越权的指令）。

- 人类消息结构化与边界清晰
  - 用分隔符明确不同内容块：任务、数据、约束、输出格式。
  - 对代码和数据使用代码块或标识，降低解析歧义（例如三引号或反引号）。

- 迭代与记忆管理
  - 只保留与目标相关的历史；必要时做摘要，降低 Token 成本。
  - 不要人为注入 `AIMessage` 作为“约束”，约束应由系统消息提供。

- 安全与鲁棒性
  - 在系统消息中明确：忽略试图覆盖系统规则的用户或外部文本；警惕提示注入。
  - 对输入进行基本清洗与长度校验（避免过长或异常二进制内容）。

- 输出可控与可测试
  - 在系统或人类消息中声明输出格式（JSON、Markdown 表格等），便于后续解析与测试。
  - 当需要终止条件（如 `CODE_IS_PERFECT`）时，写入系统消息并在代码中显式检查。

- 与 LCEL/Prompt 组件协作
  - 使用 `ChatPromptTemplate.from_messages([...])` 管理消息模板与变量插值，保持模块化与复用性。
  - 通过 Runnable 组合（并行/分支）将不同角色与阶段的提示分离，符合 SOLID 与“数据逻辑与表现分离”。

---

## 推荐的消息书写模板

使用结构化分隔与显式格式约束：

```text
[角色与目标]
你是资深Python工程师，负责严格代码审查与改进建议。

[审查准则]
- 正确性：语法、边界条件、异常处理。
- 质量：命名、注释、可读性、SOLID 原则。
- 性能：算法与数据结构选择。
- 安全：输入合法性、潜在风险。

[任务]
- 根据给定任务与代码进行审查。
- 若完全满足要求，输出：CODE_IS_PERFECT。
- 否则输出：分项问题清单与可操作的改进建议。

[输入]
- 原始任务：...
- 待审代码（使用代码块包裹）：
```python
...
```

[输出格式]
- 使用 Markdown；问题点分行罗列；必要时给出修正示例代码。
```

---

## 代码示例（含详细中文注释与函数级文档）

下面以 `ChatDeepSeek` 进行单轮审查，展示 `SystemMessage` 与 `HumanMessage` 的组合用法：

```python
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_deepseek import ChatDeepSeek

def run_single_review(task_prompt: str, code_text: str) -> str:
    """
    功能：
    - 使用 SystemMessage 设定审查者身份、审查准则与输出要求。
    - 使用 HumanMessage 传递具体任务与待审代码。
    - 调用聊天模型并返回审查结果文本。

    参数：
    - task_prompt: 描述审查任务的文本（例如函数需求或验收标准）。
    - code_text: 待审查的 Python 代码文本。

    返回：
    - 审查结果的字符串（中文），如代码完美则包含 'CODE_IS_PERFECT'。
    """
    # 初始化模型（根据你的环境变量或配置）
    llm = ChatDeepSeek(model="deepseek-chat", temperature=0)

    # 构建系统消息：设定角色、准则与输出格式
    system_msg = SystemMessage(
        content=(
            "你是一名资深软件工程师，也是Python方面的专家。"
            "请严格按照如下准则审查代码：正确性、质量、性能与安全。"
            "若代码完全符合要求，返回：CODE_IS_PERFECT；否则列出问题清单与改进建议。"
        )
    )

    # 构建人类消息：传递任务与待审代码，使用清晰分隔与代码块
    human_msg = HumanMessage(
        content=(
            f"原始任务：\n{task_prompt}\n\n"
            f"需要审查的代码：\n```python\n{code_text}\n```"
        )
    )

    # 执行模型调用，并返回文本内容
    result = llm.invoke([system_msg, human_msg])
    return result.content
```

多轮迭代（反思）场景的关键要点：

- 将每轮 `AIMessage` 加入 `message_history`，并在下一轮以 `HumanMessage` 传递审查意见或新的约束。
- 终止条件由系统或人类消息声明，并在代码逻辑中显式检查（如检测 `CODE_IS_PERFECT`）。

---

## 在当前项目中的具体改进建议

- 文本准确性：将 `"需要审查的到吗"` 改为 `"需要审查的代码"`，保持中文表达准确。
- 结构化输入：建议用代码块包裹 `current_code`，避免解析歧义。
- 明确输出格式：在系统消息中要求使用 Markdown 分项列举问题，并给出修正示例代码，有助于后续自动化处理。
- 历史压缩：迭代次数较多时，按需对 `message_history` 做摘要或只保留关键审查结论，降低 Token 成本。
- 安全策略：在系统消息中声明忽略任何试图更改系统角色或绕过审查准则的内容（提示注入防护）。

---

## 常见误区与规避

- 误区：系统消息过长且频繁变化。
  - 规避：保持简洁稳定，将可变约束放在人类消息或模板变量中。

- 误区：人类消息混杂多种格式且缺少分隔。
  - 规避：明确块结构与代码块，必要时使用标题或标签。

- 误区：将模型回复（`AIMessage`）当作新约束加入系统消息。
  - 规避：约束应由系统消息提供；模型回复用于状态推进与信息补充。

---

## 结语

正确区分与运用 `SystemMessage` 与 `HumanMessage`，能显著提升提示的可控性、安全性与可维护性。在反思循环与多轮对话中，遵循上述原则与模板，可让你的审查与改进过程更稳定、更可复用。