# 事件驱动投研 Agent 真实推理 Demo 设计

> 状态：Draft，供实施前持续评审
>
> 版本：0.5.0
>
> 日期：2026-08-24
>
> 适用仓库：tidewise-reason
>
> 方法论上游：[事件驱动定性投研方法论 Spec](../specs/event-driven-investment-research-methodology.md)
>
> 本文设计从真实案例反向识别领域对象、补齐权威数据、投影 Graphiti、构建 Codex 工具并
> 完成首次真实推理的步骤；当前仍处于设计阶段，没有向 PostgreSQL、Neo4j 或 Graphiti
> 写入案例数据。

## 0. 已冻结的设计原则

本方案冻结以下十条原则。

1. **产业数据只取数据库。** 案例中的 IndustryChain、全部 ChainNode、membership 和
   topology Link 必须来自当前 PostgreSQL；不虚构产业链、节点或跨链关系。
2. **Event 只有一种。** 不区分 ResearchEvent、ScenarioEvent。真实事件和模拟事件使用
   同一 Data Event payload；`modality` 属于 Event，案例类别和评估隔离属于 CaseConfig / Reason
   ProjectionMeta，不向正式 Event 临时增加 `event_type` 或本地投影字段。
3. **不滥造数据概念。** 领域数据只围绕现有的 Event、Entity、Link、Storyline、Evidence、
   Variable 和 Signal。不同业务含义使用各自的 `type`。
4. **AgentContext 是执行核心。** Graphiti/数据库负责把必要事实放入 AgentContext，
   Codex/LLM 通过一次分析中的多轮理解、检索、假设、反方审议和修订形成结论。
5. **算法是护栏，不是投研替身。** 确定性算法校验 PIT、ID、数据库 Link、Schema、周期、
   引用和节点覆盖；方向、机制、周期解释和叙事由 Agent 提议，不写死为自动传播规则。
6. **Signal 必须有影响周期。** 每个 Signal 及每一次下游传导都要有 onset、peak、decay/end、
   transmission lag、依据、反方和失效条件；未知可以成为合法结果。
7. **各工序不混责。** Event Curation 只发布可信 5W1H；Graphiti Ingestion 只识别推理必要
   mention、匹配规范 Anchor 并建立 reviewed Event Anchor Link；Event Analysis 只生产直接
   Signal、影响周期和 Storyline 路由；Investment Reasoning 才负责产业传导、价值捕获、
   市场预期差、可投资映射和机会/风险判断。
8. **节点受益不等于可投资。** 节点经营影响、价值捕获、市场预期差和投资载体映射必须
   分层表达；缺少任一层时保留 UNKNOWN、机会候选或停止，不得直接输出证券方向。
9. **领域模型由 Demo 反向产生。** 先明确本次真实推理问题和输出，再识别必须进入
   Graphiti 的对象、字段和关系；不得为了未来通用性预建与本例无关的 Schema。每个缺口
   必须逐项映射到 PostgreSQL owner，只有权威业务事实缺失时才扩展表、字段或 Link。
10. **Evidence 不进入下游推理。** Evidence→Event 是独立的清洗、拆分、核验和发布工序；
    Event Analysis 与 Investment Reasoning 都从已发布 Event 开始。Codex 的 AgentContext
    不包含 Evidence 正文、摘要或片段，推理结果只直接引用 Event；Evidence 仅保留为 Event
    的上游 provenance 和审计来源。

第一批研究宇宙统一采用数据库中的两条产业链：

```text
ICHed1... 稀土资源与分离冶炼产业链
  稀土精矿 → 分解浸出 → 混合稀土溶液 → 萃取分离 → 稀土分离氧化物
                                                                  │ 共享数据库节点
ICH9d2... 磁性材料产业链                                          │
  稀土分离氧化物 → 钕铁硼合金 → 稀土永磁材料 → 永磁驱动电机 → 新能源汽车电驱系统
```

两条链通过同一个数据库 Entity `CND590...`「稀土分离氧化物」自然拼接，共 9 个唯一节点、
8 条数据库 Link。这里没有补边，也没有案例专用拓扑。

四组分层案例和三个候选扩展场景为：

```text
分层案例
├─ GEO-01       地缘政治实体 + 出口许可 Event
├─ MACRO-01     宏观政策实体 + 总量调控 Event
├─ INDUSTRY-01  数据库产业链 + 跨境供给中断 Event
└─ COMPANY-01   数据库 Company + 财报 Event（独立停止条件案例）

端到端场景
├─ SCN-GEO       地缘 Event → 产业链发现 → 9 节点多周期分析
├─ SCN-MACRO     政策 Event → 产业链发现 → 9 节点多周期分析
└─ SCN-INDUSTRY  产业 Event → 产业链发现 → 9 节点多周期分析
```

COMPANY-01 不是强行接在三条路径末端的预设答案。当前数据库没有 Company→ChainNode
和 Company→Security Link，因此它用于验证 Agent 能否在企业身份真实、财报 Event 可分析，
但经营暴露关系不足时停止，不通过名称相似生成个股结论。

第一步只实现一个真实纵向 Demo。本文保留其余案例作为后续扩展方向，但不会在首次运行前
为任何案例冻结下游 Variable、Signal、节点方向或最终结论。首次运行的结果由专业投研评审
判断，评审意见再反向修正领域模型和执行流程。

## 1. 范围和验收目标

### 1.1 四层数据与三个场景

| 分层案例    | 主要 Entity type                    | case_family  | 用途                               |
| ----------- | ----------------------------------- | ------------ | ---------------------------------- |
| GEO-01      | GEOPOLITIC_RIVALRY、COUNTRY         | GEOPOLITICAL | 宏观地缘语义、地域 Scope、出口约束 |
| MACRO-01    | MACRO_ECONOMIC、COUNTRY             | MACRO_POLICY | 政策公布、生效和经营兑现分离       |
| INDUSTRY-01 | INDUSTRY_CHAIN、CHAIN_NODE、COUNTRY | INDUSTRY     | 供给中断沿真实产业 Link 的传导     |
| COMPANY-01  | COMPANY                             | CORPORATE    | 财报内容、经营 Signal 和停止门禁   |

前三组各运行一条端到端场景。COMPANY-01 独立验证公司层，不要求前三条场景必须推导到
Company 或 Security。

### 1.2 第一批要证明什么

- 一个真实 Event 能在不读取 Evidence 内容的情况下启动完整推理；
- Agent 能从已发布 Event 的结构化 5W1H 中提出规范 Entity 候选；
- 候选可以落到数据库真实 ID，并通过 membership 找到 IndustryChain；
- Agent 能从 Variable 目录选择变量并提出多个 Signal，而非一个统一“利好/利空”；
- Agent 能在多轮中按需补取 Event、Entity、Link、Signal 和 Storyline；
- Agent 只沿数据库 Link 提出下游影响，但不机械传播每一条 Link；
- 每条 AFFECTED 链的全部 membership 节点都有 short、medium、long 结果，允许 UNKNOWN 或
  INSUFFICIENT_EVIDENCE；
- Event 与 Signal 能以不同 Link type 进入 Storyline；
- Event Pipeline 只产生直接 Signal，不混入下游传播或节点机会结论；
- Investment Pipeline 能区分节点经营影响、价值捕获、市场预期差和可投资映射；
- 每个受影响节点能够输出 OPPORTUNITY_CANDIDATE、RISK_POINT、MIXED、NO_CLEAR_EDGE 或
  INSUFFICIENT_EVIDENCE；
- 缺少真实 Company/Security/Concept/Index Link 时，结果明确 UNMAPPED 而不是编造标的；
- Storyline v0 能保存窗口外仍有效的历史 Signal，分析后形成可审计的 v1 thesis delta；
- 结果能直接回到 Event、Entity、Link、Variable、Signal 和 Storyline；Event 可通过独立审计
  链路回到 Evidence；
- 数据缺失、关系过粗或机制不成立时，Agent 能停止或降低置信度。

这里的“证明”不是要求模型命中预设方向。首次 Demo 只判断：输入是否真实且充分、推理是否
沿真实对象和关系展开、结论是否有业务机制、周期和停止条件，以及专业投研人员是否认为
它形成了可讨论的分析。任何与设计者直觉不同但逻辑完整的结果都保留进入人工复盘。

### 1.3 首次真实 Demo 的问题和最小领域面

首次 Demo 的问题为：

> 截至指定 decision_at，一个已清洗发布的稀土供给或政策 Event 会影响哪些数据库产业链，
> 各节点的短、中、长期经营趋势、潜在机会或风险是什么，推导依据和失效条件是什么？

仅由这个问题反向得到以下最小领域对象：

| 对象      | 本次为什么需要                                              |
| --------- | ----------------------------------------------------------- |
| Evidence  | 仅用于上游清洗、拆分和审核 Event，不进入 Codex 推理 Context |
| Event     | 两条推理 Pipeline 的事实起点                                |
| Entity    | 承载 Country、Region、IndustryChain、ChainNode、Company 等  |
| Variable  | 统一供给、价格、成本、库存、产能、需求等变化口径            |
| Signal    | 表达 Variable 在某 Entity 上的方向、机制和影响周期          |
| Storyline | 保存 Anchor 的 prior thesis 和本轮可审计变化                |
| Link      | 表达所有事实关联、产业拓扑、Signal 传导和 Storyline 关联    |

首次 Demo 必须支持以下关系，不为本例暂时用不到的对象预建通用关系：

```text
Evidence ──PROVENANCE_FOR──> Event              # 只供上游审计
Event ──EVENT_ENTITY(role)──> Entity
Event ──PRODUCES──> Direct Signal
Signal ──DESCRIBES──> Variable
Signal ──APPLIES_TO──> Entity
IndustryChain ──CONTAINS──> ChainNode
ChainNode ──INPUT_TO / IS_COMPONENT_OF / DEPENDS_ON──> ChainNode
Signal ──TRANSMITS_TO──> Signal                 # 每跳引用真实 topology Link
Storyline ──ANCHORED_TO──> Entity
Storyline ──ASSOCIATED_WITH──> Event / Signal
Company ──EXPOSED_TO──> ChainNode               # 只有推导到公司时才成为必需
```

其中 Evidence→Event 可以存入 Graphiti 供审计，但下游 Context assembler 必须过滤 Evidence
节点和正文。Reasoning Tree 从 Event 开始，不从 Evidence 开始。

### 1.4 当前不做

- 多因子、机器学习收益预测、量化回测或自动交易；
- 目标价、精确涨跌幅和仓位建议；
- 用图路径存在替代经济因果；
- 将模拟 Event/Evidence 混入生产数据；
- 让 Codex 自由执行任意 Cypher 或直读 Data PostgreSQL；
- 在没有 Company→Security、估值和预期数据时输出“买入”或“可持有”；
- 持久化或依赖模型内部不可验证的原始思维链。

## 2. 当前系统事实

### 2.1 PostgreSQL 快照

截至 2026-08-23，本地已应用 migration 68。只读统计为：

| 表                                 | 记录数 | 本案例含义                      |
| ---------------------------------- | -----: | ------------------------------- |
| raw_evidences                      |  1,366 | 已有来源材料                    |
| evidences                          |  1,954 | 已有 Atomic Evidence            |
| events / event links               |      0 | 尚无正式 Event 数据             |
| geopolitic_rivalries               |      0 | GEO Entity 需用评估夹具         |
| macro_economics                    |      0 | MACRO Entity 需用评估夹具       |
| industry_chain                     |    709 | 必须从中取案例链                |
| chain_node                         |  3,051 | 必须从中取案例节点              |
| industry_chain_node_memberships    |  3,352 | 必须冻结完整 membership         |
| industry_chain_graph_edges         |  2,645 | 必须只使用 approved/active Link |
| company                            | 13,264 | 可复用 Company 身份             |
| company_industry_links             |      0 | 无 Company→Industry 暴露        |
| storylines / storyline_event_links |      0 | 第一批使用隔离评估 Storyline    |
| storyline_domains                  |     35 | 可复用分类目录                  |

### 2.2 当前 Event 和 API 缺口

Data 的 events 表已有 5W1H、FACT/PLAN/SPEC、时间和 Evidence Link，但实体 Link 仍是弱
合同：actor_id 无规范外键，角色枚举不足，event_asset_links 又把 POSITIVE/NEGATIVE
混入事实关联。

版本化 API 能读取 Evidence、Event 列表、IndustryChain、ChainNode 和部分 research graph；
尚无完整 GPR、MacroEconomic、Company、Storyline 和 Event authoring API。Reasoning
Server 不得为方便直写 Data PostgreSQL。案例使用经审核的数据库导出片段；生产化前由
Data Service 补齐正式读取/写入合同。

Data 已有 `ResearchThemeImportRequest`、`ResearchThemeSnapshotItem` 和
`ResearchReasoningTreeSnapshotImportItem`，能够发布一句话结论、主题影响和展示型推理树。
案例最终结果应优先对齐这些现有产物，而不是另造一套对外发布模型；Reason 内部仍需保存
更丰富的 operating impact、value capture、expectation gap、逐周期结果和 lineage，再通过
确定性 mapper 生成 Data `analyst_snapshot`。Local Evaluation 不向 Data 发布模拟 Event
或 Theme。

当前 Storyline 没有可供 Reason 使用的完整版本化读写 API；Data Research Theme 是一次
不可变发布结果，不能替代跨多次分析持续演进的 Storyline。真实 Demo 暂由 Reason
Artifact Store 保存隔离的 Storyline v0/v1，生产化前再冻结跨服务合同。

### 2.3 投资机会数据缺口

当前数据库产业链和节点拓扑足以验证经营传导，但尚不足以确认具体可投资机会：

- 没有 ChainNode/IndustryChain→Company 的正式经营暴露 Link；
- 没有 Company→Security 的正式发行主体 Link；
- Concept/CommodityIndex/MarketIndex 的 PIT 投资载体映射尚未形成完整案例快照；
- 缺少 decision_at 时点已清洗发布的价格、估值、盈利预期变化和市场拥挤 Event/Signal；
- 缺少部分节点议价权、成本转嫁、供应集中度、扩产周期、客户认证和替代难度 Evidence。

因此第一批前三个场景的最高合法结论是“节点机会候选/风险点”。只有完成真实投资载体
映射和市场预期证据后，才能验收“可投资机会”；COMPANY-01 继续负责验证该停止门禁。

### 2.4 Graphiti 正式 Ontology 起点

硬编码液冷 `graphiti_demo` 已退役并删除。正式 `ontology` 包从 Evidence Curation 所需的
Country、Region、Organization、Industry、Concept、IndustryChain、ChainNode 及稳定底图
Link 开始。Evidence 作为 Episode 摄取，不再被重复建模为 Entity；后续 Adapter 按底图投影、
Evidence 摄取和 Event 摄取选择不同 Ontology 子集。

### 2.5 最小领域面与 PostgreSQL 缺口检查

Graphiti Schema 只定义本次 Demo 需要表达的对象和关系。随后必须逐项与 PostgreSQL
权威模型比较，不能把“Graphiti 需要一个边”直接等同于“Data 必须新建一张表”。判断规则：

| Graphiti 需求                        | 当前 PG 情况                                | 首次 Demo 决策                                              |
| ------------------------------------ | ------------------------------------------- | ----------------------------------------------------------- |
| Evidence→Event provenance            | 已有 Event/Evidence 关系设计，但 Event 为空 | 先完成真实 Evidence→Event 清洗与发布路径                    |
| Event→Entity(role)                   | actor/asset Link 角色和目标身份不足         | 需要 Data owner 设计通用 EventEntity Link 或正式发布合同    |
| IndustryChain→ChainNode membership   | 已有复合键                                  | 直接投影，不新增 membership ID                              |
| ChainNode→ChainNode topology         | 已有 approved/active Link                   | 直接投影，保留数据库 Link ID                                |
| Variable                             | 尚无当前统一受控目录                        | 先定义 Demo 最小目录；生产 owner 和持久化位置须在实施前确认 |
| Event→Direct Signal                  | 当前 Data 不拥有此分析结果                  | 由 Reason owner 持久化，不能为方便直接写 Data PG            |
| Signal→Signal transmission           | 当前无正式合同                              | 由 Reason owner 持久化；每跳必须引用真实 topology Link      |
| Storyline→Event/Signal + version     | Data 当前 Storyline 合同不足                | Demo 由 Reason 隔离持有；生产扩展需单独 owner/API 设计门    |
| Company→ChainNode / Company→Security | 缺失                                        | 首次节点 Demo 可不补；若要求个股结论则成为 Data P0 业务缺口 |

扩展 PostgreSQL 的触发条件是：缺失项属于稳定、可复用、需要跨运行共享的权威业务事实。Signal、
Analysis Result、RunCard 等推理产物仍由 Reason owner 管理，不得全部塞入 Data PG。任何正式
迁移必须在首次 Schema 映射表评审后单独实施，本设计阶段只登记缺口。

## 3. 数据库取材：两条链、全部节点和全部 Link

### 3.1 强制取材规则

案例的产业结构必须满足：

```text
IndustryChain Entity.id ∈ Data snapshot
ChainNode Entity.id ∈ Data snapshot
membership = (industry_chain_id, chain_node_id) ∈ Data snapshot
topology Link.id ∈ industry_chain_graph_edges
topology Link.status = active
topology Link.review_status = approved
```

`industry_chain_node_memberships` 没有单独 ID，数据库身份是复合键
`(industry_chain_id, chain_node_id)`。执行配置必须原样保留复合键，不伪造 membership ID。
该约束来自 Data migration 中的复合主键和 edge 外键合同：
[000027_add_typed_master_data_schema.sql](../../../tidewise-ai/data-service/backend/migrations/000027_add_typed_master_data_schema.sql)。

Data research-graph 查询按 `industry_chain_id` 约束边和 membership，因此必须显式请求下列
两条链。不能只查第一条链，再靠全库端点扫描“偶然发现”第二条链。
当前查询实现见
[internal/data/entity/data.go](../../../tidewise-ai/data-service/backend/internal/data/entity/data.go)。

本文已通过只读数据库审计逐项记录两条链和节点/edge ID，但尚未生成可执行的
entities/links 数据文件和 snapshot hash。因此目前可以确认“设计没有虚构产业拓扑”，还
不能确认当前 Data 读取合同足以直接投影本例。该问题进入 Phase 1 的 Schema→PG 映射，
不再作为“冻结标准测试数据”的前置任务。

### 3.2 ICHed1：稀土资源与分离冶炼产业链

- Entity ID：`ICHed1a9d5c-6531-506f-bcd0-7ea12ff3e759`
- observable variables：开采配额、分离配额、产量、价格、回收量
- 5 个 membership、4 条 approved/active `input_to` Link，无孤立节点

| position / stage | ChainNode Entity ID                       | 名称                 |
| ---------------- | ----------------------------------------- | -------------------- |
| 1 / upstream     | `CNDe6a6d0ff-7fa3-5751-970b-14b037672cb7` | 稀土精矿             |
| 2 / midstream    | `CND69b64d2c-2e9b-5ae4-a7a1-4d3cdb8a5073` | 稀土分解浸出服务     |
| 3 / midstream    | `CND5cdb05d8-4b70-547e-b59c-984d47e9878b` | 混合稀土溶液         |
| 4 / midstream    | `CNDafbf1596-2d6a-5140-a95e-3ff98187a07a` | 稀土溶剂萃取分离服务 |
| 5 / downstream   | `CND590758ed-67f9-533c-8221-b81712a71668` | 稀土分离氧化物       |

| Link ID                                   | from → to                             | link_type |
| ----------------------------------------- | ------------------------------------- | --------- |
| `IGE1094ddb2-3be3-5168-b45d-15c54586e7e9` | 稀土精矿 → 稀土分解浸出服务           | INPUT_TO  |
| `IGE0631b507-4065-5cf4-974a-fdb099e6cab0` | 稀土分解浸出服务 → 混合稀土溶液       | INPUT_TO  |
| `IGEfa9a1a18-06a2-5f57-b8d8-3ccb793a52aa` | 混合稀土溶液 → 稀土溶剂萃取分离服务   | INPUT_TO  |
| `IGE9a53d60e-3f78-545c-bdf0-8d30541ff60c` | 稀土溶剂萃取分离服务 → 稀土分离氧化物 | INPUT_TO  |

### 3.3 ICH9d2：磁性材料产业链

- Entity ID：`ICH9d2e55f8-42cc-53fe-9927-7a6c2363705e`
- observable variables：产量、原料价格、均价、路线结构、客户认证
- 5 个 membership、4 条 approved/active Link，无孤立节点

| position / stage | ChainNode Entity ID                       | 名称               |
| ---------------- | ----------------------------------------- | ------------------ |
| 1 / upstream     | `CND590758ed-67f9-533c-8221-b81712a71668` | 稀土分离氧化物     |
| 2 / upstream     | `CNDd150620f-7ccf-5132-8b68-a44910422357` | 钕铁硼合金         |
| 3 / midstream    | `CND9d9243c0-ec40-58ab-a0e8-67697d620dad` | 稀土永磁材料       |
| 4 / midstream    | `CND717f1044-ecb6-59d7-b108-06880b5a1976` | 永磁驱动电机       |
| 5 / downstream   | `CNDfbd72cb7-900b-5811-bffa-4a489d136649` | 新能源汽车电驱系统 |

| Link ID                                   | from → to                         | link_type       |
| ----------------------------------------- | --------------------------------- | --------------- |
| `IGEef3c4e57-c2e5-5398-a4fd-51e75a9687bb` | 稀土分离氧化物 → 钕铁硼合金       | INPUT_TO        |
| `IGE61fdd2c0-3bc4-51ea-ab72-c8dd7a77a3a5` | 钕铁硼合金 → 稀土永磁材料         | INPUT_TO        |
| `IGE23cd1055-e378-5c25-9d2d-61070c4446d8` | 稀土永磁材料 → 永磁驱动电机       | IS_COMPONENT_OF |
| `IGE2b009fd7-3aa3-58a9-ae6e-7e542151ddac` | 永磁驱动电机 → 新能源汽车电驱系统 | IS_COMPONENT_OF |

### 3.4 合并后的数据库研究图

`CND590...` 同时是第一条链的 downstream membership 和第二条链的 upstream membership。
因此合并后的数据库数据片段有 9 个唯一 ChainNode Entity、10 个 membership 复合键、8 条
topology Link。

`IGEef3...` 是数据库中正式 approved/active Link，但粒度较粗：从“稀土分离氧化物”直接
到“钕铁硼合金”，省略金属化、配料和熔炼工序。它可以进入 AgentContext，却不自动证明
成本、产量或价格方向。Agent 必须说明该 Link 只是聚合层供给关系；若问题需要精细工艺
机制，应降低置信度、请求相关 Event/Signal，或在该处输出 INSUFFICIENT_EVIDENCE。

### 3.5 可复用的规范 Entity

Country：

| Entity ID                                 | 名称 |
| ----------------------------------------- | ---- |
| `COU4e58f424-f51a-58e8-b883-c54c9fafcda3` | 中国 |
| `COUb7e8c768-79c4-5b2e-a7ff-2e12531f6b88` | 美国 |
| `COUe2f73701-345c-542f-984d-e42e47ddac3c` | 缅甸 |

Company：

| Entity ID                                 | 名称     | 当前可证明的内容 |
| ----------------------------------------- | -------- | ---------------- |
| `COMb078d159-6968-5002-b4b1-0096984e51e2` | 北方稀土 | Company 身份     |
| `COM75c45bc4-5c39-550c-a441-4086e4cae2de` | 中国稀土 | Company 身份     |
| `COM39fecaa9-4eb9-5259-852c-813a47bee49f` | 盛和资源 | Company 身份     |
| `COMfd34186c-3357-507b-a8de-3f5abc33e8bb` | 金力永磁 | Company 身份     |
| `COM72acaa15-1983-5c73-856e-0072fed913ff` | 中科三环 | Company 身份     |
| `COMe93583d3-cc50-5a97-b670-3a2654e73717` | 正海磁材 | Company 身份     |

当前不能从这些身份记录推出经营节点、收入暴露或证券关系。方案不增加测试用
Company→ChainNode Link。

### 3.6 可复用的 Evidence

| Evidence ID                               | 摘要                                                      | 用法                                            |
| ----------------------------------------- | --------------------------------------------------------- | ----------------------------------------------- |
| `EVD2a295483-a921-58c9-94c8-510cd0fc96ba` | L3 分析同时提到配额下调、缅甸进口收缩、出口管制和量缩价涨 | 复合辅助佐证；不可重复计权或充当三条主 Evidence |
| `EVD5ac3216b-9cc6-5e55-9a28-f051115f0bdd` | L2 稀土检测与溯源技术进展                                 | 技术上下文，不支持供给方向结论                  |
| `EVD437f230f-2de2-5ac2-bb11-983b001c936e` | 稀土等属于战略资源                                        | 背景 Evidence，不直接产生 Signal                |
| `EVD3a456c32-f366-51dc-8866-e95fbb7f561c` | 北方稀土等融资净偿还                                      | 市场观察，不能反向证明基本面机制                |

这些 Evidence 只作为 Event Curation Work 的候选输入，不进入后续 Codex AgentContext。
`EVD2a295...` 同时混合配额、进口、出口和价格结论，首次工作必须先判断能否拆成多个独立 Event，
不能将整段材料直接作为一个“稀土利好”Event。Event 清洗结果经审核发布后，Event Analysis 只
消费 Event payload、Event ID、known-at 结果和 provenance 标识。

## 4. 统一数据合同

### 4.1 七类顶层领域数据

| 顶层类型  | type / 分类                                                         | 第一批 owner                        | 说明                                     |
| --------- | ------------------------------------------------------------------- | ----------------------------------- | ---------------------------------------- |
| Evidence  | SOURCE_DOCUMENT、ATOMIC_EVIDENCE                                    | Data                                | 仅供上游 Event 清洗、发布和审计          |
| Event     | 不增加 Event type；领域视角由 Entity Link/Storyline/CaseConfig 表达 | Data；评估 Event 由 Reason 隔离持有 | 统一 Data Event，不分 Research/Scenario  |
| Entity    | COUNTRY、GPR、MACRO_ECONOMIC、INDUSTRY_CHAIN、CHAIN_NODE、COMPANY   | Data 为正式实体 owner               | 稳定对象；案例链和节点只能来自 Data      |
| Link      | `EVENT_*`、CHAIN_CONTAINS_NODE、INPUT_TO、`SIGNAL_*`、`STORYLINE_*` | 按端点和语义分 owner                | 所有关系统一由 link_type 区分            |
| Variable  | POLICY_RESTRICTION、SUPPLY、PRICE、COST、CAPACITY 等                | Reasoning（生产 owner 待确认）      | 本例最小受控变量目录                     |
| Signal    | derivation=OBSERVED/DERIVED；modality=ACTUAL/ANTICIPATED 等         | Reasoning                           | Event 对 Anchor 上 Variable 的带周期判断 |
| Storyline | GEOPOLITICAL、MACRO、INDUSTRY、CORPORATE                            | Data/Reason 待最终冻结              | 版本化投研论题                           |

Reason/Graphiti 为每个投影对象单独保存 `ProjectionMeta`：

```yaml
projection_mode: LIVE | LOCAL_EVALUATION
projection_namespace: string | null
projection_source_key: string | null
```

这些是投影与评估元数据，不是 Data Event/Entity payload 字段。LIVE 要求 namespace/key 为
null；LOCAL_EVALUATION 要求二者非空。评估 Link 可以只读引用
LIVE 的稳定 Entity 和 Variable，但 Link 自身必须属于评估 namespace；不得从 LIVE 分析数据
反向引用 LOCAL_EVALUATION，也不得跨两个评估 namespace。评估对象 canonical ID 使用：

```text
type_prefix + UUIDv5(reasoning_projection_namespace_uuid,
                     projection_namespace + "|" + top_level_type + "|" + projection_source_key)
```

文中的 `EVT-DEMO-*` 是便于讨论的本地 alias，不是最终 canonical ID。
GEO、MACRO、INDUSTRY、COMPANY 使用各自 case 子 namespace；同属 rare-earth/v1 不代表可以
互相检索 Event/Signal/Storyline。

不新增案例专用拓扑对象、ScenarioEvent、TransmissionStep 或关系引用对象等顶层类型。
Signal 之间一次传导仍是一条 Link；所依据的数据库 topology Link ID 保存在这条 Link 的
属性中。

### 4.2 必要的执行概念

本方案增加以下执行产物，它们不是领域图谱数据：

| 概念                     | 用途                                                              | owner / 持久化             |
| ------------------------ | ----------------------------------------------------------------- | -------------------------- |
| ProjectionMeta           | 保存 LIVE/LOCAL namespace、source key/hash 等投影元数据           | Reasoning / Projection     |
| CaseConfig               | 声明问题、时点、Event ID 和硬边界，不保存业务答案                 | Reasoning / Git JSON       |
| AgentContext             | 一次分析在 decision_at 可用的数据包，可在多轮工具调用中增量扩充   | Reasoning / Artifact Store |
| EventAnalysisPackage     | Event Pipeline 的直接实体关系、直接 Signal、周期和 Storyline 路由 | Reasoning / Artifact Store |
| InvestmentAnalysisResult | Anchor 的多周期机会/风险结果、一句话结论和结构化推理树            | Reasoning / Artifact Store |
| RunCard                  | 记录模型、Prompt、Tool、数据哈希、轮次和最终产物引用              | Reasoning / Artifact Store |

新增它们的原因是领域数据本身无法表达“本次运行看到了什么、两条 Pipeline 如何交接、用了
哪个版本、是否覆盖全部节点”。它们不得写成 Event、Entity 或 Evidence，也不作为事实节点
进入 Graphiti。LIVE 分析审核后，可以把 InvestmentAnalysisResult 确定性映射到 Data 现有
Research Theme / Research Reasoning Tree `analyst_snapshot` 发布合同。

### 4.3 CaseConfig

```yaml
schema_version: reasoning-case/v1
case_id: RARE-EARTH-REAL-01
case_family: DISCOVER_FROM_EVENT
projection_namespace: demo/rare-earth/real-01
projection_mode: LOCAL_EVALUATION
grounding_mode: AGENT_DISCOVERY
decision_at: 2026-08-23T00:00:00Z
trigger_window: P4D
question: ...
horizons: [short, medium, long]
input_ids:
  event_ids: [EVT...]
variable_catalog_version: rare-earth/v1
hard_constraints:
  forbid_non_database_chain_entities: true
  forbid_non_database_memberships: true
  forbid_non_database_topology_links: true
  forbid_evidence_content_in_reasoning_context: true
  forbid_predefined_signal_directions: true
```

CaseConfig 只声明真实 Event、问题、时点和不可伪造的硬约束，不保存候选产业链、预期
Signal、节点方向或最终结论。首次 Demo 使用 `AGENT_DISCOVERY`：初始 Context 不提供已确认的
Event→IndustryChain/ChainNode Subject Link，由 Agent 从 Event 5W1H 提议，工具再以正式 ID
和关系确认。GEO、MACRO、INDUSTRY、COMPANY 的边界 CaseConfig 只在首次真实闭环之后建立。

### 4.4 Event：同一个合同覆盖正式和模拟

```yaml
id: <deterministic typed UUIDv5>
modality: FACT | PLAN | SPEC
title: string
summary: string
semantic:
  who: string | null
  what: string
  when: string | null
  where: string | null
  why: string | null
  how: string | null
occurred_at: timestamp | null
announced_at: timestamp | null
lifecycle: ACTIVE | DEPRECATED | ARCHIVED

projection_meta:
  projection_mode: LIVE | LOCAL_EVALUATION
  projection_namespace: string | null
  projection_source_key: string | null
  computed_known_at: timestamp
  provenance_audit_ref: string
  source_independence_group: string
```

规则：

- 模拟一个已发生的事实仍可使用 `modality=FACT`；是否属于评估世界由 ProjectionMeta 表达；
- LOCAL_EVALUATION Event 只能关联相同 namespace 的 Signal、Storyline 和
  Reasoning Link；可以只读引用 LIVE 稳定 Entity/Variable，但不能修改它们；
- 正式与模拟 Event 使用同一套 Link、AgentContext 和推理工具；
- `computed_known_at` 由 Event Curation 根据上游发布时间等依据计算并发布；下游只消费结果
  和 `provenance_audit_ref`，缺少可证明时间时 PIT fail closed；
- Event 不增加 `event_type/effective_at/valid_from/valid_to/factual_status`；业务影响开始和结束
  属于 Signal impact window；
- Event 的事实 Link 不保存 POSITIVE/NEGATIVE。

### 4.5 Entity 与 Link

Entity 最小引用：

```yaml
id: canonical ID
entity_type: COUNTRY | GEOPOLITIC_RIVALRY | MACRO_ECONOMIC |
  INDUSTRY_CHAIN | CHAIN_NODE | COMPANY | SECURITY | ...
name: string
projection_mode: LIVE | LOCAL_EVALUATION
projection_namespace: string | null
projection_source_key: string | null
source_owner: DATA | REASONING
```

Link 最小合同：

```yaml
identity_kind: DATABASE_ID | DATABASE_COMPOSITE_KEY | REASONING_ID
id: database or reasoning ID | null
source_composite_key:
  industry_chain_id: string | null
  chain_node_id: string | null
projection_id: deterministic technical ID | null
link_type: string
from_ref: { type: EVENT | ENTITY | SIGNAL | STORYLINE | EVIDENCE, id: string }
to_ref:
  {
    type: EVENT | ENTITY | SIGNAL | STORYLINE | EVIDENCE | VARIABLE,
    id: string,
  }
known_at: timestamp
valid_from: timestamp | null
valid_to: timestamp | null
projection_mode: LIVE | LOCAL_EVALUATION
projection_namespace: string | null
projection_source_key: string | null
source_owner: DATA | REASONING
source_table: string | null
source_snapshot_hash: string
source_event_ids: []
properties: {}
```

`CHAIN_CONTAINS_NODE` 必须使用 `identity_kind=DATABASE_COMPOSITE_KEY`，其
`source_composite_key` 就是数据库 `(industry_chain_id, chain_node_id)`。Graphiti 如需技术
标识，可以生成 `projection_id`，但不得把它冒充数据库 membership ID。Topology Link 使用
`DATABASE_ID`；Signal/Storyline 等分析 Link 使用 `REASONING_ID`。

第一批关键 link_type：

```text
EVIDENCE_SUPPORTS_EVENT
EVENT_ACTOR_ENTITY
EVENT_SUBJECT_ENTITY
EVENT_TARGET_ENTITY
EVENT_LOCATION_ENTITY
EVENT_JURISDICTION_ENTITY
EVENT_INVOLVES_ENTITY

CHAIN_CONTAINS_NODE
NODE_INPUT_TO_NODE
NODE_IS_COMPONENT_OF_NODE
NODE_DEPENDS_ON_NODE

EVENT_PRODUCES_SIGNAL
SIGNAL_APPLIES_TO_ENTITY
SIGNAL_USES_VARIABLE
SIGNAL_TRANSMITS_TO_SIGNAL

STORYLINE_ANCHORED_TO_ENTITY
STORYLINE_INCLUDES_EVENT
STORYLINE_USES_SIGNAL
```

Event Anchor Link 由 Graphiti Ingestion 从 Event 5W1H 提议、规范 ID 和关系门禁确认，并以
Graphiti 为运行时关系源；它只连接直接推理锚点和必要范围/机制 Entity，不连接所有 mention，
也不提前连接产业传播产生的间接受影响节点。产业 membership 和 topology Link 只能读取
数据库，不允许 Reason 创建替代 Link。Context loader 与 verifier 必须按复合键或正式 edge ID
回查同一个 source snapshot。

### 4.6 Variable 目录

Variable 是版本化白名单，不允许 LLM 临时创造同义名称绕过校验。

| variable_id                  | 含义                               | 允许 Anchor                             |
| ---------------------------- | ---------------------------------- | --------------------------------------- |
| export_control_intensity     | 出口限制、许可或最终用途审查强度   | GPR、MacroEconomic、ChainNode           |
| licensing_lead_time          | 许可申请到批准/拒绝的时间          | ChainNode、Company                      |
| cross_border_supply_access   | 指定地域获得跨境产品的可得性       | ChainNode、Company                      |
| policy_restriction_intensity | 配额、监管或行政约束强度           | MacroEconomic、IndustryChain、ChainNode |
| approved_production_quota    | 获批的开采或分离额度               | IndustryChain、ChainNode                |
| deliverable_supply           | 合同和物流条件下可交付供给         | ChainNode、Company                      |
| production_volume            | 实际产量                           | ChainNode、Company                      |
| physical_installed_capacity  | 机器、厂房和工艺形成的物理产能上限 | ChainNode、Company                      |
| inventory_coverage           | 库存覆盖周期                       | ChainNode、Company                      |
| input_availability           | 关键投入可得性                     | ChainNode、Company                      |
| capacity_utilization         | 实际开工/利用率                    | ChainNode、Company                      |
| market_supply                | 给定 Scope 内有效供给              | ChainNode                               |
| selling_price                | 销售价格或趋势                     | ChainNode、Company                      |
| input_cost                   | 目标节点投入成本                   | ChainNode、Company                      |
| market_demand                | 给定 Scope 内现实或预期需求        | ChainNode                               |
| order_visibility             | 可验证订单和订单前景               | ChainNode、Company                      |
| bargaining_power             | 上下游价格转嫁能力                 | ChainNode、Company                      |
| substitution_pressure        | 替代来源、材料或技术压力           | ChainNode、Company                      |
| revenue_growth               | Company 已实现收入变化             | Company                                 |
| gross_margin                 | Company 已实现毛利率变化           | Company                                 |
| inventory                    | Company 已披露库存变化             | Company                                 |
| cash_flow_pressure           | 经营现金流或营运资本压力           | Company                                 |
| capacity_ramp                | 新产能爬坡状态或来源指引           | Company                                 |

关键隔离规则：approved quota 不等于 physical installed capacity 或 actual production；
deliverable supply 不等于 physical installed capacity；selling price 上升不等于 Company gross margin 上升；market demand 不等于
order visibility 或 realized revenue。

### 4.7 Signal 与影响周期

Signal 的身份为：

```text
Event × Anchor Entity × Scope × Variable × Mechanism × Impact Window
```

最小合同：

```yaml
id: deterministic ID
projection_source_key: string | null
derivation_type: OBSERVED | DERIVED
projection_mode: LIVE | LOCAL_EVALUATION
projection_namespace: string | null
source_event_ids: []
anchor_entity_id: string
variable_id: string
scope:
  jurisdictions: []
  market: string | null
  product_grade: string | null
  end_use: string | null
direction: UP | DOWN | MIXED | STABLE | UNKNOWN
assertion_modality: ACTUAL | ANTICIPATED | SOURCE_FORECAST | ASSUMED
review_status: PROPOSED | REVIEWED | REJECTED
lifecycle_state: INACTIVE | ACTIVE | DECAYING | EXPIRED | INVALIDATED | SUPERSEDED
known_at: timestamp
effective_at: timestamp | null
horizon_tags: [short, medium, long]
mechanism: string
impact_window:
  onset_earliest: timestamp | null
  onset_latest: timestamp | null
  peak_earliest: timestamp | null
  peak_latest: timestamp | null
  decay_starts_earliest: timestamp | null
  decay_starts_latest: timestamp | null
  expected_end_earliest: timestamp | null
  expected_end_latest: timestamp | null
  transmission_lag_min: duration | null
  transmission_lag_max: duration | null
  duration_basis: POLICY_TERM | INVENTORY | ORDER_CYCLE | CAPACITY_CYCLE |
    CONTRACT | HISTORICAL_ANALOG | EXPERT_ASSUMPTION | UNKNOWN
  decay_rule: string | null
  unknown_reason: string | null
  observations_to_resolve_unknown: []
  next_review_at: timestamp
magnitude: LOW | MEDIUM | HIGH | UNKNOWN
magnitude_basis:
  method: DETERMINISTIC_CALCULATION | EVENT_STATEMENT | HISTORICAL_ANALOG |
    EXPERT_ASSUMPTION | UNKNOWN
  artifact_refs: []
  explanation: string
confidence:
  event_provenance: LOW | MEDIUM | HIGH
  mechanism: LOW | MEDIUM | HIGH
  temporal: LOW | MEDIUM | HIGH
assumptions: []
counter_signal_ids: []
invalidation_conditions: []
```

`direction`、`assertion_modality`、`review_status` 和 `lifecycle_state` 是四个正交字段。例如
“预计供给下降、政策尚未生效”应写成 `direction=DOWN`、
`assertion_modality=ANTICIPATED`、`review_status=REVIEWED`、
`lifecycle_state=INACTIVE`，不能写成 `direction=DOWN/ANTICIPATED`。

`horizon_tags` 由 impact window 派生，只用于检索和 Storyline 路由，不参与 Signal 唯一
身份。`derivation_type` 只说明 Signal 来自原始观察还是分析推导；ACTUAL、ANTICIPATED、
SOURCE_FORECAST、ASSUMED 只由 `assertion_modality` 表达。

### 4.8 Signal 传导仍然是 Link

不新增 TransmissionStep。每次源 Signal 到目标 Signal 的传导使用
`link_type=SIGNAL_TRANSMITS_TO_SIGNAL`：

以下只展示该 Link 的专用字段；identity、projection namespace、时间和来源字段继承统一 Link
合同。

```yaml
id: deterministic reasoning link ID
link_type: SIGNAL_TRANSMITS_TO_SIGNAL
from_ref: { type: SIGNAL, id: source_signal_id }
to_ref: { type: SIGNAL, id: target_signal_id }
properties:
  topology_link_id: IGE...
  topology_data_hash: sha256:...
  traversal_direction: FORWARD | REVERSE
  mechanism: string
  scope: {}
  transmission_lag_min: duration | null
  transmission_lag_max: duration | null
  impact_window:
    onset_earliest: timestamp | null
    onset_latest: timestamp | null
    peak_earliest: timestamp | null
    peak_latest: timestamp | null
    decay_starts_earliest: timestamp | null
    decay_starts_latest: timestamp | null
    expected_end_earliest: timestamp | null
    expected_end_latest: timestamp | null
    duration_basis: POLICY_TERM | INVENTORY | ORDER_CYCLE | CAPACITY_CYCLE |
      CONTRACT | HISTORICAL_ANALOG | EXPERT_ASSUMPTION | UNKNOWN
    decay_rule: string | null
    unknown_reason: string | null
    observations_to_resolve_unknown: []
    next_review_at: timestamp
  buffers: []
  substitutions: []
  necessary_conditions: []
  invalidation_conditions: []
  confidence: LOW | MEDIUM | HIGH
source_event_ids: []
```

每条跨节点 Signal Link 只引用一条数据库 topology Link。工具必须同时校验：

- `topology_link_id` 属于当前 AgentContext；
- FORWARD 时 source Signal Anchor 等于 edge.from、target Anchor 等于 edge.to；
- REVERSE 时 source Anchor 等于 edge.to、target Anchor 等于 edge.from；
- 多跳路径由多条 Signal Link 组成，前一跳 target Anchor 与后一跳 source Anchor 连续；
- 每一跳分别具有 transmission lag、impact window、duration basis 和 unknown 处理。

同一节点内两个 Signal 的变量派生不冒充 topology 传播，可以共同引用源 Event 并在 mechanism
中说明关系。Link 是否具有实际传导意义、方向和周期，由 Agent 基于 Event、Signal、
Variable、上下文和反方信息提出，不能由图遍历器自动决定。

### 4.9 Storyline

Storyline 身份为 `Anchor Entity × ResearchQuestion × Scope`，以 type 区分 GEOPOLITICAL、
MACRO、INDUSTRY 和 CORPORATE。它通过 Link 关联 Event 与 Signal：

```text
STORYLINE_ANCHORED_TO_ENTITY
STORYLINE_INCLUDES_EVENT
STORYLINE_USES_SIGNAL
```

`STORYLINE_INCLUDES_EVENT` 和 `STORYLINE_USES_SIGNAL` 的 properties 保存：

```text
role = SUPPORTS | WEAKENS | CONTRADICTS | REVERSES |
       EXTENDS | SHORTENS | TRIGGERS | CONTEXT_ONLY
route_reason
relevant_horizons
effective_from / effective_until
router_version
```

Storyline 每次发布保留 version、Base/Bull/Bear/Alternative、支持与反方 Event/Signal、数据缺口、
短中长期视图、失效条件和 next_review_at。评估 Storyline 使用相同数据类型，只以
`projection_mode=LOCAL_EVALUATION` 隔离。

### 4.10 Event Analysis Package

Event Pipeline 的交接产物必须包含：

```yaml
package_id: string
event_id: EVT...
decision_at: timestamp
event_provenance_audit_ref: string
accepted_event_entity_link_ids: []
unresolved_entity_mentions: []
direct_signal_ids: []
storyline_route_candidates:
  - storyline_id: STL...
    role: SUPPORTS | WEAKENS | CONTRADICTS | REVERSES | CONTEXT_ONLY
    reason: string
counter_event_ids: []
counter_signal_ids: []
validation_issues: []
review_status: PROPOSED | REVIEWED | REJECTED
artifact_hash: sha256:...
```

`direct_signal_ids` 只能引用 Event 直接支持的 Signal。该 Package 严禁包含
`SIGNAL_TRANSMITS_TO_SIGNAL`、下游 Node Signal、value capture 或 opportunity/risk 结论。
Investment Pipeline 只能消费 `review_status=REVIEWED` 且 hash 未过期的 Package。

### 4.11 Investment Analysis Result 与推理树

每个稳定 Analysis Anchor 形成一个结果，推理树使用嵌套执行 Schema 表达：

```text
Event
→ Direct Signal
→ Signal Transmission Link
→ Node Signal
→ Operating Impact
→ Value Capture
→ Market Expectation Gap
→ Investable Mapping
→ Opportunity/Risk Conclusion
```

推理树节点保存 statement、domain_refs、source_event_ids、assumptions、counter_refs、confidence
和 invalidation_conditions；推理树边保存 relation、mechanism、topology_link_id 和条件。
它是可审计的理由摘要，不保存模型原始隐藏思维链，不投影为 Graphiti 事实。

每次运行在数据库确实已有时才加载：

- Event 发生前的 Storyline v0；
- 超出新 Event trigger window、但仍 ACTIVE 或 DECAYING 的历史 Signal；
- 反向 Event/Signal，或明确记录真实缺失；
- 新 Event 对 v0 的作用；
- 分析后的 Storyline v1、`previous_version_id`、`thesis_delta`、新增/失效驱动和
  `next_review_at`。

DISCOVERY Context 不加载可能泄漏候选产业链的 Storyline；Anchor 通过规范 ID 门禁后，
ANALYSIS Context 才加载对应 v0。

## 5. 首次真实 Demo 与后续边界案例

### 5.0 首次真实 Demo 输入

首次运行不使用本节后续人工编写的数值 Event，也不把任何 Signal 表格作为标准答案。执行时：

1. 从当前 PostgreSQL 选择与稀土供给、配额或出口约束相关的真实 Evidence；首选候选是
   `EVD2a295483-a921-58c9-94c8-510cd0fc96ba`，但其来源等级和复合内容必须在 Event Curation
   中明确；
2. Event Curation 将一条复合材料拆成独立可审核 Event，例如配额变化、进口收缩和出口约束
   不得混成一个 Event；
3. 人工确认其中一个 Event 的 5W1H、modality、时间、lifecycle 和 known-at 后发布；
4. 下游只接收该 Event，不接收原始 Evidence；
5. 使用真实 ICHed1、ICH9d2、9 个唯一 ChainNode、membership 和 8 条 topology Link；
6. Codex 自主提出实体关联、Variable、Direct Signal、影响周期、受影响链和节点结果；
7. 不用预制方向判分，由专业投研评审记录合理、错误、遗漏和证据不足之处。

以下 GEO/MACRO/INDUSTRY/COMPANY 内容保留为真实 Demo 跑通后的边界问题草案，用于检查政策
生效日、临时供给与物理产能、区域 Scope、公司映射停止等风险。它们不是首次 Demo 输入，
其中的数值和方向不得提前写入 AgentContext 或首次推理验收。

### 5.1 GEO-01：稀土分离氧化物出口许可约束

#### Entity

- 评估 Entity：`entity_type=GEOPOLITIC_RIVALRY`，名称“中美关键矿产与高端制造博弈”；
- 正式 Country Entity：中国 `COU4e58...`、美国 `COUb7e...`；
- 隐藏验收期望的 Subject grounding：数据库 ChainNode `CND590...`「稀土分离氧化物」。

评估 GPR Entity 使用 `projection_mode=LOCAL_EVALUATION`，不伪装成当前为空的
geopolitic_rivalries 生产记录。

#### Evidence 与 Event

评估 Evidence 描述：

> 在评估世界中，中国对面向美国最终用户的部分稀土分离氧化物提高最终用途审查要求，
> 许可周期延长，2026-08-20 起实施。

统一 Event：

```yaml
id: <deterministic EVT UUIDv5>
modality: FACT
occurred_at: 2026-08-20T00:00:00Z
announced_at: 2026-08-20T00:00:00Z
projection_meta:
  projection_source_key: GEO-01/event
  projection_mode: LOCAL_EVALUATION
  projection_namespace: demo/rare-earth/v1/GEO-01
  computed_known_at: 2026-08-20T00:00:00Z
```

Graphiti Anchor Grounding 轮次应产生并通过校验的 Event Anchor Link：

```text
Event --EVENT_ACTOR_ENTITY--> 中国
Event --EVENT_JURISDICTION_ENTITY--> 中国
Event --EVENT_TARGET_ENTITY--> 美国
Event --EVENT_SUBJECT_ENTITY--> 稀土分离氧化物 CND590...
Evidence --EVIDENCE_SUPPORTS_EVENT--> Event
```

不创建不存在的 PolicyBody Entity，也不把“永磁材料”直接塞进 Event 来替代后续推导。

#### 供真实运行后讨论的直接 Signal 假设

| Anchor                     | Variable                   | direction | assertion / lifecycle | 周期边界                           |
| -------------------------- | -------------------------- | --------- | --------------------- | ---------------------------------- |
| GPR Entity                 | export_control_intensity   | UP        | ACTUAL / ACTIVE       | 生效即 onset，规则撤销或替代后衰减 |
| 稀土分离氧化物，美国 Scope | licensing_lead_time        | UP        | ANTICIPATED / ACTIVE  | 0–7 天 onset，实际许可数据校准     |
| 稀土分离氧化物，美国 Scope | cross_border_supply_access | DOWN      | ANTICIPATED / ACTIVE  | 0–30 天，受在途、库存和豁免影响    |

表内方向是设计阶段的投研假设，不进入首次 AgentContext，也不作为首次运行的正确答案。
真实运行后可以用它们讨论模型为何相同或不同。Agent 实际提出的 Signal
`review_status` 必须先为 PROPOSED；peak、decay、end 或其他尚无依据的字段必须写 UNKNOWN，
并同时填写 unknown_reason、observations_to_resolve_unknown 和 next_review_at。

其余上游和下游 Signal 必须由 Agent 在 AgentContext 中提议，不预埋固定答案。尤其不得把
出口约束自动解释为中国国内价格上涨、全球 physical installed capacity 下降或全链统一利好。

#### Storyline

- GEO Storyline：出口许可如何造成中美区域供给分化；
- ICHed1 Industry Storyline：出口端约束如何反向影响分离链产量、库存和价格；
- ICH9d2 Industry Storyline：分离氧化物可得性如何影响磁材、电机和电驱。

### 5.2 MACRO-01：稀土开采与分离总量调控

#### Entity、Evidence 与 Event

- 评估 Entity：`entity_type=MACRO_ECONOMIC`，名称“中国稀土总量调控周期”；
- 正式 Country Entity：中国 `COU4e58...`；
- 隐藏验收期望的 Subject grounding：ICHed1 以及 `CNDe6...` 稀土精矿、`CNDaf...`
  萃取分离服务；
- 评估 Evidence：当期稀土开采和分离总量控制指标较上一可比期下调 10%，
  2026-08-20 公布、2026-09-01 生效。

10% 仅是评估输入，不代表真实政策。`EVD2a295...` 只能作为同主题 L3 corroboration。

```yaml
id: <deterministic EVT UUIDv5>
modality: FACT
occurred_at: null
announced_at: 2026-08-20T00:00:00Z
projection_meta:
  projection_source_key: MACRO-01/event
  projection_mode: LOCAL_EVALUATION
  projection_namespace: demo/rare-earth/v1/MACRO-01
  computed_known_at: 2026-08-20T00:00:00Z
```

2026-09-01 的政策生效日保存在 Event `semantic.when` 和相应 Signal `effective_at` / impact
window 中，不扩展正式 Event payload。

#### PIT 必须正确

在 decision_at：

- 政策公布是已知 Event；
- policy_restriction_intensity 和 approved_production_quota 的未来变化是
  `assertion_modality=ANTICIPATED`、`lifecycle_state=INACTIVE`；
- production_volume、market_supply、price 和下游 cost 都只能是待验证 Signal；
- 行政 quota 由 approved_production_quota 表达；没有机器、厂房或工艺能力 Evidence 时，
  不产生 physical_installed_capacity Signal，或输出 UNKNOWN。不得从“未提及设备变化”
  推导 STABLE，更不得由 quota 下调推导 DOWN。

#### 必须考虑的反方

库存、回收料、进口、非法供给、实际执行偏差、需求走弱、新增资源和分离效率。不得由
quota 下调直接推出公司收入、毛利或 Security 上涨。

### 5.3 INDUSTRY-01：跨境矿源与物流阶段性中断

#### Entity、Evidence 与 Event

- 正式 Country Entity：缅甸 `COUe2f...`、中国 `COU4e58...`；
- 隐藏验收期望的 Subject grounding：数据库 ChainNode `CNDe6...`「稀土精矿」；
- 评估 Evidence：缅甸某稀土矿源因洪水和边境运输中断 21 天，合同可交付量阶段性下降
  30%，physical installed capacity 未改变；
- 30% 和 21 天仅为评估输入。

```yaml
id: <deterministic EVT UUIDv5>
modality: FACT
occurred_at: 2026-08-20T00:00:00Z
announced_at: 2026-08-20T00:00:00Z
projection_meta:
  projection_source_key: INDUSTRY-01/event
  projection_mode: LOCAL_EVALUATION
  projection_namespace: demo/rare-earth/v1/INDUSTRY-01
  computed_known_at: 2026-08-20T00:00:00Z
```

21 天中断期属于 direct Signal impact window，不作为 Event `valid_to`。

后续边界复盘会重点检查 Agent 是否有理由区分：

```text
deliverable_supply DOWN       ACTUAL / ACTIVE
physical_installed_capacity STABLE     ACTUAL / ACTIVE
```

分解浸出、萃取分离、氧化物、磁材、电机、电驱的 Signal 由 Agent 逐轮提议，必须检查库存
覆盖、原料占比、合同定价、替代来源、需求和客户认证。Event 恢复不等于所有下游影响同日
清零。

### 5.4 COMPANY-01：金力永磁财报与经营质量

#### Entity、Evidence 与 Event

- 正式 Company Entity：`COMfd34186c-3357-507b-a8de-3f5abc33e8bb` 金力永磁；
- 评估 Evidence 包含：高性能钕铁硼收入同比 +18%、毛利率同比 -2.5 个百分点、库存同比
  +30%、经营现金流承压、管理层预计新增产能未来两个季度继续爬坡；
- 所有数字均为评估输入，不与真实财报混合。

统一 Event 使用 Data payload 的 `modality=FACT`，通过 EVENT_SUBJECT_ENTITY Link 指向正式
Company；CaseConfig `case_family=CORPORATE`，ProjectionMeta namespace 为
`demo/rare-earth/v1/COMPANY-01`。

Agent 可提出 revenue_growth、gross_margin、inventory、cash_flow_pressure 和 capacity_ramp
Signal，但必须区分实际披露与管理层 SOURCE_FORECAST。

#### 停止门禁

数据库没有 Company→ChainNode、Company→Security Link，故：

- 不创建测试 OPERATES_AT/PRODUCES_AT Link；
- 不以公司名称推断其产业节点；
- 不把财报 Signal 反向用于证明前三个场景；
- Company fundamental 可以分析，Security pricing/result 必须
  INSUFFICIENT_EVIDENCE；
- 长期可持有结论因经营暴露、竞争壁垒、现金流、资本开支、估值和预期数据不足而停止。

## 6. 三个端到端场景

### 6.1 共同 required nodes

三个场景的初始 AgentContext 都不直接泄漏候选链清单。Agent 先从 Event 语义提出 Entity
候选，再通过工具获得 membership 并发现产业链。Verifier 不要求两条候选链都必须“受影响”，
而是要求 Agent 对隐藏候选宇宙中的每条链给出 AFFECTED、STRUCTURAL_ONLY、
NO_CLEAR_IMPACT 或 INSUFFICIENT_EVIDENCE 分类及依据。工具加载被发现链的完整数据库数据，
并只对 Agent 分类为 AFFECTED 的链执行完整节点覆盖检查。第一批候选宇宙最多包含以下
9 个唯一节点：

```text
CNDe6a6d0ff-7fa3-5751-970b-14b037672cb7
CND69b64d2c-2e9b-5ae4-a7a1-4d3cdb8a5073
CND5cdb05d8-4b70-547e-b59c-984d47e9878b
CNDafbf1596-2d6a-5140-a95e-3ff98187a07a
CND590758ed-67f9-533c-8221-b81712a71668
CNDd150620f-7ccf-5132-8b68-a44910422357
CND9d9243c0-ec40-58ab-a0e8-67697d620dad
CND717f1044-ecb6-59d7-b108-06880b5a1976
CNDfbd72cb7-900b-5811-bffa-4a489d136649
```

每条 AFFECTED 链的每个 membership 节点、每个 horizon 都必须输出结果；链内没有明确影响
的节点仍使用 NO_CLEAR_IMPACT、UNKNOWN 或 INSUFFICIENT_EVIDENCE，不能省略。
STRUCTURAL_ONLY、NO_CLEAR_IMPACT 或 INSUFFICIENT_EVIDENCE 的链允许停在链级，但必须给出
分类依据和数据缺口，避免为无关链强行生成节点结论。

Scenario RunCard 还必须保存：

```yaml
chain_assessments:
  - chain_entity_id: ICH...
    classification: AFFECTED | STRUCTURAL_ONLY | NO_CLEAR_IMPACT |
      INSUFFICIENT_EVIDENCE
    selection_basis:
      entity_ids: []
      membership_keys: []
      topology_link_ids: []
      semantic_reason: string
      data_gaps: []
```

每个 AFFECTED IndustryChain Anchor 形成独立 Analysis Result。若两条链都被判为 AFFECTED，
ICHed1 结果包含 5 个 membership 节点，ICH9d2 结果包含 5 个 membership 节点；共享的
`CND590...` 在两个 Anchor Scope 中各有一份节点结果，此时 verifier 检查 10 个
Anchor–Node membership 结果、9 个唯一 Entity ID。若某链未受影响，则只验收链级分类，
不得把固定 10 个结果当成隐藏答案。Scenario RunCard 只聚合 Analysis Result 不可变引用和
上述 chain_assessments，不成为另一种 Analysis Result。

### 6.2 SCN-GEO

用户问题：

> 截至 2026-08-23，稀土分离氧化物出口许可约束会影响哪些数据库产业链？对各节点的
> 短、中、长期投研含义是什么？

Agent 起始数据不是预制答案，而是已清洗发布的 GEO Event、已确认的 Country Link、Event 的
结构化 5W1H、Variable 子目录和相关 Storyline 摘要。`CND590...`、两条 IndustryChain、
9 个 ChainNode、10 个 membership 和 8 条 topology Link 只有在 Agent 先提出 Subject
实体候选并调用 Context 扩充工具后才进入 Context。

期望 Agent 自主完成：

1. 从 Event Subject `CND590...` 的两个 membership 发现 ICHed1 与 ICH9d2；
2. 区分美国进口 Scope 与中国国内 Scope；
3. 消费已审核 EventAnalysisPackage 的直接 Signal，再判断是否需要向上游反向分析、向下游
   正向分析；
4. 对粗粒度 `IGEef3...` 给出机制限制；
5. 对所有 AFFECTED 链形成完整节点三周期结果；
6. 分别判断节点稀缺性、议价权、成本转嫁、替代和价值捕获；
7. 在缺少市场预期和投资载体映射时输出 UNKNOWN/UNMAPPED，只标记节点机会候选或风险；
8. 输出库存、许可实际发放、替代供给、回收、客户迁移和政策缓和等反方；
9. 在 Company/Security 层停止。

最低禁止项：不得输出“整个稀土产业链统一利好”；不得将出口约束等于全球产能下降；
不得给个股方向。

### 6.3 SCN-MACRO

用户问题：

> 稀土开采和分离总量指标测试下调如何影响相关产业链？各节点短、中、长期趋势如何？

期望多轮推导：

```text
政策公布 Event
→ Agent 区分 announced_at 与 future effective_at
→ quota / restriction Signal 候选
→ ICHed1 节点逐步讨论实际产量、库存、开工和氧化物供给
→ 通过共享 CND590 节点进入 ICH9d2 的候选分析
→ Agent 判断粗粒度 Link 是否足以支持 cost / availability Signal
→ 节点经营影响 → 价值捕获 → 市场预期/映射 UNKNOWN
→ AFFECTED 链全节点三周期机会候选/风险 + 反方 + next checks
```

最低禁止项：政策尚未生效时不得把经营影响写成 ACTIVE；quota 不等于 realized production；
physical installed capacity 不因本 Event 自动下降；不得直接推出公司盈利或股价上涨。

### 6.4 SCN-INDUSTRY

用户问题：

> 缅甸稀土矿源和运输中断测试 Event 影响哪些数据库产业链？对各节点意味着什么？

期望多轮推导：

```text
供给中断 Event
→ deliverable_supply DOWN 与 physical_installed_capacity STABLE
→ ICHed1 全链：库存 → 开工 → 中间品 → 分离氧化物
→ 共享 CND590 节点
→ ICH9d2：合金 → 磁材 → 电机 → 电驱
→ 逐节点周期、缓冲、替代、价值捕获、反方和失效条件
→ 市场预期/映射不足时只输出节点机会候选或风险
```

最低禁止项：临时交付中断不得推成永久产能短缺；分离节点允许“价格上升但开工下降”的
MIXED；没有成本占比、库存或需求信息时，下游方向必须允许 UNKNOWN。

### 6.5 节点结果合同

每个节点结果嵌套在其 IndustryChain Anchor 的 Analysis Result artifact 中。父结果保存
`context_id`、`decision_at`、`anchor_entity_id`、`storyline_id`、`question`、
`knowledge_version` 和 `run_card_id`。节点不是 Security，不使用 RESEARCH_HOLD：

```yaml
node_entity_id: CND...
horizon: short | medium | long
window: {} # 本次 short/medium/long Analysis Result 的观察窗口
fundamental_trend: IMPROVING | STABLE | DETERIORATING | MIXED | UNKNOWN
thesis_state: STRENGTHENING | STABLE | WEAKENING | INVALIDATED | UNKNOWN
node_operating_implication: BENEFICIARY | BOTTLENECK | COST_PRESSURE |
  DEMAND_PRESSURE | MARGIN_PRESSURE | MIXED | NO_CLEAR_IMPACT
operating_impact:
  direction: POSITIVE | NEGATIVE | MIXED | NEUTRAL | UNKNOWN
  variable_ids: []
  mechanisms: []
value_capture:
  assessment: STRONG | PARTIAL | WEAK | NEGATIVE | UNKNOWN
  pricing_power: string | null
  scarcity_or_barrier: string | null
  cost_pass_through: string | null
  profit_leakage: []
  conditions: []
  source_event_ids: []
market_expectation_gap:
  direction: POSITIVE | NEGATIVE | NONE | UNKNOWN
  prior_expectation: string | null
  revised_view: string | null
  already_priced_in: NOT_EVIDENT | PARTIAL | LARGELY | OVEREXTENDED | UNKNOWN
  source_event_ids: []
investable_mapping:
  status: MAPPED | PARTIAL | UNMAPPED | UNKNOWN
  company_ids: []
  security_ids: []
  concept_or_index_ids: []
  source_event_ids: []
investment_relevance: OPPORTUNITY_CANDIDATE | RISK_POINT | MIXED |
  NO_CLEAR_EDGE | INSUFFICIENT_EVIDENCE
research_posture: PRIORITIZE_RESEARCH | WATCH | RISK | INSUFFICIENT_EVIDENCE
confidence: LOW | MEDIUM | HIGH
signal_ids: []
reasoning_link_ids: []
topology_link_ids: []
supporting_event_ids: []
counter_event_ids: []
assumptions: []
conditions: []
risks: []
invalidation_conditions: []
next_checks: []
valid_until: timestamp
```

门禁顺序是：节点经营变化不自动等于价值捕获，价值捕获不自动等于市场预期差，市场预期差
不自动证明存在可投资载体。当前前三个场景缺少正式投资载体和定价数据时，允许输出
`OPPORTUNITY_CANDIDATE + UNMAPPED + UNKNOWN`，不得输出具体证券“可投资”。

`window` 是当前 horizon 的分析观察窗口。节点结果不另造聚合 impact_window；真实影响
区间由 `signal_ids` 引用的各 Signal 及 `reasoning_link_ids` 引用的逐跳 Link 分别保存，避免
把多条路径强行压成一个未经定义的总周期。

## 7. AgentContext 与多轮 Agent 推理

### 7.1 AgentContext 的目的

AgentContext 是一次分析的可复现数据包，不是新的领域数据类型。它把 Agent 在
`decision_at` 可以看到的必要数据组织为：

```yaml
context_id: deterministic hash
pipeline: EVENT_ANALYSIS | INVESTMENT_REASONING
phase: DISCOVERY | ANALYSIS
question: string
decision_at: timestamp
trigger_window_start: timestamp
trigger_window_end: timestamp
horizons: []
scope: {}
anchor_entity_ids: []
case_config_hash: sha256:...
allowed_projection_namespaces: []

events: []
entities: []
links: []
variables: []
signals: []
storylines: []
reviewed_event_analysis_package_ids: []

loaded_chain_ids: []
loaded_node_ids: []
data_gaps: []
conflicts: []
retrieval_budget: {}
provenance:
  data_snapshot_hash: sha256:...
  graph_snapshot_hash: sha256:...
  tool_versions: {}
```

AgentContext 内仍然只有七类领域数据；`loaded_*`、hash 和 budget 是本次执行元数据。
`loaded_*` 只记录 Agent 已经通过检索获得的数据，不包含 verifier 隐藏的预期答案。

两条 Pipeline 共用 AgentContext envelope，但冻结不同的数据边界：

```text
EVENT_ANALYSIS Context
→ Curated Event/mention/Variable 子目录，不包含 Evidence 内容
→ REVIEWED EventAnalysisPackage

INVESTMENT_REASONING DISCOVERY Context（anchor_entity_ids 可空）
→ 新 Event + REVIEWED Package，不加载泄漏答案的 Storyline
→ Agent 提出并校验一个或多个 stable Analysis Anchor
→ 为每个 Anchor 冻结 ANALYSIS Context
→ 加载窗口外仍有效 Signal + Storyline v0 + 完整候选链
→ 每个 Anchor 分别形成 InvestmentAnalysisResult
```

最终 Signal、Storyline 和节点 Analysis Result 必须引用已经规范化的 Anchor Entity ID；
DISCOVERY 阶段的候选不得直接发布为结论。

Context Builder 按 owner 合并数据：Data Service 提供 LIVE Entity、正式 membership 和
topology Link；Graphiti 提供时序 Event/Signal/Storyline 投影与语义召回；Artifact Store
提供已审核运行产物；Event provenance 仅作为审计标识，不展开 Evidence 内容。
Graphiti 召回结果不得覆盖 Data 的正式 ID/Link；冲突必须同时进入 `conflicts`，交给 Agent
解释或请求补证。

### 7.2 不一次塞入全库

初始 Context 只包含：

- 用户问题、decision_at、scope 和 horizon；
- 起始 Event，以及在当前 grounding_mode 下已经审核的 Entity Link；
- `AGENT_DISCOVERY` 下未落地的 5W1H 文本 mention；不得预载隐藏 Subject Entity 或
  membership；
- 小规模相关 Variable 目录；
- 数据缺口；DISCOVERY 阶段不得加载锚定隐藏候选链或包含案例预期路径的 Storyline。

Agent 可以在同一次分析中多轮请求扩充：

- 精确读取候选 IndustryChain 的全部 nodes/memberships/edges；
- 查询某个 Event 的 provenance 状态和可信度等级，但不返回 Evidence 内容；
- 补取已经清洗成 Event/Signal 的节点库存、价格、产量等观察；
- 补取相关历史 Event、Signal 和 Storyline 版本；
- 补取 Company 暴露；若数据库没有，工具明确返回空和 stop reason。

每次扩充都受 PIT、实体/Link type、结果数量、token 和查询轮次预算约束，并追加到同一个
Context lineage。LOCAL_EVALUATION 检索还必须满足对象 namespace 位于
`allowed_projection_namespaces`；不得读到另一个 case 的 Event/Signal/Storyline。不得让 Agent
自由扫库或执行任意 Cypher。

只有当 Anchor 已由 Agent 发现并通过规范 ID 门禁后，ANALYSIS Context 才能加载该 Anchor
的当前 Storyline；这样 Storyline 历史不会反向泄漏 真实 Demo 的产业链答案。

### 7.3 两条多轮推理循环

轮次不是固定 Prompt 链，可以由 Agent 按数据缺口调整。Event Analysis Loop 建议：

1. **理解问题**：提取 Anchor、Scope、horizon、Event 语义和未知项；
2. **实体落地**：提出 Entity/Link 候选，工具映射规范 ID 并返回歧义；
3. **直接 Signal 假设**：选择 Variable，只提出 Event 直接支持的方向、机制和影响周期；
4. **反方检查**：补取冲突 Event、Signal 状态和替代解释；
5. **Storyline 路由**：提出关联候选和角色，不更新 thesis；
6. **校验与修订**：生成 EventAnalysisPackage 并完成审核。

Investment Reasoning Loop 建议上限 8 轮：

1. **产业链发现**：通过 EventAnalysisPackage、语义召回和 membership 找候选链；
2. **Context 扩充**：加载候选链完整图、历史有效 Signal 和 Storyline v0；
3. **节点传导**：逐边提出 derived Signal、机制、周期、缓冲和替代；
4. **价值捕获**：判断稀缺性、议价权、成本转嫁、利润泄漏和扩产难度；
5. **投资映射与预期**：请求 Company/Security/Concept/Index Link 和市场 Event/Signal；
6. **Bear/Alternative**：使用同一冻结 Context 独立寻找反方和停止条件；
7. **多周期综合**：只覆盖 AFFECTED 链全部节点，形成机会候选/风险和推理树；
8. **校验与修订**：审核结果后提出 Storyline v1，不改写 v0。

系统保存每轮的结构化请求、候选、引用、校验错误和结论理由摘要，不依赖或持久化模型的
原始隐藏思维链。

同一循环既支持单 Agent 也支持多 Agent：Codex/Claude Code 可以由一个执行器依次承担
Planner、Signal Analyst、Bear Analyst 和 Synthesizer 角色；Agno 可以把这些角色拆成多个
Agent。它们必须共享同一个 PIT AgentContext，并通过相同工具和结构化产物交接，不能让
Bear Agent 或 Synthesizer 私自获得主分析未见过的未来数据。

### 7.4 LLM 与确定性算法的边界

| 工作           | Codex / LLM                        | 确定性工具                             |
| -------------- | ---------------------------------- | -------------------------------------- |
| Event 理解     | 解释 5W1H、歧义和语境              | 校验字段、时间和 provenance audit ref  |
| Entity linking | 提出候选和消歧理由                 | 查规范 ID、别名和类型                  |
| 产业链发现     | 语义判断哪些链值得研究             | 返回真实 membership/edge，拒绝非 DB ID |
| Signal         | 提出 Variable、方向、机制、周期    | 校验目录、Schema、PIT、周期完整性      |
| 传播           | 判断是否沿某 Link 发生、缓冲和替代 | 校验 topology Link 存在与归属          |
| 价值捕获       | 解释稀缺、议价、成本传导和利润迁移 | 校验引用、指标计算和 Event/Signal 时点 |
| 投资载体映射   | 判断暴露的业务意义和纯度           | 返回正式 Company/Security/Concept Link |
| 市场预期差     | 比较 prior expectation 与新判断    | 返回 PIT 行情、估值、预期 Event/Signal |
| Storyline      | 形成主叙事、反叙事和版本变化       | 校验路由、引用和 namespace             |
| 多周期结果     | 综合上下文并解释不确定性           | 校验全节点覆盖和枚举值                 |
| 数字/日期      | 解释确定性计算结果                 | 算术、单位、日期、hash 和去重          |

数据库 Link 是候选推理空间，不是自动因果规则。算法不得执行“从起点遍历所有可达节点，
统一复制方向并按固定比例衰减”。

### 7.5 必要的算法概念

这些是执行算法，不是新的领域数据类型：

| 算法                      | 输入                                   | 输出                                                 | 明确不负责            |
| ------------------------- | -------------------------------------- | ---------------------------------------------------- | --------------------- |
| PIT Context Filter        | decision_at 与七类数据                 | 当时可知、当时有效的数据片段                         | 判断投资方向          |
| Semantic Candidate Recall | Event 文本、Entity 名称/描述、研究问题 | 带理由和分数的 Entity/Chain 候选 ID                  | 宣布候选一定受影响    |
| Graph Grounding           | Agent 候选 ID 与 Data Entity/Link      | 规范 ID、membership、真实路径或缺口                  | 自动传播 Signal       |
| Agent Deliberation Loop   | 当前 AgentContext、工具目录、停止预算  | 下一轮检索请求、Signal/Link/Storyline 候选、结果草稿 | 绕过事实和权限门禁    |
| Proposal Gate             | Agent 候选与当前 Context               | 结构、PIT、Link、周期和引用错误                      | 重写 Agent 的业务机制 |
| Coverage Verifier         | 已选链、membership、结构化结果         | 缺失节点/horizon 和非法结论列表                      | 替缺失节点生成答案    |

Semantic Candidate Recall 可以组合向量/全文召回和 LLM rerank，以充分利用语义理解；
Graph Grounding 只把召回结果落到数据库真实 ID。二者分开后，既不会把检索做成死板关键字
规则，也不会让 LLM 自行发明产业链。

## 8. Codex / Claude Code / Agno 工具

只暴露四个深接口；Codex 可以在同一分析中多次调用前两个。

### 8.1 `create_agent_context`

```python
create_agent_context(
    pipeline,
    question,
    decision_at,
    trigger_window,
    horizons,
    scope,
    anchor_entity_ids=None,
    event_ids=None,
    case_id=None,
) -> AgentContext
```

完成 PIT 截面、起始 Event、grounding_mode 允许的已审核 Entity Link、未解析 mention 和
Variable 子目录加载；仅 ANALYSIS phase 加载已确认 Anchor 的 Storyline。Event provenance
只保留审计标识，不展开 Evidence 内容。
AGENT_DISCOVERY 不预载 Subject Link 或会泄漏候选链的 Storyline。工具只读，不生成 Signal，
不写 Graphiti。

### 8.2 `expand_agent_context`

```python
expand_agent_context(
    context_id,
    requests,
) -> AgentContext
```

`requests` 只能是有界语义任务，例如：

```text
resolve_entities
load_industry_chain
load_node_observations
retrieve_supporting_events_signals
retrieve_counter_events_signals
load_related_events_signals_storylines
check_company_exposure
load_value_capture_events_signals
load_market_expectation_events_signals
load_investable_mappings
```

工具内部可以查询 Data API 和 Graphiti，但只返回经过 PIT、类型、ID 和预算门禁的数据。
它不替 Agent 决定受影响方向。

### 8.3 `review_event_analysis`

```python
review_event_analysis(
    context_id,
    proposed_event_entity_links,
    proposed_direct_signals,
    proposed_storyline_links,
) -> EventAnalysisPackage | list[dict]
```

它负责：

- Event/Entity/Variable/Signal/Storyline ID 与 type；
- known_at/effective_at 和 projection namespace；
- direction/modality/review/lifecycle 正交字段；
- impact window、unknown reason 和 next observations；
- Direct Signal 是否确由当前 Event 支持；
- Package 是否错误包含下游 Signal Link、节点结果或投资结论；
- 重复、冲突和越权写入；
- 人工审核状态。

验证通过后，审核人可以将 Package 标为 REVIEWED 并确定性投影直接 Signal 和路由 Link；
工具不生成下游 Signal，不写最终 Storyline 版本。

### 8.4 `verify_and_record_investment_analysis`

```python
verify_and_record_investment_analysis(
    context_ids,
    anchored_results,
    review_decision,
) -> RunCard
```

它逐一校验每个 Anchor InvestmentAnalysisResult，再校验候选链均已分类、每条 AFFECTED 链
完整 membership×三个 horizon、逐跳 Signal Link、经营影响、价值捕获、市场预期、投资载体
映射、推理树引用、反方、周期和停止条件。人工接受后保存结果与聚合 RunCard，并分别追加
评估 Storyline 版本；不回写 Event 或数据库产业 Link，也不触碰上游 Evidence。

### 8.5 计划 CLI

```text
bash scripts/reasoning-tool.sh schema inspect --demo rare-earth
bash scripts/reasoning-tool.sh event curate --evidence-id EVD... --review
bash scripts/reasoning-tool.sh graph project --demo rare-earth
bash scripts/reasoning-tool.sh event analyze --event-id EVT... --executor codex
bash scripts/reasoning-tool.sh event review --event-id EVT... --file ...
bash scripts/reasoning-tool.sh context expand --context-id ... --request ...
bash scripts/reasoning-tool.sh investment analyze --event-id EVT... --executor codex
bash scripts/reasoning-tool.sh investment verify --context-id ... --file ...
bash scripts/reasoning-tool.sh demo run --event-id EVT... --executor codex
```

同一四接口后续可增加 MCP 或 Agno adapter；领域合同不依赖某个执行器。

## 9. Graphiti 投影

### 9.1 只投影七类数据

Graphiti 中只投影或引用：Evidence、Event、Entity、Link、Variable、Signal、Storyline。
Analysis result 和 RunCard 只保存外部 artifact reference，避免结论反向变成事实。

Evidence 只属于 Event Curation 和审计子图。两条下游 Pipeline 的查询入口、Graph traversal
和 AgentContext 都从 Event 开始，并由 adapter 明确排除 Evidence 节点与内容。

### 9.2 确定性与 LLM 抽取的边界

- Data 的 IndustryChain、ChainNode、Country、Company 和 topology Link 按正式 ID 确定性
  upsert；
- membership 使用数据库复合键，不让 LLM 生成 ID；
- Local Evaluation 的 Event/GPR/Macro/Storyline 使用 namespace + key 派生
  ID，但仍使用相同顶层类型；
- Graphiti/LLM 可以从 Event 5W1H 提出 Event Anchor Link 候选，只有规范 ID、允许端点、角色、
  文本依据和置信门禁通过后才成为 reviewed Link；纯 mention 和间接影响不进入该层；
- 直接 Signal 必须先通过 `review_event_analysis`；下游 Signal 与 Signal Link 必须先通过
  `verify_and_record_investment_analysis`；
- 不依赖 Graphiti 抽取 LLM 为稳定主数据生成 ID；
- 不清空整个 group，重放同一 namespace 必须幂等。

### 9.3 投影顺序与 Graphiti 约束

本次真实 Demo 按以下层次投影，后一层只能引用已经校验的前一层：

1. Event Curation 独立保存 Evidence→Event provenance，可选投影审计子图；
2. 投影本例实际需要的 Entity 与最小 Variable 目录；
3. 投影 membership 与 topology Links；
4. 将已清洗发布的 Event 作为 Episode/Event 投影，Graphiti Ingestion 从 5W1H 建立 reviewed
   Event Anchor Links；
5. Event Analysis 审核后投影 Direct Signal、Event→Signal、Signal→Entity、Signal→Variable；
6. Direct Signal 完成后投影 immutable Storyline version 及 Event/Signal 的正式路由 Link；
7. Investment Pipeline 审核后投影 derived Signal 与逐跳 Signal→Signal Link；
8. InvestmentAnalysisResult 只写 Artifact，Storyline 只保存 artifact reference/hash。

Graphiti 0.29.3 + Neo4j Community 只有默认 `neo4j` database，不能把 case namespace 当数据库
名。case 隔离由受控 adapter 使用 namespace 属性、namespace 专用 label/技术 UUID 和参数化
查询共同实现；不得依赖当前 Neo4j search property filter 自动隔离，也不得让 Agent 自由
Cypher。Neo4j 不能保存嵌套 map，scope、impact_window、confidence 和 scenarios 在 Pydantic
Artifact 中保留完整结构，图投影只保存必要标量、canonical JSON/hash 和 artifact ref。

正式 Entity、基础 topology 和 Variable 使用确定性 projection adapter upsert；Graphiti
Episode 承担 Event 时态语义索引和 provenance，LLM 可以提出 Anchor 候选和关系角色，但
不得生成稳定 Entity ID 或 topology。reviewed Event Anchor Link 由受控 adapter 写入；
`valid_at/invalid_at` 表达实际有效期，预计结束时间只存 Signal impact window；
直到 Signal 实际 EXPIRED/INVALIDATED 才设置 invalid_at。

### 9.4 必须阻止的图关系

```text
Event --POSITIVE/NEGATIVE--> Security
Event --RELATED_TO--> 所有可达节点
Company 名称相似 --OPERATES_AT--> ChainNode
Signal --TRANSMITS_TO--> Signal 但没有匹配端点的数据库 topology_link_id、方向和机制
Storyline --CAUSES--> 股价上涨
AnalysisResult --BECOMES--> Evidence/Event
```

## 10. 可执行验收规则

CaseConfig 中的 assertions 使用确定性字段，不把验收再次交给 LLM 主观评分：

```yaml
assertions:
  allowed_chain_classifications:
    [AFFECTED, STRUCTURAL_ONLY, NO_CLEAR_IMPACT, INSUFFICIENT_EVIDENCE]
  forbid_non_database_chain_entities: true
  forbid_non_database_memberships: true
  forbid_non_database_topology_links: true
  forbid_evidence_content_in_reasoning_context: true
  forbid_predefined_signal_directions: true
  required_node_horizons: [short, medium, long]
  require_full_node_coverage_for: [AFFECTED]
  allowed_directions: [UP, DOWN, MIXED, STABLE, UNKNOWN]
  forbid_derived_signals_in_event_package: true
  require_value_capture_before_opportunity: true
  require_market_events_or_signals_for_expectation_gap: true
  require_mapping_for_investable_conclusion: true
```

首次 Demo 的硬约束只检查来源、身份、时间、Schema、真实拓扑、Pipeline 分责和机会升级
条件，不固定任何 Direct Signal 或下游方向。业务逻辑是否成立由首次真实结果的专业复盘
判断；经多轮确认后，只有无争议的硬边界才能进入后续回归 assertions。

### 10.1 共同门禁

- Context 外出现新的 IndustryChain、ChainNode、membership 或 topology Link：失败；
- 任一 AFFECTED 链的 membership 节点缺 short/medium/long：失败；
- EventAnalysisPackage 出现下游 derived Signal、Signal transmission 或投资结论：失败；
- Signal 无 Variable、Anchor、机制或 impact window：失败；
- unknown 无原因、next observation 或 next_review_at：失败；
- future-effective 政策影响在 decision_at 被标 ACTIVE：失败；
- 临时交付下降被写成 physical installed capacity 下降：失败；
- Company 与 Security 混同：失败；
- 没有 value capture Event/Signal 却输出已确认 Opportunity：失败；
- 没有市场预期 Event/Signal 却输出非 UNKNOWN expectation gap：失败；
- 没有正式暴露 Link 却输出具体可投资标的：失败；
- Storyline prior thesis 被当成市场已定价证据：失败；
- 推理树无法沿 Event/Signal/真实 topology Link 回溯：失败；
- 没有关系时明确 abstain：通过；
- 下游方向与设计者预想不同但 Event、机制、反方和周期完整：允许进入人工评审。

## 11. 计划文件结构

### 11.1 后续改造点总览

| 层               | 当前状态                                               | 设计中的后续改造                                       | 当前是否实施 |
| ---------------- | ------------------------------------------------------ | ------------------------------------------------------ | ------------ |
| Data Service     | 产业数据完整；Event/Storyline/暴露 API 不完整          | 快照 API、Event aggregate、Storyline 版本、暴露 Link   | 否           |
| Graphiti         | 第一批正式 Ontology 已定义                              | 基础数据确定性投影、Evidence/Event Ingestion、Anchor Grounding、PIT、namespace、幂等增量 | 部分 |
| Reasoning Server | 无通用 AgentContext、两条 Pipeline 和机会判断          | 两个深 Pipeline、四个 Agent 工具、合同、门禁、Artifact | 否           |
| Agent 编排       | 单次固定检索和一次分析                                 | Event Package→DISCOVERY→ANALYSIS→Storyline version     | 否           |
| 发布             | Data 已有 V3 analyst_snapshot，但缺 canonical 研究身份 | 先做 lossy mapper；未来评审 Research Theme V4          | 否           |
| 测试             | Ontology 公共合同测试，无真实纵向运行                   | 首次真实运行后再固化硬边界回归测试                     | 部分         |

以下目录只是建议落点，本轮不会创建。

### 11.2 建议目录

正式 Ontology 已落在 `ontology/`；后续 Harness 建议结构：

```text
reasoning_harness/
  contracts/
    domain.py
    execution.py
    result.py
    projection.py
    __init__.py
  variable_catalog.py
  context.py
  event_ingestion.py
  anchor_grounding.py
  event_pipeline.py
  investment_pipeline.py
  event_review_gate.py
  investment_result_gate.py
  storyline_memory.py
  reasoning_tree.py
  publication_mapper.py
  ports.py
  cli.py

  adapters/
    tidewise_data.py
    graphiti.py
    artifact_store.py
    llm.py
    in_memory.py

reasoning_demo/
  schemas/
  curation/
    event-publication.json
  config/
    rare-earth-demo.json
  runs/
    .gitkeep

scripts/
  reasoning-tool.sh
  test-reasoning-harness.sh

tests/
  unit/
  integration/
  demo/
```

`reasoning_demo/config` 只声明问题、时点、Event ID 和运行边界，不保存预期 Signal 或节点
方向。真实 Entity/Link 在运行时从 owner 读取并投影；`runs/` 保存一次运行的 Artifact 引用，
不把运行结果冒充事实数据。Event Curation 的上游审计产物与下游推理配置分开。

## 12. 逐步执行计划

执行策略是先做一个真实纵向闭环。第一次推理前不建设固定测试集、不冻结下游 Signal、
不规定节点方向；只固定真实 ID、时间截面和不允许伪造数据的硬边界。

### Phase 0：确定首次 Demo 问题和输出

1. 明确 decision_at、触发 Event 范围和研究问题；
2. 输出限定为一句话结论、受影响产业链分类、节点短中长期结果和结构化推理树；
3. 明确当前最高结论是节点机会候选/风险点，缺载体和市场预期时不输出证券方向；
4. 明确 Evidence→Event 是上游工作，两条推理 Pipeline 从 Event 开始。

产物：方法论 Spec、本文和 Context glossary。当前阶段已完成。

### Phase 1：从 Demo 反向定义最小 Graphiti Schema

1. 逐步展开“Event 如何影响真实产业链节点”的推理过程；
2. Graphiti 推理 Schema 只定义 Event、Entity、Link、Variable、Signal、Storyline；Evidence
   默认保留在上游 owner，只有实际需要图审计时才增加只读 provenance 投影；
3. 冻结本例需要的 relation type、Signal impact window 和 Storyline 关联字段；
4. 建立 `Graphiti 对象/关系 → 用途 → PG 来源 → owner → 投影方式 → 缺口` 映射表；
5. 删除任何无法由本例证明必要性的对象、字段和关系。

完成标准：每个 Schema 元素都能指向本次真实推理中的一个明确用途。

### Phase 2：补齐权威 PostgreSQL 数据与 Event Curation

1. 从 Data 读取真实 ICHed1、ICH9d2、9 个 ChainNode、membership 和 8 条 topology Link；
2. 对稳定业务事实缺口决定加表、字段、Link 或版本化读取合同，保持 Data/Reason owner；
3. 选择真实 Evidence，经清洗、去重、拆分、5W1H 归一和人工审核发布一个 Event；
4. Event 保存 provenance 和 known-at 结果；下游不接收 Evidence 内容；
5. 不要求 Data 为推理关系新增通用 Event→Entity 镜像表；Variable、Signal、Storyline 按 owner
   单独持久化；
6. 若现有 Evidence 无法形成边界清晰的 Event，则继续选择来源，不伪造事实补齐案例。

完成标准：存在一个可审计的真实 Event，且本例全部稳定事实都能从权威 owner 读取。

### Phase 3：投影本例所需事实到 Graphiti

1. 实现确定性 projection adapter，不让 LLM 生成正式 ID；
2. 投影本例实际需要的 Entity、Variable、Storyline、membership、topology Link 和已发布 Event；
3. Evidence→Event provenance 如需图审计可单独投影，但下游查询必须过滤 Evidence；
4. 实现 Anchor Grounding：从 Event 5W1H 召回规范候选、校验角色并写 reviewed Event Anchor
   Link；不映射所有 mention，不建立间接受影响节点；
5. 使用 namespace、参数化查询和幂等 receipt，不清空其他 namespace；
6. 在 Neo4j Browser 和受控查询中核对对象、端点、方向、ID 和时间。

完成标准：Graphiti 已包含启动推理所需事实，且没有案例专用虚构产业节点或拓扑。

### Phase 4：构建 Codex 多轮推理工具和两条 Pipeline

1. 定义 AgentContext、EventAnalysisPackage、InvestmentAnalysisResult 和 ReasoningTree；
2. 实现 `create_agent_context`、`expand_agent_context`、`review_event_analysis`、
   `verify_and_record_investment_analysis` 四个深接口；
3. Event Analysis 只消费 reviewed Event Anchor Links，完成 Variable、Direct Signal、impact
   window 和 Storyline routing；
4. Investment Reasoning 完成产业链发现、逐节点传导、价值捕获、预期差、映射和多周期判断；
5. 脚本只负责检索、Context 组装、ID/时间/真实拓扑校验和产物保存，不写死业务结论；
6. Context 工具不得返回 Evidence 内容，Codex 不获得任意 Cypher 或 Data PG 写权限。

完成标准：一个命令能够从已发布 Event 启动完整推理并产出结构化结果。

### Phase 5：运行第一次真实推理并专业复盘

1. Codex 基于当前 Graphiti 和受控工具完成 Event Analysis；
2. 审核 Direct Signal 后继续 Investment Reasoning；
3. 输出一句话结论、产业链分类、节点短中长期影响、机会/风险和推理树；
4. 专业评审不按预制答案打分，而是记录逻辑成立、过度推断、遗漏变量、周期不合理、
   Context 缺失、错误关系和合法 UNKNOWN；
5. 根据评审结果修改 Schema、PG 数据、投影、工具、Prompt 或 Pipeline，并再次运行。

完成标准：得到一份可审计的真实推理结果和一份明确的问题清单，而不是“命中标准答案”。

### Phase 6：形成回归样本并扩展案例

只有首次闭环经过人工复盘并稳定后才：

1. 将真实运行中确认的硬边界整理为回归样本，不固定存在争议的业务结论；
2. 依次加入 MACRO、GEO 和 COMPANY 场景；
3. 补 Company→ChainNode、Company→Security、Concept/Index 映射和市场预期数据；
4. 接入 append-only Storyline、Data 发布、MCP/Agno、权限、UAT 和回滚；
5. 仅当价值捕获、市场预期差和投资载体映射均有事实支持时升级为具体投资候选。

完成标准：同一 Schema 和工具能处理多类真实 Event，并保持事实可追溯和结论可证伪。

## 13. 最终验收清单

### 数据

- [ ] 两条 IndustryChain 来自数据库；
- [ ] 9 个唯一 ChainNode 来自数据库；
- [ ] 10 个 membership 均与数据库复合键一致；
- [ ] 8 条 topology Link 均为 approved/active 数据库 Link；
- [ ] 没有案例专用产业节点、产业链或拓扑；
- [ ] Event 不分 Research/Scenario；
- [ ] 真实 Evidence 已经独立清洗、拆分和审核成 Event；
- [ ] 两条下游 Pipeline 的 AgentContext 不包含 Evidence 内容；
- [ ] Data Event payload 未被 Reason 私自增加 event_type/projection_mode/known_at；
- [ ] 领域数据只使用七类顶层类型。

### Agent 推理

- [ ] AgentContext 包含必要而非全库数据；
- [ ] Agent 可以多轮补取 Context；
- [ ] EventAnalysisPackage 只有直接 Signal；
- [ ] Investment Pipeline 只消费 REVIEWED Package；
- [ ] LLM 负责语义、机制、Signal 和竞争性解释；
- [ ] 算法不机械传播 Signal；
- [ ] 每条 Signal Link 引用真实 topology Link；
- [ ] 每条 AFFECTED 链的全部节点和三个 horizon 均有结果；
- [ ] 节点经营影响、价值捕获、市场预期差和投资映射分别表达；
- [ ] 没有映射或市场 Event/Signal 时不会输出虚假可投资机会；
- [ ] 一句话结论与结构化推理树可回到 Event/Signal/真实 Link；Event provenance 可由独立
      审计接口回到 Evidence；
- [ ] Storyline v0 不被覆盖，审核后形成带 thesis delta 的 v1；
- [ ] 支持、反方、假设、失效和 next checks 完整；
- [ ] Event、Signal 或关系不足能够停止。

### 工程与治理

- [ ] Reason 不直写 Data PostgreSQL；
- [ ] Graphiti 投影幂等且不清空其他 namespace；
- [ ] Local Evaluation 与 LIVE 数据隔离；
- [ ] Context、数据片段和结果均有 hash；
- [ ] Codex 不获得任意 Cypher；
- [x] 正式 ontology Entity/Link 公共合同测试通过；
- [ ] 首次真实 Demo 完成专业复盘后，才把确认的硬边界转成回归测试。

## 14. 下一步

本轮完成 Phase 0，并把执行方式修正为真实 Demo 驱动。当前不创建固定测试数据或标准答案。

下一步执行 Phase 1：围绕首次稀土真实推理问题，逐项写出最小 Graphiti Schema 以及
`对象/关系 → 推理用途 → PG 来源 → owner → 缺口 → 投影方式` 映射表。映射表确认后进入
Phase 2，决定哪些 PostgreSQL 业务事实确实需要补表、字段或 Link，并完成真实
Evidence→Event 清洗发布工序。
