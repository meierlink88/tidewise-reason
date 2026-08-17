# OpenSPG + KAG 0.8 规模与查询性能评估

> 评估日期：2026-08-13
> 场景：全球政治经济事件驱动投研；约 3,000 个 event/日、3,000 次推理命题/日；
> 稳定实体包括联盟、国家、机构、市场、板块、概念、公司、股票、指数、行业、产业链、
> 产业链节点、商品、产品和变量定义；动态数据包括 Event、Variable Signal、影响关系、
> 推导结果与证据 Chunk。

## 结论

OpenSPG + KAG 的技术方向可以承载这个场景的早期和中期规模，但官方 OpenSPG 0.8
单机 Compose 不能直接视为超大图谱生产方案。

- 每天 3,000 次写入和 3,000 次推理的平均吞吐很低，不是主要矛盾。
- 稳定实体主数据预计在十万到低百万节点级，也不是主要矛盾。
- 真正决定规模的是每个 Event 展开的 Signal、证据 Chunk、向量和关系数量，以及保留年限。
- 5 年后，合理但未治理的数据模型就可能达到数千万至一亿动态节点、约一亿至三亿关系，
  再叠加数千万向量。此时默认单机部署会出现内存、I/O、热点邻接和混合检索竞争。
- Neo4j Enterprise 可以通过大内存/NVMe、集群和 secondary 做读扩展；但 OpenSPG 官方
  0.8 资料没有给出经过验证的 OpenSPG Server 集群、分片、十亿级图谱或高并发 KAG
  推理基准，因此这些能力必须通过生产化改造和自有压测确认。

因此建议继续用 OpenSPG + KAG 做 PoC，但把它定位为从 PostgreSQL 派生的语义推理读模型，
从第一天就控制图的时间范围、查询展开和向量数量。

## 架构事实

OpenSPG 0.8 官方 Compose 是一个 OpenSPG Server，加单实例 MySQL、Neo4j 和 MinIO。
Neo4j 同时被配置为 `graphstore` 与 `searchengine`，Server JVM 为 2–8 GB，Neo4j page cache
仅 1 GB。这是方便部署的验证拓扑，不是 HA/水平扩展拓扑。
[官方 Compose](https://github.com/OpenSPG/openspg/blob/v0.8/dev/release/docker-compose.yml#L365-L495)

KAG 0.8 在应用期会根据已构建的索引调用图、Chunk、文档 Retriever，再接入 Solver；
官方列出的集成方式是 HTTP API、MCP 和页面嵌入。发布说明讨论效果、响应延迟和流式稳定性，
但没有公开节点/关系规模、QPS、P95/P99 或十亿级存储基准。
[KAG 0.8 发布说明](https://github.com/OpenSPG/KAG/releases/tag/v0.8.0)

KAG 的 OpenSPG 客户端把精确图查询、文本搜索和向量搜索都发到 OpenSPG Server；图推理
客户端调用同步 Reasoner API。KAG 内部会并行部分 Retriever，但一次完整推理仍可能包含
问题解析、图查询、向量检索和多轮 LLM 调用。
[Graph API](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/tools/graph_api/impl/openspg_graph_api.py)
[Search API](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/tools/search_api/impl/openspg_search_api.py)
[Reasoner Client](https://github.com/OpenSPG/KAG/blob/v0.8.0/knext/reasoner/client.py)

本地环境核查结果：Neo4j 5.25.1 Enterprise、`1 primary / 0 secondary`、
`record-aligned-1.1` store、1 GB page cache；OpenSPG Server 与 Neo4j 均为单实例，且图与
搜索共用该 Neo4j。当前图还没有 ABox 数据，因此本地状态只能证明拓扑，不能证明容量。

## 场景规模粗估

下表不是官方上限，而是容量规划假设。稳定实体主数据先按 30 万至 200 万节点、300 万至
3,000 万关系估算。动态层按每个 Event 产生 5–20 个 Signal/证据/推导节点、20–50 条关系：

| 保留期 | Event | 动态节点 | 动态关系 |
| --- | ---: | ---: | ---: |
| 1 年 | 约 110 万 | 约 550 万–2,200 万 | 约 2,200 万–5,500 万 |
| 5 年 | 约 548 万 | 约 2,700 万–1.10 亿 | 约 1.10 亿–2.74 亿 |
| 10 年 | 约 1,095 万 | 约 5,500 万–2.19 亿 | 约 2.19 亿–5.48 亿 |

KAG 的 KnowledgeUnit、Chunk、Outline、Summary、AtomicQuery 等索引会继续产生存储放大，
所以不能只用业务节点与边估算物理数据量。

若每个 Event 建 5–20 个 1024 维 float32 向量，5 年约为 2,700 万–1.10 亿个向量；仅向量
值约 110–440 GB，还未计算节点属性、HNSW/Lucene 索引、图关系、副本和备份。向量通常会
比国家、公司、行业等主数据更早成为容量与内存瓶颈。

3,000 次推理/日的全天平均 QPS 约 0.035；即使集中在 8 小时内也只有约 0.10 QPS。
但 QPS 会掩盖复杂度：一条深度命题可能被 Planner 分解成多个子问题，并触发多次图查询、
向量检索和 LLM 调用。应按峰值并发与每个命题的子查询数压测，而不是按日请求数判断。

## 能支撑到什么程度

### 适合 OpenSPG + KAG 的部分

- 十万到低百万级稳定实体及其类型化关系。
- 每日数千 Event 的增量 UPSERT；这个平均写入速率对 Neo4j 很低。
- 有明确起点、时间窗口、关系白名单和 1–3 跳边界的图查询。
- 将规则推导与复杂影响传播异步执行，物化有限的结论或直接影响关系。
- KAG 对图事实、证据 Chunk 和 LLM 的混合求解。

Neo4j 的物理格式上限远高于本场景的粗估；当前 Enterprise 推荐的 block format 支持
`2^48` 节点且关系无定义上限，但物理格式上限不代表可接受的查询性能。
[Neo4j store formats](https://neo4j.com/docs/operations-manual/current/database-internals/store-formats/)

Neo4j Enterprise 集群可用 primary 提供故障容错、secondary 分担读取；这能扩展读负载，
但不自动消除单个图中高扇出遍历的计算量。
[Neo4j clustering](https://neo4j.com/docs/operations-manual/current/clustering/introduction/)

### 默认架构不能证明的部分

- 十亿级关系或上亿向量下的 OpenSPG/KAG 端到端 P95/P99。
- OpenSPG Server 多副本、任务调度和推理会话的 HA 行为。
- OpenSPG 对 Neo4j cluster routing、读写分离和故障切换的官方生产认证。
- 一个图中同时进行批量构建、规则推理、向量检索和交互查询时的资源隔离。
- KAG 深度推理在 10、50、100 个并发命题下的模型配额、排队和超时行为。

所以“Neo4j 能存很大”不能直接推出“OpenSPG 开箱即用能稳定支撑超大图谱”。

## 最可能的性能瓶颈

1. **热点实体的关系爆炸**：中国、美国、半导体、AI、原油或大型公司会连接大量 Event。
   从这些节点做无时间过滤的 2–3 跳遍历，会发生组合爆炸。
2. **图与向量共用 Neo4j**：遍历、批量写入、全文/向量检索争用同一 page cache、I/O、
   transaction memory 和 CPU。
3. **向量索引膨胀**：把每条行情、每个变量观测和每个重复新闻 Chunk 都向量化，会比图
   主数据更早耗尽内存与磁盘。
4. **宽 KGDSL/Cypher 规则**：未锚定实体、未限制时间、可变长度路径无上限，容易扫描或
   展开大部分图。Neo4j 官方也建议尽早过滤并限制 variable-length pattern。
   [Neo4j query tuning](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/query-tuning/)
5. **KAG/LLM 链路延迟**：完整命题延迟通常由 Planner、Retriever fan-out 和多轮模型调用
   主导，而不是一次 Neo4j 点查。
6. **推导事实膨胀**：若每次规则运行都把所有中间路径和结论永久物化，图会出现二次甚至
   指数级增长。
7. **单机故障与恢复**：默认 Compose 无图数据库副本，也没有证明 Server 多副本调度一致性。

## 观潮家的建模与运行边界

### 应该入图

- 联盟、国家、机构、市场、板块、概念、公司、证券、指数、行业、产业链/节点、商品、产品；
- 产能、技术、成本、需求、利润等受控变量的定义；
- 经过治理的 Event、Variable Signal、主体/客体、直接影响、证据引用、来源、有效时间、
  置信度和规则版本；
- 对高频事实做过聚合的状态变化和少量可解释推导结果。

### 不应全部展开入图

- 每一笔成交、逐 Tick 行情、全量日内 K 线；
- 完整财务时序或原始指标明细；
- 重复转载的全文和重复 Chunk；
- 每次推理的所有临时中间路径。

这些原始数据继续由 PostgreSQL/时序库/对象存储持有；图中保留稳定 ID、摘要、变化事件和
证据引用。OpenSPG 是语义推理读模型，不是行情数据库或唯一事实源。

## 生产化建议

1. **控制查询合同**：强制起始实体、`as_of`/时间窗、允许的关系类型、最大 3 跳、每层
   fan-out/top-k 和总结果上限；禁止无界路径。
2. **冷热分层**：交互推理只读取近 1–3 年热事件与聚合历史；原始历史事件、全文和中间
   推导归档，需要时按命题检索回热上下文。
3. **证据去重**：同一事实的多来源保留 provenance，但不要复制完整实体/Chunk/向量。
4. **规则异步化**：事件进入后异步计算直接影响和受控派生事实；在线命题优先读取物化结果，
   只对小范围做即时深推理。
5. **索引从查询反推**：为稳定 ID、时间、状态和常用筛选字段建立索引；不要给所有 Text
   属性创建向量。Neo4j 索引需要帮助查询从小集合开始。
   [Neo4j indexes](https://neo4j.com/docs/cypher-manual/current/indexes/search-performance-indexes/using-indexes/)
6. **生产存储升级**：本地 1 GB page cache 只用于体验。生产采用 NVMe、按实际 store/index
   体积配置 page cache；需要 HA/读扩展时评估 Neo4j Enterprise cluster。page cache 能否覆盖
   热工作集直接影响随机遍历性能。
   [Neo4j memory configuration](https://neo4j.com/docs/operations-manual/current/performance/memory-configuration/)
7. **隔离构建与交互负载**：至少分开队列、并发配额和时间窗；在压测证明共库可接受前，
   不让大批量构建与深度推理争用交互查询资源。

## 必做压测门槛

在技术选型定案前，构造代表 3–5 年的合成/脱敏数据，至少覆盖 3,000 万节点、1 亿关系和
1,000 万向量，并测试：

- 定点实体查询、带时间过滤的一跳/二跳/三跳；
- 中国、美国、AI、半导体等超点查询；
- KGDSL 规则推导和推导物化；
- 向量 top-k、图 + Chunk 混合召回；
- 事件持续写入时的 5/20/50 并发命题；
- Neo4j 故障、重启、备份恢复和索引重建。

记录 P50/P95/P99、超时/失败率、每命题子查询与模型调用数、Neo4j DB hits、峰值并发事务、
transaction memory、GC、I/O、page-cache hit ratio、向量召回延迟和队列深度。Neo4j 官方建议
持续关注 page-cache hit ratio，理想状态为 98–100%。
[Neo4j metrics](https://neo4j.com/docs/operations-manual/current/monitoring/metrics/reference/)

最终是否继续使用 OpenSPG，不应由“能否导入 1 亿条”决定，而应由上述真实命题在目标并发下
能否达到观潮家的响应时间、正确性、可解释性和恢复目标决定。
