# OpenSPG + KAG 执行原理与股票产业链趋势推理数据需求

## 结论先行

OpenSPG 和 KAG 可以支撑“产业链事件→节点变化→公司受益/受损→证券映射”的可解释推理，但它们不会仅凭一组静态实体和 LLM 自动产生可靠的市场趋势。

- **OpenSPG** 负责领域 Schema（TBox）、事实图（ABox）、文本/向量索引、KGDSL 规则和确定性图推理。官方将其核心能力划分为 SPG-Schema、SPG-Builder、SPG-Reasoner 和 KNext 可编程框架。来源：[OpenSPG v0.8 README](https://github.com/OpenSPG/openspg/tree/v0.8#core-capabilities)。
- **KAG Builder** 负责把结构化记录或非结构化文档转换成图、Chunk 及其互索引；**KAG Solver** 则把自然语言问题转成逻辑形式和任务 DAG，调用图检索、Chunk 检索、数值计算、LLM 演绎等 Executor，最后带引用生成答案。来源：[KAG v0.8.0 README](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md#5-%E6%8A%80%E6%9C%AF%E6%9E%B6%E6%9E%84)、[KAG 论文](https://arxiv.org/abs/2409.13731)。
- 官方供应链示例已证明 OpenSPG 能表达“产品价格上涨→下游企业成本上涨→利润下降”这种因果传导，且规则可新建派生事件和 `leadTo` 边。来源：[供应链示例说明](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/README_cn.md)、[供应链 Schema](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/SupplyChain.schema)、[concept.rule](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/concept.rule)。
- 但“判断一个时间序列正在走强/走弱”与“沿产业链传导这个变化”是两个不同问题。前者需要可追溯的时序观测、口径、窗口、阈值或预测模型；后者需要产业链拓扑、供需/成本/产能暴露和经验证的传导规则。KAG 的 Math Executor 会让 LLM 生成 Python 并执行，它是问答时的计算工具，不应替代投研数据层的受控指标生产。来源：[`PyBasedMathExecutor`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/executor/math/py_based_math_executor.py)。

**对当前 PostgreSQL 设计的审计结论**：假设当前 PG 事实完整投影到 OpenSPG，现有模型已经足以做“产业链结构、依赖机制、物理约束和证据”的初步图推理，也能通过 Industry Storyline 间接召回相关 Event；但还不能独立完成“时序趋势判定 → 节点传导 → 公司暴露 → 证券映射”。核心缺口是数值观测面、Event 到产业链对象的强类型连接、Company 到 ChainNode 的经营暴露、Company 到 Security 的发行关系，以及可执行和可回放的规则。这个判断不依赖已退役的旧事件语义模型，而是从 OpenSPG 图/规则和 KAG Retrieval/Math/Deduce 的实际输入要求倒推。PG 证据来自 `tidewise-ai` 当前 migration、Context 和已接受 ADR；详见第六节。

## 研究范围和事实标注

截至 2026-08-20，官方最新正式 release 仍为 OpenSPG `v0.8` / KAG `v0.8.0`；本文针对本地运行时约束使用该版本的官方源码、README、官方示例与 KAG 原始论文。文中区分：

- **官方机制**：官方文档或源码明确实现的能力。
- **工程设计**：为观潮家投研方法论推导出的建模建议，不冒充 OpenSPG/KAG 官方产品承诺。

## 一、OpenSPG 和 KAG 各自执行什么

| 层 | 职责 | 对趋势投研的意义 |
| --- | --- | --- |
| OpenSPG Schema | 定义 EntityType、ConceptType、EventType、属性、关系、索引和可编程规则 | 固定“产业链”“节点”“指标”“事件”“趋势”“暴露”“影响”的语义和合法连接 |
| KAG Builder | 扫描数据，映射/抽取实体与关系，向量化，写入 OpenSPG | 将结构化时序数据和文档证据转成可检索的图与 Chunk |
| OpenSPG Graph/Search | 保存图事实，提供结构化图查询、文本和向量检索 | 提供产业链路径、实体对齐、指标事实和原文证据 |
| OpenSPG Reasoner | 用 KGDSL/GQL 查询和执行属性/关系/事件传导规则 | 做可复现的分类、聚合、阈值判定和因果传导 |
| KAG Solver | 把问题转成逻辑形式与任务 DAG，调用 Retrieval / Math / Deduce / Output | 将一个复合投研问题拆成“找事实→算指标→做传导→整理证据” |
| KAG Generator | 汇总 task result、图数据与 Chunk 并调用 LLM 生成最终答案 | 把结构化推理链转成投研可读的结论和引用，但不应代替底层事实与规则 |

OpenSPG 的官方 README 明确将 Schema、Builder 和 Reasoner 分为不同核心能力，Reasoner 以 KGDSL 表达逻辑规则；KAG 官方 README 则把 `kg-builder` 和 `kg-solver` 分开，并说明 Solver 整合检索、知识图谱推理、语言推理和数值计算。来源：[OpenSPG v0.8 README](https://github.com/OpenSPG/openspg/tree/v0.8#core-capabilities)、[KAG v0.8.0 README](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md#5-%E6%8A%80%E6%9C%AF%E6%9E%B6%E6%9E%84)。

## 二、写入时：从原始数据到图、索引和可推理事实

### 2.1 Schema 先决定哪些知识可被稳定表达

Schema 是执行契约，不是数据本身。它限定合法类型、属性和边，也决定哪些字段进入 Text/Vector 索引，并可以在属性、关系和概念上附加规则。供应链官方 Schema 定义了 `Product`、`Company`、`ProductChainEvent`、`CompanyEvent`、`Index`、`Trend` 及 `leadTo`，并用属性规则计算近 1/3/6 月的聚合值。来源：[供应链 Schema](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/SupplyChain.schema)。

### 2.2 结构化数据链路

KAG v0.8.0 的默认结构化 Builder Chain 是：

```text
Scanner / Reader
  -> SPGTypeMapping
  -> optional BatchVectorizer
  -> KGWriter
  -> OpenSPG Graph/Search storage
```

- `DefaultStructuredBuilderChain` 将 mapping、可选 vectorizer 和 writer 串起。来源：[`default_chain.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/default_chain.py)。
- `SPGTypeMapping` 从 OpenSPG 加载 Schema，验证目标类型/字段，然后把记录的 `id`、`name`、属性和引用型属性组装成节点与边，并支持自定义 `link_func`。来源：[`spg_type_mapping.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/mapping/spg_type_mapping.py)。
- `BatchVectorizer` 读取 Schema 的索引元数据，为指定文本字段生成 dense/sparse vector 字段。来源：[`batch_vectorizer.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/vectorizer/batch_vectorizer.py)。
- `KGWriter` 把 `SubGraph` 通过 KNEXT `GraphClient.write_graph` 写入 OpenSPG，默认是 `UPSERT`，也支持 `DELETE`。来源：[`kg_writer.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/writer/kg_writer.py)。

对观潮家来说，已经在业务数据库里结构化且经过审定的价格、库存、产能、订单、估值、暴露等记录，应当走确定性 mapping，不应先经 LLM 重新抽取一次。

### 2.3 非结构化文档链路

KAG v0.8.0 的默认非结构化 Builder Chain 是：

```text
Reader
  -> Splitter
  -> Extractor
  -> Vectorizer
  -> optional PostProcessor
  -> KGWriter
```

`SchemaConstraintExtractor` 会用项目 Schema 约束 LLM 进行 NER、实体标准化、关系抽取和可选的事件抽取，并把抽取图和原始 Chunk 通过 `source` 边关联。来源：[`default_chain.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/default_chain.py)、[`schema_constraint_extractor.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/extractor/schema_constraint_extractor.py)。

这条链适合将公告、财报、政策、行业新闻、调研纪要变成“候选事实 + 原文证据”，但 LLM 抽取结果应保留候选/审核状态，不应与交易所、企业披露或行情源的结构化事实混为同一信任等级。

### 2.4 事件写入与规则派生

OpenSPG 的 Graph API 在 `writerGraph` 收到 `enableLeadTo=true` 时，会调用 ReasonProcessor，再把推理得到的记录写回图存储。来源：[`GraphController.java`](https://github.com/OpenSPG/openspg/blob/v0.8/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi/GraphController.java)。

官方供应链 `concept.rule` 先根据 `index=价格` 且 `trend=上涨` 把产品事件分到“价格上涨”概念，再沿 `Product.hasSupplyChain -> Product <- Company.product` 路径新建下游公司的“成本上涨”事件，然后再新建“利润下降”事件。来源：[`concept.rule`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/concept.rule)。

这证明了“传导规则”的执行机制，但官方示例本身是简化的定性规则，没有自动解决投研所需的传导强度、滞后、边际变化、回滚条件和相互抵消。这些都必须由观潮家的领域模型和规则版本补齐。

## 三、问答时：从自然语言到逻辑形式、求解和证据

### 3.1 Planner 将复合问题拆成任务 DAG

`KAGLFStaticPlanner` 把用户问题和可用 Executor 的 schema 交给 LLM，返回任务计划；当子问题依赖前序输出时，它还会根据已有上下文重写 query。来源：[`lf_kag_static_planner.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/planner/lf_kag_static_planner.py)。

KAG 的逻辑节点包括：

- `get_spo(s,p,o)` / Retriever：找实体、属性、关系和相关 Chunk；
- `Math`：对前置结果做数值计算；
- `Deduce`：做 entailment、judgement、extract、choice 等 LLM 语义演绎；
- `Output`：选取前序别名对应的结果。

这些逻辑节点的解析在官方源码中是显式类型。来源：[`logic_node_parser.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/parser/logic_node_parser.py)。

### 3.2 Pipeline 按依赖调用 Executor

`KAGStaticPipeline` 的执行顺序是：

1. Planner 产生任务 DAG；
2. 将 task 放入 Context；
3. 按依赖分组，组内并行执行；
4. 依 task 指定的名称选择 Executor；
5. 把整个 Context 交给 Generator；
6. 可选判断答案是否无效并重试。

来源：[`kag_static_pipeline.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/pipeline/kag_static_pipeline.py)。

### 3.3 Hybrid Retrieval 不是只做向量搜索

官方 `domain_kg` / `supplychain` 配置了三类检索器：

- `kg_cs`：高置信实体链指 + exact one-hop path selection，适合按 Schema 精确查图；
- `kg_fr`：较宽松的实体链指 + fuzzy one-hop + 图到 Chunk 的 PPR 追溯；
- `rc`：对原始 Chunk 做向量检索。

`KAGHybridRetrievalExecutor` 按 priority 分组调用 retriever，组内并行，合并图 SPO 和 Chunk；当高优先级组已找到知识时可提前停止后续组。来源：[官方 `domain_kg/kag_config.yaml`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/domain_kg/kag_config.yaml)、[`kag_hybrid_retrieval_executor.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/executor/retriever/kag_hybrid_retrieval_executor.py)。

KAG 通过 `OpenSPGGraphApi` 调用 OpenSPG 的 graph/reasoner 能力，通过 `OpenSPGSearchAPI` 做文本和向量检索。来源：[`openspg_graph_api.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/tools/graph_api/impl/openspg_graph_api.py)、[`openspg_search_api.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/tools/search_api/impl/openspg_search_api.py)。

### 3.4 Reasoner、Math 和 Deduce 的可信边界

- OpenSPG Server 公开 `reason/run`、`reason/thinker` 和 `reason/schema` 等 API，用于结构化图查询与规则推理。来源：[`ReasonController.java`](https://github.com/OpenSPG/openspg/blob/v0.8/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi/ReasonController.java)。
- `PyBasedMathExecutor` 让 LLM 根据问题和上下文生成 Python，在有超时的子进程中执行；因此它适合问答时的临时计算，不适合未经审核地产生长期使用的投研指标。来源：[`py_based_math_executor.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/executor/math/py_based_math_executor.py)。
- `KagDeduceExecutor` 用 LLM 执行 entailment、judgement、extract、choice 等语义演绎。它的结论应标识为语义推断，不能与 OpenSPG 规则所产生的确定性事实混淆。来源：[`kag_deduce_executor.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/executor/deduce/kag_deduce_executor.py)。

### 3.5 Generator 把证据链转成答案

`LLMIndexGenerator` 汇总 task 结果、检索到的 Chunk 和图数据，给引用生成 ID，再调用 LLM 生成最终答案。这一层的作用是组织与表达，不是自动为图中缺失的业务事实补真。来源：[`llm_index_generator.py`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/generator/llm_index_generator.py)。

## 四、要推理股票产业链与节点趋势，必须灌注什么数据

### 4.1 不是所有数据都应该塞成图节点

KAG v0.8 的 IndexManager 内建 `KnowledgeUnit`、`Chunk`、`Table`、`Summary`、`Outline` 和
`AtomicQuery` 等索引类型，并在应用期按知识库索引选择 Retriever。对本场景更合理的原生分层是：

| 原生承载面 | 应放的数据 | 原因 |
| --- | --- | --- |
| OpenSPG Graph / KnowledgeUnit | 产业链、节点、公司、证券、Event、稳定关系、约束和少量当前状态 | 适合精确路径、实体对齐、规则求值和多跳检索 |
| Table / 数值 Executor | 价格、产量、库存、开工率、订单、财务和行情时序，以及窗口统计结果 | 适合过滤、聚合、排序和趋势计算，避免把每个行情点展开成图 |
| Chunk / 原文互索引 | 公告、财报、政策、行业材料和每个结构化事实的原文依据 | 用于语义召回、补足上下文和引用 |
| KGDSL / 自定义 Executor | 确定性传导规则、趋势算法、瓶颈评分、情景与失效条件 | 把“有数据”变成可复现的计算与推理合同 |

官方依据：[KAG v0.8 发布说明](https://github.com/OpenSPG/KAG/releases/tag/v0.8.0)、
[KAG v0.8.0 README](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md)。这也意味着
“把 PG 全表逐行转成图节点”并不是目标；应按 Solver 实际需要选择图、表和 Chunk 的承载面。

下表是“最小可推理数据面”。其中结构化事实应通过 mapping 直接写入；公告/新闻/调研文本通过非结构化链建图与 Chunk 互索引。

| 数据面 | 必要字段/关系 | 支持的推理 |
| --- | --- | --- |
| 主数据 | 稳定 ID、标准名、别名、来源代码；`Company -> Security`、`Company -> Product/Commodity`、`Company -> IndustryChainNode` | 实体对齐，从经营主体映射到上市证券 |
| 产业链拓扑 | `IndustryChain -> Node`，`Node -> downstreamNode`，投入/产出/代替/互补/制约关系，关系有效期 | 定位上下游路径、受冲击范围与潜在瓶颈 |
| 公司/节点暴露 | 产品、收入、采购、成本、产能、产量、客户/供应商集中度；`exposureType`、`weight`、`unit`、`period`、`source` | 区分“与该节点有关”和“业绩对该节点高度敏感” |
| 时序观测 | 对象、指标、观测时间、公布时间、数值、单位、频率、口径、币种、地域、数据源、版本/修订标记 | 判断价格、库存、产能、利润率、订单、运价、开工率等的方向与强度 |
| 事件事实 | `eventId`、类型、subject/object、`eventTime`、发生/知悉时间、状态、范围、持续期、来源、可信度、事实/预测/传闻标记 | 表达停产、扩产、涨价、去库、政策、技术替代等非等间隔冲击 |
| 可选物化的计算结果 | 输入序列 ID，窗口，对比基准，公式/模型版本，方向，强度，置信度，`asOfTime`，有效期 | 把“涨了 5%”与“中期趋势向上”区分开；也可以只在 Table/Math 路径按需计算，不强制新增领域实体 |
| 传导规则元数据 | 规则 ID/版本，触发指标与阈值，传导路径，方向，强度/弹性，滞后，作用期，适用条件，失效条件，样本证据 | 将领域专家经验变成可审计的 KGDSL/工作流规则 |
| 市场响应 | 证券价格/成交/波动率、行业/市场基准、预期差、估值、业绩预期、资金流，及同一 `asOfTime` | 区分基本面趋势、市场预期和已定价程度 |
| 文档与 Chunk | 原文、文档 ID、发布方、发布/获取时间、页码/段落、权威等级、与抽取事实的 `source` 边 | 让 KAG 在图事实之外回溯语境和原始证据 |
| 治理与溯源 | `sourceSystem/sourceRecordId`、生效/失效时间、写入时间、版本、payload hash、审核状态、推导方式、规则/模型版本 | 防止已撤回、修订或 LLM 猜测被当成当前事实 |

官方供应链示例已给出 `ProductChainEvent(subject,index,trend)` 和 `CompanyEvent(subject,index,trend)` 的最小形式，但投研生产版必须追加时间、数值、单位、窗口、来源、置信度、趋势方法和版本，否则只能做定性传导，无法判断时效性和趋势强度。官方示例依据：[事件 Schema](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/SupplyChain.schema)、[事件数据说明](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/builder/data/README_cn.md)。

## 五、需要灌注的规则，不只是数据

### 5.1 观测到趋势：受控指标规则

建议先在可回测的数据/特征层生产趋势计算结果，供 KAG 的 Table/Math 路径读取；只有需要
跨查询复用、追踪或作为规则前提的结果，才物化为 OpenSPG 事实：

```text
TrendResult = f(
  subject, indicator,
  as_of_time,
  current_window, baseline_window,
  pct_change, slope, z_score, breadth,
  data_quality, method_version
)
```

最低限度应定义：

1. 窗口：5/20/60 交易日或周/月/季；
2. 对比基准：环比、同比、历史分位、行业基准；
3. 方向：up/down/flat/turning；
4. 强度：变化率、斜率、z-score、广度；
5. 稳健性：最小样本数、缺失率、异常值处理；
6. 时间边界：`asOfTime`、知悉时间和失效时间，避免前视偏差；
7. 公式/模型版本和输入数据 lineage。

OpenSPG 规则引擎能做 `group().sum`、`date_diff`、`now`、算术比较和条件判定，官方供应链 Schema 就用它计算近 1/3/6 月资金流。因此简单聚合和阈值可用 KGDSL；需要复杂时序、特征稳定性、横截面标准化和回测的部分，更适合在受控数据工程/特征服务中完成后写入。官方能力依据：[供应链 Schema](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/SupplyChain.schema)。

### 5.2 趋势到节点：聚合和广度规则

一个节点的趋势不应等于单一事件标签。建议至少组合：

- 节点主产品/商品的价格和价差；
- 产量、产能、开工率、库存和交付周期；
- 订单/需求、出口/进口、政策配额；
- 该节点中公司指标上行的广度和加权广度；
- 数据覆盖率和鲜度。

派生节点趋势应保留组成贡献，否则 KAG 只能返回“节点上行”而无法解释“由什么推动”。

### 5.3 节点到节点：因果传导规则

每条传导规则至少要明确：

- 起点指标和触发阈值；
- 关系类型：成本传导、供给制约、需求拉动、替代、互补、产能依赖；
- 影响方向：正/负/非单调；
- 传导强度或弹性；
- 滞后区间和作用期；
- 适用范围：地域、产品规格、产能利用率、合同类型；
- 可中断条件：长单锁价、库存缓冲、替代材料、政策干预、扩产；
- 传导叠加和抵消规则；
- 规则版本、证据样本和置信度。

官方 `concept.rule` 可作为“如何新建派生事件和 `leadTo` 边”的语法参考，但不应直接把它的无强度、无滞后简化规则当作投研模型。来源：[`concept.rule`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/concept.rule)。

### 5.4 节点到公司：暴露与业绩影响规则

不能只用 `Company -> belongsToIndustryChainNode` 作为影响规则。至少需要三类暴露：

1. **收入暴露**：该节点/产品的收入占比、出货量和价格弹性；
2. **成本暴露**：关键原料成本占比、锁价比例、库存周期和转嫁能力；
3. **产能/供应风险暴露**：产能地理分布、供应商集中度、可替代性和扩产周期。

派生的 `CompanyImpact` 应同时输出 direction、magnitude/range、lag、confidence、drivers、invalidators 和 evidence，并区分图规则推导与 LLM 语义演绎。

### 5.5 公司到股票：不要跳过“已定价”

`Security -> issuedBy -> Company` 只解决身份映射，不能直接得出股价方向。需要额外的市场层事实和规则：

- 当前估值与历史/同业基准；
- 盈利预期与最新事实的预期差；
- 事件前后相对行业/市场的超额收益；
- 拥挤度、换手、资金流和波动率；
- 结论的 `asOfTime`、时间跨度和失效条件。

因此更合理的输出是“基本面影响 + 市场预期差 + 证据与失效条件”，而不是仅从产业链事件跳到“股价必涨/必跌”。

## 六、按当前 PostgreSQL 类型判断初步推理能力

### 6.1 审计口径

本节不以 `tidewise-reason` 当前是否已有 ABox 为判断依据，而是假设 `tidewise-ai` 的当前 PG
事实都会投影到 OpenSPG。审计基线是本地已应用 migration 68 的表与约束（68 只为 StorylineDomain
增加 code，不改变本节推理路径），以及 Data Context、
ADR 0028 和 ADR 0036。已退役的旧分析持久化对象只作为历史事实，不作为分析框架。

### 6.2 已经适合投影到 Graph / KnowledgeUnit 的部分

1. **产业链本体和 DAG 已较完整。** `industry_chain` 有范围、目标产出、终端用途、地域、
   `as_of_date`、技术路线和 `observable_variables`；Membership 有节点顺序、上下游阶段、纳入原因
   和证据；Graph Edge 有 `input_to / is_component_of / depends_on`、机制、条件、压缩路径标记、
   审核状态和证据，且数据库禁止 active DAG 成环。依据：
   [`000027_add_typed_master_data_schema.sql`](../../../tidewise-ai/data-service/backend/migrations/000027_add_typed_master_data_schema.sql)、
   [`000030_add_industry_relationship_import_contract.sql`](../../../tidewise-ai/data-service/backend/migrations/000030_add_industry_relationship_import_contract.sql)、
   [`000057_make_chain_node_industry_chain_independent.sql`](../../../tidewise-ai/data-service/backend/migrations/000057_make_chain_node_industry_chain_independent.sql)。
2. **产业链卡点语义已经存在。** `chain_node_physical_constraints` 覆盖产能、良率、材料纯度、
   设备能力、扩产周期、资源可得性等类型，并绑定节点或节点关系、机制、条件和来源。依据：
   [`000017_add_chain_node_relations.sql`](../../../tidewise-ai/data-service/backend/migrations/000017_add_chain_node_relations.sql)。
3. **Event 与证据链质量较好。** Event 有六要素、事实/计划/推测模态、发生/宣布时间；每个 Event
   必须关联 Atomic Evidence，并可关联 Actor 与 Asset。依据：
   [`event.schema`](../../../tidewise-ai/data-service/doctype/event.schema)、
   [`000060_rebuild_event_domain.sql`](../../../tidewise-ai/data-service/backend/migrations/000060_rebuild_event_domain.sql)、
   [ADR 0028](../../../tidewise-ai/docs/adr/0028-rebuild-event-domain-around-atomic-evidence.md)。
4. **Industry Storyline 提供了弱的 Chain → Event 入口。** `INDUSTRY` Storyline 强制锚定一个
   IndustryChain，`storyline_event_links` 可关联 Event；这适合召回某条链持续演进的事件集合。
   依据：[`000066_add_storyline_persistence.sql`](../../../tidewise-ai/data-service/backend/migrations/000066_add_storyline_persistence.sql)、
   [ADR 0036](../../../tidewise-ai/docs/adr/0036-independent-storyline-persistence.md)。
5. **Raw Evidence / Atomic Evidence 可直接成为 Chunk 与 source 链。** 这为最终回答回溯原文提供了
   比纯图结论更好的基础。

### 6.3 从 KAG 执行链看，当前仍然断开的路径

| 原生推理所需路径 | 当前 PG 设计 | 结果 |
| --- | --- | --- |
| Event → IndustryChain / ChainNode / Product | Event Actor 只允许 Country、Person、Organization、Company；Asset 只允许 Security、Commodity、Index、Rate、Forex、Derivative，且目标是 opaque ID、无外键 | 除 Storyline 的链级间接关联外，Solver 无法精确知道事件落在哪个节点；只能靠文本相似度猜 |
| ChainNode → Company | 只有 `company_industry_links`，没有公司在节点上的参与、产品、收入/成本/产能暴露关系 | 能找行业公司，不能识别真正控制卡点或受影响程度 |
| Company → Security | migration 67 明确删除 `security_profiles.issuer_company_entity_id` | 无法从节点/公司稳定落到股票；依据：[`000067_make_company_independent.sql`](../../../tidewise-ai/data-service/backend/migrations/000067_make_company_independent.sql) |
| 数值观测 → Table/Math | `observable_variables` 只是名称数组；当前没有带值、单位、统计期、发布时间和修订版本的经营/产业/行情观测合同 | Math Executor 没有可计算的输入，不能独立判断趋势或拐点 |
| 图事实 → KGDSL 传导 | Edge 的 `mechanism`、`condition_note` 和物理约束是文本事实，当前没有已注册的可执行趋势、传导、抵消与失效规则 | KAG Deduce 可以给语言判断，但那不是可回放的确定性规则推理 |
| point-in-time 推理 | Event 区分发生/宣布时间，Evidence 有发布/采集时间；关系多为 current status + verified_at | 可做部分时点过滤，但缺统一 `known_at`、有效期、修订序列和历史快照，回测容易前视 |

PG 的 `event.schema` 也不能原样等同于 OpenSPG EventType 投影：投影层仍需把发生时间映射为
OpenSPG 事件时间，并把 Actor/Asset 解析成 Schema 中合法的 subject/object 关系，否则会失去
官方供应链示例依赖的事件分类和 `leadTo` 规则入口。

`event_asset_links.impact_direction` 已经是 Positive/Negative/Neutral 的分析标签。如果把它作为首轮
推理输入，KAG 很可能只是检索这个标签，而不是从事件、拓扑、观测和规则独立推出方向。

同理，`research_themes`、`research_reasoning_trees`、节点和 signal snapshot 已经包含 direction、
strength、mechanism、checkpoint 和 invalidation 条件；migration 59 还特意把它们改成 aggregate-local
key/display snapshot，移除了对正式产业链节点和边的绑定。它们适合作为 analyst prior、产品展示或
评测金标，不适合作为证明 KAG 推理能力的基础输入。依据：
[`000059_retire_data_event_semantics.sql`](../../../tidewise-ai/data-service/backend/migrations/000059_retire_data_event_semantics.sql)、
[ADR 0026](../../../tidewise-ai/docs/adr/0026-retire-data-event-semantic-and-formal-research.md)。

### 6.4 精确回答“当前类型能不能做初步推理”

| 问题 | 判断 |
| --- | --- |
| 某产业链有哪些节点、上下游依赖和物理卡点？ | **可以**，这是当前最成熟的图推理面 |
| 某条 Industry Storyline 最近关联了哪些 Event、证据是什么？ | **可以**，但关联粒度停在链而非具体节点 |
| 某个已手工绑定节点的 Event 会沿哪些边传播？ | **可做 PoC**，前提是补 Event→Node 关系和少量 KGDSL 规则 |
| 节点最近 1/3/6 个月趋势是增强还是减弱？ | **当前不可以独立推导**，缺结构化数值观测和确定性趋势算法 |
| 哪些公司控制卡点、业绩弹性最大？ | **当前不可以**，缺 Company→Node 的经营暴露 |
| 最终影响哪些证券、市场是否已定价？ | **当前不可以**，发行关系已移除，且缺行情、估值和预期差数据面 |

所以更准确的结论是：**现有 PG 类型能支撑一个有价值的“产业链结构与卡点解释 PoC”，但不能
支撑一个不依赖既有分析标签的“节点趋势与股票趋势推理 PoC”。** 要跨过这条线，不需要恢复旧
事件语义模型；只需要按 OpenSPG/KAG 原生执行链补齐连接、Table 数据和可执行规则。

## 七、建议的最小可行推理闭环

不要一开始就追求全市场。选一条因果逻辑清晰、数据可得的产业链，建立以下最小闭环：

1. **闭合静态图**：1 条产业链、5–15 个节点、20–50 家公司、对应证券；先补齐 Event→Node、Company→Node 和 Company→Security，边含暴露权重和有效期。
2. **Table 时序面**：每个核心节点 3–5 个领先/同步指标，至少覆盖一个完整景气周期，保留单位、统计期、发布时间和修订。
3. **受控趋势计算**：用版本化代码或自定义 Executor 产生 5/20/60 日方向、强度、广度与转折；先作为查询结果，确需复用时再物化到图。
4. **EventType 投影**：将政策、停产、扩产、涨价、库存变化映射为有 subject/object、事件时间、来源和模态的 OpenSPG EventType。
5. **3–5 条可验证规则**：例如“原料价格突破 + 低库存→下游成本压力”、“产能利用率高 + 库存下降→节点景气向上”、“暴露高 + 无长单锁价→公司成本敏感”。
6. **文档证据**：对每个事件和主要暴露绑定公告/财报/官方统计 Chunk。
7. **隔离的金标问题集**：至少覆盖事实查询、趋势判定、传导路径、公司排名、反例/失效条件和证据回溯；首轮推理知识库排除 analyst snapshot 与已标注的 Asset impact direction，避免答案泄漏。

验证顺序应是：

```text
单条结构化事实可查
  -> 静态产业链路径可查
  -> 趋势指标可重算
  -> KGDSL 传导结果可重放
  -> KAG 能拆解复合问题
  -> 最终答案能回溯到图事实和原文
  -> 与人工投研金标和历史时点回测对照
```

## 八、实施时的关键边界

1. **图谱不是时序仓库的替代品**：原始行情和高频指标继续留在专用数据库；OpenSPG 保存与推理直接相关的观测、派生趋势、关系和证据指针。
2. **事实、规则推导和 LLM 演绎分层**：建议用 `assertionKind = observed | ruleDerived | modelDerived | llmHypothesis` 或等价字段隔离，并保留规则/模型版本。
3. **所有结论都要带 `asOfTime`**：股票投研最容易在回测中引入未来数据；“事件发生时间”与“市场可知时间”必须分开。
4. **规则要有反例和失效条件**：只灌注正向逻辑会导致过度传导。可替代供应、长单锁价、库存缓冲、产能扩张和需求崩塌都应作为阻断或抵消条件。
5. **不要把 KAG 的最终文本直接写回事实图**：要沉淀的派生事件应经显式规则或受控 Workflow 生成，附证据、版本和置信度后再通过 Writer/API 写入。

## 主要官方来源索引

- [OpenSPG v0.8 官方仓库与核心能力](https://github.com/OpenSPG/openspg/tree/v0.8)
- [KAG v0.8.0 官方 README](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md)
- [KAG 原始论文：LLM-friendly representation、mutual indexing 与 logical-form-guided hybrid reasoning](https://arxiv.org/abs/2409.13731)
- [KAG 默认 structured/unstructured Builder Chain](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/default_chain.py)
- [结构化 SPG 字段与引用映射](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/mapping/spg_type_mapping.py)
- [Schema 约束的实体/关系/事件抽取](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/extractor/schema_constraint_extractor.py)
- [BatchVectorizer](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/vectorizer/batch_vectorizer.py)
- [KGWriter UPSERT/DELETE](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/builder/component/writer/kg_writer.py)
- [OpenSPG Graph API 与 leadTo 推理写回](https://github.com/OpenSPG/openspg/blob/v0.8/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi/GraphController.java)
- [OpenSPG Reason API](https://github.com/OpenSPG/openspg/blob/v0.8/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi/ReasonController.java)
- [KAG Logical Form parser](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/parser/logic_node_parser.py)
- [KAG static Planner](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/planner/lf_kag_static_planner.py)
- [KAG static Solver Pipeline](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/pipeline/kag_static_pipeline.py)
- [KAG hybrid retrieval executor](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/executor/retriever/kag_hybrid_retrieval_executor.py)
- [KAG Math Executor](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/executor/math/py_based_math_executor.py)
- [KAG Deduce Executor](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/executor/deduce/kag_deduce_executor.py)
- [KAG 带引用的 Generator](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/generator/llm_index_generator.py)
- [官方供应链示例](https://github.com/OpenSPG/KAG/tree/v0.8.0/kag/examples/supplychain)
- [官方供应链 Schema](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/SupplyChain.schema)
- [官方供应链 concept.rule](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/concept.rule)
