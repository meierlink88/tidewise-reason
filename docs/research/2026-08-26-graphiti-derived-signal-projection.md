# Graphiti 0.29.3 派生 Signal 投影方式研究

> 日期：2026-08-26  
> 版本边界：[`graphiti-core==0.29.3`](https://github.com/getzep/graphiti/releases/tag/v0.29.3)  
> 研究问题：当 Reasoning Server 已经得出“Signal：短期兑现强度偏弱 → 影响标准 ChainNode：AI服务器”时，应如何通过 Graphiti 持久化，同时保留来源、时效和标准锚点身份？

## 结论

对这个场景，Graphiti 官方 API 中最接近正确语义的是 **`add_triplet()`**：推理引擎已经确定了源节点、关系和目标节点，不需要再通过 `add_episode()` 让另一个 LLM 重新猜一次。Graphiti 官方把 `add_triplet()`定义为手动写入一个由两个节点和一条事实边构成的 fact triple，并说明它会对节点和边做解析/去重；既有节点可以直接使用既有 UUID。[Adding Fact Triples](https://help.getzep.com/graphiti/working-with-data/adding-fact-triples)、[`Graphiti.add_triplet()`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/graphiti.py#L1645-L1736)

推荐图形是：

```text
(Signal:Entity:Signal)
  -[:RELATES_TO {
      name: "AFFECTS_CHAIN_NODE",
      fact: "AI服务器节点的短期兑现强度偏弱",
      valid_at: ...,
      invalid_at: ...,
      reference_time: ...,
      episodes: [supporting_event_episode_uuid, ...],
      direction: "COOLING",
      horizon: "SHORT_TERM",
      confidence: 0.72,
      reasoning_run_id: "...",
      source_event_ids: ["EVT...", ...]
  }]->(AI服务器:Entity:ChainNode)
```

Neo4j 中的物理关系类型仍是 Graphiti 的 `RELATES_TO`；领域关系名称放在 `name=AFFECTS_CHAIN_NODE`，自然语言结论放在 `fact`。`EntityEdge` 原生保存 `name`、`fact`、`episodes`、`valid_at`、`invalid_at`、`expired_at`、`reference_time` 和自定义 `attributes`。[`EntityEdge` 数据模型](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/edges.py#L263-L356)

但 **Graphiti 0.29.3 没有一个公开的单一 API，可以同时完成“保存一个派生 Episode + 使用指定 UUID 写入确定性 fact triple + 自动构建完整 Episode 双向来源索引”**。因此 Reasoning Server 仍需要一个很薄的 `DerivedSignalProjector`，组合 Graphiti 的公开对象/API；不需要修改 Graphiti 源码，也不应直接用裸 Cypher 作为正常写入路径。

## 为什么不是只调用 `add_episode()`

`add_episode()`的官方定位是将一次数据摄取保存成 Episode，再由 LLM 抽取节点和关系；Episode 通过 `MENTIONS` 连接其识别出的实体，并为事实提供来源。[Adding Episodes](https://help.getzep.com/graphiti/core-concepts/adding-episodes)

0.29.3 的实现会依次完成：历史 Episode 上下文获取、实体/边抽取、实体/边解析与去重、属性和时间提取、矛盾事实失效、embedding 以及批量写图；最后将事实 UUID 写入 `EpisodicNode.entity_edges`，将 Episode UUID 写入 `EntityEdge.episodes`。[`add_episode()`入口](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/graphiti.py#L980-L1223)、[`_process_episode_data()`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/graphiti.py#L685-L758)、[事实的 Episode attribution](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/utils/maintenance/edge_operations.py#L270-L320)

因此，对尚未结构化的 Event，`add_episode()`是正确入口；但对已经完成的投研推导，它有两个问题：

1. 推导结果已经明确，再让 Graphiti LLM 重做关系抽取会增加语义漂移；
2. `entity_types`、`edge_types` 和 `edge_type_map` 能约束领域类型和端点类型组合，但不能把目标限制为某个既有 ChainNode UUID。[Custom Entity and Edge Types](https://help.getzep.com/graphiti/core-concepts/custom-entity-and-edge-types)、[`add_episode()`参数](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/graphiti.py#L980-L1059)

只用 `add_episode()`并非不可行：可将完整推导写成 `EpisodeType.json`，定义 `Signal`、`ChainNode` 和 `SignalAffectsChainNode` 类型，让 Graphiti 自动保留来源。但它更适合“允许 Graphiti 解析锚点”的场景。Tidewise 要求结果严格落到已预制 ChainNode，不能把概率式实体解析当作最终身份校验。

## 为什么 `add_triplet()`更适合已经成立的推导

官方文档明确支持：既有实体使用既有 UUID，新实体使用新 UUID，然后构造 `EntityEdge` 并调用 `add_triplet()`；也可以直接复用 Graphiti 搜索返回的节点对象。[Adding Fact Triples](https://help.getzep.com/graphiti/working-with-data/adding-fact-triples)

0.29.3 源码表明 `add_triplet()`会：

- 为节点名称和事实生成 embedding；
- 优先按 UUID 读取端点；找不到时才进入实体解析；
- 查找同端点关系和全图相关关系；
- 执行事实去重和矛盾失效；
- 写入节点和事实边。

来源：[`Graphiti.add_triplet()`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/graphiti.py#L1645-L1736)、[`resolve_extracted_edge()`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/utils/maintenance/edge_operations.py#L623-L847)。

这与“Reasoning Server 已确定 Signal 和标准锚点，再把结果交给 Graphiti 做图存储、embedding、事实解析和时态维护”的职责边界一致。

### 0.29.3 的来源限制

`add_triplet()`返回值只有 nodes 和 edges，不创建真实 Episode，也不创建 `MENTIONS`。其内部为事实解析临时构造了一个空 `EpisodicNode`，但没有保存它。[`AddTripletResults` 与实现](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/graphiti.py#L117-L130)、[`add_triplet()`临时 Episode](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/graphiti.py#L1715-L1736)

另外，当新 fact 被解析为已有 fact 时，0.29.3 会向已有边的 `episodes` 追加传给 resolver 的 Episode UUID；在 `add_triplet()`路径中，这个 UUID 来自上述未保存的临时 Episode。这意味着不能只靠裸 `add_triplet()`保证重复关系的来源链完整。[完全相同事实复用逻辑](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/utils/maintenance/edge_operations.py#L681-L704)

所以 Tidewise 投影器需要在 `add_triplet()`返回后做一次公开模型级的来源归一化：把真实支持 Event Episode UUID 合并到最终 `EntityEdge.episodes`，保存返回边；如系统依赖 `get_episode_entities()`或 `remove_episode()`的双向索引，还应把最终 Fact UUID 合并到相关 `EpisodicNode.entity_edges`。这些类都有官方支持的 CRUD `save()`，但调用方要自行承担一致性。[CRUD Operations](https://help.getzep.com/graphiti/working-with-data/crud-operations)、[`EpisodicNode`/`EntityEdge` 模型](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/nodes.py)、[`EntityEdge.save()`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/edges.py#L335-L382)

## 来源与时间应该如何表达

### `episodes`

放入真正支撑本次 Signal 的 **Event Episode UUID**，不是 Evidence ID，也不是 Data Service Event ID。业务 ID 另外放入 `attributes.source_event_ids`，便于跨系统审计。

如果 Signal 由一次独立推理运行产生，建议同时记录：

- `reasoning_run_id`
- `methodology_version`
- `model_id`
- `source_event_ids`
- `source_fact_uuids`
- `rationale`

不建议把原始 Event Episode 到 Signal 强行建成 `MENTIONS`：Event 原文并没有“提到”后续派生的 Signal。Graphiti 对事实来源的原生表达是 `EntityEdge.episodes`；`MENTIONS`表达的是 Episode 中识别到的实体。[Episode/MENTIONS 语义](https://help.getzep.com/graphiti/core-concepts/adding-episodes)、[`EntityEdge.episodes`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/edges.py#L263-L282)

### 时间字段

- `created_at`：Fact 实际写入图谱的时间，由系统产生；
- `reference_time`：本次推理的 `as_of` 时间，即推理引擎看到信息的截点；
- `valid_at`：Signal 开始被认为对该节点成立的时间；
- `invalid_at`：Signal 已知不再成立的时间。若只有“短期”分类、没有可信截止时点，不应伪造它；先留空，由后续相反 Signal 或复核结果使旧事实失效；
- `expired_at`：Graphiti 在系统层面对旧事实执行失效处理的时间，不应拿来表达业务影响周期。

Graphiti 的字段定义见 [`EntityEdge`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/edges.py#L263-L282)；其矛盾处理会给旧边设置 `invalid_at`/`expired_at`，而不是覆盖历史事实。[edge resolution/invalidation](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/utils/maintenance/edge_operations.py#L623-L847)

因此“影响周期”还应保留显式领域属性，例如：

```json
{
  "horizon": "SHORT_TERM",
  "impact_start_at": "2026-08-26T07:00:00Z",
  "expected_until": null,
  "direction": "COOLING",
  "confidence": 0.72
}
```

`horizon` 是投研分类；`valid_at/invalid_at` 是 Graphiti 的事实有效区间。两者有关，但不能混为一个字段。

### `group_id`

Signal、ChainNode、Fact 边和支持它的 Event Episode 应使用当前投研图同一个 `group_id`。Graphiti 官方将 `group_id`定义为图命名空间，节点和边必须保持一致；跨 namespace 组合需要应用层分别查询再合并，不适合用来隔离同一投研图里的数据类型。[Graph Namespacing](https://help.getzep.com/graphiti/core-concepts/graph-namespacing)

## 四种写入方式对比

| 方式 | Graphiti 行为 | 对本场景的判断 |
|---|---|---|
| `add_episode()` | 保存 Episode，LLM 抽取/解析节点和事实，自动建立 MENTIONS、来源和时态事实 | 适合原始 Event；派生关系只有在允许概率式实体解析时使用 |
| `add_triplet()` | 调用方给定两端和 Fact，Graphiti生成 embedding 并做解析、去重、失效 | **派生 Signal→标准 ChainNode 的首选入口**；需补齐 0.29.3 来源归一化 |
| `EntityNode`/`EntityEdge.save()` | 官方 CRUD，按 UUID find-or-create/update | 只作为投影器补齐来源索引或初始化/修复；单独使用会绕过 `add_triplet()`的 embedding、去重和失效流程 |
| driver/Cypher | 直接操作 Neo4j 物理模型 | 不作为业务写入方式；会绕过 Graphiti provider 抽象和维护逻辑，只留给迁移、诊断或紧急修复 |

## Tidewise 推荐执行顺序

1. Reasoning Pipeline 从 48 小时 Event/Fact 和 Storyline/产业链拓扑中产生结构化 Variable、Signal、方向、周期、置信度和推理依据。
2. 从图谱按业务 ID/UUID取得唯一标准 `ChainNode`；找不到或出现多个候选就进入 review，不创建新 ChainNode。
3. 为 Signal 使用稳定业务 UUID，构造 `EntityNode(labels=["Entity", "Signal"])`。
4. 构造 `EntityEdge(name="AFFECTS_CHAIN_NODE")`，填入自然语言 `fact`、时间字段、真实 Event Episode UUIDs 和推理审计 attributes。
5. 调用 `graphiti.add_triplet(signal_node, edge, chain_node)`。
6. 检查返回端点 UUID 必须等于预期 Signal 和 ChainNode UUID；检查返回关系没有被解析成错误端点。
7. 对返回 Fact 执行来源归一化：移除不存在的临时 Episode UUID，合并真实支持 Event Episode UUID，并通过 Graphiti 公开 CRUD 保存；如果需要 Episode→Fact 双向反查，同步 `EpisodicNode.entity_edges`。
8. 用 Graphiti 搜索和 Neo4j Browser 验证：事实可按文本/节点召回，`episodes`可追溯到 Event，时间过滤能区分当前/历史 Signal。

这个组合不要求修改 Graphiti 源码，也没有必要自己重写 `add_episode()`；它只是针对 Graphiti 0.29.3 的一个受控派生事实投影器。

## 最小验收条件

- 图中只有一个目标 `AI服务器:ChainNode`，UUID 与底图一致；
- Signal 是独立、可追踪的领域实体；
- `Signal -[RELATES_TO/name=AFFECTS_CHAIN_NODE]-> ChainNode` 可被 Graphiti fact search 召回；
- Fact 的 `episodes`只包含真实存在且参与推导的 Event Episode UUID；
- Fact 具备 `reference_time`、`valid_at` 及领域影响周期属性；
- 同一推导重复投影不会产生重复 Signal 或 Fact；
- 相反或更新 Signal 不覆盖历史，而是创建新 Fact 并使旧 Fact 进入失效状态；
- 不因投影派生关系而创建新的同名 ChainNode。
