# Graphiti 与 OpenSPG：Agent 顶层下的事件图底座比较

> 调研日期：2026-08-21  
> Graphiti 审计基线：稳定版 [`v0.29.3`](https://github.com/getzep/graphiti/tree/v0.29.3)，固定提交 [`021d3a57d511f21b10adaf7fa923bd5c1fce5e9d`](https://github.com/getzep/graphiti/commit/021d3a57d511f21b10adaf7fa923bd5c1fce5e9d)。  
> 证据范围：Graphiti 官方仓库、文档、源码和测试；OpenSPG 对比复用本仓库已有的一手源码审计。下文将“官方事实”和“工程判断”分开。

## 结论

**Graphiti 很适合成为 Codex 类 Agent 下的“动态事件记忆与时态证据图”，但不适合作为唯一权威数据源，也不是 OpenSPG 的完整同类替代。**

- 如果观潮家的目标是让 **LLM/Agent 真正完成逐节点推导**，而底座主要负责事件、事实、时间、来源和检索，Graphiti 比 OpenSPG + KAG 更贴近这个分工：它原生以 Episode 摄取变化信息，保留事实有效期和失效历史，并提供官方 MCP。
- 如果仍需要底座执行 **强 Schema、确定性业务规则、KGDSL 多跳归约或 Concept `leadTo` 推导**，OpenSPG 更强。Graphiti 没有同等级的 TBox、规则引擎或递归固定点求值。
- 因此建议进行 **受控替代 PoC，而不是立即替换**：让 Agent 使用同一套领域 Tool 合同，分别接 OpenSPG 和 Graphiti，用相同 Event、产业链、时间窗口和纠错场景验证。
- 对当前场景，最可能的目标架构不是“裸 Graphiti”，而是 **Graphiti + 观潮家数据合同/校验层 + 领域 MCP + Codex Agent**。这层领域服务必须补齐精确产业链遍历、`as_of` 过滤、规则卡读取、事件修订和分析结果审计。
- 原始 Event、指标和人工修订应保留在 PostgreSQL/事件仓等权威层；Graphiti 图应被视为可以从权威数据重建的语义投影。

## 逐项比较

| 维度 | Graphiti 官方事实 | OpenSPG 官方事实 | 对观潮家的工程判断 |
| --- | --- | --- | --- |
| 核心模型 | Entity、事实边和 Episode；Episode 保存摄取内容与来源，事实边保存支持它的 Episode ID | SPG-Schema 原生区分 Entity、Concept、Event，并约束属性和关系 | Graphiti 更像动态记忆；OpenSPG 更像领域语义平台 |
| 双时态 | 节点/边包含 `created_at`；事实边包含 `valid_at`、`invalid_at`、`expired_at`、`reference_time` | Event 与 KGDSL 有时间能力，但完整双时态和修订史需要领域建模 | 事件持续变化、历史回看和纠错是 Graphiti 的明显优势 |
| 增量更新 | `add_episode` 增量抽取、去重、冲突识别和失效旧事实，不要求全图重算 | 支持类型化图写入和派生事实；生命周期策略需业务定义 | 高频 Event 更适合 Graphiti，但失效判断受 LLM 与候选召回影响 |
| Schema / ontology | Pydantic 类型指导 LLM 抽取，并形成标签和属性；未匹配时仍允许生成自由关系类型 | SPG-Schema 是更深的 TBox，支持类型化关系、Concept/Event、语义约束 | Graphiti 的类型是“软抽取合同”，不能替代 OpenSPG 的强 Schema；需应用层校验 |
| 规则/递归 | 未发现 Datalog、规则固定点、业务规则执行器；BFS 是检索算子，社区使用标签传播 | KGDSL 支持有界 `repeat`、路径约束/归约；Concept `leadTo` 可递归派生 Event | Graphiti 不会自动完成产业链传导；若推导由 Agent 承担，这是职责转移而非缺陷消失 |
| 检索 | 节点/边支持向量、BM25、BFS；可用 RRF、MMR、节点距离、Cross-Encoder 重排；Episode 支持 BM25 | OpenSPG 负责精确图查询，KAG 提供图文混合检索、规划与推理 | Graphiti 适合相关事实召回；“遍历产业链全部节点”应使用专门的精确图工具，不应依赖 top-k 搜索 |
| 溯源 | Episode 保留原始内容、来源说明和 metadata；事实边记录支持它的 Episode；可按 Episode 取回节点和边 | KAG 可建立节点/边到 Chunk 的 `source` 链；结构化来源版本需补充 | Graphiti 的 Episode lineage 更直接，但仍需补 source ID/version/hash、采集时间、审核状态、模型/提示词版本 |
| 文档能力 | Episode 可摄取 text/message/json；保存原文并对实体/事实做混合检索 | KAG 的 Knowledge/Chunk 互索引和图文 Retriever 更完整 | Graphiti 足以做事件证据记忆，但不是完整研报 GraphRAG；大规模文档发现仍可另设 GraphRAG/KAG 通道 |
| Agent 接口 | 官方 MCP 提供写 Episode、查事实/节点、删 Episode/边、加三元组、建社区等工具 | OpenSPG 有 HTTP；KAG MCP 主要把 `qa_pipeline` 暴露给 Agent | Graphiti 更 Agent-native，但现成 MCP 缺少观潮家的业务级工具 |
| 部署 | 支持外部 Neo4j ≥ 5.26；官方 MCP 可用现有 Neo4j，或 Compose 启 Neo4j + MCP | 官方产品拓扑含 Server、MySQL、Neo4j、MinIO，KAG 还需模型/索引配置 | Graphiti 运维明显更轻；建议独立 Neo4j database，避免与 OpenSPG 标签和索引混用 |
| 成熟度 | Apache-2.0、当前稳定版 0.29.3；有单测、Neo4j/FalkorDB 集成测试、MCP 测试、类型检查和 CodeQL | OpenSPG/KAG 已有完整平台、UI、Schema/Reasoner/Builder 体系 | Graphiti 可以 PoC，但未到 1.0；官方对 Zep 托管服务的生产声明不能等同于 OSS Graphiti |

Graphiti 模型与能力的一手证据：[`README`](https://github.com/getzep/graphiti/blob/v0.29.3/README.md)、[`nodes.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/nodes.py)、[`edges.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/edges.py)、[`graphiti.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/graphiti.py)、[`search_config.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/search/search_config.py)、[`search_filters.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/search/search_filters.py)。OpenSPG 对比证据：[`SPG-Schema 文档`](https://github.com/OpenSPG/openspg/blob/v0.8/docs/4.%E5%BC%80%E5%8F%91%E6%89%8B%E5%86%8C/1.SPG-Schema.md)、[`KGDSL repeat 实现`](https://github.com/OpenSPG/openspg/blob/v0.8/reasoner/lube-logical/src/main/scala/com/antgroup/openspg/reasoner/lube/logical/planning/PatternMatchPlanner.scala#L279-L297)、[`CausalConceptReasoner`](https://github.com/OpenSPG/openspg/blob/v0.8/builder/core/src/main/java/com/antgroup/openspg/builder/core/reason/impl/CausalConceptReasoner.java)、[KAG v0.8.0 README](https://github.com/OpenSPG/KAG/blob/v0.8.0/README.md)。

## Graphiti 的事件与双时态机制

### 官方事实

`add_episode` 接收事件内容、来源类型、来源说明和 `reference_time`，创建 `EpisodicNode`，再通过 LLM 抽取实体和事实、解析重复实体/边、提取事实时间、识别冲突，最后增量写图。官方支持 `message`、`text`、`json` 和 `fact_triple` 等 Episode 类型，也提供批量摄取。[`Graphiti.add_episode`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/graphiti.py)

它的事实边时间字段可以组成双时态语义：

- `valid_at` / `invalid_at`：事实在现实世界中何时成立、何时停止成立；
- `created_at` / `expired_at`：事实何时进入系统、何时在系统中被判定失效；
- `reference_time`：来源 Episode 的时间锚点。

当新事实与旧事实冲突时，维护代码会保留旧边并写入 `invalid_at` 和 `expired_at`，而不是简单覆盖，从而保留历史。[`edge_operations.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/utils/maintenance/edge_operations.py)

### 工程边界

这不是一个自动保证正确性的通用双时态数据库。`EntityNode` 自身只有 `created_at`，其 summary/attributes 会更新在同一 UUID 上；因此“双时态”主要是 **fact-centric**，不是全图主数据版本系统。[`EntityNode`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/nodes.py)、[`Neo4j node queries`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/models/nodes/node_db_queries.py)

此外：

1. 时间提取、重复判断和语义冲突识别都依赖 LLM；
2. 冲突解析只会处理被候选检索召回的旧边，漏召回就可能漏失效；
3. 官方建议同一 `group_id` 的 Episode 顺序处理，MCP 也按组排队，以降低摄取竞态；
4. `SearchFilters` 能表达 `valid_at/invalid_at/created_at/expired_at`，但审计的默认搜索调用不会自动合成“某时点有效”的完整谓词。观潮家必须在领域 Tool 中固定实现下面的过滤；
5. `add_episode` 只取有限个近期 Episode 作为抽取上下文；历史一致性不能只依赖这段语言上下文，仍需可重放的权威 Event 流。

```text
valid_at <= as_of
AND (invalid_at IS NULL OR invalid_at > as_of)
AND (expired_at IS NULL OR 查询明确要求历史系统视图)
```

检索实现证据：[`search.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/search/search.py)、[`Neo4j search_ops.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/driver/neo4j/operations/search_ops.py)。

## Schema、类型边与规则的真实边界

### 官方事实

Graphiti 允许把 Pydantic 模型作为 `entity_types` / `edge_types` 传入，并通过 `edge_type_map` 限定某类端点允许选择哪些边类型。模型字段会参与提示词和属性抽取。[`extract_nodes.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/prompts/extract_nodes.py)、[`extract_edges.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/prompts/extract_edges.py)

但抽边提示词也明确允许：事实不匹配给定类型时，由模型生成一个新的自由关系类型。Neo4j 初始化主要建立 UUID、时间和全文索引，并不把这些 Pydantic 类型变成类似 SPG-Schema 的图库级领域约束。[`Neo4j graph_ops.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/driver/neo4j/operations/graph_ops.py)

Graphiti 的搜索配置包含 BFS，默认最大搜索深度是 3；这只是为检索扩展邻域。社区构建使用标签传播算法和 LLM 摘要。官方源码未提供 KGDSL、Datalog、前/后向链或固定点规则求值器。[`search_config_recipes.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/search/search_config_recipes.py)、[`community_operations.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/utils/maintenance/community_operations.py)

### 工程判断

因此，Graphiti 中可以存储这样的“规则卡”：

```text
PropagationRule {
  mechanism,
  sourceVariable,
  targetVariable,
  direction,
  applicability,
  invalidators,
  lagRange,
  durationRange,
  evidenceRefs,
  version
}
```

但 Graphiti 不会自行执行它。Agent 必须读取规则卡、取回相关 Event/Evidence 和精确产业链子图，再由 LLM 逐节点判断。这符合“LLM 负责推导”的设计思想；同时也意味着稳定性要由结构化输入、输出约束、工具级遍历保证、评测集和结果审计共同保证。

OpenSPG 的优势恰好相反：它更适合把一部分规则变成确定性的 KGDSL/Concept 逻辑，但其 Planner/Reasoner 与顶层 Codex Agent 会产生一定职责重叠。

## Provenance、修订与删除

### 官方事实

- Episode 保存原始 `content`、`source_description`、`episode_metadata`；可以通过配置关闭原文保存。
- `EpisodicNode.entity_edges` 记录 Episode 提供的事实边，`EntityEdge.episodes` 记录支持该事实的 Episode ID。
- API/MCP 可以按 Episode 取回相关实体，也可删除 Episode 或事实边。

来源：[`nodes.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/nodes.py)、[`edges.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/edges.py)、[`MCP server`](https://github.com/getzep/graphiti/blob/v0.29.3/mcp_server/src/graphiti_mcp_server.py)。

### 工程风险

Graphiti 的 Episode lineage 很适合追溯新闻/公告到图事实，但它不是完整的 W3C PROV 或投研审计模型。观潮家仍需显式保存：来源记录 ID、版本/哈希、采集与披露时间、审核状态、抽取模型/提示词版本、规则版本、AnalysisRun 和 DerivedSignal 的输入引用。

另外，审计源码显示 `remove_episode` 会删除“该 Episode 是 `edge.episodes` 首项”的事实边；如果一条事实后来又挂载了其他支持 Episode，共享事实的删除语义必须通过 PoC 专门验证。这是基于源码的风险判断，不等同于已确认的生产缺陷。[`remove_episode`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/graphiti.py)、[删除测试](https://github.com/getzep/graphiti/tree/v0.29.3/tests)

## 检索、Agent 接口与部署

### 官方事实

Graphiti 对节点和事实边组合使用向量、全文/BM25 和 BFS，可选 RRF、MMR、Cross-Encoder、节点距离或 Episode mentions 重排。高级 `search_` 能返回节点、边、Episode 和社区；基础 `search` 主要返回事实边。[`search_config.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/search/search_config.py)

官方 MCP 支持 stdio 和 HTTP，暴露的能力包括 `add_memory`、节点/事实搜索、获取 Episode、增加三元组、获取 Episode 实体、删除 Episode/边、建社区和清图等。[`MCP README`](https://github.com/getzep/graphiti/blob/v0.29.3/mcp_server/README.md)

Graphiti 支持 Neo4j ≥ 5.26，也支持 FalkorDB、Neptune；官方 MCP Compose 是 Neo4j + MCP Server 两个服务，也可以通过环境变量连接既有 Neo4j。[`README`](https://github.com/getzep/graphiti/blob/v0.29.3/README.md)、[`docker-compose-neo4j.yml`](https://github.com/getzep/graphiti/blob/v0.29.3/mcp_server/docker/docker-compose-neo4j.yml)

### 工程判断

现成 MCP 是通用记忆工具，不足以保证投资分析的完整性。建议在其前面提供稳定领域接口：

```text
resolve_story_anchor(name)
get_chain_nodes(anchor_id)                    # 精确、穷举，不是 top-k
get_active_events(anchor_id, as_of, horizon)
get_event_evidence(event_ids)
get_propagation_rules(anchor_id, as_of, version)
get_node_neighbors(node_id, relation_types, max_depth)
revise_or_retract_event(event_id, revision)
write_analysis_run(result, evidence_refs, model_version, prompt_version)
```

对于已经结构化的事实，Graphiti 有 `add_triplet`，但官方 MCP 创建的三元组并不会自动产生 Episode provenance。需要来源审计的数据应优先用结构化 JSON Episode 摄取，或由领域写入服务同时创建 Episode 和事实关联，而不是裸调 `add_triplet`。

## LLM 依赖与“推导由谁完成”

### 官方事实

Graphiti 默认依赖 OpenAI 兼容的 LLM 和 embedding；也支持 Anthropic、Gemini、Groq 与兼容端点。官方说明强烈建议使用可靠的结构化输出模型，小模型或缺乏结构化输出的模型可能造成 Schema 错误和摄取失败。LLM 参与实体/关系抽取、去重、冲突识别、时间抽取、摘要和社区描述；embedding 参与解析与检索。[`README`](https://github.com/getzep/graphiti/blob/v0.29.3/README.md)、[`pyproject.toml`](https://github.com/getzep/graphiti/blob/v0.29.3/pyproject.toml)

### 工程判断

Graphiti 使用 LLM 的重点是“把动态信息维护成可检索的时态记忆”，不是“执行完整投研分析”。当 Codex 类 Agent 位于顶层时，合理分工是：

```text
Graphiti
  摄取 Event/Evidence → 实体解析 → 事实时间/失效 → 混合检索 → 来源回溯

Codex Agent
  确定锚点与周期 → 穷举产业链节点 → 读取相关规则与证据
  → 对每个节点推导 → 交叉检查正反证据 → 输出并记录 AnalysisRun
```

这会减少 KAG Planner 与 Agent 的重叠，但不能把所有数据治理交给 LLM。关键 ID、关系白名单、时间字段、方向枚举和来源引用必须在 Graphiti 写入前后由确定性代码校验。

## 生产成熟度判断

### 官方事实

Graphiti 是 Apache-2.0 项目，审计稳定版本为 0.29.3，要求 Python ≥ 3.10。仓库 CI 包含单元测试、Neo4j/FalkorDB 集成测试、MCP/live-server 测试、Pyright、Ruff 与 CodeQL；但官方 MCP README 仍将该服务标为 experimental。[`pyproject.toml`](https://github.com/getzep/graphiti/blob/v0.29.3/pyproject.toml)、[`.github/workflows`](https://github.com/getzep/graphiti/tree/v0.29.3/.github/workflows)、[`MCP README`](https://github.com/getzep/graphiti/blob/v0.29.3/mcp_server/README.md)

官方 README 明确区分自托管 Graphiti 与托管 Zep：OSS 版本的性能取决于自己的部署，需要自己实现工具、管理、扩展和运维；Zep 的 SLA、支持和托管引擎能力不能直接归属于 Graphiti OSS。

### 工程判断

Graphiti 已具备真实工程基础，但不能仅凭 README 判断它比 OpenSPG “更高效”或更适合生产。仓库没有针对“高频金融 Event + 双时态修订 + 10/50 节点产业链穷举”的官方基准。还应关注：

- 摄取中的多轮 LLM 调用导致的延迟、成本和非确定性；
- 同组并发、乱序 Event 和补录旧 Event 的正确性；
- 实体合并错误、冲突漏召回和错误失效的恢复方式；
- 默认遥测是否按部署政策通过 `GRAPHITI_TELEMETRY_ENABLED=false` 关闭；
- Neo4j 数据库隔离、备份、索引迁移和版本升级。

## 推荐的 PoC 架构

```text
PostgreSQL / Event / Evidence / 原始文档（权威数据）
                    │
       Tidewise Event Normalizer + Validator
       ID、类型、事件时间、来源版本、关系白名单
                    │
           Graphiti + 独立 Neo4j database（可重建投影）
       Episode / Entity / Fact / temporal history
                    │
              Tidewise Domain MCP
       精确产业链遍历、as-of、规则、证据、写回
                    │
              Codex 类 Agent + LLM
       逐节点推导、冲突检查、解释、任务编排
                    │
          AnalysisRun / DerivedSignal
```

### 同数据验收项

使用当前 ReasonSmoke 数据和一组真实 Event，同时测试 OpenSPG 与 Graphiti：

1. 新 Event 从摄取到可查询的 P50/P95 和 LLM token 成本；
2. 同名实体、重复事实、正反事实和补录旧 Event 的处理正确率；
3. `as_of + 短/中/长期 horizon` 是否无前视偏差；
4. 3、10、50 节点产业链是否 100% 穷举，路径和证据是否完整；
5. Event 修订/撤回后，旧事实和旧 DerivedSignal 是否正确失效；
6. 结论能否回溯到 Episode、Evidence、规则版本、模型和提示词；
7. 相同 Agent 提示词下的结论稳定性、总延迟、成本和运维复杂度。

## 最终建议

1. **将 Graphiti 纳入优先 PoC。** 对“Event 先进入系统，事实随时间修订，Agent 在分析时读取有效事件并自行推导”的目标，它比 OpenSPG 更自然；但权威 Event/指标仍应留在结构化主库。
2. **不要把它当成零成本替换。** Graphiti 不提供 OpenSPG 的强 Schema 与确定性规则层；这些能力要么由 Tidewise 领域层接管，要么继续保留 OpenSPG。
3. **让领域 Tool 合同先于底座选型。** Agent 不应直接依赖 Graphiti 通用 search 或 OpenSPG KGDSL；先固定精确遍历、时点检索、溯源和写回接口，才能公平 A/B。
4. **PoC 通过后，Graphiti 可以替代“OpenSPG + KAG 主控栈”的大部分位置**，但不是替代所有语义治理。最终很可能是 Graphiti 管动态事实，Tidewise 管业务合同，Codex Agent 管推导。

一句话判断：

> **若坚持“LLM 是推理执行者”，Graphiti 比 OpenSPG 更适合作为轻量、时态、Agent-native 的事件证据底座；若坚持“图平台必须执行强 Schema 和确定性规则”，OpenSPG 仍然更合适。**
