# MiroFish 与 OpenSPG/KAG 性能与规模适配调查

> 调查日期：2026-08-13  
> MiroFish 源码基线：`b5b53acc57189a4a42e44a23e149dc655c98fe82`

## 结论

MiroFish 和 OpenSPG/KAG 不是同类引擎，不存在一个可直接复用的“谁更快”结论。

- 对受 Schema 约束的大型长期知识图谱、定点图查询、有界多跳遍历和规则推理，OpenSPG/KAG 的架构更合适。
- 对一次民意/社交网络的多智能体沙盘模拟，MiroFish 有 OASIS 能力，OpenSPG/KAG 本身没有。
- MiroFish 当前代码没有证明自身具有“超大图谱、高实时吞吐”。其大规模宣传主要来自 OASIS 的模拟代理数量，低延迟宣传主要来自 Zep Cloud 的托管检索能力，不是 MiroFish 端到端性能基准。

## 架构差异

| 维度 | OpenSPG/KAG | MiroFish |
|---|---|---|
| 主要定位 | 语义知识图谱、混合检索、符号/逻辑推理 | 基于种子材料的多智能体社会模拟应用 |
| 图存储 | 自己管理 OpenSPG + Neo4j 查询链路 | 当前主分支强制使用 Zep Cloud，不自带本地图数据库 |
| 查询 | 索引定位、属性图遍历、KGDSL/推理器、向量/文本召回 | Zep top-k 语义搜索 + Python 应用层工具 |
| 实时更新 | 由调用方组织事件导入和索引更新 | 模拟活动按 5 条组批推送 Zep，Zep 再异步处理 |
| 大图查询风险 | 无界多跳和高扇出仍可导致查询爆炸 | 多个工具会拉取全部节点/边到 Python 再筛选，大图下更危险 |

## MiroFish 的“大数据”和“实时”怎么看

### 1. “数千/百万智能体”是模拟规模，不是图查询吞吐

MiroFish README 宣传数千智能体，其模拟底座是 OASIS。OASIS 官方宣称可支持百万代理，但这是社会模拟的代理数量能力，不是同时执行百万次 LLM 调用，也不是知识图谱 QPS。MiroFish 当前每个 Twitter/Reddit 模拟环境把 LLM 并发信号量设为 30，README 还警告消耗高并建议初次少于 40 轮。

### 2. “亚 200ms”是 Zep Cloud 厂商指标

MiroFish 当前主分支仅连接 Zep Cloud，甚至会拒绝自定义 `ZEP_API_URL`。Zep 官方声称 Context Graph 检索可亚 200ms，且数据量增大时接近常数时间；但这是托管服务的检索 SLA/基准，受 API 和处理并发限制，不包括 MiroFish 的 LLM 规划、模拟、全图拉取、本地排序和报告生成。

### 3. MiroFish 的部分图工具不适合超大图

源码中：

- `_local_search` 会下载全部节点/边，在 Python 中关键词打分和排序；
- `panorama_search` 会拉取全部节点和边后才分类；
- `get_node_edges` 为了同时取入边/出边，在已知 `graph_id` 时会拉取全部边再本地过滤；
- `filter_defined_entities` 拉取全部节点/边，然后对每个节点遍历全部边，最坏可达 `O(V×E)`。

因此，MiroFish 的 `quick_search` 可能借 Zep 取得较低的 top-k 检索延迟，但其宽幅/全景“图推理”工具会随单图增大而明显恶化。

### 4. 当前应用层也不是水平扩展架构

MiroFish 的项目状态主要保存在本地文件/JSON，任务状态在单进程内存字典，模拟平台数据使用本地 SQLite。默认 Docker Compose 也只是单应用容器。这些选型适合单机体验和实验，不是开箱即用的 HA/水平扩展方案。

## 对观潮家的建议

观潮家的核心负载是长期积累的全球实体、每日事件/指标、可治理的领域 Schema，以及时间限定的因果/影响链推理。应继续以 OpenSPG/KAG 作为语义图谱和推理主干。

MiroFish 可以作为未来的可选“情景沙盘”：从 OpenSPG 取得某一命题的有界子图，模拟市场参与者、舆论或政策反应，再把结果作为“模拟证据”而不是事实回传。不建议用 MiroFish/Zep 替代 OpenSPG 作为全局事实库和正式规则推理引擎。

## 证据来源

- [MiroFish 官方 README](https://github.com/666ghj/MiroFish)
- [MiroFish Zep 检索与全图工具源码](https://github.com/666ghj/MiroFish/blob/b5b53acc57189a4a42e44a23e149dc655c98fe82/backend/app/services/zep_tools.py#L457-L1229)
- [MiroFish 全图分页加载源码](https://github.com/666ghj/MiroFish/blob/b5b53acc57189a4a42e44a23e149dc655c98fe82/backend/app/utils/zep_paging.py#L55-L151)
- [MiroFish 实体读取与本地边扫描源码](https://github.com/666ghj/MiroFish/blob/b5b53acc57189a4a42e44a23e149dc655c98fe82/backend/app/services/zep_entity_reader.py#L84-L405)
- [MiroFish 进程内任务状态](https://github.com/666ghj/MiroFish/blob/b5b53acc57189a4a42e44a23e149dc655c98fe82/backend/app/models/task.py#L56-L170)
- [Zep 性能说明](https://help.getzep.com/performance)
- [Zep FAQ：规模、限流与托管方式](https://help.getzep.com/faq)
- [OASIS 官方仓库](https://github.com/camel-ai/oasis)
- [OASIS 论文](https://arxiv.org/abs/2411.11581)
- [OpenSPG 官方仓库](https://github.com/OpenSPG/openspg)
- [KAG 官方仓库](https://github.com/OpenSPG/KAG)

## 限制

两个项目没有提供可直接对齐的端到端吞吐/p95 基准，本结论是基于当前官方文档、固定版本源码路径和观潮家工作负载的架构判断。真正选型验收应在相同数据集和问题集上测量导入速率、查询 p50/p95/p99、推理总延迟、并发、资源和成本。
