# LangChain Core Runnables（LCEL）详解与最佳实践

> 适用场景：需要用可组合的管道（pipe）方式构建和编排 LLM 应用，进行并行、路由、增量赋值、回退与重试等高级控制。

---

## 1. 概览

- LCEL（LangChain Expression Language）提供了声明式、可组合的“管道”语法，通过 `|` 把各个组件连接起来，形成可维护、可扩展的链式程序。
- `langchain_core.runnables` 中的各种 `Runnable` 是 LCEL 的核心抽象，统一了同步、异步、批量与流式执行接口。
- 常见类型：
  - `RunnablePassthrough`：原样传递输入；配合 `.assign(...)` 在输入字典上新增键。
  - `RunnableBranch`：根据条件进行动态路由，选择并执行第一个匹配的分支；支持默认兜底分支。
  - `RunnableLambda`：把任意 Python 函数包装为可管道的 runnable。
  - `RunnableParallel`：并行执行多个 runnable，聚合为一个字典输出。
- 关键方法：
  - `.invoke(input)`、`.ainvoke(input)`：同步/异步单次调用。
  - `.batch(list_of_inputs)`：批量调用；内部可并发。
  - `.stream(input)`：流式输出（对支持 streaming 的组件）。
  - `.assign(**new_fields)`：在当前输入字典基础上新增键（常与 `RunnablePassthrough` 配合）。
  - `.with_fallbacks([fallback_runnable, ...])`：主 runnable 失败时使用备用链。
  - `.with_retry(...)`：失败重试（例如网络抖动或偶发模型错误）。

---

## 2. 原理速览（管道运算符）

LCEL 利用 Python 的管道式组合：

- `a | b` 等价于 `a.__or__(b)`，表示把左侧输出作为右侧的输入。
- 每个 `Runnable` 都实现了可被管道连接的接口，使得我们可以用最少代码表达复杂的编排逻辑。

示例：自定义最小 Runnable（教学示例，帮助理解管道原理）

```python
# -*- coding: utf-8 -*-
class SimpleRunnable:
    """
    一个最小可运行体示例：
    - 用于演示 LCEL 背后的管道拼接原理。
    - 实际项目中请使用 langchain_core.runnables 提供的标准 Runnable 类型。
    """
    def __init__(self, func):
        # 存储处理函数
        self.func = func

    def __or__(self, other):
        # 管道拼接：返回一个新的 SimpleRunnable，其逻辑是先运行本函数，再把结果交给 other
        def chained(x):
            return other(self.func(x))
        return SimpleRunnable(chained)

    def invoke(self, x):
        # 同步调用接口
        return self.func(x)

# 使用：把输入加 5，再乘 2
add5 = SimpleRunnable(lambda x: x + 5)
mul2 = SimpleRunnable(lambda x: x * 2)
chain = add5 | mul2
print(chain.invoke(3))  # 输出 16
```

---

## 3. 常用 Runnable 类型详解

### 3.1 RunnablePassthrough

- 作用：
  - 原样传递输入，不进行修改；
  - 配合 `.assign(...)` 在“当前输入字典”上新增键，便于后续步骤使用。
- 典型用途：
  - 在并行映射中保留原始输入，以便后续组件既能拿到“决策结果”，又能读取“原始请求”。
  - 在不改变输入结构的情况下，为输入字典增添衍生字段（如 `output`、`features` 等）。
- 示例：

```python
# -*- coding: utf-8 -*-
from langchain_core.runnables import RunnablePassthrough

# 1) 原样透传输入
passthrough = RunnablePassthrough()
result = passthrough.invoke({"request": "用户的原始输入"})
# result == {"request": "用户的原始输入"}

# 2) 在输入字典上新增键（assign）
#    说明：assign 接受若干 key=lambda x: ... 的形式，返回一个在原输入基础上新增键的 runnable。
producer = RunnablePassthrough.assign(
    output=lambda x: f"已处理: {x['request']}"
)
result2 = producer.invoke({"request": "你好"})
# result2 == {"request": "你好", "output": "已处理: 你好"}
```

- 注意：
  - 命名清晰、避免键名冲突。若原始输入已包含键 `request`，并行映射中最好使用 `raw` 作为保留原输入的键名，避免出现 `x["request"]["request"]` 的双层访问混淆。

### 3.2 RunnableBranch

- 作用：根据一组“条件函数 → runnable 分支”的配对来路由，执行匹配到的第一个分支；若无匹配，则走默认分支。
- 使用方法：

```python
# -*- coding: utf-8 -*-
from langchain_core.runnables import RunnableBranch, RunnablePassthrough

# 分支定义：每个分支都在原输入字典基础上新增 output 字段
branches = {
    "booker": RunnablePassthrough.assign(output=lambda x: f"订票处理: {x['raw']['request']}"),
    "info": RunnablePassthrough.assign(output=lambda x: f"信息查询: {x['raw']['request']}"),
    "unclear": RunnablePassthrough.assign(output=lambda x: f"意图不明确: {x['raw']['request']}")
}

# 路由：根据 decision 选择分支；默认走 unclear
router = RunnableBranch(
    (lambda x: x["decision"].strip().lower() == "booker", branches["booker"]),
    (lambda x: x["decision"].strip().lower() == "info", branches["info"]),
    branches["unclear"],  # 默认/兜底
)

# 输入示例
inp = {"decision": "Booker", "raw": {"request": "帮我订票"}}
print(router.invoke(inp))
# 输出：{"decision": "Booker", "raw": {"request": "帮我订票"}, "output": "订票处理: 帮我订票"}
```

- 注意：
  - 条件匹配顺序很重要，应互斥或确定优先级。
  - 建议规范化类别值：`strip().lower()`，降低 LLM 输出格式差异造成的错误。
  - 默认分支必须存在，避免分类失败导致异常。

### 3.3 RunnableLambda

- 作用：把任意 Python 函数包装为 runnable，以参与管道。
- 限制：函数应接受单一参数；若需要多值输入，先在上游把多个值封装为一个字典。
- 示例：

```python
# -*- coding: utf-8 -*-
from langchain_core.runnables import RunnableLambda

# 把函数包装为 runnable
cleaner = RunnableLambda(lambda x: {**x, "request": x.get("request", "").strip()})
print(cleaner.invoke({"request": "  你好  "}))
# 输出：{"request": "你好"}
```

### 3.4 RunnableParallel

- 作用：并行执行多个 runnable，并把各自输出聚合为字典。
- 常见用法：把来自不同来源的上下文、保留的原始输入、以及模型产出的中间结果汇总到统一结构中，便于下游 prompt/handler 使用。
- 示例：

```python
# -*- coding: utf-8 -*-
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

retriever_a = lambda x: f"A检索结果: {x['query']}"
retriever_b = lambda x: f"B检索结果: {x['query']}"

parallel = RunnableParallel({
    "context_a": retriever_a,
    "context_b": retriever_b,
    "raw": RunnablePassthrough(),
})

print(parallel.invoke({"query": "篮球规则"}))
# 输出：{"context_a": "A检索结果: 篮球规则", "context_b": "B检索结果: 篮球规则", "raw": {"query": "篮球规则"}}
```

---

## 4. 与 Chapter2-Routing/example.py 对应的路由模式

在 `example.py` 中，采用了“并行保留输入 + 路由分支 + 结果提取”的经典结构：

```python
# -*- coding: utf-8 -*-
from langchain_core.runnables import RunnablePassthrough, RunnableBranch

# 说明：以下 handler 为示例函数，实际项目中可替换为你的业务逻辑。
def booking_handler(text: str) -> str:
    """
    订票处理器
    参数:
        text: 用户原始输入文本
    返回:
        订票相关响应字符串
    """
    return f"[BOOKING] 已处理: {text}"


def info_handler(text: str) -> str:
    """
    信息查询处理器
    参数:
        text: 用户原始输入文本
    返回:
        信息查询响应字符串
    """
    return f"[INFO] 已处理: {text}"


def unclear_handler(text: str) -> str:
    """
    不明确意图处理器（兜底）
    参数:
        text: 用户原始输入文本
    返回:
        引导或澄清响应
    """
    return f"[UNCLEAR] 无法识别意图，请补充说明: {text}"

# 假设：upstream 决策链产出 decision（如 "booker"/"info"/"unclear"）
def coordinator_router_chain(x: dict) -> str:
    """
    路由器链（示例版）
    说明:
        这里用简单规则模拟 LLM 决策：
        - 包含 "订" → booker
        - 包含 "查" → info
        - 其他 → unclear
    """
    text = x.get("request", "")
    if "订" in text:
        return "booker"
    if "查" in text:
        return "info"
    return "unclear"

# 为 RunnableBranch 定义分支：保留输入并新增 output
branches = {
    "booker": RunnablePassthrough.assign(output=lambda x: booking_handler(x["raw"]["request"])),
    "info": RunnablePassthrough.assign(output=lambda x: info_handler(x["raw"]["request"])),
    "unclear": RunnablePassthrough.assign(output=lambda x: unclear_handler(x["raw"]["request"]))
}

# 构建路由器：读取 decision，选择分支；默认走 unclear
delegation_branch = RunnableBranch(
    (lambda x: x["decision"].strip().lower() == "booker", branches["booker"]),
    (lambda x: x["decision"].strip().lower() == "info", branches["info"]),
    branches["unclear"],
)

# 最终协调器：并行得到决策 + 保留原始输入 → 路由分支 → 提取 output
coordinator_agent = {
    "decision": coordinator_router_chain,  # 产出路由决策
    "raw": RunnablePassthrough(),          # 原样保留原始输入（使用 raw 键避免混淆）
} | delegation_branch | (lambda x: x["output"])  # 仅返回分支计算出的 output

# 调用示例
print(coordinator_agent.invoke({"request": "帮我订一张票"}))
# 输出类似："[BOOKING] 已处理: 帮我订一张票"
```

与 `example.py` 的结构一致：
- 并行映射中既拿到 `decision`（来自路由器链），又保留原始输入（通过 `RunnablePassthrough()`）。
- `RunnableBranch` 使用 `decision` 决定具体分支，分支内部用 `.assign(output=...)` 增量构造结果。
- 末端用一个 `lambda` 把字典中的 `output` 提取为最终返回值。

---

## 5. 最佳实践清单

- 输入/输出结构
  - 保持输入结构稳定，分支 runnable 的输入形状须一致。
  - 并行映射中的键名要清晰，建议用 `raw` 代表“保留的原始输入”。
- 路由健壮性
  - 统一匹配规则：`strip().lower()`，避免大小写与空白差异。
  - 提供默认兜底分支，记录日志或输出友好提示。
- 错误处理
  - 必要字段缺失要有显式处理（如 `KeyError`），给出清晰错误信息。
  - 复杂链路中使用 `.with_fallbacks(...)` 与 `.with_retry(...)` 提升稳定性。
- 性能优化
  - 能并行就并行：用 `RunnableParallel` 聚合不同来源的上下文/结果。
  - 降低不必要的 LLM 调用，尽量把预处理/后处理放在 `RunnableLambda` 或 `.assign` 中。
  - 合理使用 `.batch(...)` 与异步 `.ainvoke(...)` 以提高吞吐。
- 可维护性（SOLID）
  - 单一职责：把 handler 逻辑拆分为小而清晰的函数。
  - 模块化：数据逻辑与表现分离，统一编码 UTF-8，中文注释到位。
  - 命名统一、结构清晰，便于团队协作与导航。

---

## 6. 常见陷阱与规避

- 键名冲突与双层访问：避免 `x["request"]["request"]` 的混淆，使用 `raw` 等更清晰的命名。
- 条件顺序与互斥：`RunnableBranch` 从上到下匹配第一个条件，需确保优先级正确。
- 多参数函数：`RunnableLambda` 只接受单参数，若需多值请封装成一个字典或上游 `.assign(...)` 聚合。
- 缺少默认分支：路由失败会抛错，请务必提供兜底。
- 过度耦合：把路由逻辑与业务处理器解耦，便于扩展与测试。
- 流式与内存：长流式输出时注意内存与资源管理，必要时分块处理。

---

## 7. 速查代码片段

- Passthrough + assign：

```python
RunnablePassthrough.assign(output=lambda x: some_handler(x["raw"]["request"]))
```

- 并行聚合：

```python
RunnableParallel({"a": chain_a, "b": chain_b, "raw": RunnablePassthrough()})
```

- 动态路由：

```python
RunnableBranch(
    (lambda x: x["decision"].strip().lower() == "type_a", runnable_a),
    (lambda x: x["decision"].strip().lower() == "type_b", runnable_b),
    default_runnable,
)
```

- 包装自定义函数：

```python
RunnableLambda(lambda x: {**x, "normalized": normalize(x)})
```

- 回退与重试：

```python
main = prompt | llm | parser
safe = main.with_fallbacks([parser])  # 失败时仅返回解析后的安全结果
robust = safe.with_retry(stop_after_attempt=3)  # 最多重试 3 次
```

---

## 8. 结语

- `langchain_core.runnables` 为构建生产级 LLM 应用提供了统一、强大的编排抽象。掌握 `RunnablePassthrough`、`RunnableBranch`、`RunnableLambda` 与 `RunnableParallel`，即可覆盖大部分实际需求。
- 结合本文的示例与最佳实践，保持清晰的数据结构、健壮的路由与合理的并行/重试策略，可以显著提升系统的可维护性与稳定性。

---
