# Semantica 与 Graphiti：推理边界、成熟度及 Tidewise 适用性

> 调研日期：2026-08-26（Asia/Shanghai）
> Semantica 证据快照：`main` [`97f7154`](https://github.com/semantica-agi/semantica/commit/97f71542207a965d47a472a951267cf886e4c50e)，最新正式版 [`v0.6.6`](https://github.com/semantica-agi/semantica/releases/tag/v0.6.6)（tag commit `78fc902`，2026-08-20）
> Graphiti 证据快照：`main` [`993e081`](https://github.com/getzep/graphiti/commit/993e081a6d7948a0d8851c12a5fbdbeb49fed862)，最新正式版 [`v0.29.3`](https://github.com/getzep/graphiti/releases/tag/v0.29.3)（tag commit `021d3a5`，2026-07-27）
> 证据范围：两个项目的官方 README、文档、固定 commit 源码、测试、CI、release、issue，以及 Graphiti/Zep 作者论文；不采用第三方介绍。本文把可直接核验的内容标成“**事实**”，把基于这些事实的评价标成“**判断**”。

## 结论先行

**判断：它们不是同一层的直接替代品，但存在一部分基础设施重叠。**

- **Graphiti** 的核心是动态、双时态的 Context Graph / Agent Memory：把 Episode 变成 Entity/Fact，保存来源与有效期，处理后续信息带来的事实失效，再用 BM25、向量和图遍历检索上下文。它把上下文交给上层 Agent/LLM，不负责证明定理、执行领域规则或生成最终投研结论。[官方定位](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/README.md#L41-L54)、[官方文档](https://help.getzep.com/graphiti/getting-started/overview)、[论文的检索定义](https://arxiv.org/html/2501.13956v1#S3)
- **Semantica** 是覆盖 ingestion、KG、ontology、provenance、decision、rule reasoning、REST/MCP/UI 的宽平台。它确有基础前/后向链、正 Horn Datalog 和 Allen 区间运算，但其 Rete 与 SPARQL 能力仍明显未完成，所谓 LLM `GraphReasoner` 只是把整张调用方传入的图转成文本后进行一次模型调用。[官方能力表](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/README.md#L78-L109)、[Datalog 源码](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/datalog_reasoner.py#L242-L430)、[`GraphReasoner` 源码](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/graph_reasoner.py#L84-L162)
- 如果“推理”指 **确定性规则蕴含或递归传递闭包**，Semantica 是两者中唯一真正提供这类能力的项目；但当前只有基础 `Reasoner` 和 Datalog 可认真评估，不能把其全部宣传能力视作生产成熟。
- 如果“推理”指 **给 Agent 提供随时间演化、可追溯、可检索的事实上下文**，Graphiti 的专用实现、测试门禁和项目历史更成熟；但这仍是 memory/retrieval 成熟度，不是符号推理成熟度。
- 如果目标是 **端到端事件驱动投研推理**——从 Event 经产业链产生带方向、强度、期限、条件和反证的 Signal/Analysis Result——**两者都不是开箱即用的完整推理引擎**。Tidewise 仍需保留自己的 Analysis Context、领域规则/工具和上层 Agent 推理。

对本仓库的直接建议是：**继续使用已固定的 Graphiti `0.29.3` 作为受控时态图 provider，不用 Semantica 整体替换它。** 若近期确有确定性递归规则需求，只把 Semantica Datalog 当成隔离、只读的 PoC 候选；在证明语义、性能、证明链和维护门禁之前，不进入生产依赖。

## 一、概念上哪里相同，哪里不同

### 1.1 能力分层

| 层级 | Semantica | Graphiti | 比较结论 |
| --- | --- | --- | --- |
| 数据摄取与图构建 | 多来源 ingestion、抽取、冲突/去重、KG 构建 | Episode 摄取、实体/关系抽取、去重、事实失效 | **有明显重叠** |
| 时间事实 | 双时态事实、快照与 Allen 区间计算 | Fact 的 transaction time + world time、历史失效 | **有重叠，但语义与实现不同** |
| 检索 | 图/向量/RDF/LPG 多后端能力 | BM25、cosine、BFS 与多种 reranker | **有重叠；Graphiti 更聚焦 Agent memory** |
| 确定性规则推理 | 基础前/后向链、Datalog；Rete/SPARQL 尚不完整 | 没有通用规则语言或定理证明器 | **Semantica 独有** |
| 自然语言问题求解 | `GraphReasoner` 单次 LLM 调用 | 返回检索到的 nodes/edges/episodes/communities | **两者都不是完整 Planner/Solver** |
| 决策/因果记录 | 决策节点、显式因果边、路径与启发式评分 | Episode/Fact 来源与矛盾失效 | **语义不同，不应混称因果推理** |
| 最终业务结论 | 需要调用方规则或 LLM | 明确交给上层 Agent/LLM | **都不替代 Tidewise Reasoning 层** |

**事实：** Semantica 官方把自身描述为 LLM/向量库/Agent 框架之下的“deterministic infrastructure layer”，同时提供 Context Graph、决策、ontology、provenance、reasoning、存储和应用表面；其架构是从 Sources 一直到 REST/MCP/CLI 的端到端平台。[README 定位与能力](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/README.md#L59-L109)、[架构](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/README.md#L162-L180)

**事实：** Graphiti 官方把自身定义为“build and query temporal context graphs for AI agents”；其 OSS 能力边界是单个 Context Graph 的抽取、双时态模型、事实失效和混合检索。用户、thread、managed storage、治理、规模化性能与 SLA 属于 Zep，而 Zep 使用的规模化 Context Graph Engine 是 proprietary。[Graphiti README](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/README.md#L41-L122)、[官方 Overview](https://help.getzep.com/graphiti/getting-started/overview)

**判断：** 最准确的关系不是“Semantica vs Graphiti 谁是更强的推理引擎”，而是：

```text
Graphiti  ≈ 专用的时态事实记忆 / Context Graph 数据面
Semantica ≈ 宽覆盖的 KG + Context + 治理 + 轻量规则工具箱
Tidewise Reason ≈ 领域所有权、Analysis Context、规则/工具编排与最终结论层
```

Semantica 的图构建、时态事实、检索和 provenance 会与 Graphiti 重叠；它的 Datalog/基础规则引擎则位于 Graphiti 之上或旁边。因此二者既不是纯粹同类，也不是完全互补。

## 二、Semantica 的推理能力：哪些是真的，哪些还不成熟

### 2.1 基础前向链与后向链：真实但轻量

**事实：** `Reasoner` 将事实保存为进程内字符串集合，用固定 `IF ... AND ... THEN ...` 语法解析规则，通过正则变量匹配做前向链；默认最多 50 轮。后向链从目标递归证明前提，默认深度 10。`InferenceResult` 能记录本次规则、直接 premises 和规则置信度。[源码](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/reasoner.py#L57-L455)、[单元测试](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/tests/reasoning/test_reasoner.py)

**判断：** 这是一套可以执行简单领域规则的内存引擎，不是包含规则版本、持久化 materialization、增量 truth maintenance、并发隔离、分布式执行或完整证明图的生产 rule platform。它适合小规模确定性规则 PoC，不足以单独承担 Tidewise 的完整推理服务。

### 2.2 Datalog：当前最可信的 Semantica 多跳能力

**事实：** `DatalogReasoner` 使用进程内 `Set[DatalogFact]` 与 predicate index，解析正向 Horn clause，通过 semi-naive delta evaluation 反复求不动点；它支持递归关系、join、变量查询，也能一次性把 `ContextGraph` nodes/edges 转成事实。[数据结构与解析](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/datalog_reasoner.py#L18-L175)、[不动点与查询实现](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/datalog_reasoner.py#L242-L430)

**事实：** 官方测试覆盖了祖先递归、三跳可达、两个 body atom 的 join、变量绑定和 mock `ContextGraph` 导入；这些是小型正确性样例，不是生产规模 benchmark。[Datalog 测试](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/tests/reasoning/test_datalog_reasoner.py)

**事实：** 当前 parser 只构造正向 body atoms；公开 API 的 `derive_all()` 返回事实字符串，`query()` 返回绑定字典，没有返回每个派生事实的规则/前提 DAG。代码中也没有把 Datalog 执行下推至 Neo4j/RDF store 的路径；`load_from_graph()` 是把图内容复制进内存事实集合。[parser 与结果 API](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/datalog_reasoner.py#L129-L175)、[执行与导入 API](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/datalog_reasoner.py#L242-L430)

**判断：** 可把它准确描述为“有限 active domain 上的正 Horn、进程内递归闭包引擎”。不能把它描述为完整 Datalog 数据库、时态 Datalog、概率规则系统或具备完整 proof provenance 的生产推理平台。

对产业链推理而言，Datalog 可以计算：

```prolog
reachable(X, Y) :- direct_link(X, Y).
reachable(X, Z) :- direct_link(X, Y), reachable(Y, Z).
```

但它不会仅凭 `reachable(A, B)` 自动知道影响方向、强度、滞后、持续期、条件或反证；这些仍需 Tidewise 明确建模为事实与规则。

### 2.3 时态计算：确定性区间运算，不是未来预测

**事实：** `TemporalReasoningEngine` 是纯 Python、零 LLM 的 Allen interval algebra，实现 13 种区间关系，并提供 `active_at`、区间合并、gap、coverage、timeline 和双时态 revision coverage 等操作。[源码](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/kg/temporal_reasoning.py#L1-L207)、[测试](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/tests/kg/test_temporal_reasoning.py)

**判断：** 这能回答“两个已知区间是什么关系”“某事实在某时点是否有效”，但不能预测事件影响会持续多久。当前也没有看到把 Allen 运算直接嵌入 Datalog rule body 的统一时态逻辑执行器；应用需要自行编排两套 API。

### 2.4 Rete：当前不能按真实 Rete 引擎使用

**事实：** 官方 README 已提示 alpha matcher “intentionally simple”，不应直接用于 production compliance gate。[README 限制说明](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/README.md#L501-L539)

**事实：** 当前源码比这段措辞更明确：`AlphaNode._matches()` 对任何 Fact 都返回 `True`，`BetaNode._can_join()` 对任意左右 Fact 也返回 `True`；多条件 network construction 也没有形成可验证的完整 join propagation。官方开放 issue [`#300`](https://github.com/semantica-agi/semantica/issues/300) 同样把核心匹配称为 placeholder。[Rete 源码](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/rete_engine.py#L64-L104)

**判断：** “项目包含 `ReteEngine` 类”是事实；“项目已有高性能、可正确执行业务条件的 Rete engine”不是当前证据支持的结论。

### 2.5 SPARQL Reasoner：执行路径尚未实现，且文档漂移

**事实：** current main 的 `SPARQLReasoner.execute_query()` 无条件抛出 `NotImplementedError`，说明 triplet-store execution path 尚未实现；`_has_type()` 仍无条件返回 `True`，规则 expansion 只是拼接字符串。[执行路径](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/sparql_reasoner.py#L332-L353)、[规则转换和类型占位](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/sparql_reasoner.py#L155-L189)、[`_has_type`](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/sparql_reasoner.py#L292-L295)

**事实：** 同一 commit 的 reference 文档仍展示 `execute_query()` 可执行查询，并写着“不配置 triplet store 时返回空 bindings；配置后可查询 live backend”。这与源码 current behavior 冲突。[reference 文档](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/docs/reference/reasoning.md#L237-L280)；官方 issue [`#1083`](https://github.com/semantica-agi/semantica/issues/1083) 记录了旧实现静默返回空结果的问题。

**判断：** current main 改成 fail-loudly 比静默空结果更安全，但源码/文档不一致本身是成熟度风险。SPARQL store 能力与 `SPARQLReasoner` 也应分开看：项目有多种 RDF store connector，不代表这个 reasoning facade 已完成。

### 2.6 LLM GraphReasoner：一次性图上下文问答，不是 Agent Planner

**事实：** `GraphReasoner.reason()` 遍历调用方传入 dict 的全部 `entities` 和 `relationships`，格式化成文本，拼一个固定 prompt，然后调用一次 provider；没有内置子图检索、路径规划、工具循环、规则/数值算子选择或结构化结果校验。[源码](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/reasoning/graph_reasoner.py#L84-L162)

**判断：** 它更接近“Graph-to-prompt wrapper”，不能替代 Tidewise 的 Analysis Context assembly 或多阶段投资推理 Agent。图大时，调用方仍必须先做时间过滤、检索和边界裁剪。

### 2.7 “因果推理”的准确边界

**事实：** Semantica 可让调用方显式记录 `CAUSED`、`INFLUENCED`、`PRECEDENT_FOR` 边并遍历它们；没有显式边时，`trace_decision_causality()` 还会把“共享 entity 且时间更早”的 decision 作为 potential cause。[显式关系 API](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/context/context_graph.py#L3629-L3684)、[显式边与启发式遍历](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/semantica/context/context_graph.py#L4453-L4580)

**判断：** 这属于因果语义边记录、图遍历与启发式候选，不是从观察数据识别因果结构，也不是结构因果模型、`do()` 干预或反事实估计。对投研场景，应把它叫“已声明传导链/潜在线索”，不能叫“自动证明了因果”。

## 三、Graphiti 的“推理”边界

### 3.1 真正成熟的部分：时态图构建与上下文检索

**事实：** Graphiti 的 `EntityEdge` 同时保存 `created_at`、`expired_at`（系统/transaction time）和 `valid_at`、`invalid_at`（事实在现实世界的有效区间），并保留生成它的 Episode IDs 与 `reference_time`。[数据模型](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/graphiti_core/edges.py#L263-L282)

**事实：** `add_episode()` 执行 Episode 读取、entity/edge 抽取、resolution/deduplication、attribute/timestamp extraction、contradiction invalidation 和持久化；这是一个 LLM 辅助的动态图构建流水线。[入口与参数](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/graphiti_core/graphiti.py#L980-L1059)、[处理与写入](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/graphiti_core/graphiti.py#L1121-L1223)

**事实：** 所谓“automatic fact invalidation”的矛盾识别并不是符号规则证明：prompt 要求 LLM 返回 duplicate/contradiction indices，代码再按时间顺序设置 `invalid_at/expired_at`。[矛盾 prompt](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/graphiti_core/prompts/dedupe_edges.py#L43-L100)、[edge resolution 与 invalidation](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/graphiti_core/utils/maintenance/edge_operations.py#L623-L847)

**事实：** 基础 `search()` 返回相关 `EntityEdge`，高级 `search_()` 返回 nodes、edges、episodes 和 communities。搜索方法是 BM25、cosine、BFS；reranker 包括 RRF、MMR、node distance、episode mentions 和 cross encoder。[公开搜索 API](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/graphiti_core/graphiti.py#L1527-L1629)、[搜索配置](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/graphiti_core/search/search_config.py#L29-L129)

**判断：** Graphiti 可以可靠地为上层推理挑选“可能相关、带时间和来源的事实”，但 BFS 是候选扩展，不是返回可验证业务 proof 的逻辑执行器。它不会自动执行“若供应中断且库存低，则下游毛利在 30–90 天承压”这样的领域规则。

### 3.2 时间字段存在，不等于调用方自动得到正确 as-of 语义

**事实：** 默认 `SearchFilters()` 不自动施加“当前仍有效”的过滤；`valid_at`、`invalid_at`、`expired_at` 等时间条件需要调用方显式提供。[默认 filter 与字段](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/graphiti_core/search/search_filters.py#L55-L67)、[时间 filter 构造](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/graphiti_core/search/search_filters.py#L120-L273)

**判断：** Graphiti 具备保存时态语义的机制，但 point-in-time correctness 仍依赖 Reasoning Server 显式定义 `as_of`、horizon、乱序 Event、revision 和失效策略。当前仓库把 temporal filtering 留给 Analysis Context 是正确边界，而不是重复造轮子。

### 3.3 论文 benchmark 证明的是 memory-augmented QA，不是 Graphiti 独立逻辑推理

**事实：** Graphiti/Zep 作者论文把 memory retrieval 明确定义为 search → rerank → constructor，产出格式化 text context，供 LLM Agent 生成回答；实验也是先取 top facts/nodes，再由 GPT 模型生成答案。[检索定义](https://arxiv.org/html/2501.13956v1#S3)、[实验设置](https://arxiv.org/html/2501.13956v1#S4)

**事实：** 论文在 LongMemEval 的 `temporal-reasoning` 类别报告了端到端提升，也同时说明实验只覆盖 Graphiti 搜索能力的一部分；DMR 只有最多 60 条消息、主要是单轮事实检索，作者自己认为该 benchmark 不足。论文作者均来自 Zep，版本为 arXiv v1，并非独立第三方评测。[DMR 边界](https://arxiv.org/html/2501.13956v1#S4.SS2)、[LongMemEval 结果](https://arxiv.org/html/2501.13956v1#S4.SS3)、[作者与版本](https://arxiv.org/abs/2501.13956)

**判断：** 这些结果支持“Graphiti/Zep 检索出的时态记忆能帮助 LLM 回答时间问题”，不能支持“Graphiti 自身是成熟的符号/因果/投资推理引擎”。

## 四、项目成熟度：必须按各自本职工作比较

| 成熟度维度 | Semantica | Graphiti | 判断 |
| --- | --- | --- | --- |
| 产品范围 | 单仓库覆盖 ingestion、KG、ontology、reasoning、provenance、REST/MCP/UI，范围很广 | 聚焦 temporal context graph，另有 REST/MCP 示例 | Semantica 更完整但也更容易出现“表面已接通、内核未完成” |
| 规则推理 | 基础 Reasoner、Datalog 可执行；Rete/SPARQL 未完成 | 无通用规则引擎 | 规则蕴含只能选 Semantica，但成熟度仍偏早期 |
| 时态记忆 | 有双时态模型与区间工具 | Episode provenance、双时态 Fact、冲突失效、混合检索是一体化主路径 | Graphiti 更成熟、更聚焦 |
| LLM 问答 | 全图转文本的一次调用 | 只返回检索上下文，上层 LLM 回答 | 都不是完整 Agent reasoning runtime |
| 主 CI | 3 组 Explorer 前端测试 + package build；不运行 Python `pytest` | unit、Neo4j/FalkorDB integration、Ruff、Pyright、live REST/MCP workflows | Graphiti 的核心门禁明显更强 |
| 生产边界 | 广泛 connector 与 server surface；核心推理声明和实现仍不一致 | 官方明确 OSS core 需用户自建外围；规模化/治理/SLA 属于 proprietary Zep | 两者都不能把官方 demo service 原样当生产系统 |
| 版本状态 | `v0.6.6`，release 后 main 高速变化 | `v0.29.3`，仍是 pre-1.0 且 main 持续修复 | 都需要 pin + contract tests；版本号本身不是成熟度证明 |

### 4.1 测试与发布证据

**事实：** Semantica current main 的主 CI 只运行 `test:graph-store`、`test:graph-workspace`、`test:plugin-registry` 三组 Explorer 前端测试，然后安装 Python 依赖、构建 wheel、检查前端静态资源；没有执行 `pytest`。release workflow 同样直接构建和发布，不运行 Python tests。[主 CI](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/.github/workflows/ci.yml)、[release workflow](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/.github/workflows/release.yml)

**事实：** Semantica 仓库确有 reasoning tests，但没有覆盖 Rete 的真实条件匹配；specialized tests 对 current SPARQL behavior 只验证 `NotImplementedError`。[reasoning tests](https://github.com/semantica-agi/semantica/tree/97f71542207a965d47a472a951267cf886e4c50e/tests/reasoning)、[specialized tests](https://github.com/semantica-agi/semantica/blob/97f71542207a965d47a472a951267cf886e4c50e/tests/reasoning/test_specialized_reasoners.py#L33-L54)

**事实：** Graphiti current main 有独立 unit 与 Neo4j/FalkorDB database-integration jobs，还有 Ruff、Pyright、CodeQL，以及带真实 LLM secret 时运行的 live REST/MCP workflows。[unit 与 DB integration](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/.github/workflows/unit_tests.yml#L31-L115)、[lint](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/.github/workflows/lint.yml)、[typecheck](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/.github/workflows/typecheck.yml)、[live REST](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/.github/workflows/server-tests.yml)、[live MCP](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/.github/workflows/mcp-server-tests.yml)

**事实：** Graphiti 的常规 CI 仍显式排除 full integration、temporal integration 和 evals，并只在 DB job 启动 Neo4j/FalkorDB；Neptune/Kuzu provider parity 不在这条门禁中。[unit-test exclusions 与 DB matrix](https://github.com/getzep/graphiti/blob/993e081a6d7948a0d8851c12a5fbdbeb49fed862/.github/workflows/unit_tests.yml#L31-L115)

**判断：** Graphiti 作为“受控嵌入的 Python temporal-memory library”可评为 **中高成熟度**；它不是 turnkey production platform。Semantica 作为“宽 OSS 平台”活跃且模块很多，但其 reasoning subsystem 只能评为 **成熟度参差、整体偏早期**：Datalog/基础 Reasoner 是可用原型，Rete/SPARQL 不能进入生产判定路径。

### 4.2 活跃维护不等于接口稳定

**事实：** Semantica `v0.6.6` 是一轮涵盖 backup/restore、数据库导出、outbound request 和 triplet-store 的安全发布；Graphiti `v0.29.3` 也包含 Falkor routing、BFS direction、MCP restart 等多项修复。[Semantica v0.6.6](https://github.com/semantica-agi/semantica/releases/tag/v0.6.6)、[Graphiti v0.29.3](https://github.com/getzep/graphiti/releases/tag/v0.29.3)

**事实：** 截至本次快照，Graphiti 仍有用户报告的 historical backfill temporal-correctness gaps（[`#1489`](https://github.com/getzep/graphiti/issues/1489)）和 Episode 可能静默丢弃（[`#1707`](https://github.com/getzep/graphiti/issues/1707)）。这些是未关闭的上游报告，本调研没有独立复现，不能直接推断所有部署都受影响。

**判断：** 两个项目都在快速收敛。应把“持续修复”同时视为维护活跃的正面证据和行为仍会变化的风险证据；Tidewise 当前的精确 pin、可执行 contract checks 和外围幂等/审计不是多余复杂度。

## 五、对 Tidewise Reason 的适用性

### 5.1 现有架构已经给 Graphiti 放在了正确位置

**本仓库事实：** [ADR 0001](../adr/0001-use-graphiti-for-local-temporal-memory-evaluation.md) 明确把 Graphiti 定义为 temporal memory、extraction、retrieval provider，并指出 MCP search 不能保证完整产业链遍历；最终投资结论与 Analysis Context 属于 Reasoning 层。`CONTEXT.md` 也规定 Graphiti 不成为权威事实 owner，Analysis Result 不能静默提升为事实。[Reasoning Context](../../CONTEXT.md)

**本仓库事实：** [ADR 0002](../adr/0002-ingest-published-evidence-as-graphiti-episodes.md) 已发现 Graphiti monolithic `add_episode()` 会把未匹配候选保存成新 Entity，因此 Tidewise 改用受约束的 canonical resolution；[ADR 0005](../adr/0005-resolve-event-candidates-before-graphiti-projection.md) 又明确 Graphiti Episode similarity 不能替代 Event 业务身份判定。

**本仓库事实：** [ADR 0006](../adr/0006-retire-openspg-runtime-and-fix-reason-port.md) 已固定 Reasoning Server 与 Graphiti/Neo4j 的运行边界；[Local Graphiti Evaluation](../design/local-graphiti-evaluation.md) pin `graphiti-core==0.29.3` 与 Neo4j Community 5.26.28。这与上游截至本日的最新稳定版一致。

**判断：** 当前架构没有误把 Graphiti 当“最终推理引擎”。相反，它主动补上了 Graphiti 官方 OSS core 不负责的认证、canonical entity ownership、异步交付、幂等、temporal eligibility、完整链遍历和最终结果合同。上游审计强化了这些 ADR，而不是推翻它们。

### 5.2 为什么不建议用 Semantica 整体替换 Graphiti

1. **职责重叠而非能力补齐。** Semantica 的 ingestion、KG、ContextGraph、provenance、graph/vector stores 会复制当前 Graphiti + Reason 已有的 provider 与服务边界；真正新增的主要能力只是轻量规则/Datalog。
2. **会重新打开已关闭的所有权问题。** 若让 Semantica 自行抽取、去重和写图，就必须重新证明 Data 仍是 Entity/Event/Evidence authority，重新实现 canonical resolution、Event Candidate 判断与投影幂等。
3. **当前推理成熟度不足以抵消迁移成本。** Rete/SPARQL 不可用，GraphReasoner 太薄，Datalog 无持久化下推与完整 proof trace；用整个宽平台只为了一个进程内 Datalog 引擎不划算。
4. **时态能力没有形成单一推理闭环。** Allen interval、Datalog、ContextGraph 与 LLM GraphReasoner 是不同 API，仍需 Tidewise 自行组织 as-of、horizon、规则选择、证据链和结论。

### 5.3 Semantica 仍可能有价值的窄用法

**判断：** 如果要验证“确定性规则能否降低 LLM 在基础图计算上的不稳定性”，可做一个不改变 production architecture 的小 PoC：

1. 输入只使用 Reason 已组装的、provider-neutral `AnalysisContext` 只读快照，不让 Semantica 直接摄取 Evidence/Event，也不让它写权威图。
2. 只验证正 Horn 能表达的任务，例如：可达候选、显式 topology 上的传递关系、规则 eligibility、互斥/缺失前置条件检查。
3. 不把 `positive/negative`、强度、期限或因果方向从裸 topology 自动生成；这些必须有领域事实或可审核规则。
4. Tidewise 自己记录 `rule_id/version`、输入事实 IDs、每步 premises 和输出；不能依赖当前 Datalog 的字符串结果充当完整 proof trace。
5. 以 3/10/50 节点、环路、乱序 Event、revision、as-of、矛盾事实和重放为验收集，并把结果与当前 provider-neutral traversal 对照。
6. PoC 只证明“是否值得采用某个规则引擎 seam”，不自动证明要采用 Semantica 整个平台。

## 六、最终选择矩阵

| 真实问题 | 选择 |
| --- | --- |
| 需要持续摄取 Event/Episode、保存双时态事实、来源和历史失效 | **Graphiti 更成熟、更适合** |
| 需要 BM25 + vector + graph traversal 为 Agent 找上下文 | **Graphiti 更成熟、更适合** |
| 需要正 Horn 递归闭包、简单 IF/THEN 前后向链 | **Semantica 有能力，先做隔离 PoC** |
| 需要生产 Rete 或 SPARQL rule reasoning | **当前不要选 Semantica** |
| 需要自然语言问题自动规划、工具调用、多步求解 | **两者都不提供完整方案** |
| 需要结构因果识别、干预、反事实或投资影响预测 | **两者都不提供** |
| 需要 Tidewise 的 Event→Signal→产业链→Storyline→Analysis Result | **保留 Reasoning Server 领域层；Graphiti 只做 provider** |

一句话回答原问题：

> **Graphiti 在“时态 Agent memory / Context Graph”这件事上更成熟；Semantica 在概念上多了一层轻量符号规则能力，但其推理模块成熟度很不均衡。两者不是同类推理引擎，不能用一个总分比较；对 Tidewise 当前架构，Graphiti 应继续做时态事实与检索底座，Semantica 最多先作为只读 Datalog 实验件，而不是替代方案。**
