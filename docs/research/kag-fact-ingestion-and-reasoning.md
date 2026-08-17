# KAG v0.8.0 事实入库、推理依赖与 PostgreSQL 同步适配性

## 结论

OpenSPG/KAG **适合做观潮家 PostgreSQL event 事实的下游语义图谱与推理索引，但不适合直接承担开箱即用的 PostgreSQL 周期复制/CDC 职责**。

- **适合的部分**：OpenSPG 原生建模 `EventType`，KAG 可把结构化记录映射成事件节点和关系，写入接口支持 `UPSERT` 与 `DELETE`，Solver 会用图事实、图自由层和原始 Chunk 做混合检索/推理。
- **不足的部分**：v0.8 中 PostgreSQL/JDBC 数据源枚举和元数据客户端分支被注释；KAG 内置 Scanner 没有 PostgreSQL；未提供 WAL/LSN、水位、tombstone、自动差异删除或 exactly-once 语义。
- **建议落位**：PG 继续做事实 source of truth；在 PG 与 OpenSPG 之间放一个观潮家拥有的同步/清洗适配器，负责增量读取、契约校验、去重、来源与版本记录、删除传播和对账；适配器再调 KAG `KGWriter` 或 OpenSPG Graph API。

## 证据范围与标注

本笔记锁定两个官方发布点：

- KAG `v0.8.0`，commit `de777280584fec0c3d888804eaafa86f169f13db`；
- OpenSPG `v0.8`，commit `ceeb3ef549df79ca4c4878e7ff452c73584991f3`。

下文区分：

- **[官方说明]**：README、示例说明或发布说明直接声称的能力；
- **[源码事实]**：v0.8.0/v0.8 实现中可直接观察的接口或行为；
- **[工程推断]**：基于上述实现得出的适配性判断，不当作官方产品承诺。

## KAG 推理是否依赖事实数据

### 文档声称

**[官方说明]** KAG 被定义为基于 OpenSPG 引擎和 LLM 的逻辑推理问答框架，强调 KG 的“逻辑性和事实性”；它把精确匹配、文本检索、数值计算和语义推理组合起来，并互索引图结构与原始文本 Chunk。参见 [KAG v0.8.0 README_cn，第 28–37、45–59、157–165 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md#L28-L37)。

### 源码中的实际依赖

**[源码事实]** 供应链示例的 Solver 同时配置了三类检索器：`kg_cs` 精确图检索、`kg_fr` 模糊图/图到 Chunk 检索、`rc` 向量 Chunk 检索，三者均指向 OpenSPG 的 Graph/Search API，而不是 PostgreSQL。参见 [supplychain `kag_config.yaml`，第 38–117 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/kag_config.yaml#L38-L117)。

**[源码事实]** `OpenSPGGraphApi` 在初始化时构造 `ReasonerClient` 和 `GraphClient`，并通过 GQL/Reasoner 获取实体及一跳图；`OpenSPGSearchAPI` 通过 `SearchClient` 做文本和向量检索。参见 [`openspg_graph_api.py`，第 64–84、156–202、239–266 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/tools/graph_api/impl/openspg_graph_api.py#L64-L84) 和 [`openspg_search_api.py`，第 8–51 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/tools/search_api/impl/openspg_search_api.py#L8-L51)。

**[工程推断]** KAG 的图检索和符号推理直接依赖已写入 OpenSPG 的事实；如果 event 未同步、已过期或错误，图检索/规则推理就会使用这些过期或错误事实。它可以退到 Chunk/LLM 路径，但这不等于实时查询 PG。

## 事实如何进入 KAG/OpenSPG

### 结构化事实路径

**[源码事实]** 默认结构化 Builder Chain 是 `mapping -> (optional vectorizer) -> writer`；它并不自带 PostProcessor。参见 [`DefaultStructuredBuilderChain`，第 32–73 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/default_chain.py#L32-L73)。

**[源码事实]** `SPGTypeMapping` 先从 OpenSPG 加载 Schema，校验目标类型/字段，然后把源记录的 `id`、`name`、属性和引用型属性装配为节点与边；它也允许为属性提供自定义 `link_func`。参见 [`spg_type_mapping.py`，第 39–98、108–174、198–214 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/mapping/spg_type_mapping.py#L39-L98)。

**[官方说明 + 源码事实]** 官方供应链示例明确说结构化数据需要“字段 mapping + 实体链指”；示例用 `CSVScanner -> SPGTypeMapping -> BatchVectorizer -> KGWriter`导入事件。参见 [供应链 Builder 说明，第 6–55 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/builder/README_cn.md#L6-L55) 和 [`indexer.py`，第 101–150、158–195 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/builder/indexer.py#L101-L150)。

**[源码事实]** `KGWriter` 把 `SubGraph` 通过 KNEXT `GraphClient.write_graph` 发给 OpenSPG，默认操作为 `UPSERT`，也支持 `DELETE`。参见 [`kg_writer.py`，第 27–58、105–137 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/writer/kg_writer.py#L27-L58) 和 [`GraphClient.write_graph`，第 66–74 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/knext/graph/client.py#L66-L74)。

### 非结构化文本路径

**[源码事实]** 默认非结构化链是 `reader -> splitter -> extractor -> vectorizer -> optional post_processor -> writer`。参见 [`DefaultUnstructuredBuilderChain`，第 76–121 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/default_chain.py#L76-L121)。

**[源码事实]** `SchemaConstraintExtractor` 面向 Chunk 调用 LLM 做 NER、实体标准化、关系抽取和可选的事件抽取，再把节点/边与源 Chunk 通过 `source` 边关联。参见 [`schema_constraint_extractor.py`，第 33–90、267–302、416–469、529–558 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/extractor/schema_constraint_extractor.py#L33-L90)。

**[工程推断]** PG 中已结构化、已审定的 event 事实应走直接 mapping，不应经过 LLM 再抽取一次；LLM 抽取更适合文档中的候选事实。

## Event 建模能力

**[源码事实]** OpenSPG 把事件定义为具有时间特征的特殊实体，可表达时间、地点、主体和客体；`EventType` 提供 time/subject/object 属性分组。参见 [`EventType.java`，第 25–85 行](https://github.com/OpenSPG/openspg/blob/v0.8/server/core/schema/model/src/main/java/com/antgroup/openspg/core/schema/model/type/EventType.java#L25-L85)。

**[源码事实]** 系统为事件定义内建 `eventTime`，值类型为 `STD.Timestamp`，注释要求 Unix timestamp；Schema 检查要求 EventType 至少包含 subject 分组属性。参见 [`BuiltInPropertyEnum.java`，第 28–39 行](https://github.com/OpenSPG/openspg/blob/v0.8/server/core/schema/service/src/main/java/com/antgroup/openspg/server/core/schema/service/type/model/BuiltInPropertyEnum.java#L28-L39) 和 [`EventTypeChecker.java`，第 22–54 行](https://github.com/OpenSPG/openspg/blob/v0.8/server/core/schema/service/src/main/java/com/antgroup/openspg/server/core/schema/service/alter/check/EventTypeChecker.java#L22-L54)。

**[源码事实]** `EventRecord` 以显式 `eventId` 作为记录 ID。参见 [`EventRecord.java`，第 24–51 行](https://github.com/OpenSPG/openspg/blob/v0.8/builder/model/src/main/java/com/antgroup/openspg/builder/model/record/EventRecord.java#L24-L51)。

**[官方示例]** 供应链示例直接把 `ProductChainEvent.csv` 的 `id,name,subject,index,trend` 导入 `ProductChainEvent: EventType`，并使用 `leadTo` 规则派生公司事件。参见 [事件数据说明，第 86–105 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/builder/data/README_cn.md#L86-L105)、[事件 Schema，第 205–228 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/SupplyChain.schema#L205-L228) 和 [`EventKGWriter`，第 9–21 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/builder/operator/event_kg_writer_op.py#L9-L21)。

**[源码事实]** `writerGraph` 收到 `enableLeadTo=true` 时会运行 `ReasonProcessor`，并把推理产生的记录再写回图存储。参见 [`GraphController.java`，第 165–217 行](https://github.com/OpenSPG/openspg/blob/v0.8/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi/GraphController.java#L165-L217)。

**[工程推断]** 观潮家应把“PG 声明的原始事实”与“OpenSPG 规则派生事实”分开建模，至少保留 `fact_kind/source/source_event_id/source_version/derived_by_rule`，避免推理结果反向被当作源系统声明。

## 增量、更新与删除语义

**[源码事实]** OpenSPG 的记录操作枚举明确定义：`UPSERT` 是“存在则更新，否则插入”，`DELETE` 是“存在则删除”。参见 [`RecordAlterOperationEnum.java`，第 16–21 行](https://github.com/OpenSPG/openspg/blob/v0.8/builder/model/src/main/java/com/antgroup/openspg/builder/model/record/RecordAlterOperationEnum.java#L16-L21)。

**[源码事实]** Graph HTTP API 分别暴露节点/边的 upsert 和 delete，`writerGraph` 也接受 `UPSERT OR DELETE`。参见 [`GraphController.java`，第 109–167 行](https://github.com/OpenSPG/openspg/blob/v0.8/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi/GraphController.java#L109-L167) 和 [`WriterGraphRequest.java`，第 19–30 行](https://github.com/OpenSPG/openspg/blob/v0.8/server/api/facade/src/main/java/com/antgroup/openspg/server/api/facade/dto/service/request/WriterGraphRequest.java#L19-L30)。

**[源码事实]** Neo4j 实现按 `label + id` 执行 `MERGE`，再用 `SET n += properties` 合并属性；删除则按 `label + id` 执行 `DETACH DELETE`。参见 [`Neo4jDataUtils.java`，第 49–143 行](https://github.com/OpenSPG/openspg/blob/v0.8/common/util/src/main/java/com/antgroup/openspg/common/util/neo4j/Neo4jDataUtils.java#L49-L143)。

**[工程推断]**

- 要做幂等同步，必须用 PG 中稳定的业务事件 ID；同一 ID 重放会命中同一节点。
- `SET +=` 是属性合并，一次 UPSERT 中缺少的旧属性不会自动清除；“全量快照里消失的行”也不会自动被删除。
- 因此同步器必须显式处理 tombstone/软删除，并在需要“完全替换”时先删旧边/属性或采用新版本事件节点。

## PostgreSQL 数据源与周期调度

### 连接器现状

**[源码事实]** OpenSPG v0.8 的 `DataSourceType` 实际启用的是 ODPS（batch）和 SLS（stream）；PostgreSQL 与其 JDBC driver 处在注释中。参见 [`CommonEnum.java`，第 29–74 行](https://github.com/OpenSPG/openspg/blob/v0.8/server/common/model/src/main/java/com/antgroup/openspg/server/common/model/CommonEnum.java#L29-L74)。

**[源码事实]** `DataSourceMetaFactory` 中 PostgreSQL/JDBC 分支同样被注释，实际只为 ODPS 构造专用元数据客户端。参见 [`DataSourceMetaFactory.java`，第 20–43 行](https://github.com/OpenSPG/openspg/blob/v0.8/server/common/service/src/main/java/com/antgroup/openspg/server/common/service/datasource/meta/client/DataSourceMetaFactory.java#L20-L43)。

**[源码事实]** KAG v0.8.0 导出的 Scanner 包括 CSV、JSON、文件/目录、语雀、ODPS 和 SLS，没有 PostgreSQL Scanner。参见 [`kag.builder.component.__init__`，第 34–47、69–103 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/__init__.py#L34-L47)。

**[源码事实]** Scanner 是可扩展抽象；自定义实现只需实现 `load_data`，也可覆写 `generate` 做流式产出。参见 [`ScannerABC`，第 20–58、85–99 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/interface/builder/scanner_abc.py#L20-L58)。

### 调度现状

**[源码事实]** OpenSPG 通用 Scheduler 支持 `PERIOD/ONCE/REAL_TIME`，周期任务需要 Quartz cron，并按 cron 生成执行实例。参见 [`SchedulerJob.java`，第 47–72 行](https://github.com/OpenSPG/openspg/blob/v0.8/server/core/scheduler/model/src/main/java/com/antgroup/openspg/server/core/scheduler/model/service/SchedulerJob.java#L47-L72) 和 [`SchedulerServiceImpl.java`，第 84–127 行](https://github.com/OpenSPG/openspg/blob/v0.8/server/core/scheduler/service/src/main/java/com/antgroup/openspg/server/core/scheduler/service/api/impl/SchedulerServiceImpl.java#L84-L127)。

**[源码事实]** Builder 调度 DAG 包含 Reader、Splitter、Extractor、Vectorizer、Alignment 和 Writer；只有数据源是 ODPS 时才加入分区预检查。参见 [`KagBuilderTranslate.java`，第 92–213 行](https://github.com/OpenSPG/openspg/blob/v0.8/server/core/scheduler/service/src/main/java/com/antgroup/openspg/server/core/scheduler/service/translate/builder/KagBuilderTranslate.java#L92-L213)。

**[工程推断]** “有通用 cron Scheduler”不等于“有 PostgreSQL 增量同步”。可以扩展 OpenSPG 内部 Scheduler/Scanner，但这会把 PG 连接、凭据、水位、重试和删除语义耦合进 KAG 运行时；对观潮家更稳妥的是外部同步器调度。

## 是否有类似 Semantica 的清洗链路

答案是：**有可组合的构建期标准化/轻量清洗能力，但不是完整的事实治理或 CDC 清洗平台。**

| 能力 | v0.8.0 证据 | 判断 |
|---|---|---|
| 字段标准化/关联 | `SPGTypeMapping` 支持字段 mapping 与自定义 `link_func` | 结构化事实可用，但规则需项目自己写 |
| Schema 约束抽取 | `SchemaConstraintExtractor` 做 NER、标准化、关系/事件抽取 | 适合文本候选事实，不建议用于改写已审定 PG 事实 |
| 无效数据过滤 | `KAGPostProcessor` 过滤缺 id/label 的节点和缺 label 的边，未知节点类型改为 `OTHER_TYPE` | 轻量结构检查，不是业务契约校验 |
| 实体对齐 | `KAGPostProcessor` 可按向量相似度加 `similar` 边，也可借助外部图 | 是实体链指/对齐，不是确定性主数据合并 |
| Chunk 内去重 | Schema 抽取器按实体名去重并合并同 id/name/label 节点属性 | 局部去重，不是跨批次冲突解决 |
| 溯源 | 非结构化抽取会把节点通过 `source` 边连到 Chunk | 有文本片段来源；结构化链不会自动建 PG row/version 溯源 |
| 治理闭环 | 在检查的 v0.8.0 官方代码中，未找到通用隔离区、审核/发布门、字段级 lineage、冲突策略、PG CDC cursor/tombstone 组件 | **不等价于 Semantica 式完整治理链**；这是源码审查推断，不是官方否定性声明 |

`KAGPostProcessor` 证据见 [`kag_postprocessor.py`，第 27–56、81–105、107–195 行](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/postprocessor/kag_postprocessor.py#L27-L56)。需要特别注意：它在默认非结构化链中是 optional，而默认结构化链根本不包含它。

## 建议的观潮家同步边界

```text
PostgreSQL (authoritative event facts)
  -> Tidewise-owned sync adapter / CDC consumer
     -> cursor + overlap window / outbox LSN
     -> contract validation + deterministic normalization
     -> stable-ID dedup + source/version/provenance
     -> explicit UPSERT / DELETE commands
  -> OpenSPG EventType graph
  -> KAG graph/chunk indexes and Solver
```

### 同步器应拥有的职责

1. **增量位点**：低频同步可用 `(updated_at, primary_key)` 复合水位 + 小量重叠回扫；更高实时性用 outbox/WAL CDC。
2. **幂等键**：`event.id = source_system + source_event_id`，不用文本名称或批次时间生成随机 ID。
3. **契约与时间**：至少校验 `eventTime` Unix timestamp、subject、事件类型、引用实体 ID；建议同时保留 `occurred_at`、`observed_at`、`source_version`。
4. **变更语义**：区分 append-only event、可修正 fact 与撤回/tombstone；删除必须显式调 OpenSPG `DELETE`。
5. **事实溯源**：保留 `source`、`source_table`、`source_pk`、`source_version`、`ingested_at`、`payload_hash`；规则派生事实另加 `derived_by_rule`。
6. **可观测与对账**：记录每批读取/通过/拒绝/upsert/delete 数量，定期按 ID 和 hash 对账 PG 与 OpenSPG。
7. **安全边界**：PG 使用只读账号，凭据留在同步器运行环境，不写入 KAG 项目配置或图谱。

### 选型判断

| 需求 | 适配性 |
|---|---|
| 每小时/每日追加 event，稳定主键，少删除 | **适合**，外部水位同步 + `UPSERT` 即可 |
| event 会修正、撤回、关系会变更 | **可用但需自建变更规则**，特别是旧属性/旧边清理和 tombstone |
| PostgreSQL 开箱即用的周期整库同步 | **不适合**，v0.8 无启用的 PostgreSQL 连接器 |
| 低延迟 WAL CDC、exactly-once、自动 schema evolution | **不是 KAG v0.8.0 的开箱能力** |
| 基于事件、实体关系和专家规则的多跳推理 | **是 OpenSPG/KAG 的强项** |

## 最终建议

对观潮家，应把 OpenSPG/KAG 定位为 **derived semantic read model**，而不是 PG replica：

- 第一阶段先用外部定时任务读 `updated_at + id`，进行确定性映射后批量 upsert，同时实现显式删除和每日对账。
- 只把通过观潮家事实契约的 event 写入 OpenSPG；原始 payload/失败记录保留在同步器的审计存储中。
- 当变更量、延迟或删除要求超过轮询能力时，再升级到 outbox/WAL CDC，而无需改变 OpenSPG 作为下游语义索引的边界。
