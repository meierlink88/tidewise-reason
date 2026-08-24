# 事件驱动定性投研方法论 Spec

> 状态：Draft，供持续讨论
>
> 版本：0.5.0
>
> 日期：2026-08-24
>
> 适用范围：观潮家事件驱动投研分析与 Agent Harness
>
> 上游依据：[CONTEXT.md](../../CONTEXT.md)、[ADR 0001](../adr/0001-use-graphiti-for-local-temporal-memory-evaluation.md)
>
> 参考项目：[Vibe-Trading](https://github.com/HKUDS/Vibe-Trading)、[FinRobot](https://github.com/AI4Finance-Foundation/FinRobot)、[K-Quant](https://github.com/K-Quant/K-Quant)

## 0. 目的与演进方式

本文将当前讨论共识固化为可持续演进的规范，作为后续领域建模、Graphiti 投影、Agent
职责、Skills、Tools、分析流水线、产品表达和系统验收的上游依据。

本文不是最终版本。尚未达成共识的内容必须保留在“待讨论问题”中，不得被实现方自行
解释成最终规则。

本方法论采用 **Demo 驱动演进**：先围绕一个真实问题反向识别最小领域对象和关系，补齐
权威数据缺口，将事实投影到 Graphiti，搭建 Codex/LLM 可执行的多轮推理流程，并实际运行
一次。第一次运行不预置标准答案；业务结论由专业投研评审判断是否合理，评审结果再用于
修正 Schema、数据、工具和 Pipeline。固定回归样本和自动化期望只能在真实闭环跑通后建立。

规范性术语：

- **必须 / MUST**：缺失即不符合本方法论；
- **应当 / SHOULD**：默认要求，偏离时必须说明理由；
- **可以 / MAY**：可选能力；
- **不得 / MUST NOT**：明确禁止。

## 1. 核心定位

本方法论包含一个上游事实工序和两条职责不同、前后衔接的推理 Pipeline：

```text
Event Curation Work（不属于下游投研推理）
Evidence
  → 清洗 / 去重 / 拆分 / 事实核验
  → 发布可审计 Event

Graphiti Event Ingestion and Anchor Grounding
Curated Event
  → Episode / Event 时态语义索引
  → 从 5W1H 召回规范 Anchor 候选
  → 实体匹配、角色校验和 Event Anchor Link

Event Analysis Pipeline
Grounded Event + reviewed Event Anchor Links
  → Event × Anchor × Scope × Variable × Mechanism
  → 带影响周期和失效条件的直接 Signal
  → Storyline 最终路由

Investment Reasoning Pipeline
Analysis Anchor + decision_at + 新 Event + 仍有效的历史 Signal + 当前 Storyline
  → 受影响产业链发现
  → 节点经营影响传导
  → 节点价值捕获能力
  → 市场预期差与可投资载体映射
  → 短期 / 中期 / 长期机会或风险判断
  → 一句话结论 + 可审计推理树
  → 经审核后更新 Storyline
```

Event Curation Work 回答“哪些来源材料可以形成哪些 Event”；它可以使用清洗、抽取和审核
工具，但其产物 Event 才是下游推理的事实起点。Evidence 内容不得进入 Event Analysis 或
Investment Reasoning 的 AgentContext，也不得被 Agent 绕过 Event 直接解释为 Signal。

Graphiti Event Ingestion 回答“这个 Event 的直接 5W1H 应落到哪些规范推理锚点”。它只为
进入推理路径的稳定 Entity 建立 Event Anchor Link，不把所有文本 mention 图谱化，也不得
把需要 Variable/Signal 或产业链传播才能得出的间接受影响节点提前写成 Event 事实。

第一条推理 Pipeline 回答“这个已接受 Event 直接改变了什么”，产物可以被不同 Anchor 的
后续研究复用；第二条推理 Pipeline 回答“截至某个决策时点，这些变化对目标 Anchor 和投资人
意味着什么”。不得把三者合并为一次从新闻直接跳到股票方向的自由回答。

节点经营趋势不是最终预测目标。一个节点只有在同时审议以下三层后，才能被标记为投资
机会候选或风险点：

1. **经营影响**：供给、需求、价格、成本、库存、产能、交付和替代发生什么变化；
2. **价值捕获**：该节点能否通过稀缺性、议价权、进入壁垒、利润池迁移或份额变化获得
   经济价值；
3. **投资可达性**：是否存在有真实业务暴露的 Company、Security、MarketConcept、
   CommodityIndex 或 MarketIndex，以及市场是否可能已经反映该变化。

缺少第二层时只能输出节点经营影响；缺少第三层时可以输出“机会候选/风险点”，但不得
升级为已确认的可投资机会或证券方向。

本方法论的专业定位是：

> 根据决策时点可知的事实，推导某个锚点的基本面趋势、市场趋势偏向、投资逻辑强弱、
> 条件化可持有状态与风险，并随新事件持续更新和证伪。

本方法论不得宣称：

> 仅凭新闻、故事线或知识图谱逻辑，可以稳定预测证券未来必然上涨或下跌。

## 2. 范围与非目标

### 2.1 范围

本方法论覆盖：

- 财报、公告、新闻、快讯和市场准事实数据的统一接入；
- 地缘政治、国家政策、宏观经济、商品和市场事件；
- 产业链上游、中游、下游节点变化；
- 板块、Market Concept、商品指数、市场指数和公司个股；
- 短期、中期、长期的独立分析；
- 基本面趋势、市场趋势偏向、持有条件和风险；
- 证据分级、冲突处理、反方审议、失效和持续监控。

### 2.2 当前非目标

当前阶段明确不做：

- 多因子量化选股；
- GNN、关系矩阵或机器学习收益预测；
- 程序化策略、组合优化和自动交易；
- 仅以历史收益回测判断事实逻辑是否成立；
- 无证据的精确涨跌幅和目标价预测；
- 将 Agent 共识、LLM 总结或故事完整度视为事实；
- 将 Graphiti 当成自动产生投资结论的推理模型。

### 2.3 “不做量化”的准确含义

“不做量化”指不建设量化投资模型、因子预测和程序化交易系统，不代表禁止使用数字。

专业基本面研究仍必须使用确定性工具完成：

- 财务同比、环比、利润率、现金流和资产负债变化；
- 产能、产量、库存、价格、订单和交付周期变化；
- 公司收入或成本暴露；
- 估值区间、敏感性和同业比较；
- 指数成分、权重和历史版本；
- 日期、持续时间、时区和交易时点；
- 原文数字、单位、币种和引用一致性检查。

LLM 不得自行心算或编造上述数字。

## 3. 领域对象与统一语言

### 3.0 顶层数据类型约束

领域 Schema 不从“未来可能需要什么”出发。每一次新增对象、字段或关系必须由当前 Demo
问题中的真实推理步骤反向证明其必要性，并逐项说明：它承载什么事实、事实 owner 是谁、
当前 PostgreSQL 是否已有权威表达、如何投影到 Graphiti、缺失时为何必须扩展。Graphiti
中的技术投影元数据不等于 PostgreSQL 领域事实，不得为了图存储方便机械增加业务表。

领域模型只使用已经确认的七类顶层数据：

```text
Evidence | Event | Entity | Link | Variable | Signal | Storyline
```

- Country、IndustryChain、ChainNode、Company 等通过 `Entity.entity_type` 区分；
- 地缘、宏观政策、产业、企业是案例或分析视角，由 Event 的规范 Entity Link、Storyline
  Anchor 和 CaseConfig `case_family` 表达；Event 本身不增加与 Data 合同冲突的 type；
- membership、节点拓扑、事件实体角色、信号来源、信号传播和 Storyline 路由通过
  `Link.link_type` 区分；
- Observation、Claim、StateChange、MetricObservation 等是既有类型上的分类或语义角色，
  不是新的顶层数据类型；
- 案例执行配置、PIT 快照、Analysis Context、Analysis Result 和 Run Card 是推理执行产物，
  不冒充领域图谱数据。

七类数据在本地评估中可以通过 Reason `ProjectionMeta` 保存运行 namespace、来源 key 和
投影 hash；这些字段不扩展 Data Event payload，也不自动要求增加 PostgreSQL 字段。

只有在上述七类无法表达且确有独立生命周期、权威 owner 或校验规则时，才允许新增数据
或规则概念；新增时必须说明用途、owner、持久化位置以及为何不能复用既有类型。

### 3.1 Evidence

不可变、可定位来源的材料，例如公告原文、财报页码、政策文件、新闻正文或行情快照。

Evidence 必须保留来源身份、原始内容或片段、发布时间、摄入时间、来源等级、版本或
内容哈希。Evidence 只进入上游 Event Curation Work，用于清洗、去重、拆分、核验和发布
Event；它不是后续 Event Analysis 或 Investment Reasoning 的输入。下游结果通过 Event
保留的 provenance 间接回溯 Evidence，不允许 Codex 跳过 Event 直接从原文生成 Signal。

### 3.2 Observation（Evidence 语义类型）

来源在某一时刻提供的一条原始观察。以下内容默认是 Observation，而不是 Event：

- 某指数在一个时点的点位；
- 财报中的一项收入数字；
- 新闻媒体转述的公司人士说法；
- 一条未经确认的快讯；
- 某商品当日库存数值。

### 3.3 Claim（Evidence / Event 语义角色）

某个可识别主体提出的主张，例如公司管理层指引、政府表态、媒体引用或分析师观点。

Claim 必须记录主张者，不得未经验证自动提升为 Event。

### 3.4 Event

具有明确时间和分析意义的发生、变化、计划或评估情景。Event 由上游 Evidence 清洗和审核
工序发布，是两条下游推理 Pipeline 唯一允许的事实起点。真实世界 Event 必须能够通过上游
Link 回溯一个或多个 Evidence；本地评估内容仍使用同一 Event 数据类型，通过 Reason 的
ProjectionMeta 与正式数据隔离，不另造 ResearchEvent、ScenarioEvent 等平行概念。

Event 必须至少回答：

- 发生了什么；
- 涉及哪些实体；
- 现实发生时间和正式宣布时间；
- 来源与证据；
- 当前 lifecycle；
- `modality=FACT | PLAN | SPEC`。

正式 Event payload 遵循 Data 权威合同：

```text
id + title + summary + strict 5W1H semantic
+ modality + occurred_at? + announced_at? + lifecycle
```

本地评估 Event 不得进入生产 Storyline 或写入生产数据域，但它与正式 Event 使用相同字段、
Link 和推理流程。`known_at` 在 Event Curation Work 中依据上游 Evidence `published_at` 等
信息计算并随 Event provenance 发布；下游 AgentContext 只消费计算结果，不读取 Evidence
内容。影响何时生效和持续多久属于 Signal，不向 Event 临时增加
`effective_at/valid_*`。

财报文件本身不是完整 Event。“公司发布财报”是 Event；财报中的经营数字是
MetricObservation；指标的实质变化可以派生 StateChange。

### 3.5 State Change（Event 的语义分类）

从一个状态到另一个状态、具有投研意义的变化，例如：

- 库存从正常区间进入紧张区间；
- 毛利率连续多个报告期下降；
- 指数成分发生调整；
- 商品期限结构发生实质改变；
- 政策从征求意见进入正式实施。

State Change 可以由确定性规则从 Observation 派生，也可以成为 Event 的一部分。

### 3.6 Analysis Anchor

一次分析的稳定目标。允许的 Anchor 至少包括 Country、Region、GeopoliticRivalry、
MacroEconomic、IndustryChain、IndustryChainNode、MarketConcept、CommodityIndex、
MarketIndex、Company 和 Security。

Analysis Anchor 必须是稳定研究对象，不得再把 Storyline 本身定义为 Anchor；该语言已经
同步到 Reasoning Evaluation Context。

Event Anchor Link 是现有 Link 的一种业务用途，不是新的顶层数据类型。它把 Event 5W1H
中的直接语义落到规范 Analysis Anchor，或落到会实质改变范围和机制的 Country、Region、
PolicyBody 等必要 Entity。是否建立 Link 的判断标准是：缺少该规范 Entity 是否会改变 Anchor
发现、Variable/Signal、作用范围、机制、周期或 Storyline 路由。纯叙述 mention 不建立 Link。

### 3.7 Variable

对 Anchor 有投研意义、允许被 Signal 引用的受控变化维度，例如可交付供给、库存覆盖、
投入成本、产能利用率或毛利率。Variable 必须来自版本化目录，记录变量 ID、定义、单位或
定性口径、允许的 Anchor 类型、互斥/派生规则和维护 owner。

### 3.8 Signal

一个带时间范围的、事件原生的判断：某个 Anchor 上受控变量发生或预计发生变化。

Signal 必须引用一个 Variable，并属于：

```text
Event × Anchor × Scope × Controlled Variable × Mechanism × Impact Window
```

它不得是实体永久属性，也不得直接等于投资结论。“Variable Signal”只是“引用了受控
Variable 的 Signal”的业务简称，不是第八种顶层数据类型。

short、medium、long 是 Analysis Result 观察 Signal 的视图，不参与 Signal 唯一身份。
Signal 可以保存由 impact window 派生的 horizon tags 便于路由，但 tags 不得改变其身份。

### 3.9 Storyline

围绕一个 Analysis Anchor 和一个明确研究问题，持续维护事实、变量信号、竞争性解释、
现实观测、历史结论和失效条件的版本化动态投资论题。

Storyline 不是 Evidence、Event、单向宣传叙事、一次 Agent 回答或永久公司标签。

一个 Anchor 可以有多条不同主题的 Storyline。例如黄金指数可以分别维护“地缘避险”、
“实际利率”和“央行购金”三个研究论题。

### 3.10 Analysis Result

在确定 decision_at、Anchor、问题和 horizon 后，基于当时可用 Event、Signal、Entity/Link
和 Storyline 形成的可复现解释。Evidence 不作为该解释的直接输入。

Analysis Result 不得被静默提升为 Evidence 或 Event。

两条 Pipeline 分别产生两个执行产物；它们不是新的图谱顶层数据类型：

- **Event Analysis Package**：一个 Event 的 reviewed Event Anchor Link、直接 Signal、影响
  周期、Event provenance 标识、冲突和已判定 Storyline 路由；
- **Investment Analysis Result**：一个稳定 Anchor 的一句话结论、结构化推理树、逐节点和
  逐周期判断、价值捕获、市场预期差、可投资映射、反方与失效条件。

最终对外发布优先映射到 Data 已有的 Research Theme 和 Research Reasoning Tree
`analyst_snapshot` 合同。Reason 可以保留更丰富的不可变运行产物和 lineage，但不得在
Graphiti 中把最终结论伪装成 Event、Signal 或 Evidence。

## 4. 时间与证据门禁

### 4.1 时间字段

| 字段                  | 含义                              |
| --------------------- | --------------------------------- |
| occurred_at           | 事件在现实中发生的时间            |
| effective_at          | Signal 预计或实际开始生效的时间   |
| published_at          | Evidence 来源公开发布的时间       |
| announced_at          | Event 被正式宣布或披露的时间      |
| known_at              | Event Curation 发布的最早可知时间 |
| ingested_at           | 系统实际摄入的时间                |
| decision_at           | 本次分析冻结知识截面的时间        |
| valid_from / valid_to | 事实、关系或状态在现实中的有效期  |

### 4.2 PIT 规则

任何历史分析必须满足 known_at 不晚于 decision_at，并使用 decision_at 当时有效的：

- 实体身份；
- 产业链关系；
- 概念成分；
- 指数成分和权重；
- Storyline 历史版本；
- 财报和指标修订版本。

事后补录、后验归因和当前 Storyline 摘要不得伪装成当时已知。

`known_at` 与 `decision_at` 属于 CaseConfig、AgentContext 和 Analysis Result 的 PIT 快照，
不属于正式 Event payload；同一个 Event 可以被多个不同 decision_at 的分析复用。缺少可证明
`known_at` 的上游发布时间依据时必须 fail closed。下游只消费计算结果和审计标识。

同源转载必须去重；来源数量不得直接等于独立证据数量。

## 5. 输入归一化

### 5.1 财报与公告

财报与公告应拆为：

```text
SourceDocument
  ├─ Publication Event
  ├─ Metric Observations
  ├─ Management Claims / Guidance
  ├─ State Changes
  └─ Signal Candidates
```

### 5.2 新闻与快讯

新闻是 Evidence 容器。系统必须区分记者确认的事实、引述主体的 Claim、未经验证的
传闻、作者解释以及同一事件的重复报道。

快讯可以触发候选 Event；在缺少足够证据时不得自动成为高置信度正式 Event。

### 5.3 市场准事实数据

价格、指数、成交、库存、汇率和利率等是 MarketObservation。

只有满足预先定义的变化规则或研究问题需要时，才派生 MarketStateChange，例如趋势
状态改变、异常波动、价差结构改变、突破业务阈值或与相关资产出现实质背离。

不得将所有 tick 或日线记录作为独立 Event 注入 Storyline。

## 6. Variable 与 Signal 合同

### 6.1 最小字段

正式 Signal 必须包含：

- signal_id；
- source_event_ids；
- Anchor 类型和 ID；
- variable_id，并能回到版本化 Variable 目录；
- derivation_type：OBSERVED 或 DERIVED；
- direction：UP、DOWN、MIXED、STABLE 或 UNKNOWN；
- assertion_modality：ACTUAL、ANTICIPATED、SOURCE_FORECAST 或 ASSUMED；
- review_status：PROPOSED、REVIEWED 或 REJECTED；
- lifecycle_state：INACTIVE、ACTIVE、DECAYING、EXPIRED、INVALIDATED 或 SUPERSEDED；
- mechanism；
- known_at 和 effective_at；
- onset、peak 和 end 的区间或 unknown；
- transmission_lag：从上一级变化传导到当前 Anchor 的最早和最晚时滞；
- decay_rule：何时开始衰减、按什么业务条件衰减，或明确为 unknown；
- duration_basis：影响周期来自政策期限、库存覆盖、订单周期、产能周期、历史经验还是待验证假设；
- magnitude：LOW、MEDIUM、HIGH 或 UNKNOWN，以及依据；
- Event provenance、Mechanism 和 Temporal 三个置信维度；
- assumptions；
- counter_signals；
- invalidation_conditions；
- projection_mode：LIVE 或 LOCAL_EVALUATION。

`onset`、`peak`、`end`、`transmission_lag` 或 `decay_rule` 可以为 unknown，但必须同时记录
缺失原因、下一次检查时间和可使其变为已知的观测项。不得只写“短期”“长期”而不声明
实际窗口，也不得把源 Signal 的周期原样复制给下游 Signal。

### 6.2 推导优先级

信号时间、方向和强度的依据优先级是：

1. 正式披露、合同、政策和确定性期限；
2. 可验证业务机制：库存、订单、交付、产能、定价和替代关系；
3. 历史同类事件和行业经验；
4. 明确标注的专家情景；
5. LLM 候选假设。

LLM 候选假设不得在没有其他依据时自动升级为已审核 Signal。

### 6.3 多信号与多跳规则

一个 Event 可以为不同 Anchor 和变量产生多个方向不同的信号，不得压缩成统一“利好”
或“利空”。

多跳传播必须逐跳说明：

- 经济或业务机制；
- 方向和时间滞后；
- 当前跳自身的 onset、peak、decay、end 和 duration basis；
- 必要条件；
- 替代或缓冲机制；
- 对应证据；
- 什么情况说明该跳不成立。

跨 Entity 的每一跳使用一条 Signal→Signal Link，并只引用一条数据库 topology Link；工具
必须校验 topology edge 端点与两个 Signal Anchor 一致、FORWARD/REVERSE 方向明确、连续
多跳的相邻 Anchor 能够衔接。多条路径共同影响同一目标 Signal 时，每条 Link 分别保存自身
impact window 和 duration basis。

不得使用“产业链每经过一跳固定衰减或固定延迟”的全局规则。

## 7. Storyline 合同

### 7.1 身份和边界

Storyline 身份建议由以下组合确定：

```text
Analysis Anchor × Research Question × Scope
```

示例：

- 黄金指数 × 地缘冲突下的避险与实际利率 × 全球；
- 光伏硅料节点 × 供需与价格趋势 × 中国；
- 某上市公司 × AI 服务器业务对盈利和估值的影响 × A 股。

Storyline 是跨多次分析延续的“投研论题状态”，不是 Event Analysis Pipeline 的前置答案。
Event Analysis Pipeline 只能提出 Event/Signal 与 Storyline 的关联候选；Investment
Reasoning Pipeline 才能读取上一版本作为基线，并判断新信息是确认、削弱、反转、延长、
缩短还是与该论题无关。只有完整分析通过审核后，才能形成下一版本。

### 7.2 必备内容

Storyline 必须包含：

- Anchor、research question 和 scope；
- created_at、as_of 和版本；
- thesis_state：EXPLORING、STRENGTHENING、STABLE、WEAKENING、INVALIDATED 或 STALE；
- Base、Bull、Bear 和 Alternative scenarios；
- 相关 Event 和 Signal 引用；
- 支持与反驳 Event/Signal；
- 未解决问题和证据缺口；
- invalidation conditions；
- short、medium、long horizon views；
- 历史 Analysis Result 引用；
- next_review_at。

### 7.3 防叙事偏差

每次更新 Storyline 必须：

- 同时检索支持和反驳当前 thesis 的 Event 与 Signal；
- 保留已经失效的旧版本；
- 标记缺失证据，不用语言完整度填补；
- 至少维护 Bear Scenario 或 Alternative Explanation；
- 说明新事件是确认、削弱、反转还是与当前论题无关；
- 不允许因价格事后变化倒推原事件一定是原因；
- 不允许用 Storyline 自身历史结论证明新结论。

DISCOVERY 阶段不得用 Storyline 泄漏预设的产业链答案。ANALYSIS 阶段读取 Storyline 时，
必须把历史结论标为 prior thesis，而不是当前事实，并同时检索没有被旧 Storyline 收录的
反向 Event 和 Signal。

## 8. 上游事实工序与两条 Pipeline 的处理合同

### 8.0 上游 Event Curation Work

Evidence 清洗成 Event 是独立于两条推理 Pipeline 的事实生产工序：

1. **Collect Evidence**：接收来源材料并保存不可变原文、发布时间和来源身份；
2. **Clean and Deduplicate**：清洗正文、去转载重复、识别同源内容；
3. **Split Claims and Occurrences**：把一条复合材料拆成可独立审核的事实、计划或主张；
4. **Normalize Event**：形成统一 5W1H、modality、occurred_at、announced_at 和 lifecycle；
5. **Review and Publish**：核验事实边界，建立 Evidence→Event provenance Link，发布 Event；
6. **Hand Off Event**：只把 Event payload、Event ID、known-at 结果和 provenance 标识交给
   Event Analysis Pipeline，不交付 Evidence 正文或片段。

Event Curation 可以使用 LLM 辅助抽取，但事实拆分、去重、来源和发布时间必须经过确定性
校验或人工审核。一个复合 Evidence 可以形成多个 Event；多个 Evidence 也可以合并支持一个
Event。这个工序不得生成 Variable、Signal、Storyline 路由或投资结论。

详细设计见 [Evidence→Event Curation Pipeline](../design/evidence-to-event-curation-pipeline.md)。

### 8.1 Graphiti Event Ingestion and Anchor Grounding

已发布 Event 进入 Graphiti 后，按以下顺序完成直接语义落图：

1. **Create Event Episode**：以 Event ID、5W1H、modality、时间、lifecycle 和 provenance
   标识创建或幂等更新 Episode/Event 投影，不加载 Evidence 内容；
2. **Extract Reasoning Mentions**：从 5W1H 识别可能进入推理路径的 mention，不追求把所有
   人名、地名和机构名图谱化；
3. **Retrieve Canonical Anchor Candidates**：只在已投影的稳定 Entity、产业链、节点、商品、
   产品、公司、概念、指数及必要地域/机制实体中召回候选；
4. **Resolve and Type Roles**：Graphiti/LLM 提议规范 ID 和 SUBJECT、TARGET、DIRECT_ANCHOR、
   JURISDICTION、LOCATION、ACTOR 等角色；
5. **Validate Grounding**：确定性门禁校验 ID、Entity 类型、允许的 Link 端点、Event 文本依据、
   置信度和歧义；未确认结果只保留为候选，不进入 Signal 构建；
6. **Write Reviewed Event Anchor Links**：把通过门禁的 Link 写入 Graphiti，并在运行 Artifact
   中保存可重放快照；不要求在 Data PostgreSQL 复制一套推理关系表。

Graphiti 原生 `MENTIONS` 只代表 Episode 提及 Entity，不等于 reviewed Event Anchor Link。
Event Curation 拥有 Event 事实，Data 拥有稳定 Entity 与基础 topology；Graphiti 是 Event
Anchor Link 的运行时查询和时态语义存储，Artifact Store 保存精确运行 lineage 与重建依据。

### 8.2 Event Analysis Pipeline

Event 分析按以下顺序工作：

1. **Accept Grounded Event**：接收已发布 Event 和 reviewed Event Anchor Links，校验身份、
   lifecycle、known-at、provenance、Anchor 歧义和未解决项，不加载 Evidence 内容；
2. **Select Variables**：从受控目录选择 Event 直接影响的 Variable；Variable 目录必须先于
   Event 投影，LLM 不得为单次 Event 临时创造同义变量；
3. **Propose Direct Signals**：提出方向、机制、幅度依据和完整 impact window；
4. **Challenge Direct Signals**：检查替代解释、Event modality、实体范围和过度推断；
5. **Retrieve Storyline Candidates**：Graphiti 可依据 Anchor、Variable、历史 Event/Signal 和
   语义相似度召回候选，但候选不构成正式 Link；
6. **Route Storylines**：在 Direct Signal 完成后判定 Storyline 及 SUPPORTS、WEAKENS、CONTRADICTS、
   REVERSES、CONTEXT_ONLY 等角色；
7. **Validate Package**：经 PIT、ID、引用、周期、Schema 和审核门禁形成 Event Analysis
   Package。

该 Pipeline 只能产生 Event 能够直接支持的 Signal。它不得遍历整条产业链、不得生成节点
机会评级，也不得从 Event 直接产生 Security 方向。

### 8.3 Investment Reasoning Pipeline

正式的 Anchor 分析必须声明：

- 用户问题；
- Analysis Anchor；
- decision_at；
- 市场和地域范围；
- short、medium、long horizon；
- 是否要求公司基本面和估值；
- 允许使用的 Event provenance 等级；
- 当前 Storyline 版本。

Event-led 请求可以先进入 DISCOVERY AgentContext，此时 Anchor 可空。Agent 基于 Event 和
Entity/Link 语义提出 Anchor 候选；候选经规范 ID 和关系门禁确认后，系统必须
为每个稳定 Anchor 分别冻结 ANALYSIS AgentContext。新事件检索窗口只决定触发集，例如
48 小时；上下文还必须包含窗口外仍处于 INACTIVE、ACTIVE 或 DECAYING 的相关 Signal，
以及 decision_at 时点有效的 Storyline 版本。

标准流程为：

1. **Freeze Context**：冻结 decision_at、Anchor、Storyline、实体和关系版本；
2. **Retrieve Active Thesis Inputs**：读取新 Event、仍有效的历史 Signal、相互竞争的 Event
   和当前 Storyline；Evidence 内容不进入此 Context；
3. **Discover Affected Chains**：由 Agent 提出候选，工具只负责真实 ID、membership 和
   topology grounding；
4. **Analyze Operating Transmission**：逐跳分析供需、价格、成本、库存、产能、交付、
   替代与缓冲；
5. **Analyze Value Capture**：判断稀缺性、议价权、利润池、进入壁垒、扩产难度和持续性；
6. **Map Investable Exposure**：核验 Company、Security、MarketConcept、CommodityIndex
   或 MarketIndex 的真实暴露 Link；
7. **Analyze Market Expectations**：基于时点合格的价格、估值、预期修正、拥挤或市场反应
   Event/Signal 判断已反映程度，缺失时输出 UNKNOWN；
8. **Build Competing Explanations**：构造 Base、Bull、Bear 和 Alternative；
9. **Produce Horizon Views**：分别形成短、中、长期机会候选、风险点或证据不足；
10. **Risk and Falsification Review**：登记反方证据、尾部风险、falsifiers 和 next checks；
11. **Publish Result**：生成一句话结论和结构化推理树，不写回事实层；
12. **Version Storyline**：经审核后追加新版本并登记监控触发器。

### 8.4 Pipeline 交接门禁

Investment Reasoning Pipeline 只消费通过校验的 Event Analysis Package。它可以对直接
Signal 提出质疑或要求重新解释，但不得静默改写 Event、Evidence 或直接 Signal。Event
Analysis Pipeline 不读取当前 Storyline 的结论来决定事实与方向，只能在完成直接 Signal
后做候选路由，防止循环论证。

### 8.5 合法 abstain

以下情况必须允许输出 INSUFFICIENT_EVIDENCE，而不是强行给趋势：

- Anchor 或 Security 身份不确定；
- Event 缺少可验证的 known-at 或 provenance audit reference；
- 主路径缺少业务机制；
- 支持与反驳证据同样强且无法区分；
- 公司业务暴露无法确认；
- 市场定价和估值数据不足；
- 时间窗口无法合理推断；
- Storyline 已超过新鲜度要求。

## 9. 多周期结论

### 9.1 Horizon 语义

short、medium、long 是研究语义，不是全系统写死的天数：

- short：信息反应、情绪、流动性和即时经营冲击；
- medium：订单、库存、价格传导、政策执行和盈利修正；
- long：产能、资本开支、技术替代、竞争格局、现金流和估值重构。

具体窗口必须按 Anchor、变量和机制配置。

### 9.2 每个 Horizon 的最小输出

每个周期、每类 Anchor 都必须独立输出：

- window；
- fundamental_trend：IMPROVING、STABLE、DETERIORATING、MIXED 或 UNKNOWN；
- thesis_state：STRENGTHENING、STABLE、WEAKENING、INVALIDATED 或 UNKNOWN；
- operating_impact：经营变量变化及其机制；
- value_capture：STRONG、PARTIAL、WEAK、NEGATIVE 或 UNKNOWN，并说明议价权、稀缺性、
  成本传导、利润泄漏和扩产/替代约束；
- investment_relevance：OPPORTUNITY_CANDIDATE、RISK_POINT、MIXED、NO_CLEAR_EDGE 或
  INSUFFICIENT_EVIDENCE；
- investable_mapping_status：MAPPED、PARTIAL、UNMAPPED 或 UNKNOWN；
- market_expectation_gap 和 already_priced_in；缺少独立市场 Event/Signal 时必须为 UNKNOWN；
- confidence：LOW、MEDIUM 或 HIGH；
- key reasons、conditions、risks、falsifiers 和 next checks；
- valid_until。

其余字段按 Anchor 类型约束：

| Anchor 类型                                  | research_posture                                         | market_trend_bias / already_priced_in     |
| -------------------------------------------- | -------------------------------------------------------- | ----------------------------------------- |
| IndustryChain / IndustryChainNode            | PRIORITIZE_RESEARCH、WATCH、RISK、INSUFFICIENT_EVIDENCE  | 不强制；没有市场映射时必须省略或 UNKNOWN  |
| Company                                      | WATCH、RISK、AVOID、INSUFFICIENT_EVIDENCE                | 不得用 Company 结果冒充 Security 定价结果 |
| MarketConcept / CommodityIndex / MarketIndex | WATCH、RISK、AVOID、INSUFFICIENT_EVIDENCE                | 必须输出，允许 UNKNOWN                    |
| Security                                     | RESEARCH_HOLD、WATCH、RISK、AVOID、INSUFFICIENT_EVIDENCE | 必须输出，允许 UNKNOWN                    |

不得用一个综合看多或看空覆盖三个周期，也不得把节点研究优先级写成证券持有建议。

### 9.3 机会与风险判断门禁

节点级结论必须逐层满足：

```text
Node Signal
→ Operating Impact
→ Value Capture
→ Market Expectation Gap
→ Investable Mapping
→ Investment Relevance
```

- 有经营改善但没有价值捕获依据：最多输出 `PRIORITIZE_RESEARCH`，不得输出已确认机会；
- 有价值捕获但没有市场预期 Event/Signal：可以输出 `OPPORTUNITY_CANDIDATE`，同时把
  `market_expectation_gap=UNKNOWN`；
- 没有真实 Company/Security/Concept/Index 暴露 Link：必须
  `investable_mapping_status=UNMAPPED`，不得输出证券方向；
- 基本面受益但市场已基本反映：不得把它表述为新的预期差机会；
- 经营受损、价值泄漏或风险上升可以形成 `RISK_POINT`，但仍需说明是否存在可投资载体；
- Storyline 保存的是本系统 prior thesis，不能证明市场已经或尚未反映。

### 9.4 “可持有”定义

RESEARCH_HOLD 表示：在当前 horizon 和已声明条件下，基本面 thesis 尚未被否定，风险和
估值处于允许范围。

它不是买入指令、永久持有标签、正收益保证、仓位建议或交易时点建议。

结论有效期取以下条件中最早发生者：

- horizon 到期；
- falsifier 发生；
- 上游 Evidence 被撤回或修订并导致 Event lifecycle 改变；
- Storyline 超过新鲜度 SLA；
- 估值或风险条件超出合同范围。

## 10. 不同 Anchor 的差异化规则

### 10.1 IndustryChain / IndustryChainNode

必须分析供给、需求、价格、库存、开工率、产能、交付周期、上下游议价、替代路径和
扩产难度。随后必须判断该节点是否控制稀缺资源、能否转嫁成本、是否承接利润池、扩产和
客户认证是否困难，以及替代供应是否足以削弱其价值捕获。节点趋势必须先映射到经已发布
Event/Signal 支持的 Company 经营暴露，再映射到 Security 或其它投资载体，不得直接等于
股票趋势。

### 10.2 MarketConcept

MarketConcept 是市场主题，不是实体产业链节点。必须分析概念定义、PIT 成分、公司业务
纯度、与真实产业节点的映射、概念漂移和拥挤。公司被纳入概念不得自动证明其有实质
业务暴露。

### 10.3 Commodity / CommodityIndex

必须分析供需、库存、产区、运输、汇率、政策、现货和期货口径、期限结构及换月影响，
并区分实体供需冲击与避险定价。

### 10.4 MarketIndex

必须使用 PIT 成分和权重，分析权重股主导程度、宏观与行业共同作用，以及指数走势与
成分公司基本面的可能背离。

### 10.5 Company / Security

Company 和 Security 必须分开：

```text
Company Fundamental Trend
    ↓
盈利、现金流、资产负债、竞争力、治理
    ↓
Security Pricing Context
    ↓
已经清洗为 Event/Signal 的估值、预期、流动性、拥挤、融资和交易制度事实
```

公司基本面改善不得直接等于 Security 继续上涨。

长期 RESEARCH_HOLD 至少检查业务位置、收入成本和现金流兑现、竞争壁垒、资产负债、
治理、资本配置、估值、已反映程度和 thesis 失效条件。

## 11. Agent Harness

### 11.1 建议角色

| Agent                      | 核心职责                           | 不得做                 |
| -------------------------- | ---------------------------------- | ---------------------- |
| Research Director          | 定义问题、Anchor、horizon 和计划   | 直接编写最终事实       |
| PIT Guardian（确定性职责） | 冻结时点并检查未来信息             | 修改 Evidence          |
| Evidence/Event Curator     | 清洗、去重、拆分、核验和发布 Event | 生成投资评级           |
| Signal Analyst             | 提出信号和周期候选                 | 无机制输出利好/利空    |
| Storyline Analyst          | 更新竞争性叙事和 thesis 状态       | 删除失败叙事           |
| Industry Chain Analyst     | 分析节点、卡点、替代和传导         | 把节点趋势等同股价     |
| Fundamental Analyst        | 财报、经营、现金流和竞争力         | 依赖 LLM 心算数字      |
| Valuation/Pricing Analyst  | 估值、预期和已反映程度             | 无数据给精确目标价     |
| Bear/Risk Analyst          | 反方证据、替代解释和尾部风险       | 迎合主 Agent 结论      |
| Research Synthesizer       | 按 horizon 综合结构化产物          | 绕过缺失上游强行评级   |
| Monitor Agent              | 新事件、失效条件和新鲜度监控       | 自动改写事实或公开结论 |

PIT Guardian 是流程中的逻辑职责，不要求由 LLM Agent 承担。生产实现 MUST 使用确定性时间
过滤器；LLM 只能解释被过滤原因或请求补充数据，不能推翻 PIT 结果。

### 11.2 LLM 与工具边界

LLM 适合理解问题、识别候选、提出机制、发现冲突、规划检索、解释工具结果和形成草稿。

确定性工具必须负责时间过滤、版本冻结、实体映射、财务计算、单位币种转换、业务暴露、
估值敏感性、引用校验、Schema 校验、产物哈希和运行记录。

Bull 与 Bear 必须使用同一个冻结事实包独立工作。Synthesizer 不得绕过事实、财务、
反方和风险产物。

本方法论采用“Agent 提议、确定性工具校验、必要时人工审核”，不得把投研语义全部写死
成规则引擎：

- Codex/LLM 负责 Event 语义理解、实体和产业链候选召回、Variable 选择、Signal 方向与
  机制假设、周期解释、主叙事/反叙事和证据缺口判断；
- 确定性算法负责 PIT、规范 ID、数据库 Link 存在性、Schema、单位、周期字段完整性、
  节点覆盖、引用和权限；
- 数据库中存在 Link 只表示 Agent 可以考虑该路径，不代表 Signal 必然沿该 Link 传播；
- LLM 提出的路径只有在引用真实 Link、给出业务机制并通过门禁后，才能成为已审核
  Signal 之间的传导 Link；
- 没有足够语义或事实依据时，Agent 应输出候选、UNKNOWN 或 INSUFFICIENT_EVIDENCE，
  而不是由算法补齐“标准答案”。

### 11.3 执行器无关

Codex、Claude Code 和 Agno 是可替换执行器。方法论必须通过统一的 Agent 输入输出
Schema、Tool 接口、Skill 文档、Artifact 合同、权限白名单、审批门禁和运行记录表达，
不得依赖某个模型的隐藏思维链或框架私有 memory。

## 12. Graphiti 边界

Graphiti 是推理引擎的核心时态语义数据源、关系抽取和检索基础设施，不拥有 Evidence、
Event、稳定 Entity、基础产业链 topology 或最终投资结论的事实权威。

Graphiti 只承载或投影七类顶层领域数据：Evidence、Event、Entity、Link、Variable、Signal
和 Storyline。Observation、Claim、StateChange、Interpretation/Hypothesis 通过这些既有
类型的 type、role 或属性表达。Analysis Context、Analysis Result、Run Card 和监控运行产物
保存在 Artifact Store；Storyline 可以保存其不可变引用，但不得把它们提升为新的事实节点。

Evidence 即使为 provenance 或 Event Curation 投影到 Graphiti，也必须与下游推理查询隔离。
Event Analysis 和 Investment Reasoning 的 Context assembler 从 Event 开始，不返回 Evidence
正文、摘要或片段；Reasoning Tree 的首个事实节点是 Event。

Graphiti Ingestion 可以使用 LLM 识别 5W1H mention、解析规范 Entity 候选和提出直接事实
关系，但不得为稳定主数据生成新 canonical ID。通过门禁的 Event Anchor Link、Signal、
Storyline 路由和 derived reasoning Link 以 Graphiti 为运行时关系源；对应 Event Analysis
Package、Investment Analysis Result 和 RunCard 保存在 Artifact Store，用于审计、重放和
Graphiti 重建，而不是在 Data PG 镜像全部推理关系。

Event Anchor Link 只连接 Event 直接支持的推理锚点及必要范围/机制 Entity。Graphiti 可以在
Direct Signal 前召回 Storyline 候选，但正式 Event/Signal→Storyline Link 必须在 Direct Signal
完成并通过挑战后建立；产业链传播得到的间接受影响节点只能由 Investment Reasoning 产生。

Graphiti 不得：

- 将 LLM 输出自动提升为 Event；
- 将 Analysis Result 自动写回 Evidence；
- 用当前 Storyline 覆盖历史版本；
- 让 Agent 自由查询原始 Neo4j 绕过时间和来源约束；
- 仅凭图路径存在就声明因果关系；
- 将模型或结论反向用于提高事实可信度。

权威 Tidewise 来源事实和稳定主数据仍由其 owning system 管理；Graphiti 是可替换的推理
关系、时态语义记忆与 AgentContext provider。

## 13. 三个参考项目的吸收边界

| 项目         | 吸收                                                                                                          | 当前不吸收                                                     | 本系统定位                        |
| ------------ | ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------- |
| K-Quant      | Macro/Meso/Micro、时序知识、事件冲突、关系演化、传导解释                                                      | 关系矩阵、HIST/GNN、Qlib、ensemble、股票预测模型               | 时序知识和事件传导方法            |
| FinRobot     | 财报三表、财务桥接、估值敏感性、代码算数字、专项 Agent、Bull/Bear/Judge、报告溯源                             | 粗略涨跌预测、关键词概率、自动目标价、整套 UI/连接器           | 基本面、财务、估值和研报方法      |
| Vibe-Trading | Plan/Ground/Execute/Validate/Deliver、Hypothesis 生命周期、Tools/Skills、Agent DAG、PIT、run card、监控与审批 | 因子、策略生成、量化回测、Broker、Shadow Account、技术指标策略 | Agent Harness、流水线、治理和监控 |

三个项目只提供可借鉴能力，不反向决定观潮家领域模型和技术栈。

## 14. Analysis Result 最小输出

每次结果至少包含：

1. Anchor、问题、市场、decision_at 和知识版本；
2. 当前 Storyline 摘要；
3. 本次新增或变化的关键 Event；
4. Signal 及其影响周期；
5. 主传导机制；
6. 反向路径和替代解释；
7. 每个受影响节点的 operating impact；
8. 每个受影响节点的 value capture 及其依据；
9. Company/Security/Concept/Index 的 investable mapping 或明确 UNMAPPED；
10. 市场预期差和已反映程度，或明确 UNKNOWN；
11. short、medium、long 独立的 opportunity/risk 判断；
12. 一句话结论和结构化推理树；
13. 基本面趋势与市场趋势偏向的区别；
14. RESEARCH_HOLD、WATCH、RISK、AVOID 或 INSUFFICIENT_EVIDENCE；
15. 证据等级和缺口；
16. 风险、falsifiers 和 next checks；
17. 结论有效期和重新评估触发器；
18. 使用的 Agent、工具、模型、Skill 版本和产物引用。

结构化推理树至少表达：

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

每个树节点保存可审计陈述、领域对象引用、Event/Signal/Link 引用、假设、反方、置信度和
失效条件；Event 的上游 Evidence provenance 由审计接口单独提供，不进入推理树。不得保存
或要求模型暴露原始隐藏思维链。

## 15. 验收门禁

### 15.1 正确性

- 每个下游关键事实都引用已发布 Event；Event 必须能通过上游审计接口回到 Evidence；
- 每个进入分析的 Event 都有可审计依据计算出的 AgentContext known_at；
- 每个 Signal 都有 Anchor、变量、机制和周期；
- 每个 Signal 的影响周期都能区分 onset、peak、decay/end 和逐跳 transmission lag；
- 每条多跳路径都有逐跳依据和失效条件；
- Storyline 同时包含支持和反驳其 thesis 的 Event/Signal；
- Event Analysis Package 不包含跨节点传导或投资结论；
- Investment Analysis Result 只引用经过审核的直接 Signal；
- 节点经营改善、价值捕获、市场预期差和可投资映射没有被相互替代；
- 没有市场 Event/Signal 时 market expectation gap 为 UNKNOWN；
- 没有真实暴露 Link 时不得输出具体可投资标的；
- Company 和 Security 不混淆；
- MarketConcept 和 IndustryChainNode 不混淆；
- 基本面趋势和股价趋势偏向不混淆；
- 证据不足能够作为合法终态；
- Analysis Result 不被回写为事实。

### 15.2 可复现性

在 decision_at、Event 快照及其 provenance 版本、Storyline、Ontology、Agent/Skill/Tool 和
模型版本相同时，
应当可以重新生成语义一致的结构化结论。自然语言措辞可以不同，但事实、信号、风险、
失效条件和状态不得无解释漂移。

### 15.3 专业性

最终结果必须能回答：

- 到底发生了什么，哪些只是 Claim？
- 影响哪个 Anchor 的哪个变量？
- 为什么、何时开始、何时可能衰减？
- 哪些事实支持，哪些事实反驳？
- 短、中、长期为什么可能不同？
- 公司基本面与 Security 定价之间差什么？
- 市场是否可能已经反映？
- 什么情况说明判断错了？
- 下一步应该核查什么？

## 16. 案例实施前的数据门禁

要从“节点经营变化”走到“可投资机会或风险”，必须只读核验或补齐以下事实：

- 节点价格、成本、库存、开工、订单、需求和交付观察；
- 已清洗为 Event/Signal 的节点议价权、成本转嫁、供应集中度、客户认证、扩产周期和替代
  难度事实；
- ChainNode/IndustryChain 到 Company 的真实业务暴露 Link；
- Company 到 Security 的正式发行主体 Link；
- ChainNode/IndustryChain 到 MarketConcept、CommodityIndex、MarketIndex 的正式映射；
- decision_at 时点可知并已清洗发布的价格、估值、盈利预期变化、市场反应和拥挤
  Event/Signal。

缺失上述后半部分数据时，真实 Demo 可以输出“节点机会候选或风险点”，但不得输出
“具体证券可投资”或 RESEARCH_HOLD。

## 17. 待讨论问题

1. 生产 Storyline Version 最终由 Data 还是 Reason 拥有，跨服务 append/read 合同是什么？
2. Bull/Base/Bear 是同一 Storyline 的 Scenario，还是独立竞争 Storyline？
3. short、medium、long 是否按 Anchor 类型分别配置默认窗口？
4. 第一版 Controlled Variable 词表覆盖哪些变量，由谁维护？
5. Signal 何时从 PROPOSED 晋级为 REVIEWED，哪些情形必须人工审核？
6. magnitude 只用定性档位，还是允许确定性区间？
7. 多个方向冲突的信号如何合成，是否允许不合成？
8. 不采用数值概率时，置信度的升级和降级规则是什么？
9. 市场“已反映程度”采用哪些定性和描述性证据？
10. RESEARCH_HOLD 是否适用于板块、概念和指数，还是只适用于 Security？
11. Storyline 刷新 SLA、分裂、合并和过期规则是什么？
12. Data Research Theme 是否升级 V4 承载 canonical ID/horizon，还是长期只做展示投影？
13. 不做量化回测后，事后验证采用趋势、条件兑现还是专家复核？
14. 哪些 Company→ChainNode、Company→Security 和市场预期数据先补以验证真实可投资映射？
15. WATCH、RISK、AVOID 的产品表达如何避免被理解为交易建议？

## 18. 后续讨论顺序

建议按以下顺序继续设计和执行：

1. 定义第一个真实 Demo 的问题、时点和输出，不预置业务答案；
2. 从该问题反向识别真正需要的领域对象、字段和关系，形成最小 Graphiti Schema；
3. 将 Schema 逐项映射到 PostgreSQL，缺失的权威事实才由对应 owner 补表、字段或 Link；
4. 选取真实 Evidence，经独立 Event Curation Work 清洗、拆分和审核成 Event；
5. 把本例所需 Entity、Variable、Storyline、产业链和 topology 确定性投影到 Graphiti；
6. 将 Event 作为 Episode 入图，由受控 Graphiti Ingestion 建立 reviewed Event Anchor Links；
7. 建立 Event Analysis 与 Investment Reasoning 的 Codex 工具和多轮 Pipeline；
8. 运行一次真实推理，人工审阅一句话结论、节点周期结果和推理树；
9. 根据真实运行暴露的问题修正 Schema、PG 数据、AgentContext、工具和 Prompt；
10. 闭环稳定后才建立固定回归样本，再扩展 MACRO、GEO、COMPANY 和 LIVE 发布。

## 19. 变更记录

### 0.5.0 — 2026-08-24

- 将 Event 处理冻结为 Event Curation、Graphiti Ingestion/Anchor Grounding、Event Analysis、
  Storyline Routing 和 Investment Reasoning 的有序工序；
- Event Curation 只发布可信 5W1H，不生成 Variable、Signal、Storyline 或间接影响；
- Graphiti 从 Event 5W1H 识别推理必要 mention，匹配规范 Anchor，并经门禁建立 Event Anchor
  Link；不把所有 mention 图谱化；
- Variable/Direct Signal 只能在 reviewed Event Anchor Links 之后生成，正式 Storyline 路由
  只能在 Direct Signal 之后确认；
- 明确 PG 拥有 Evidence、Event、稳定 Entity 和基础 topology，Graphiti 承载运行时推理
  关系，Artifact Store 保存审计和重建快照，避免在 PG 镜像全部推理关系；
- 增加 Evidence→Event Curation Pipeline 的独立设计引用。

### 0.4.0 — 2026-08-23

- 将实施方式改为真实 Demo 驱动，不在首次运行前冻结标准答案或下游 Signal；
- 领域对象和关系由具体案例问题反向识别，而不是先建设通用 Graphiti Schema；
- 新增独立 Event Curation Work，明确 Evidence 清洗成 Event 是上游事实生产工作；
- Event Analysis 与 Investment Reasoning 均从已发布 Event 开始，Evidence 内容不进入下游
  AgentContext 或推理树；
- 执行顺序改为最小 Schema→PG 缺口→Graphiti 投影→Codex 工具→真实推理→人工复盘。

### 0.3.0 — 2026-08-23

- 将方法论显式拆成 Event Analysis Pipeline 与 Investment Reasoning Pipeline；
- 明确 48 小时等窗口只筛选新 Event，窗口外仍有效 Signal 和当前 Storyline 继续进入分析；
- 增加节点经营影响、价值捕获、市场预期差、可投资映射和机会/风险五层判断；
- 将 Storyline 冻结为跨分析版本的 prior thesis，不允许反向决定 Event 事实和直接 Signal；
- 增加 Event Analysis Package、Investment Analysis Result 和结构化推理树执行合同；
- 明确复用 Data Research Theme / Research Reasoning Tree 发布合同，并补齐证券机会的数据门禁。

### 0.2.0 — 2026-08-23

- 将顶层领域数据收敛为 Evidence、Event、Entity、Link、Variable、Signal、Storyline；
- 统一 Event 合同，以 modality 和投影元数据区分本地评估，不再建立 ResearchEvent 与
  ScenarioEvent 平行类型；
- 将 Variable 与 Signal 分开建模，并补齐 Signal 的影响周期、审核状态和生命周期；
- 增加 GeopoliticRivalry、MacroEconomic Analysis Anchor；
- 按 Anchor 类型拆分 horizon 结果合同，节点不再使用 RESEARCH_HOLD；
- 明确 Agent 提议、确定性工具校验的混合推理边界。

### 0.1.0 — 2026-08-22

- 首次固化当前讨论结果；
- 确认事件→变量信号→Storyline→多周期结论主链；
- 明确事实、主张、解释、假设和结果隔离；
- 明确不做量化投资，但保留确定性财务与估值计算；
- 明确 K-Quant、FinRobot、Vibe-Trading 的吸收与排除边界；
- 将 Analysis Anchor 限定为稳定研究对象，Storyline 定义为动态论题；
- 保留 Storyline、周期、状态和持久化 owner 等待讨论问题。
