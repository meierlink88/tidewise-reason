# Vibe-Trading 与 OpenSPG + KAG 推理机制对比

> 研究日期：2026-08-18  
> 研究对象：[`HKUDS/Vibe-Trading`](https://github.com/HKUDS/Vibe-Trading)  
> 源码基线：commit [`4ad3b6b077b7ecf33744d1582064c109ca8234c0`](https://github.com/HKUDS/Vibe-Trading/tree/4ad3b6b077b7ecf33744d1582064c109ca8234c0) (2026-08-17)  
> 证据范围：仅使用项目自有 README、仓库源码和配置。该 commit 的仓库树中未找到项目论文或官方学术技术报告，因此机制判断以可执行代码为准。

## 一句话结论

Vibe-Trading 是一个“**LLM 作为调度器与策略代码生成器 + 金融工具/回测引擎作为计算器 + 证据门禁作为纠错器”的 agent 工程系统，不是基于领域本体、知识图谱和符号规则的推理引擎。

## 1. 总体架构

Vibe-Trading 的主路径可概括为：

```text
用户自然语言
  ↓
ContextBuilder：系统规则 + tool 描述 + skill 摘要 + 会话/记忆
  ↓
AgentLoop：LLM → tool calls → tool results → LLM ... → 最终文本
  ├─ 数据/研究工具
  ├─ skill 文档按需加载
  ├─ 策略代码生成 + 回测引擎
  ├─ 证据/标的身份门禁
  └─ 可选：Swarm DAG 多 agent 工作流
```

项目自身把通用流程归纳为 Plan → Ground → Execute → Validate → Deliver，其中 Execute 包括生成可测策略代码和调用回测/分析工具，Validate 包括指标、基准、Monte Carlo、Bootstrap、Walk-Forward 和 run card：[README L332-L342](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/README.md#L332-L342)。

### 核心不是 LangGraph 图执行

虽然依赖中安装了 `langgraph` 和 checkpoint 包：[`pyproject.toml` L24-L32](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/pyproject.toml#L24-L32)，但主 agent 的实际执行是 `AgentLoop.run()` 中的手写 `while iteration < max_iterations` ReAct 循环：[`loop.py` L692-L746](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/loop.py#L692-L746)、[`loop.py` L814-L900](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/loop.py#L814-L900)。因此，不应由依赖表推断它的主推理是 LangGraph state graph。

## 2. 主 Agent 的 LLM/工具编排

### 2.1 Context 决定“怎么想”

`ContextBuilder` 把以下内容组装成系统 prompt：

- 强制输出原则：每个数字必须来自当前会话工具调用，数据必须有 as-of，工具未返回的不允许用模型记忆补齐：[`context.py` L23-L64](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/context.py#L23-L64)。
- 工具摘要和 skill 摘要，完整工具 schema 通过 API `tools` 数组另行传给模型：[`context.py` L335-L352](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/context.py#L335-L352)。
- 基于任务类型的显式路由规则：回测必须先加载 `strategy-generate`，生成配置和代码，再回测、读指标、做归因/验证；Swarm 只在用户显式要求团队/委员会分析时调用：[`context.py` L78-L135](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/context.py#L78-L135)。

这意味着系统的高层“推理方法”很大一部分是 prompt policy + skill 文档，而不是编译成专用规则引擎的金融知识。

### 2.2 ReAct 循环

每轮的关键步骤是：

1. 估算上下文容量，依次微压缩工具结果、折叠长文本、必要时调 LLM 生成结构化摘要：[`loop.py` L917-L938](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/loop.py#L917-L938)。
2. 将当前 messages 和 tool definitions 传给 `stream_chat`；默认最多 50 轮，最后一轮不传工具定义，强制模型输出文本：[`loop.py` L702-L719](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/loop.py#L702-L719)、[`loop.py` L1000-L1013](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/loop.py#L1000-L1013)。
3. 如果 LLM 没有 tool call，将其文本候选答案交给 grounding ledger 校验；不合格则拒绝、追加纠错 prompt 并继续循环：[`loop.py` L1136-L1204](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/loop.py#L1136-L1204)。
4. 如果有 tool call，把 assistant tool-call message 和 tool result 回填到 messages，进入下一轮：[`loop.py` L1299-L1315](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/loop.py#L1299-L1315)。

工具调度有工程约束，但不是语义推理：成功调用过且不可重复的工具会被阻止；连续只读调用最多 8 线程并行，写工具串行：[`loop.py` L1458-L1475](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/loop.py#L1458-L1475)、[`loop.py` L1604-L1651](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/loop.py#L1604-L1651)、[`loop.py` L1690-L1708](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/loop.py#L1690-L1708)。

## 3. Swarm 多 Agent 推理

Swarm 是第二种编排模式：预设 YAML 定义 agent 角色、system prompt、工具白名单、skill 和任务依赖；`SwarmTask.depends_on` 形成 DAG：[`models.py` L169-L222](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/swarm/models.py#L169-L222)。

Runtime 按拓扑层执行：同层 task 线程并行，不同层串行，上游失败会阻塞下游，而不是让综合 agent 在缺少关键观点时仍然生成“结论”：[`runtime.py` L1-L4](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/swarm/runtime.py#L1-L4)、[`runtime.py` L294-L363](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/swarm/runtime.py#L294-L363)、[`runtime.py` L524-L556](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/swarm/runtime.py#L524-L556)。

每个 worker 并不调用主 `AgentLoop`，而是独立创建 `ChatLLM` 并运行轻量 ReAct for-loop；它的 prompt 包含角色、上游摘要、筛选后的 skills、预取的 grounding 数据与执行规则：[`worker.py` L1-L4](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/swarm/worker.py#L1-L4)、[`worker.py` L183-L304](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/swarm/worker.py#L183-L304)、[`worker.py` L375-L467](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/swarm/worker.py#L375-L467)。

`investment_committee` 预设是典型例子：多头和空头研究并行，风险官依赖两者，PM 再依赖风险审查做最终文本决策：[`investment_committee.yaml` L239-L261](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/swarm/presets/investment_committee.yaml#L239-L261)。这是“角色分工 + 上游文本综合”，不是多 agent 在共享知识图谱上做联合逻辑求解。

## 4. 数据与工具

当前 README 声明 23 个免费市场数据源（加可选 QVeris），`source="auto"` 依标的类型选择 loader，再按市场特定 fallback chain 尝试其他数据源：[README L346-L378](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/README.md#L346-L378)。除 OHLCV 外，README 列出 22 个只读基本面/资金流/公告/期权/筛选等数据工具：[README L408-L410](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/README.md#L408-L410)。

Agent 的能力分两层：

- **Tools** 是可执行函数/schema，负责拉数据、计算、读写文件、回测、跑 swarm 等。
- **Skills** 是按需加载的 Markdown 方法论与 API 契约；它们先以一行摘要进入 system prompt，完整文档由 LLM 通过 `load_skill` 拉取：[`context.py` L246-L279](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/context.py#L246-L279)。

数学计算正逐步从 skill 文档收敛到可测试的 `src/quantlib`，skill 调用实现而不是携带另一份公式，`quantlib_call` 用模块白名单和 `__all__` 调度：[README L585-L610](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/README.md#L585-L610)。这一层是普通程序数值计算，比 LLM 文本推理更可重现。

## 5. 记忆与状态

### 5.1 运行内状态

`WorkspaceMemory` 很轻：只保存本次 run 的 `run_dir` 和工具调用计数器，并将摘要注入 prompt：[`memory.py` L1-L4](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/memory.py#L1-L4)、[`memory.py` L13-L53](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/memory.py#L13-L53)。对话消息列表才是 ReAct 的主循环状态，长上下文通过多层压缩续命。

### 5.2 跨会话记忆

`PersistentMemory` 是 `~/.vibe-trading/memory` 下的 Markdown 文件存储，启动时读取 `MEMORY.md` 的最多 200 行快照：[`persistent.py` L1-L26](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/memory/persistent.py#L1-L26)、[`persistent.py` L200-L224](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/memory/persistent.py#L200-L224)。

每次用户查询最多自动召回 3 条相关记忆并放入 `<recalled-memories>`：[`context.py` L297-L332](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/context.py#L297-L332)。检索实现是可选 SQLite FTS5，失败时退化为标题/描述/关键词/正文的 token 重合打分，再可选扩展文件间的 semantic links：[`persistent.py` L362-L455](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/memory/persistent.py#L362-L455)。

因此，这里存在“检索后注入 LLM”的小型 RAG-like 行为，但默认核心是文件 + FTS/关键词检索，不是向量数据库、本体约束或图谱路径检索。

## 6. 策略生成、回测与交易决策

### 6.1 自然语言到策略代码

`strategy-generate` skill 规定了明确流程：解析标的/时间/逻辑 → 写 `config.json` → 生成 `code/signal_engine.py` → AST 语法检查 → 调用内建 backtest → 读取 metrics → 必要时修改后重跑：[`strategy-generate/SKILL.md` L7-L17](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/skills/strategy-generate/SKILL.md#L7-L17)。

LLM 生成的 `SignalEngine.generate(data_map)` 返回每个标的的 `pd.Series`，取值 `[-1, 1]` 表示空头至多头目标权重：[`strategy-generate/SKILL.md` L45-L70](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/skills/strategy-generate/SKILL.md#L45-L70)。所以“策略思考”的不确定性主要发生在 LLM 将用户语言翻译成 Python 规则的过程。

### 6.2 策略代码到回测结果

`backtest` tool 先验证配置、source 和策略文件，再在受控 runner 子进程中执行内建引擎：[`backtest_tool.py` L15-L74](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/tools/backtest_tool.py#L15-L74)。引擎顺序是：加载数据 → 调用生成的 `SignalEngine` → 对齐权重 → 逐 bar 执行 → 计算 equity/基准/指标 → 可选统计验证 → 输出 artifacts 和 run card：[`base.py` L652-L723](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/backtest/engines/base.py#L652-L723)、[`base.py` L726-L850](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/backtest/engines/base.py#L726-L850)。

为抑制 look-ahead，信号会按标的自身交易日历后移 1 bar，再 clip 到 `[-1,1]`，以 next-bar-open 语义执行：[`base.py` L153-L164](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/backtest/engines/base.py#L153-L164)、[`base.py` L211-L236](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/backtest/engines/base.py#L211-L236)。各引擎再施加手数、费用、T+1、涨跌停、保证金、资金费等市场规则；当前引擎覆盖见 [README L566-L580](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/README.md#L566-L580)。

Monte Carlo 和 Bootstrap 虽然使用随机数，但默认都固定 `seed=42`，配置也能显式覆盖：[`validation.py` L29-L73](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/backtest/validation.py#L29-L73)、[`validation.py` L136-L176](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/backtest/validation.py#L136-L176)。

### 6.3 “投资决策”不等于“自动下单”

Swarm 的 PM “final call”首先是文本综合结果。真实 broker 下单是另一个 connector/live 边界：README 明确说实盘受用户 mandate 的标的白名单、单笔/暴露上限、每日交易次数和 kill switch 限制，下单工具不通过 MCP 暴露，研究/回测路径与实盘端点结构隔离：[README L495-L513](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/README.md#L495-L513)。

直连 SDK 下单还必须经过 `sdk_order_gate`：无有效 mandate、mandate 过期、halt 开启、无法定价 notional 或超限均 fail closed，最终决策写入 audit：[`sdk_order_gate.py` L1-L21](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/live/sdk_order_gate.py#L1-L21)、[`sdk_order_gate.py` L88-L157](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/live/sdk_order_gate.py#L88-L157)。

## 7. 是否使用知识图谱 / RAG

### 知识图谱：没有发现作为核心推理存储

在该 commit 的机制代码、依赖和项目文档中，没有发现 Neo4j、OpenSPG、GraphRAG、三元组存储、本体 schema 或基于图路径的问答求解器。项目中出现的“图”主要是：

- Swarm 的任务依赖 DAG；
- 金融数据的相关网络/时序分析；
- 持久记忆文件间的可选 semantic links。

这些都不等价于“以领域知识图谱为事实底座的推理”。项目的事实底座是本次 run 的工具返回、数据文件和上游 agent 摘要。

### RAG：有广义的按需检索，没有统一的图谱/向量 RAG 管线

可算作广义 RAG-like 的部分包括：

- `load_skill` 按需取回方法论文档后注入对话；
- persistent memory 的 FTS/关键词召回；
- `read_url` / `read_document` / `web_search` / 市场数据工具在本次循环中取回外部上下文；
- Swarm 将上游 worker 的摘要作为下游 prompt context。

但这些由 LLM 选择工具并将结果塞回 messages，不是先统一建索引、再由固定 retriever 召回 chunks 的专用 RAG pipeline。

## 8. 可解释性与确定性边界

### 可解释的部分

- 每轮 LLM、tool call、tool result、最终答案均进入 `trace.jsonl`，大文本原子落盘到 sidecar，每条记录 flush + fsync：[`trace.py` L1-L8](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/trace.py#L1-L8)、[`trace.py` L64-L110](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/trace.py#L64-L110)、[`trace.py` L142-L179](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/trace.py#L142-L179)。
- 每次 run 记录 prompt hash、tool registry、package versions 和 skill 覆盖范围：[`loop.py` L757-L810](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/loop.py#L757-L810)。
- 回测 run card 记录 config hash、strategy hash、data sources、指标和 artifacts hash：[`run_card.py` L25-L94](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/backtest/run_card.py#L25-L94)。
- `GroundingLedger` 在 run 内锁定标的身份、授权市场工具调用，并校验最终答案的身份断言和价格数字：[`grounding.py` L811-L842](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/grounding.py#L811-L842)、[`grounding.py` L922-L1005](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/grounding.py#L922-L1005)、[`grounding.py` L1134-L1150](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/agent/grounding.py#L1134-L1150)。

这些提供的是**执行可追溯性**：能看到使用了什么 prompt/工具/数据/代码，数字是怎么算出来的。它不是形式逻辑证明，也不保证 LLM 的文本综合过程完备。

### 确定性分层

| 层 | 确定性 | 边界 |
|---|---|---|
| 回测/量化计算 | 较高 | 固定代码、配置、数据快照、版本和 seed 时可重放；引擎还有 next-bar shift 和市场规则。 |
| 数据获取 | 中 | `auto` fallback 可在不同时间由不同 loader 服务，市场数据本身也会修订；必须依赖 run card/原始 artifact 锁定当次输入。 |
| Agent 工具选择与策略生成 | 低到中 | 默认温度是 0.0，但模型/provider 差异、模型版本和 tool-call 生成仍不保证逐 token 重放；部分 provider 还会强制温度 1。 |
| Swarm 文本综合 | 低 | 并行 worker 返回的摘要、重试和下游综合都由 LLM 完成；DAG 只固定依赖顺序，不固定结论。 |

温度默认值见 [`env_schema.py` L137-L146](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/config/env_schema.py#L137-L146)；Kimi reasoning 模型需求时会被强制为 1.0：[`llm.py` L1391-L1404](https://github.com/HKUDS/Vibe-Trading/blob/4ad3b6b077b7ecf33744d1582064c109ca8234c0/agent/src/providers/llm.py#L1391-L1404)。

## 9. OpenSPG + KAG 的对应推理机制

本仓库运行的不是一个金融工具 Agent，而是 OpenSPG 知识图谱引擎与 KAG Solver。本机容器实际安装的 Python distribution 为 `openspg-kag 0.8.0.20250703.2020`，以下对比因此锁定 OpenSPG `v0.8` / KAG `v0.8.0`，不把后续分支能力混入结论。

### 9.1 知识构建在推理之前

KAG 将系统分为 `kg-builder` 和 `kg-solver`。Builder 对结构化数据执行 `mapping -> optional vectorizer -> writer`，对非结构化文本执行 `reader -> splitter -> extractor -> vectorizer -> optional post-processor -> writer`：[`default_chain.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/default_chain.py)。

它的关键是把长期事实放入 Schema 约束的领域图中：

- TBox 定义 EntityType、ConceptType、EventType、属性、关系、索引和规则；
- ABox 存放具体实体、事件和关系；
- 原始 Chunk 与图中知识互相索引，使图路径和文本证据可以共同进入求解。

KAG 官方将这定义为“Schema-Constraint 知识构建 + 知识与 Chunk 互索引”：[`README_cn.md` L196-L221](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md#L196-L221)。

### 9.2 自然语言问题转为混合求解计划

KAG 的 `KAGLFStaticPlanner` 把用户问题和可用 Executor schema 交给 LLM，生成 Task DAG；依赖上游输出的任务还会用 LLM 重写查询：[`lf_kag_static_planner.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/planner/lf_kag_static_planner.py)。

`KAGStaticPipeline` 按依赖分组并行执行任务，但这些节点是求解操作符，不是人格化角色：

- Retriever：图上精确/模糊检索、图到 Chunk 检索、向量 Chunk 检索；
- Math：数值计算；
- Deduce：entailment、judgement、extract、choice 等 LLM 语言推理；
- Output/Generator：汇总任务结果、图数据与 Chunk 引用生成答案。

调度代码见 [`kag_static_pipeline.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/pipeline/kag_static_pipeline.py)，引用组装见 [`llm_index_generator.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/generator/llm_index_generator.py)。官方的概括是将精确匹配、文本检索、数值计算和语义推理组合为图谱推理、逻辑计算、Chunk 检索和 LLM 推理：[`README_cn.md` L303-L309](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md#L303-L309)。

### 9.3 它也不是纯确定性证明器

OpenSPG 图查询和显式规则在固定图数据/规则下可以确定性执行，但 KAG 自然语言 QA 闭环仍在三处使用 LLM：计划、`KagDeduceExecutor` 语言推理和最终答案生成：[`kag_deduce_executor.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/executor/deduce/kag_deduce_executor.py)。所以它比 Vibe-Trading 多了可程序化的语义图和规则层，但不应被描述为“所有答案都是形式逻辑证明”。

## 10. 机制对比

| 维度 | Vibe-Trading | OpenSPG + KAG |
|---|---|---|
| 系统定位 | 面向金融研究、回测和交易工具的应用级 Agent | 领域知识建模、构建、检索与问答推理基础设施 |
| 主推理状态 | 对话 messages、tool calls/results、文件 artifact | Schema + 图事实 + Chunk + Solver Context |
| 规划 | LLM 每轮自主选工具，边做边观察 | LLM 先产生逻辑形式/Task DAG，再选专用 Executor |
| 多跳方式 | 多次 tool call 或角色 DAG 中的文本摘要传递 | 类型、属性、关系、图路径与逻辑形式约束的混合求解 |
| 长期知识 | Markdown memory + FTS5/关键词，以用户偏好和项目记忆为主 | 持久 TBox/ABox、图索引、文本 Chunk 及它们的互索引 |
| 专家知识 | Skill prompt、工具实现、回测/量化代码 | Schema、概念对齐、关系规则、抽取/映射契约 |
| 数值与时序 | 强：市场 loader、量化函数、多市场回测、统计验证 | 有 Math Executor，但不自带 Vibe 这类完整交易回测工具链 |
| 事实与因果链 | 主要依赖当次 API/文档结果与 LLM 综合；无统一领域图 | 擅长跨文档实体对齐、图关系、规则派生和多跳检索 |
| 证据机制 | trace/run card + 标的/价格数字 GroundingLedger | 图数据、任务过程、Chunk 引用与 reporter；不自带同等的交易价格门禁 |
| 确定性核心 | 工具、回测、统计 seed、证据/安全 gate | 图查询、显式规则、数值计算；计划/Deduce/最终表述仍受 LLM 影响 |
| 主要风险 | 工具选择、策略代码和投资观点可随模型/上下文变化 | 图中过期/错误事实、抽取/对齐错误会被多跳放大；LLM 规划也可偏离 |

最简洁的区分是：

> Vibe-Trading 推理“下一步调什么金融工具，如何把结果变成策略与报告”；OpenSPG + KAG 推理“这个领域问题需要查哪些实体/关系/文本，并如何沿图和规则组合答案”。

## 11. 对当前 Tidewise 仓库的判断

不建议用 Vibe-Trading 替代 OpenSPG + KAG，也不建议只靠 KAG 做全部金融研究工作流。两者更合理的位置是上下层互补：

```text
用户问题
  -> Tidewise 研究 Agent（可借鉴 Vibe 的 ReAct / skills / tools / evidence gates）
     -> OpenSPG + KAG：实体消歧、产业链/事件图、规则、多跳证据
     -> 市场数据/回测工具：价格、因子、组合、历史验证
     -> 证据门禁：标的、时点、数值、引用、事实/派生/假设分层
     -> 结论与可重放 artifact
```

但必须注意“产品潜力”与“当前状态”的差距：

- 仓库 [`README.md`](../../README.md) 明确记录：当前 Tidewise OpenSPG 项目仍是 pre-projection 默认 Schema，`schemas/Tidewise.schema` 只是未提交的人工审查候选，尚未导入 PostgreSQL ABox 事实；
- 候选 [`schemas/Tidewise.schema`](../../schemas/Tidewise.schema) 主要是实体类型和描述，还没有形成可用的事件—产业链—公司—证券关系、来源/时间/置信属性和可验证规则；
- 因此，“KAG 比 Vibe 更擅长产业链多跳推理”是完成建图后的能力判断，不是当前 Tidewise 已经达到的验收结果。

### 可直接借鉴 Vibe-Trading 的部分

1. **Agent 编排层**：用 ReAct 将 KAG QA、市场数据、回测、文档和报告工具组合起来。
2. **金融 skills 契约**：把研究步骤、数据要求和验证标准显式化，但公式和计算放在可测试代码中。
3. **GroundingLedger 思路**：在最终答案发布前机械检查标的、交易场所、as-of、币种、价格与引用；再扩展为 Tidewise 的事实/规则派生/LLM 假设分层。
4. **run manifest / run card**：固定 prompt、skill、工具、模型、Schema/rule 版本、数据快照和 artifact hash，才能真正复盘投研结论。
5. **有门禁的多 Agent DAG**：用于多头/空头/风险/主理人评审；上游失败必须阻断下游，不能在缺证据时仍输出投资结论。

### 不应直接照搬的部分

- 不要把 Swarm 自然语言摘要当成可验证的图事实；
- 不要把回测表现当成产业因果规则的证明；
- 不要将 LLM 自由生成的观点直接写入 OpenSPG ABox；
- 不要把 `GroundingLedger` 的价格数字一致性扩大解读为因果正确性。

## 12. 建议的小型对照试验

如果要决定观潮家的最终架构，建议不做抽象“哪个更聪明”评测，而是固定同一批事实快照和模型，测三类问题：

1. **纯产业链题**：某事件经哪些节点传导到哪些公司/证券；
2. **纯市场数值题**：某策略在指定时间段的收益、回撤、Sharpe 与稳健性；
3. **混合题**：先由产业事件产生候选标的/因果假设，再取时序数据做历史验证和风险反证。

每题记录证据覆盖率、无来源断言数、实体消歧错误、数值不一致、可重放性、延迟和 token 成本。预期不是某一方全胜，而是：KAG 在第 1 类领先，Vibe 式工具链在第 2 类领先，组合架构在第 3 类最有价值。

## 13. 最终结论

- Vibe-Trading 没有发明一种新的基础推理模型；它是成熟度较高的金融 ReAct 代理工程，把概率式 LLM 路由与确定性回测/统计/门禁组合起来。
- OpenSPG + KAG 的独特性在领域 Schema、持久图事实、图—Chunk 互索引、逻辑形式和可程序规则；自然语言问答部分仍是 LLM 与符号操作的混合系统。
- 对观潮家，最佳取舍是**保留 OpenSPG + KAG 作为产业语义与多跳证据底座，在其上构建 Vibe 式金融工具 Agent、回测和证据门禁**。
