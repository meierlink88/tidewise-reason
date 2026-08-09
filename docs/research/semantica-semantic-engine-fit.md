# Semantica 作为中国股市事件驱动投研语义引擎的适配性核查

核查时间：2026-08-09  
核查范围：Semantica 官方 `concepts`、`modules` 及与结论直接相关的官方指南和当前 `main` 源码。源码基准提交：[`7dce9f1`](https://github.com/semantica-agi/semantica/commit/7dce9f1b69d83d0a077d3a785532af0d69b00018)。

## 结论

**Semantica 可以成为 Tidewise 语义引擎的“通用知识与推理内核”，但不能直接充当完整的中国股市事件驱动投研语义引擎。**

它开箱提供的是一组可组合的语义基础设施模块：数据接入与抽取、知识图谱、向量检索、GraphRAG、Ontology/SHACL、规则推理、时间图、溯源、决策记录。官方对自身的核心定位也是现有 AI 栈之上的 **context and accountability layer**，而不是 Agent 框架、金融领域模型或投资结论生成器（[Core Concepts](https://docs.getsemantica.ai/concepts/)）。

因此，合理的产品边界是：

- **Semantica**：承载事实、关系、向量记忆、图查询、规则执行、时间与溯源等通用能力。
- **Tidewise Semantic Runtime / 领域层**：定义中国股市统一语言，编排事件进入图谱和向量库，触发规则，计算时效与影响，提供稳定查询接口。
- **投研 Agent**：读取证据和规则派生信号，结合行情、估值、预期差和反证，形成短期/长期多空结论并记录决策。

换句话说：**可以沿“语义引擎”方向继续，但语义引擎不能简单等同于 Semantica。Tidewise 语义引擎应当是“Semantica 内核 + 中国股市领域模型 + 事件编排 + 信号/时域模型 + 查询契约”。**

## Semantica 到底是什么

官方把 27 个模块划分为六层：输入、核心处理、存储、质量保证、Context/Memory、输出与编排。模块彼此独立，需要调用方选择和组装，而不是一个自动运行的端到端产品（[Modules](https://docs.getsemantica.ai/modules/)）。

它最擅长完成下面的工作链：

```text
文档/网页/数据库/流
  → 解析、切分、标准化
  → 实体/关系/事件/三元组抽取
  → Knowledge Graph + Vector Store
  → GraphRAG / 图查询 / 语义搜索
  → 规则推理、时间查询、溯源、决策记录
```

这条链条说明 Semantica 更像“语义能力 SDK/工具箱”，不是一个已经理解中国上市公司、板块、政策冲击和价格预期的金融知识服务。

## 与目标能力逐项对照

| 目标能力 | Semantica 开箱能力 | 仍需 Tidewise 实现 | 判断 |
|---|---|---|---|
| 图谱 + 向量知识库 | `kg`/`graph_store`、`vector_store`、`AgentContext` 混合检索和 GraphRAG | 跨库 ID、写入一致性、数据生命周期、生产配置、金融实体映射 | **适合做内核** |
| 统一语言和领域知识 | OWL/RDF、SKOS、SHACL、alignment、namespace、seed、实体归一化 | A 股 Ontology、证券代码主键、别名和板块映射、抽取结果对齐、规则词汇表 | **有工具，没有领域内容和自动闭环** |
| 标准化查询能力 | 图数据库统一 CRUD、Cypher/OpenCypher；RDF/SPARQL；向量搜索；`AgentContext.retrieve()`；MCP 工具 | 面向投研的稳定语义查询 API/Tool，例如事件影响、产业链暴露、证据链和时间窗查询 | **底层接口有，领域查询层没有** |
| 固定推理规则 | Forward chaining、Rete、Datalog、SPARQL、Temporal、可解释 `InferenceResult` | 规则库、图事实到规则事实的适配、规则版本、触发、派生事实回写、数值评分和冲突处理 | **引擎有，规则与编排没有** |
| 事件驱动 | `StreamIngestor` 支持 Kafka/RabbitMQ/Kinesis/Pulsar；`EventDetector` 可提取事件 | 消息 handler、中文金融事件 schema、去重、对齐、入库、推理触发、失败恢复和告警 | **接入和检测有，事件驱动业务闭环没有** |
| 短期/长期多空结论 | 时间图、图关系、向量证据、规则派生、决策记录可支撑结论 | 行情/估值/预期差、事件衰减、市场状态、公司暴露度、反证、置信度、回测和结论 Agent | **不提供结论模型** |

## 1. 图谱 + 向量知识库

### 开箱即用

- 知识图谱保存结构化事实、关系、属性，并支持路径、中心性、社区、时间快照等能力（[Core Concepts — KG vs Vector Store](https://docs.getsemantica.ai/concepts/#knowledge-graph-vs-vector-store)）。
- 向量库支持 FAISS、Qdrant、Weaviate、Milvus、Pinecone、PgVector、内存等后端；当前源码定义了统一 `SearchResult`，包含 `id`、归一化 `score`、`metadata` 等字段（[`vector_store.py#L81-L112`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/vector_store/vector_store.py#L81-L112)）。
- `GraphStore` 封装多种图后端的 CRUD、邻居、最短路径和查询；查询本质上仍是 Cypher/OpenCypher（[`graph_store.py#L239-L280`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/graph_store/graph_store.py#L239-L280)、[`#L717-L779`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/graph_store/graph_store.py#L717-L779)）。
- `AgentContext.retrieve()` 在有 Knowledge Graph 时走 GraphRAG，否则走向量/Memory 检索（[`agent_context.py#L499-L566`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/context/agent_context.py#L499-L566)）。

### 不是开箱即用

Semantica 没有替我们定义以下一致性规则：

- 同一新闻 chunk 的向量记录如何关联到 `Event`、`Company`、`Stock` 图节点；
- Neo4j 写成功而 Qdrant 写失败时如何补偿；
- 重复新闻、修订公告、撤回公告如何更新；
- 一个事实的 `event_time`、`published_at`、`ingested_at` 和有效期如何统一；
- 事实、推断和 Agent 结论如何使用不同节点/边类型隔离。

所以它提供的是图和向量两类后端及混合检索组件，不是已经完成一致性治理的“双库知识服务”。

## 2. 统一语言与 Ontology

### 开箱即用

Semantica 的 Ontology 模块能管理 classes、properties、namespace、SKOS vocabulary、alignments、OWL/RDF 导入导出，并由 Ontology 生成 SHACL shapes。官方定义 Ontology 是“哪些类型存在、哪些关系有效、有哪些约束”的 schema（[Core Concepts — Ontology](https://docs.getsemantica.ai/concepts/#ontology)）。

这足以承载一套中国股市统一语言，例如：

```text
Company / ListedSecurity / Sector / Theme / Event / Policy / Commodity
belongs_to_sector / supplies / competes_with / benefits_from / harmed_by
event_time / publication_time / confidence / source / valid_from / valid_until
```

### 关键边界：Ontology 不会自动贯穿抽取、检索和推理

- `AgentContext` 构造器的核心输入是 `vector_store`、`knowledge_graph` 及检索参数，没有正式的 `ontology` 参数（[`agent_context.py#L124-L170`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/context/agent_context.py#L124-L170)）。
- `ContextRetriever` 的 docstring 写着 “Ontology-aware context retrieval”，但当前初始化和检索实现只读取 memory、knowledge graph、vector store 和 graph expansion 参数，源码中没有实际读取 Ontology 对象（[`context_retriever.py#L113-L150`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/context/context_retriever.py#L113-L150)）。
- SHACL 校验必须显式调用 `validate_graph()`；它返回合规报告和 violations，并不会自动修复或阻止写入，是否阻断、隔离、修复或人工复核由调用方决定（[`ontology/engine.py#L297-L383`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/ontology/engine.py#L297-L383)）。官方 SHACL 指南也明确要求把它主动放进 ingestion/CI 流程，并处理 violation（[SHACL Validation](https://docs.getsemantica.ai/guides/shacl-validation/)）。

因此，要让 Ontology 真正成为“统一语言”，Tidewise 必须显式实现：

1. 在抽取提示词或自定义 extractor 中限制实体类型和关系谓词；
2. 将公司简称、全称、证券代码、申万行业、概念板块映射到 canonical ID；
3. 对 predicate 和 event type 做 vocabulary mapping；
4. 写入前或发布前调用 SHACL validation；
5. 查询和规则只暴露 canonical vocabulary；
6. 对未对齐实体进入 quarantine/review，而不是无声写入。

## 3. 标准化查询能力

Semantica 提供多种底层查询入口：

- Property Graph：统一 CRUD 和 Cypher/OpenCypher；
- RDF Triplet Store：SPARQL；
- Vector Store：统一的相似度搜索结果；
- `AgentContext.retrieve()`：向量 + 图扩展的混合检索；
- MCP stdio server：12 个 Agent 工具，可添加实体/关系、查历史决策、运行规则和导出图（[MCP Server](https://docs.getsemantica.ai/reference/mcp_server/)）。

但这不等于已经具有投研语义查询。例如以下接口 Semantica 都没有直接提供：

```text
query_event_impact(event_id, horizon="20d")
query_company_exposure(stock_code="600xxx", event_type="政策补贴")
query_evidence_chain(thesis_id)
query_conflicting_evidence(entity_id, as_of=...)
infer_market_signals(event_id, as_of=...)
```

这些应该成为 Tidewise 领域查询契约。实现内部可以组合 Cypher、向量检索、GraphRAG 和规则推理，但不应让 Agent 自己拼底层查询或依赖 Semantica 内部对象结构。

MCP 可以用于本地交互或原型，但官方说明它是本地 `stdio` 子进程，不是远程 Backend API；自主 Python/backend 服务应原生调用 `AgentContext`（[MCP Server Guide](https://docs.getsemantica.ai/guides/mcp-server/)）。

## 4. 固定推理规则

### 开箱即用

当前 `Reasoner` 可以显式添加字符串/对象规则和事实，做 forward chaining，并返回 conclusion、rule、premises、confidence；这是可解释规则推理的基础（[`reasoner.py#L24-L55`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/reasoning/reasoner.py#L24-L55)、[`#L83-L185`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/reasoning/reasoner.py#L83-L185)）。另外还有 Rete、Datalog、SPARQL 和 Temporal reasoning（[Reasoning Reference](https://docs.getsemantica.ai/reference/reasoning/)）。

可以表达这样的定性规则：

```text
IF PolicySupport(?event, ?sector)
AND BelongsToSector(?stock, ?sector)
THEN PositiveCatalyst(?stock)
```

### 不是开箱即用

- 规则和事实必须显式装载，并显式调用推理；Reasoner 不会自动监听图谱新增事实。
- Semantica 不会自动把 Ontology 中的概念、SHACL 约束转成投研规则。
- MCP 的 `run_reasoning` 当前实现要求调用方同时传入 `facts` 和 `rules`，创建一个新的 `Reasoner`，返回派生事实；它不读取 MCP live graph，也不自动回写推断结果（[`mcp_server/__init__.py#L218-L229`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/mcp_server/__init__.py#L218-L229)）。
- 基础规则引擎擅长符号关系和确定性派生，不等于市场预测模型。估值阈值、价格反应、衰减曲线、多因素权重和概率更新仍需领域代码或统计模型。

Tidewise 需要实现的桥接是：

```text
KG 中新增/更新 Event
  → 查询受影响实体和事实
  → 转换成 Reasoner facts
  → 加载指定版本规则
  → 执行推理
  → 将 InferenceResult 作为 DerivedSignal 回写（含 rule_id、premises、confidence）
```

固定规则最适合输出 `PositiveCatalyst`、`NegativeCostPressure`、`SupplyConstraint`、`PolicyBeneficiary` 这类可解释的**中间信号**。最终“看多/看空、短期/长期”的判断还应让 Agent/评分模型综合市场数据与反证。

## 5. 事件驱动能力

Semantica 有两个容易被混为一谈的能力：

1. `StreamIngestor`：从 Kafka、RabbitMQ、Kinesis、Pulsar 消费消息；
2. `EventDetector`：从一段文本中抽取事件类型、参与者、时间、地点和置信度。

它们并没有自动连成“事件发生 → 入图 → 规则运行 → Agent 结论”的业务闭环。

源码中，Stream Processor 只做 JSON 解析、可选 transform/validate，然后调用用户设置的 `message_handler`；具体 handler 必须由调用方提供（[`stream_ingestor.py#L85-L179`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/ingest/stream_ingestor.py#L85-L179)）。所以事件驱动的触发器实际上应由 Semantic Runtime 编排。

`EventDetector` 的 pattern 模式内置事件词典主要是英文 acquisition、partnership、launch、investment、legal 等通用类别（[`event_detector.py#L85-L122`](https://github.com/semantica-agi/semantica/blob/7dce9f1b69d83d0a077d3a785532af0d69b00018/semantica/semantic_extract/event_detector.py#L85-L122)）。对于中文 A 股，需要 LLM、自定义词典/模型和明确事件 schema，例如：业绩预告、订单中标、回购增持、减持、定增、监管处罚、政策补贴、产能投放、原料涨价、出口管制等。

推荐的事件闭环应是：

```text
消息/公告/新闻
  → 原始文档与来源登记
  → 中文金融事件抽取
  → 公司/证券/板块 canonical 对齐
  → 去重、冲突处理、SHACL 质量门
  → KG + Vector 双写
  → 受影响范围查询
  → 固定规则推理
  → DerivedSignal 写回
  → Agent 读取证据、行情和反证形成 InvestmentThesis
  → 记录结论、证据链、规则版本与置信度
```

## 6. 投研结论与时间尺度

Semantica 的 temporal graph 能表示 `valid_from` / `valid_until`、历史快照和 Allen interval relations，适合回答“当时哪些事实有效”“事件 A 在事件 B 之前还是期间”（[Core Concepts — Temporal Intelligence](https://docs.getsemantica.ai/concepts/#temporal-intelligence)）。

但它没有内置以下金融语义：

- 短期是 1/5/20 个交易日，长期是季度还是 1–3 年；
- 事件冲击何时开始、何时被市场计价、如何衰减；
- 事实利好是否已经反映在估值和价格中；
- 板块贝塔、市场 regime、流动性、拥挤度如何调整信号；
- 同一事件对上游、下游、竞争对手的方向和强度；
- 多个相互冲突的事件如何合并成结论；
- “看好/看空”对应的是基本面、相对收益还是绝对价格。

这些才是投研 Agent 最关键的领域推理。建议将它们建成 Tidewise 的独立模型：

- `ImpactDirection`：positive / negative / mixed；
- `ImpactChannel`：revenue / cost / capacity / demand / valuation / liquidity / regulation；
- `Horizon`：intraday / 5d / 20d / quarter / 1y+；
- `DecayProfile`：事件影响随时间的衰减；
- `ExposureStrength`：公司与事件链路的暴露强度；
- `MarketExpectation`：已计价程度；
- `EvidenceFor` / `EvidenceAgainst`；
- `DerivedSignal` 与 `InvestmentThesis` 分层。

Semantica 的 Decision Intelligence 可以把最终 Agent 结论及 reasoning、outcome、confidence 记录为图节点，并做 precedent search 和 causal chain；它记录和检索结论，不负责判断结论是否正确（[Core Concepts — Decision Intelligence](https://docs.getsemantica.ai/concepts/#decision-intelligence)）。

## 建议的系统分层

```text
┌──────────────────────────────────────────────────────────┐
│ 投研 Agent                                                │
│ 读取证据 + 派生信号 + 行情/估值 + 反证 → 多周期投资结论    │
└───────────────────────────▲──────────────────────────────┘
                            │ 领域查询契约
┌───────────────────────────┴──────────────────────────────┐
│ Tidewise Semantic Runtime                                │
│ 事件编排 │ A 股 Ontology 对齐 │ 双写一致性 │ 规则桥接      │
│ 时效/衰减 │ 信号聚合 │ 证据链 │ 标准化查询/Tool Contract │
└───────────────────────────▲──────────────────────────────┘
                            │ 调用模块
┌───────────────────────────┴──────────────────────────────┐
│ Semantica Core                                            │
│ Extract │ KG/GraphStore │ VectorStore │ GraphRAG          │
│ Ontology/SHACL │ Reasoning │ Temporal │ Provenance/Decision│
└──────────────────────────────────────────────────────────┘
```

## 最小可行验证建议

不要先验证“Semantica 是否能自动给股票结论”，而是验证它是否能稳定支撑一条最小证据链：

1. 选一个真实中文事件，例如“某部委发布行业补贴政策”；
2. 预定义最小 Ontology：`PolicyEvent`、`Sector`、`Company`、`Stock` 及 5–8 种关系；
3. 抽取事件并对齐到唯一板块、公司和证券代码；
4. 同一份来源文本写入向量库，结构化事实写入图谱；
5. 运行一条固定规则，生成 `PolicyBeneficiary(stock)`；
6. 查询该信号的完整证据链、来源、时间和反证；
7. Agent 只基于这些证据输出“为什么可能受益”，暂不预测收益率；
8. 再逐步加入时间衰减、行情/估值和回测，升级为短期/长期多空结论。

如果这条链能够可靠运行，Semantica 作为内核是成立的；如果抽取—对齐—双写—规则—查询之间需要大量绕过框架的补丁，则应缩小 Semantica 使用范围，只保留最成熟的图谱、向量或规则模块。

## 风险与文档成熟度提醒

官方 Concepts/Modules 中存在文档与当前 `main` 源码不一致的示例：

- 文档使用 `AgentContext.query(..., mode="graphrag")`，当前 `AgentContext` 源码可见的是 `retrieve()` 和 `query_with_reasoning()`，未定义该 `query()` 方法；
- Modules 示例使用 `Reasoner.apply_transitivity()`、`apply_symmetry()`、`infer()` 以及 `DatalogEngine`，当前核心 `Reasoner` API 是 `add_fact()`、`add_rule()`、`forward_chain()`、`infer_facts()`，导出类为 `DatalogReasoner`；
- Concepts 的 `Fact(subject=..., predicate=..., obj=...)` 与当前 `Fact(fact_id, predicate, arguments, metadata)` 数据类不一致。

这不否定模块方向，但说明在生产选型前必须：锁定 Semantica 版本、以源码和测试为准、对关键 API 做 smoke test，并避免把文档中的架构描述直接当成已完成的产品集成。

另外，官方语义抽取指南明确提醒抽取结果不是事实保证，即使高置信度也可能错误，金融等高风险场景必须验证、设置信心阈值并做实体消歧（[Semantic Extraction — Common Pitfalls](https://docs.getsemantica.ai/guides/semantic-extraction/)）。GraphRAG 能提高上下文结构和可追溯性，但不能保证输入事实、因果假设或最终投资结论正确。

## 关键官方来源

- [Core Concepts](https://docs.getsemantica.ai/concepts/)
- [Modules](https://docs.getsemantica.ai/modules/)
- [Semantic Extract Reference](https://docs.getsemantica.ai/reference/semantic_extract/)
- [Ontology Reference](https://docs.getsemantica.ai/reference/ontology/)
- [Reasoning Reference](https://docs.getsemantica.ai/reference/reasoning/)
- [SHACL Validation Guide](https://docs.getsemantica.ai/guides/shacl-validation/)
- [Context Graphs Guide](https://docs.getsemantica.ai/guides/context-graphs/)
- [MCP Server Reference](https://docs.getsemantica.ai/reference/mcp_server/)
- [Semantica official repository](https://github.com/semantica-agi/semantica)
