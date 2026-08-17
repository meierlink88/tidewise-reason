# WeKnora 与 OpenSPG + KAG 0.8 对比研究

> 调研时间：2026-08-11  
> 范围：Tencent WeKnora 官方仓库 `dcaa2d3`；OpenSPG 官方仓库 `ceeb3ef`；KAG 0.8 官方发布与源码。

## 结论

**不是同一种概念，但属于相邻且有重叠的知识增强技术栈。**

- **WeKnora** 是面向文档的、开箱即用的 **RAG + ReAct Agent + 自动 Wiki 平台**。它擅长多源文档摄取、解析、分块、混合检索、问答、引用、Agent 工具编排和 Web UI；知识图谱是增强文档召回的一种可选索引。
- **OpenSPG + KAG** 是面向专业领域的 **语义知识图谱 + 知识构建 + 符号/语言混合推理框架**。OpenSPG 负责领域 Schema、实体关系、图谱构建与 KGDSL 规则；KAG Builder/Solver 负责 Schema 约束抽取、知识与 Chunk 互索引、逻辑形式规划、多跳检索与推理。

最关键的差异是：

> **WeKnora 的当前 GraphRAG 是“一跳图关系增强 Chunk 召回”；OpenSPG + KAG 的目标是“基于领域 Schema 和逻辑形式的图谱、规则、文本混合求解”。**

因此，WeKnora 不能直接替代观潮家的 OpenSPG TBox、投资领域统一语言和规则推理层；它更适合补充成为研报、公告、新闻、会议纪要等文档知识的摄取与检索服务。

## 能力对比

| 维度 | WeKnora | OpenSPG + KAG 0.8 |
|---|---|---|
| 产品主目标 | 企业文档理解、RAG 问答、ReAct Agent、自动 Wiki | 专业领域知识图谱、事实问答、逻辑与多跳推理 |
| 原始数据 | 重点是文件、网页和 SaaS 文档源 | 同时面向结构化数据、非结构化文档和专家规则 |
| 摄取流程 | 连接器/上传 → 解析/OCR/VLM/ASR → 分块 → Embedding/图抽取 | Builder 可配置扫描、解析、切分、Schema 约束或自由抽取、对齐、映射、向量化、写图 |
| Schema | 每个知识库可配置实体类型、字符串属性名、关系三元组和抽取提示 | SPG-Schema 是一等领域模型，支持类型、属性、关系、语义建模；KAG 可严格按 Schema 抽取和链接 |
| Ontology/领域语义 | 有轻量的“抽取结构”，未见与 SPG 相当的本体治理、概念标化、谓词语义或规则体系 | 领域 Schema、概念语义、实体链指/归一、领域知识注入是核心能力 |
| 知识图谱 | 文档 Chunk 中抽取实体/关系，Neo4j 存储；节点模型较轻 | OpenSPG 管理正式领域 KG，支持结构化导入、持续演化和可编程图谱构建 |
| 向量/全文检索 | 成熟且可插拔：Dense、BM25、RRF、父子 Chunk、pgvector HNSW 等 | KAG 使用 Chunk、KnowledgeUnit、AtomicQuery、Outline、Summary、Table 等索引，并与图知识互索引 |
| GraphRAG | 查询实体 → Neo4j 名称匹配 → 一跳邻居 → 关联 Chunk 并入普通候选集 | 逻辑形式驱动规划、检索和推理，可组合精确匹配、图谱推理、Chunk 检索、数值计算和 LLM 推理 |
| 固定规则 | 未发现 SPG KGDSL 同类的业务规则建模与执行机制 | OpenSPG Reasoner 提供 KGDSL，可编程表达谓词语义和逻辑规则 |
| Agent 集成 | 自带 ReAct Agent、内置工具、MCP、Web Search、Skills 和多种聊天渠道 | KAG 0.8 提供召回/推理 HTTP API、MCP 和可嵌入问答页面，通常作为外部 Agent 的知识/推理后端 |
| Web UI | 更成熟、更偏最终用户：知识库、聊天、Agent、Wiki、图视图、设置、评测、追踪 | 提供 Schema、知识库、构建任务、知识探索和推理问答 UI，更偏图谱与 KAG 开发/管理 |

## 关键证据

### 1. WeKnora 的主干是文档 RAG 和 Agent

官方将产品定义为文档理解、语义检索和自主推理框架，并把 RAG 快速问答、ReAct Agent、自动 Wiki 列为三项核心能力。它支持多种文档格式、飞书/Notion/语雀/RSS 等数据源，以及按上传批次覆盖解析、分块、多模态、图抽取和问题生成配置。[WeKnora README：定位](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/README.md#L47-L55) [知识管理与摄取能力](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/README.md#L125-L138)

其检索主干覆盖 Dense、BM25、GraphRAG、父子分块与 pgvector HNSW；混合检索在存储层之上使用加权 RRF 融合关键词与向量结果。[检索能力列表](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/README.md#L129-L147) [RRF 设计](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/website-docs/03-features/05-retrieval-engines.md#L218-L248)

### 2. WeKnora 有图谱配置，但不是 OpenSPG 式语义本体

WeKnora 允许每个知识库配置实体类型、实体属性名、关系类型、示例与自定义抽取指令；所以不能说它“没有 Schema”。但其图数据模型较轻：节点主要是 `name/chunks/attributes`，关系是 `node1/node2/type`。官方材料和已检查源码中未出现 RDF/OWL、概念层级、谓词语义、逻辑公理或 KGDSL 类规则治理能力。[图抽取配置](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/website-docs/03-features/09-knowledge-graph.md#L33-L61) [图数据模型](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/website-docs/03-features/09-knowledge-graph.md#L85-L105)

这意味着它的配置更接近“告诉 LLM 从文档抽取哪些节点、属性和边”，而不是用一套正式领域语义模型持续约束结构化事实、规则和推理。

### 3. WeKnora 当前 GraphRAG 是图增强召回

官方流程是：摄取时按 Chunk 用 LLM 抽取实体和关系并写入 Neo4j；查询时抽取查询实体，在 Neo4j 做名称包含匹配，取一跳邻居及其关联 Chunk，然后将这些 Chunk 合并到普通检索候选集。[官方 GraphRAG 查询流程](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/website-docs/03-features/09-knowledge-graph.md#L123-L130)

Agent 的 `query_knowledge_graph` 工具当前实际调用 `HybridSearch`；源码还明确提示完整图查询语言/Cypher 支持仍在开发中。[工具调用 HybridSearch](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/internal/agent/tools/query_knowledge_graph.go#L167-L187) [Cypher 限制](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/internal/agent/tools/query_knowledge_graph.go#L352-L363)

因此当前能力适合“找出与某实体相关的更多文档段落”，不能等同于基于规则的任意多跳图谱推理。

### 4. OpenSPG + KAG 的主干是领域语义与混合推理

OpenSPG 官方定义的核心能力包含 SPG-Schema、结构化/非结构化知识构建、实体链指、概念标化、实体归一，以及以 KGDSL 表达谓词语义和逻辑规则的 SPG-Reasoner。[OpenSPG 核心能力](https://github.com/OpenSPG/openspg/blob/ceeb3ef549df79ca4c4878e7ff452c73584991f3/README_cn.md#L15-L41)

KAG 明确以 OpenSPG 和 LLM 为基础，支持 Schema-Constraint 知识构建、概念语义对齐、知识与 Chunk 互索引，以及逻辑符号引导的混合推理和多跳问答。[KAG 定位与核心能力](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md#L28-L59)

其 Solver 将自然语言问题转换为由规划、推理和检索算子组成的求解过程，并组合精确匹配、文本检索、数值计算、图谱推理和 LLM 推理。[KAG 技术架构](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md#L157-L165) KAG 0.8 还提供 `KnowledgeUnit`、`Outline`、`Summary`、`Chunk`、`AtomicQuery`、`Table` 等可配置索引，支持 Schema 约束抽取、知识对齐、HTTP/MCP 接入。[KAG 0.8 Release](https://github.com/OpenSPG/KAG/releases/tag/v0.8.0)

### 5. 部署与存储并不相同

WeKnora 默认 Compose 栈包含前端、Go 应用、DocReader、PostgreSQL/ParadeDB 和 Redis；Neo4j、MinIO、Langfuse 与其他向量后端是可选项。向量/检索层支持 PostgreSQL、SQLite、Elasticsearch、OpenSearch、Qdrant、Milvus、Weaviate、Doris 和腾讯云 VectorDB；图谱只使用 Neo4j。[默认运行依赖](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/docker-compose.yml#L365-L405) [检索后端](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/website-docs/03-features/05-retrieval-engines.md#L190-L202) [Neo4j 图谱依赖](https://github.com/Tencent/WeKnora/blob/dcaa2d388358b6412044a8e853a190142fe17047/website-docs/03-features/09-knowledge-graph.md#L12-L31)

OpenSPG 官方 Compose 的核心服务直接依赖 MySQL、Neo4j 和 MinIO，Neo4j 同时被配置为 graph store 和 search engine；KAG 开发模式还需要 Python 3.10 环境和模型服务。[OpenSPG Compose](https://github.com/OpenSPG/openspg/blob/ceeb3ef549df79ca4c4878e7ff452c73584991f3/dev/release/docker-compose.yml#L1-L83) [KAG 安装](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md#L82-L150)

## 对观潮家语义引擎的建议

观潮家的目标包含统一投资领域语言、公司/行业/产业链/概念/事件的正式关系、结构化事实查询、规则与事件驱动推理。按这个目标：

1. **继续以 OpenSPG + KAG 作为语义主干。** 已构建的 `Country`、`Industry`、`IndustryChain`、`IndustryChainNode`、`MarketConcept`、`Company` 等 TBox 应继续由 SPG Schema 管理；后续将事实、来源、时效和推理规则接入 KAG/OpenSPG。
2. **不要用 WeKnora 替换 TBox 和规则引擎。** 它当前不提供与 SPG Schema + KGDSL 等价的领域语义治理和符号规则执行。
3. **可把 WeKnora 作为文档知识侧车。** 用它接入研报、公告、财报、新闻、电话会和政策文档，提供解析、OCR、多模态、混合检索、引用与文档问答；再由 Agent 通过 API/MCP 同时调用 WeKnora 文档召回和 KAG 图谱推理。
4. **短期不建议立即引入。** 当前首先应把 OpenSPG Schema、ABox 导入、事件模型、证据溯源和至少一条 KAG 推理链跑通。此时再评估 WeKnora，才能判断其文档摄取体验是否足以抵消新增 PostgreSQL、Redis、DocReader 等运维成本。

建议的职责边界是：

```text
文档/研报/公告 ──> WeKnora（可选：解析、Chunk、向量/全文召回、引用）
结构化事实/领域关系 ──> OpenSPG（Schema、KG、规则、统一语义）
复杂问题 ──> KAG（图谱 + Chunk + 逻辑形式混合求解）
最终编排 ──> 观潮家 Agent（事件驱动、工具调用、结论生成与解释）
```

