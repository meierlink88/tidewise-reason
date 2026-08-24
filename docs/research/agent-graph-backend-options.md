# Agent 顶层下的图谱与 GraphRAG 底座选型

> 调研日期：2026-08-21  
> 场景：Codex 类 Agent + LLM 负责任务规划、工具调用和投研推导；底层负责事件、产业链、证据、时间和规则的存储与检索。  
> 证据范围：只使用 OpenSPG/KAG、Semantica 和 Microsoft GraphRAG 官方仓库、文档与源码。Semantica 实现细节复用《[Semantica 推理原理与实现边界](./semantica-reasoning-engine.md)》，不重复展开。

## 结论

**可以替换 OpenSPG，但 Semantica 和 GraphRAG 不是同一类替代品。**

- **Semantica 是底座替代候选**：它同时提供图存储适配、ontology/SHACL、递归 Datalog、时态计算、溯源、向量库、REST/MCP，与 OpenSPG 重叠最大。
- **Microsoft GraphRAG 不是 OpenSPG 的等价替换品**：官方定位是将非结构化文档提取为实体、关系、Claim、Community 和 Community Report，然后执行 Local/Global/DRIFT 检索。它默认将图输出为 Parquet 表，不是一个面向事件的在线语义图数据库，也没有官方声明的递归业务规则引擎。
- **Agent 替代了 KAG 的大部分规划与推理职责，却没有自动替代知识治理**。无论选 OpenSPG、Semantica 还是自建 Neo4j/PostgreSQL，仍需维护 Event、Evidence、IndustryChainNode、有效时间、来源和派生结论的稳定合同。
- **对“事件驱动、产业链逐节点推导”，不建议以通用 GraphRAG 单独替代 OpenSPG**。GraphRAG 适合增强全文发现和跨文档综合；事件、节点、时间窗口和精确边遍历应继续由可变更的结构化图/关系数据层承担。
- **当前更稳妥的目标形态是“可插拔图工具 + 可选 GraphRAG 文档工具”**，而不是先选定某个大而全的底座。

## 先分清三种系统的职责

| 系统 | 官方核心定位 | 在 Agent 架构中最合适的角色 |
| --- | --- | --- |
| OpenSPG | 受 Schema 约束的语义图、Builder、KGDSL/规则 Reasoner、图查询 | 专业领域的类型化事实图和确定性规则底座 |
| Semantica | Context/KG 基础设施、ontology、符号推理、时态、溯源、图/向量存储和 Agent 接口 | 较轻量、可组合、完整开源的图与治理底座候选 |
| Microsoft GraphRAG | LLM 驱动的文档图抽取、社区分析、社区报告和查询聚合 | 原文/研报/新闻的发现与召回侧车，不是事件图唯一存储 |
| KAG | kg-builder + 逻辑形式引导的 Planner/Retriever/Reasoner/Generator | 如果顶层 Agent 已负责规划和多轮工具使用，可选的专业检索器，不再是必选主控层 |

KAG 官方将 `kg-solver` 描述为含规划、推理和检索算子的混合求解引擎，它会把自然语言问题转成语言与符号结合的步骤。这正是与 Codex 类 Agent 重叠最大的部分。来源：[KAG v0.8.0 README](https://github.com/OpenSPG/KAG/blob/v0.8.0/README.md)。

## 分维度比较

| 维度 | OpenSPG（KAG 可选） | Semantica | Microsoft GraphRAG |
| --- | --- | --- | --- |
| 图存储/更新 | 官方产品拓扑使用 Neo4j，支持按类型写入和图查询 | `GraphStore` 抽象支持 Neo4j、FalkorDB、Apache AGE/PG 等；应用自行组合 | 默认输出 Parquet 知识表，向量写入 LanceDB/Azure AI Search/CosmosDB；更像批量索引产物 |
| Schema/语义约束 | SPG-Schema 深，原生区分 Entity/Concept/Event，属性和关系有类型约束 | ontology、OWL/SHACL/SKOS 和 ContextGraph 覆盖广；实现成熟度需逐模块验证 | 有固定输出知识模型，可配抽取的 `entity_types`；不等于可执行的业务 ontology |
| 规则/递归推导 | KGDSL 能表达结构、约束、聚合和有界多跳；生产级时态信号传播仍需领域规则或 Agent | 简单前/后向链 + 递归 Datalog 半朴素不动点 + Allen 时态计算；递归可达性是明确优势 | 官方 Query Engine 列出 Local/Global/DRIFT/Basic Search 和 Question Generation；未提供类似 KGDSL/Datalog 的业务规则求值层 |
| 时态 | EventType 有时间特征，KGDSL 有时间 UDF；完整双时态、修订史和信号生命周期需领域建模 | Allen 区间代数、point-in-time 查询和 provenance 中的有效期/版本链是一等能力 | Claim/Covariate 可有时间字段，表中 `period` 服务于增量合并；不是时态规则引擎 |
| 溯源 | KAG 可建立节点/边到 Chunk 的 `source` 链；结构化来源版本需自行补齐 | W3C PROV-O、实体/关系/Chunk/属性跟踪、SHA-256 和版本链更完整 | Document↔TextUnit↔Entity/Relationship/Claim 保留引用 ID，利于回到原文；不等于完整决策/派生事实审计链 |
| 文档检索 | KAG 的 Knowledge/Chunk 互索引、图与文本混合 Retriever 面向专业问答 | ingest + vector store + hybrid search 模块完整度较高，但统一 Planner 弱于 KAG | 这是强项：Local 合并抽取图和原始 Chunk，Global 在 Community Reports 上 map-reduce，DRIFT 结合社区与跟进问题 |
| Agent 工具接口 | OpenSPG 有 HTTP API；KAG 官方可以 `kag mcp-server` 暴露 `qa_pipeline` | 官方 stdio MCP 直接暴露加节点/边、查决策、跑规则和图分析等工具 | 官方提供 Python API 和 CLI；可由应用封装成 Agent Tool，但官方主体仍是 index/query API |
| 运行复杂度 | 高：官方 Compose 含 Server、MySQL、Neo4j、MinIO，再加模型和索引配置 | 中：Python 模块可以轻量起步，但生产化仍要选图库、向量库和 provenance 持久化 | 中：安装简单，但索引有多轮 LLM 抽取/总结/向量化成本，官方 README 明确警告索引可能昂贵 |
| 频繁 Event 增量 | 可对类型化节点/边 UPSERT；索引与派生结论生命周期需工程治理 | 更贴近应用内实时写图，并能表达有效时间/版本；需自己编排数据管道 | 有 `update` 索引命令和增量合并字段，但官方执行模型仍是索引工作流，不是每条 Event 的低延迟事务写入 |

一手来源：

- OpenSPG 官方部署依赖：[`docker-compose.yml`](https://github.com/OpenSPG/openspg/blob/v0.8/dev/release/docker-compose.yml#L365-L495)
- OpenSPG 事件模型：[`EventType.java`](https://github.com/OpenSPG/openspg/blob/v0.8/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/type/EventType.java#L25-L85)
- OpenSPG 供应链规则示例：[KAG SupplyChain Reasoner](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/reasoner/README.md)
- KAG Schema 约束抽取与 `source` 关系：[`schema_constraint_extractor.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/extractor/schema_constraint_extractor.py#L267-L302)
- KAG MCP：[`mcp_server.md`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/baike/mcp_server.md)
- Semantica 图存储：[`graph_store.md`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/docs/reference/graph_store.md)
- Semantica Datalog：[`datalog_reasoner.py`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/datalog_reasoner.py)
- Semantica 时态推理：[`temporal_reasoning.py`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/kg/temporal_reasoning.py)
- Semantica provenance：[`provenance.md`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/docs/guides/provenance.md)
- Semantica MCP：[`mcp/README.md`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/mcp/README.md)
- GraphRAG 默认数据流：[`default_dataflow.md`](https://github.com/microsoft/graphrag/blob/7bb23cc7f32f47cf618a1ae9cca39a6695f434ae/docs/index/default_dataflow.md)
- GraphRAG 输出表：[`outputs.md`](https://github.com/microsoft/graphrag/blob/7bb23cc7f32f47cf618a1ae9cca39a6695f434ae/docs/index/outputs.md)
- GraphRAG Query Engine：[`query/overview.md`](https://github.com/microsoft/graphrag/blob/7bb23cc7f32f47cf618a1ae9cca39a6695f434ae/docs/query/overview.md)
- GraphRAG 配置与存储：[`config/yaml.md`](https://github.com/microsoft/graphrag/blob/7bb23cc7f32f47cf618a1ae9cca39a6695f434ae/docs/config/yaml.md)
- GraphRAG 官方定位和索引成本警告：[`README.md`](https://github.com/microsoft/graphrag/blob/7bb23cc7f32f47cf618a1ae9cca39a6695f434ae/README.md)

## 对事件驱动产业链的适配性

一次真实分析的最小底层操作是：

```text
resolve_anchor(story_or_chain)
get_chain_nodes(anchor_id)
get_active_events(anchor_id, as_of, horizon)
get_event_evidence(event_ids)
get_neighbors(node_id, relation_types, direction, max_depth)
get_rules(anchor_id, rule_version, as_of)
get_prior_derived_signals(anchor_id, as_of, horizon)
write_analysis_run(conclusions, evidence_refs, model_version, prompt_version)
```

Agent 可以根据上述工具结果自主分解任务、重试空查询、逐节点评估和处理正反信号。因此，底层不需要再实现一套 KAG 式总 Planner，但必须能稳定执行这些领域操作。

对这组操作：

1. **OpenSPG 适合度高**：Schema、EventType、定点图查询和规则引擎能作为稳定语义面；代价是部署和产品层复杂。
2. **Semantica 适合度中高**：图存储可换、递归 Datalog、时态和 provenance 都贴合需求；但它是年轻项目，对大图、高频修订、并发规则和端到端正确性要自行压测。
3. **Microsoft GraphRAG 单独适合度低**：它很适合用文档发现“可能还有哪些相关事实”，但它的默认知识模型不会自动执行“在 `as_of` 时点遍历指定产业链全部节点并应用业务传导规则”。

## 推荐架构

```text
PostgreSQL / 事件源 / 研报原文
                  │
        清洗、ID、时间、版本、溯源
                  │
       ┌──────────┴──────────┐
       │                       │
Structured Graph Tool      Document Discovery Tool
OpenSPG / Semantica /      Microsoft GraphRAG / KAG Chunk
Neo4j + domain service             │
       │                       │
       └──────────┬──────────┘
                  │
         Codex 类 Agent + LLM
   规划 / 反复查询 / 逐节点推导 / 自检
                  │
        AnalysisRun / DerivedSignal
        带 as_of、horizon、证据和版本
```

关键原则是不让 Agent 直接依赖某个底层的原始 Cypher、KGDSL 或 Parquet 表结构，而是通过稳定的领域 Tool 合同隔离实现。这样才能真正对 OpenSPG、Semantica 和自建图服务做同数据 A/B 测试。

## 具体选型建议

### 当前不建议立即替换 OpenSPG

现在已经有可运行的 ReasonSmoke Schema、Neo4j 数据和 OpenSPG/KAG 验证链。在 Agent Tool 层尚未抽象、同数据测试尚未完成前直接迁移，无法分辨改善是来自 Agent、数据合同还是底层。

### 何时选 Semantica

当下列条件成立时，Semantica 是最值得进入 PoC 的替代品：

- 希望完全控制 UI/API/MCP/存储适配源码；
- 规则主要是递归可达性、时间区间和可审计决策链；
- 接受自己组装数据管道和 Agent 工具；
- 愿意对未到 1.0 的年轻项目做完整源码审计和压测。

### 何时引入 GraphRAG

GraphRAG 应优先作为旁路能力，适用于：

- 用大量新闻、研报和访谈做跨文档全局主题发现；
- 通过 Community Reports 找到可能被结构化图遗漏的关联；
- 对某个实体同时召回抽取关系和原始 TextUnit；
- 作为 Agent 的“文档侦查工具”，将候选事实回送给治理层后再入正式事件图。

不应把 GraphRAG 自动抽取的关系直接当成经过审核的产业传导边或投研规则。

## “更有效率”必须用同一组任务测量

官方资料没有提供这三套系统在“事件驱动产业链”上可直接比较的基准，因此不能从 README 得出哪个性能更高。应使用相同的事件、产业链和 Agent Tool 合同测试：

1. 单条 Event 从入库到可查询的 P50/P95；
2. `as_of + horizon` 时间窗口的正确性和前视偏差；
3. 10、50 个节点全链遍历的查询次数、延迟和结果完整性；
4. 正反 Event 冲突时证据召回率和最终结论稳定性；
5. 源事实修订/撤回后，旧 DerivedSignal 能否正确失效；
6. 从结论回溯到 Evidence 原文、规则版本和模型版本的完整率；
7. 同等召回质量下的存储、向量数、LLM token 成本和运维人时。

只有通过这组测试，才能决定“OpenSPG 继续作语义底座”、“Semantica 替换”或“自建图服务 + GraphRAG 侧车”哪个更有效率。

## 最终建议

1. **短期**：保留 OpenSPG，停止继续把业务逻辑锁进 KAG Pipeline；先把上述领域 Tool 合同对 Agent 暴露。
2. **同步 PoC**：用当前 ReasonSmoke 的同一组 Event/Evidence/IndustryChain 数据，实现 Semantica 后端适配，不改 Agent 提示词和工具合同。
3. **将 GraphRAG 视为第二召回通道**：用于文档群主题发现和候选事实挖掘，不代替受治理的事件图。
4. **达到门槛再迁移**：只有当 Semantica/自建方案在时态正确性、溯源、逐节点完整性和总成本上明显优于 OpenSPG，才替换现有底座。

一句话总结：

> **Agent 让底座变得可替换，但不会让数据合同消失；Semantica 可以竞争 OpenSPG 的位置，GraphRAG 更适合竞争 KAG 的文档召回位置。**
