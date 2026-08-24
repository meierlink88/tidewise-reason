# 可与 Graphiti 组合的开源 AI Reasoning Harness

> 调研基线：2026-08-22  
> 数据范围：仅使用项目官方 GitHub 仓库、源码、发布页与官方文档。Star 是调研时 GitHub
> Repository API 快照，会继续变化。  
> 目标：寻找负责长任务规划、工具调用、状态流转和 LLM 推导的 Harness，而不是再找一个图数据库、
> GraphRAG 索引或知识图谱产品。

## 结论

**有。补充比较成熟度后，Tidewise 最值得先做 PoC 的是
[`agno-agi/agno`](https://github.com/agno-agi/agno)；
[`langchain-ai/deepagents`](https://github.com/langchain-ai/deepagents) 则是更偏 Codex 式长任务自主性的
challenger。**

Agno 在调研时有 **41,827 stars**，Apache-2.0 许可，最新发布为 `v2.9.0`；Deep Agents
有 **28,053 stars**，MIT 许可，最新发布为
[`deepagents==0.7.8`](https://github.com/langchain-ai/deepagents/releases/tag/deepagents%3D%3D0.7.8)
（2026-08-20）。两者主分支在调研日都仍持续提交。Deep Agents 官方明确把它定义为
“batteries-included agent harness”：提供子 Agent、上下文隔离、文件/沙箱、长期记忆、Skills、
自定义工具、MCP 和人工审批；执行状态、checkpoint、streaming 与 interrupt 则由下面的
LangGraph Runtime 承担。Star、许可和更新信息来自
[官方 Repository API](https://api.github.com/repos/langchain-ai/deepagents)，分层关系见
[官方架构说明](https://github.com/langchain-ai/deepagents/blob/main/openwiki/architecture/overview.md)。

两者属于同一个 Agent Harness 大类，但产品边界不同。Agno 是 Agent、Team、Workflow、持久化与
AgentOS 运行/控制平面组成的完整平台；Deep Agents 是构建在 LangGraph 上、专注长周期模型任务的
意见化 Harness。对 Tidewise 最合理的组合不是简单写成“某个 Harness 替代 KAG”，而是：

```text
用户分析命题
    ↓
Agno Workflow 或 LangGraph：确定性外层工作流、状态、retry、streaming
    ↓
Analysis Context Service：锚点、周期、ontology 片段、Evidence/Event/Signal、约束
    ↓
Graphiti：时态事实、关系、来源和按需扩展检索
    ↓
Agno Agent 或 Deep Agents + LLM：计划、调用工具、分解子任务、逐节点推导、综合结论
    ↓
确定性 Validator：时间、路径、Evidence ID、反证、输出 Schema 验证
```

这里 **Agno/Deep Agents 是 Harness，LangGraph 是 Deep Agents 的 Runtime，Graphiti 是时态
知识/记忆底座**。
三者不是同一层的竞品。它们仍然都不是业务规则引擎；“信号如何传导、哪些结论允许成立”仍应由
Tidewise 的领域规则、Analysis Context 合同和结果校验约束。

## 长任务自主性 challenger：Deep Agents + LangGraph

### Deep Agents 实际提供什么

Deep Agents 的官方 README 将其定位为可替换组件的完整 Agent Harness，内置或支持：

- 面向长任务的 Agent 工具循环和上下文管理；
- 同步/异步子 Agent，将大规模检索或节点分析隔离在独立上下文中；
- 自定义 Python tools，以及通过 LangChain MCP adapter 注入 MCP tools；
- Pydantic/JSON Schema 结构化子 Agent 输出；
- Skills、长期记忆、沙箱、权限与 human-in-the-loop；
- 把已编译的 LangGraph 当成子 Agent，从而在自由推理内部嵌入确定性流程。

依据：[Deep Agents 官方 README](https://github.com/langchain-ai/deepagents)、
[Subagents 文档](https://docs.langchain.com/oss/python/deepagents/subagents)、
[MCP 文档](https://docs.langchain.com/oss/python/langchain/mcp)、
[Backends 文档](https://docs.langchain.com/oss/python/deepagents/backends)。

需要特别纠正一个容易误判的点：**当前 Deep Agents 并不默认提供完整 Planner。**
官方 `0.7.0` changelog 显示，`TodoListMiddleware`、`write_todos`、todo state 和相应规划提示词
已经从默认 `create_deep_agent()` 中移除；需要显式加入 middleware，或由 Tidewise 实现自己的
领域 Planner。因此，Deep Agents 的“规划”本质上仍是 LLM 使用结构化任务工具维护计划，
不是 PDDL、Datalog 或因果规则求解器。依据：
[官方 changelog](https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/CHANGELOG.md)、
[TodoListMiddleware 源码](https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/todo.py)。

### LangGraph 实际提供什么

[`langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) 在调研时有 **40,204 stars**，
MIT 许可，2026-08-19 仍发布新版本；它不是开箱即用的领域 Harness，而是有状态图执行 Runtime。
节点和边可以由程序确定，也可以在受控节点中交给 LLM 决定下一步。

它对 Tidewise 的价值是：

- 每个 super-step 保存 checkpoint；
- 线程状态、历史、重放、分叉和崩溃后恢复；
- 节点级 retry policy、error handler 与失败 provenance；
- 流式事件和 token 输出；
- interrupt、人工审批、暂停与继续；
- 子图及不同持久化后端。

依据：[官方 Repository API](https://api.github.com/repos/langchain-ai/langgraph)、
[Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)、
[Fault tolerance](https://docs.langchain.com/oss/python/langgraph/fault-tolerance)、
[Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)。

因此推荐的实现方式是：外层产业链分析步骤由 LangGraph 固定，Deep Agents 只在“LLM 逐节点推导”
节点中拥有有限自主权。这样不会把“有没有查 Graphiti、有没有覆盖全部节点、有没有给 Evidence ID”
寄托在模型临场发挥上。

### Graphiti 的具体接入方式

Deep Agents 可以通过两种方式调用 Graphiti：

1. **首选：typed Python tool / HTTP client。** 把现有 Analysis Context Service 暴露成
   `build_analysis_context`、`expand_signal_paths`、`get_evidence` 等只读工具；工具返回受
   Pydantic/JSON Schema 约束的 DTO。
2. **兼容方式：MCP。** 将同一服务包装成 MCP tools，经 LangChain MCP adapter 注入。
   适合让多种 Agent 共用，但不应把原始 Neo4j/Cypher 直接暴露给模型。

基础 Analysis Context 应由 LangGraph 的强制步骤预先构建并写入运行状态，而不是等待 LLM 自己
决定是否调用检索工具。Deep Agents 的额外工具只负责按需扩展图路径。Graphiti 继续拥有
Evidence/Event/Signal 的时态与溯源事实；LangGraph checkpoint 只拥有某次分析的执行状态；
Deep Agents 自带 memory 只保存工作记忆或程序性说明，不能成为第二套领域事实库。

安全上还必须注意，Deep Agents 官方采用“trust the LLM”模型：Agent 可以执行其工具允许的任何
操作，真正边界必须放在 tool、backend 和 sandbox。对 Tidewise 应使用只读、限深、限量、带
tenant/analysis-run 身份的 Graphiti 工具，不依赖 prompt 禁止越权。依据：
[官方 README Security](https://github.com/langchain-ai/deepagents#security)、
[Permissions 文档](https://docs.langchain.com/oss/python/deepagents/permissions)。

## Deep Agents 与 Agno：同类，但不是同一种产品抽象

用户感觉 **Agno 更成熟是成立的**。两者都能承载“LLM + tools + memory/context + 多 Agent”的
推理循环，因而属于同一大类 Agent harness；但 Agno 是更完整的 Agent 平台，Deep Agents 则是
更专注于长任务上下文工程的 harness，并把耐久执行交给 LangGraph。两者都不是真正的领域规则
推理引擎，产业链因果、时间窗口、证据门槛和结论校验仍须 Tidewise 自己实现。

调研日的官方 GitHub Repository API 快照如下：

| 项目 | 项目年龄与版本信号 | Stars / 许可 / 最新发布 |
| --- | --- | --- |
| [Deep Agents](https://github.com/langchain-ai/deepagents) | 仓库创建于 2025-07-27；仍处 `0.x`，`0.7.0` 曾移除默认 Todo planner，API 与默认行为还在快速收敛 | **28,053**；MIT；[`0.7.8`](https://github.com/langchain-ai/deepagents/releases/tag/deepagents%3D%3D0.7.8)，2026-08-20 |
| [Agno](https://github.com/agno-agi/agno) | 仓库创建于 2022-05-04；已经历一次有迁移成本的 v1→v2 大版本，目前为 `2.9` | **41,827**；Apache-2.0；[`v2.9.0`](https://github.com/agno-agi/agno/releases/tag/v2.9.0)，2026-08-13 |

两仓在 2026-08-22 都有主分支提交，均非停更项目。Star 只能说明采用面与关注度；但项目年龄、
已发布 major 版本、完整运行产品和官方集成数量共同表明：**若“成熟”指一体化产品、部署面与功能
广度，Agno 明显胜出；若指 durable workflow 的语义和长任务上下文控制，不能只看 Agno 的总星数。**
Deep Agents 的 breaking/default 变化见
[官方 changelog](https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/CHANGELOG.md)，
Agno v2 的破坏性变化和迁移边界见
[官方 v2 migration guide](https://docs.agno.com/migration/v2)。

| 维度 | Deep Agents + LangGraph | Agno | 对 Tidewise 的意义 |
| --- | --- | --- | --- |
| 生产 Runtime | Harness 构建在 LangGraph 上；部署、观测与评测可配 LangSmith | 内置 AgentOS，把 Agent、Team、Workflow 暴露为生产 API，并提供 session、trace 和控制面 | Agno 的开箱生产面更完整；Deep Agents 的分层更清楚 |
| 持久化与恢复 | LangGraph checkpoint 保存图状态，支持 replay、fork、interrupt 后以 thread 恢复 | DB-backed session/workflow persistence，可继续会话与运行；AgentOS 统一托管 | 对“某个节点失败后精确恢复并审计状态演进”，LangGraph 语义更强；一般 Agent 会话 Agno 更省事 |
| Streaming / HITL | LangGraph 原生事件/token streaming 和 interrupt/resume；Deep Agents 有权限审批 | 原生 streaming；支持确认、补充输入和外部执行等 HITL 模式 | 两者都满足，Deep Agents 更适合把审批放在确定性图节点 |
| 规划/推理 | Subagents、Skills、文件系统、长上下文卸载；Planner 自 `0.7` 起需显式加 middleware 或自定义 | reasoning/tool loop、Agent/Team/Workflow 均已产品化 | Agno 更开箱；Deep Agents 更适合显式安装 Tidewise planner，不应误称内置规则推理 |
| 多 Agent | 子 Agent 默认隔离上下文，可给子 Agent 独立 tools、prompt、model 和结构化输出 | Team 是一等抽象，支持成员协作、委派与路由 | 大规模产业链节点并行分析，两者都能做；Deep Agents 的上下文隔离更贴合“受限 Analysis Context” |
| Context 管理 | filesystem/backend、Skills、长期 memory、subagent context isolation、summarization | knowledge、memory、session state、Team/Workflow context | Agno 功能更全；Deep Agents 更聚焦长任务的 context engineering |
| Tools / MCP | 自定义 tools，并通过 LangChain MCP adapter 接 MCP | 原生 tools/MCP 生态更完整，官方已有 Graphiti MCP 示例 | **Agno 接 Graphiti 的现成路径更短**；生产上仍应只暴露 Tidewise 只读 typed tools |
| 结构化输出 | Agent/子 Agent 支持 Pydantic/JSON Schema | Agent/Team 支持 `output_schema` 等 typed output | 两者都可接 Tidewise Validator |
| Evals / tracing | 主要借 LangSmith | Agno 自带 evals/observability 与 AgentOS 集成 | Agno 一体化更强；选择 Deep Agents 要接受 LangSmith 或自建观测依赖 |

能力依据：[Deep Agents README](https://github.com/langchain-ai/deepagents)、
[LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)、
[LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)、
[Agno 官方仓库](https://github.com/agno-agi/agno)、
[AgentOS 文档](https://docs.agno.com/agent-os)、
[Agno sessions](https://docs.agno.com/basics/sessions)、
[Agno HITL](https://docs.agno.com/hitl)、
[Agno teams](https://docs.agno.com/teams)、
[Agno MCP](https://docs.agno.com/tools/mcp)、
[Agno evals](https://docs.agno.com/evaluation)。

### 对 Tidewise 的选型修正

如果目标是最快得到一个带 API、session、Team、MCP、observability 的完整 Agent 产品，**Agno 应当
排在 Deep Agents 前面做 PoC**；尤其官方已有 Graphiti MCP 用例，集成风险更低。不过 Tidewise
不是通用聊天 Agent，而是“模型主导、范围受限、证据可追溯”的投研推理。基础 Analysis Context
必须被强制构建，节点覆盖、时间窗口、Evidence ID 与 Validator 也不能由模型自由决定。对此，
**LangGraph 固定外层状态机 + Deep Agents 只负责受限推理节点**仍有结构优势：durable checkpoint、
interrupt/replay 和上下文隔离边界更容易审计。

因此不应仅凭成熟度直接替换建议，而应并列验证：

1. `Agno AgentOS + Agent/Team + Tidewise typed Graphiti tools`：验证最快生产化路径；
2. `LangGraph + Deep Agents + 同一组 tools`：验证长任务恢复、上下文隔离和确定性约束；
3. 对两者使用完全相同的 frozen Analysis Context、DeepSeek 模型、输出 schema 和 Validator，比较
   结论质量、证据覆盖、token、恢复粒度和工程量。

当前建议修正为：**先用 Agno 完成第一轮 Graphiti 推理 PoC；Deep Agents + LangGraph 作为长任务
恢复与上下文隔离的 challenger。** 如果 Agno Workflow 无法满足精确恢复、replay/fork 或复杂子图
审计，再切换外层 Runtime；同一套 Graphiti 数据、Analysis Context 和 Validator 无需改变。

## 更低层方案：直接使用 LangGraph

如果 Tidewise 已经明确产业链分析步骤，而且不需要通用文件系统、自由子 Agent、Skills 和沙箱，
直接用 LangGraph 可能比 Deep Agents 更合适：

```text
Parse Question → Build Context → Analyze Nodes → Merge Conflicts
               → Validate Provenance → Repair/Reject → Publish Result
```

每个节点都可以是普通 Python、Graphiti adapter 或一次结构化 LLM 调用。这样依赖更少、行为更容易
审计，也最符合“LLM 负责语义推导，但业务范围和验收由系统控制”的思想。代价是 token 控制、
子任务委派、长上下文压缩和常用 Agent 中间件需要自行选择或实现。

所以 LangGraph 不是“另一个更强的推理模型”，而是最成熟的**确定性执行骨架**。若选 Deep Agents，
实际上仍然已经选择了 LangGraph。

## 第三选择：Microsoft Agent Framework

[`microsoft/agent-framework`](https://github.com/microsoft/agent-framework) 是 AutoGen 的活跃后继者，
调研时有 **13,029 stars**，MIT 许可，最新 Python 发布为
[`python-1.15.0`](https://github.com/microsoft/agent-framework/releases/tag/python-1.15.0)
（2026-08-21）。它支持 Python/.NET、function/MCP tools、middleware、graph workflow、streaming、
human-in-the-loop 和 workflow checkpoint。

它的 `ContextProvider` 尤其适合 Graphiti：Provider 可在每次 Agent 调用前主动注入相关上下文，
而 Graphiti tools 用于按需查询；这与“基础 Analysis Context 必须出现、额外路径由模型决定”非常
贴合。Workflow checkpoint 在每个 super-step 后保存 executor state、pending messages、requests
和 shared state。依据：
[官方 Repository API](https://api.github.com/repos/microsoft/agent-framework)、
[Context Providers](https://learn.microsoft.com/en-us/agent-framework/journey/adding-context-providers)、
[Workflow Checkpoints](https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints)、
[Tools](https://learn.microsoft.com/en-us/agent-framework/agents/tools/)。

它排在 Deep Agents/LangGraph 之后，主要因为当前 Graphiti Demo、Pydantic ontology 与 Python
代码已经形成，LangGraph 生态的适配成本更低；同时要单独验证 DeepSeek 的 OpenAI-compatible
endpoint、流式格式和 structured output 兼容性。若未来希望 Python/.NET 双栈和 Microsoft
运行治理，它是最值得保留的独立 challenger。

## Pydantic AI Harness：设计很匹配，但暂不算高成熟候选

应把两个 Star 数据分开：

- [`pydantic/pydantic-ai`](https://github.com/pydantic/pydantic-ai) 主仓：**19,436 stars**；
- [`pydantic/pydantic-ai-harness`](https://github.com/pydantic/pydantic-ai-harness) 独立 Harness：
  **800 stars**，最新 `v0.24.0`，仍是 `0.x`。

两者均为 MIT，调研日都保持活跃。官方 Harness 提供 planning、subagents、memory、context
management、Skills、执行环境和 step persistence；Pydantic AI 本体提供 typed dependencies、
typed tools、structured outputs、Pydantic Graph，以及 Temporal、DBOS、Prefect、Restate 等耐久
执行集成。依据：
[Harness 官方 README/文档](https://pydantic.dev/docs/ai/harness/)、
[Pydantic Graph](https://pydantic.dev/docs/ai/graph/graph/)、
[Durable Execution](https://pydantic.dev/docs/ai/capabilities/durable_execution/overview/)、
[Step Persistence](https://pydantic.dev/docs/ai/harness/step-persistence/)。

它与 Tidewise 的 Pydantic ontology、typed Analysis Context 和 DeepSeek Python adapter 非常契合，
但目前不能把 Pydantic AI 主仓的 19k stars 当成独立 Harness 的成熟度。官方也明确说明 Harness
的 StepPersistence 不是完整 graph-state checkpoint，并提示 `0.x` minor 版本可能发生 API 变化。
因此它适合做小型 challenger，不建议现在替换已经更成熟的 LangGraph durable runtime。

## 其他高星候选的适用性

| 项目 | 2026-08-22 stars / 许可 | 推理或规划机制 | 状态、恢复与扩展 | 对本场景的判断 |
| --- | --- | --- | --- | --- |
| [AutoGen](https://github.com/microsoft/autogen) | 60,565；代码 MIT | 多 Agent 消息与会话编排 | Memory/Tool 接口、Agent state | 官方已进入 maintenance mode，并要求新项目转 Microsoft Agent Framework，不应新选型。见[官方 README](https://github.com/microsoft/autogen/blob/main/README.md) |
| [CrewAI](https://github.com/crewAIInc/crewAI) | 57,440；MIT | 角色化 Crew 自主协作；Flow 提供确定性步骤 | Flow state、persistence/resume、tools、memory | 上手快，但 Crew 抽象和 Graphiti/领域 Pipeline 重叠，关键推理更依赖角色 prompt；不如 Deep Agents + LangGraph 易于冻结逐节点合同。见[官方概念](https://docs.crewai.com/core-concepts/Agents) |
| [LlamaIndex](https://github.com/run-llama/llama_index) | 51,791；MIT | Function/ReAct Agent；事件驱动 Workflow | Context store、tools、streaming、step retry | 数据/RAG 能力很强，但 Tidewise 已选 Graphiti 作数据底座，大量索引与检索抽象会重叠；Workflow 的耐久执行面不如 LangGraph 集中。见[Retry Policy](https://docs.llamaindex.ai/en/stable/api_reference/workflow/retry_policy/) |
| [Agno](https://github.com/agno-agi/agno) | 41,827；Apache-2.0 | ReasoningTools 的 Think → Act → Analyze；Agent/Team/Workflow | session state、DB persistence、streaming、tools | “reasoning”主要是 LLM scratchpad/tool loop，不是领域规则证明；内置 knowledge/memory 与 Graphiti 有重叠。见[Reasoning Tools](https://docs.agno.com/reasoning/reasoning-tools) |
| [DSPy](https://github.com/stanfordnlp/dspy) | 37,488；MIT | 声明式 LM modules、teleprompter/optimizer 编译 prompt 与示例 | 可扩展 retriever/tool；不拥有长任务 checkpoint runtime | 很适合后续优化“节点判断”prompt 和 evaluator，但它是 LM program optimizer，不是运行 Harness，应该作为附加层而非主编排器。见[官方仓库](https://github.com/stanfordnlp/dspy) |
| [smolagents](https://github.com/huggingface/smolagents) | 28,923；Apache-2.0 | ToolCallingAgent / CodeAgent 的精简 ReAct 循环 | tools、MCP、streaming；耐久状态较弱 | 适合轻量实验，不适合直接承担长周期分析的 checkpoint、恢复和审计。见[官方仓库](https://github.com/huggingface/smolagents) |
| [Mastra](https://github.com/mastra-ai/mastra) | 27,357；主代码 Apache-2.0，`ee/` 另有许可 | TypeScript Agents + Workflows | snapshot、suspend/resume、remaining retries、streaming | Runtime 能力不错，但当前 Tidewise/Graphiti 是 Python；跨语言服务化会增加边界，且需逐目录审查混合许可。见[Snapshots](https://mastra.ai/en/reference/workflows/snapshots)与[LICENSE](https://github.com/mastra-ai/mastra/blob/main/LICENSE.md) |
| [Haystack](https://github.com/deepset-ai/haystack) | 26,273；Apache-2.0 | Agent 工具循环 + Pipeline/Router/loop | state schema、streaming、tools/MCP、breakpoint snapshot | 比较适合检索和文档 Pipeline；作为通用耐久 Agent runtime 不如 LangGraph，Graphiti 接入仍需自定义 Tool。见[Agent](https://docs.haystack.deepset.ai/docs/agent) |

上述 Star、license、默认分支和更新时间均可由各项目官方 Repository API 复核；它们只反映关注度
与公开维护信号，不证明投研推理质量。

## Harness、Planner、规则引擎必须分开

| 层 | 负责什么 | 本次候选 |
| --- | --- | --- |
| Deterministic workflow runtime | 执行顺序、状态、checkpoint、retry、stream、resume、HITL | LangGraph、Microsoft Agent Framework Workflow |
| AI harness | 模型循环、tools、计划工具、Skills、subagents、上下文压缩 | Deep Agents、Pydantic AI Harness、CrewAI/Agno 等 |
| LLM planner/reasoner | 理解命题、选择工具、拆解任务、基于上下文形成推导 | DeepSeek 或其他模型，在 Harness 内运行 |
| Domain rule/validator | 时间窗口、传导约束、路径完整性、证据/反证和结论 Schema | Tidewise 自己实现；上述项目均不自动提供 |
| Temporal knowledge memory | Evidence/Event/Signal、实体关系、有效时间、来源与召回 | Graphiti |

Harness 可以让 LLM 更可靠地执行很多步骤，但不会把自然语言产业链逻辑自动变成可证明规则。
如果需要硬规则，例如“超过时间窗口的 Signal 不得进入结论”或“每个结论必须至少一个 Evidence ID”，
应实现为 LangGraph 的确定性节点或 Validator；如果是需要语义判断的软规则，则以版本化的领域规则
和 Analysis Context 交给 LLM，再由 Validator 验证输出是否满足可观察合同。

## 最终建议

1. **首选 PoC：Agno SDK + Workflow + 当前 Graphiti。** 使用官方 Graphiti MCP 或 typed
   Analysis Context tools；关闭与 Graphiti 重叠的 Agno Knowledge/Memory 事实能力。
2. **长任务 challenger：Deep Agents + LangGraph + 当前 Graphiti。** 验证自主规划、Skills、
   subagents、上下文压缩和 checkpoint 对复杂投研任务是否产生实质收益。
3. **保守生产路线：直接 LangGraph + 自定义 LLM 节点。** 当领域步骤已经明确时，先减少 Harness
   自主性；需要长上下文或子任务时再局部引入 Deep Agents。
4. **独立 challenger：Microsoft Agent Framework。** 验证 ContextProvider + Workflow + DeepSeek
   兼容性，作为不依赖 LangChain 栈的候选。
5. **观察项：Pydantic AI Harness。** 设计与 Tidewise 很贴合，但应等独立 Harness 脱离 `0.x`、
   完整 graph checkpoint 稳定后再评估替换。

当前最值得立即验证的最小案例，不是重新导入数据，而是把已经跑通的液冷产业链
`Analysis Context` 暴露成只读 typed tool，让 Agno Agent + ReasoningTools 对同一问题执行：制定节点
计划 → 按需扩展 Graphiti 路径 → 输出结构化判断 → Validator 对 Evidence、时间和路径进行验收。
第二轮再用 Deep Agents + LangGraph 跑同一输入，比较结论质量、可解释性、token、恢复粒度和开发
工作量。
