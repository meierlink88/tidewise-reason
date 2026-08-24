# StockTell 推理方法与观潮家数据/图谱/推理设计调整

> 调研日期：2026-08-23
>
> 一手资料：[StockTell 数据来源与方法](https://www.stocktell.me/methodology?from=evidence)、[StockTell 关系说明](https://www.stocktell.me/relations?from=methodology)
>
> 目标：研究 StockTell 的真实推理边界，并对照观潮家当前 Event、Entity、Link、Variable、Signal、Storyline 方法，提出数据类型、图谱和 Agent 推理设计调整。

## 1. 核心判断

StockTell 不是一个让 LLM 自主遍历全量图谱并预测股票的系统。它是一个：

```text
人工核定的长期产业关系模型
+ 每日事件/行情触发
+ 规则约束的链级方向
+ LLM 归纳和候选解释
+ 来源、发布和置信度护栏
+ 收盘后复盘
```

它最值得吸收的是：

1. 长期关系与当日影响严格分离；
2. 关系距离与投资结果严格分离；
3. AI 只在已审核事实和关系边界内推理；
4. 结论必须带验证入口和下一检查点；
5. 原始结论不可事后改写；
6. 市场行为不能替代订单、收入、客户等产业事实。

它不具备我们目标中的完整能力：宏观/地缘事件、多节点语义传导、Variable/Signal 影响周期、跨时点 Storyline、价值捕获、市场预期差和短中长期独立判断。因此现有方法论不能缩减成 StockTell 的静态映射模式。

最终方向应是：吸收 StockTell 的关系治理和发布闭环，同时保留 Agent 的语义发现、多轮推导、Signal 周期和 Storyline 记忆。

## 2. StockTell 的真实推理流程

官方方法页公开了七步流程：

```text
1. 捕获隔夜美股异动或全球事件
2. 使用人工关系档归入具体产业链和环节
3. LLM 归纳链级判断，规则为方向提供兜底
4. 使用预配置关系模型映射 A 股
5. 绑定真实检索或人工录入的来源
6. 执行结构、禁词和具体涨跌数字护栏
7. 发布，收盘后自动记账并回流人工复核
```

产业链环节、股票映射和关系档都不由 AI 临时决定。未逐票审核的标的使用保守的环节默认档；引用链接也不能由 AI 生成。[StockTell 数据来源与方法](https://www.stocktell.me/methodology?from=evidence)

### 2.1 这套系统实际做了三种不同工作

#### 长期事实工作

- 人工维护产业链和环节；
- 人工维护股票与产业链的关系；
- 为直接/间接关系登记公开披露入口和验证点；
- 关系升级走代码评审，每日行情不自动改档。

#### 当日推理工作

- 将 Event 或海外标的异动路由到已配置产业链；
- 生成链级方向和热力；
- 从关系模型中取出可展示的国内标的；
- LLM 负责归纳原因、风险和候选解释。

#### 治理与验证工作

- 区分具体来源与常设核验入口；
- 区分事实来源、平台推理和待验证假设；
- 将引用可达性与推理置信度分开；
- 冻结历史原文；
- 收盘后记录市场是否同向并送入人工复核。

这三类工作不应被实现成一个 LLM Prompt。

## 3. StockTell 的关系模型不能原样复制

StockTell 对外使用：触发源、直接映射、间接映射、情绪映射、弱映射、待验证。[StockTell 关系说明](https://www.stocktell.me/relations?from=methodology)

这个分类适合产品展示，但从领域建模角度，它混合了四个不同维度：

| StockTell 标签 | 实际领域含义 | 观潮家应落在哪一层 |
| --- | --- | --- |
| 触发源 | Event 中的主体/来源角色 | Event→Entity Link 的 role |
| 直接/间接/情绪/弱 | 业务暴露和传导距离 | Entity Link + 图路径的展示分类 |
| 待验证 | 关系审核生命周期 | Link.review_status |
| 已接入披露/部分待核验/待补来源 | 关系依据完整度 | Link.provenance/evidence_status |

因此不能建立一个统一 `stock_relation_type` 枚举，把这些状态混在一起。否则会出现：

- 一个关系同时既是 `DIRECT` 又是 `PENDING`，但单枚举无法表达；
- “触发源”被错误存成公司永久属性；
- “情绪映射”被误认为产业经营关系；
- 关系档被误用成 Event 对股票的正负影响。

观潮家应保存正交事实，StockTell 风格的关系档只作为可解释的产品视图。

## 4. 当前数据合同的关键缺口

### 4.1 Event 结构可保留，但 Event Link 需要重构

当前 `events` 已具有 5W1H、FACT/PLAN/SPEC、发生时间和公告时间，能够作为下游事实起点。

但当前 `event_actor_links`：

- 只允许 Country、Person、Organization、Company；
- 角色只有 MENTIONS、AFFECTS、ORIGINATES_FROM、TARGETS；
- 不能正式关联 IndustryChain、ChainNode、Commodity、MacroEconomic、GeopoliticRivalry 等研究实体；
- `actor_id` 没有对相应实体表的强引用。

当前 `event_asset_links` 又直接保存 `impact_direction=POSITIVE/NEGATIVE/NEUTRAL`。这会把“Event 与资产有关”与“Event 对资产的投研方向”混在一起。按当前方法论，方向应属于 Signal 或 Analysis Result，而不是事实 Link。

依据：`../tidewise-ai/data-service/backend/migrations/000060_rebuild_event_domain.sql:34`、`:77`、`:107`。

建议：

- 用统一的 Event→Entity Link 语义覆盖主体、对象、来源、地点、目标、涉及和触发源；
- Link 只表达事实角色和 grounding confidence；
- 删除或停止消费 EventAssetLink 上的投资方向；
- Event 对 Variable/资产的方向由 Direct Signal 表达。

### 4.2 缺少 Company→ChainNode 和 Company→Security

当前只有 Company→Industry，无法知道公司实际处于哪条产业链的哪个节点；Company→Security 的 issuer 关系也已被移除。

依据：`../tidewise-ai/data-service/backend/migrations/000067_make_company_independent.sql:117`、`:273`。

这是实现 StockTell 类“直接、间接、情绪映射”的最大 P0 缺口。没有这两类 Link，系统最多能说节点受影响，不能可靠映射公司和证券。

建议增加的 Link 语义：

```text
Company --OPERATES_AT/SUPPLIES_TO/BUYS_FROM/PROVIDES_SERVICE_AT--> ChainNode
Company --ISSUES--> Security
Company/Security --ASSOCIATED_WITH--> MarketConcept
```

Company→ChainNode Link 至少包含：

- business_role；
- exposure_basis；
- revenue_or_cost_exposure（允许 UNKNOWN）；
- customer_or_supplier_scope；
- geography；
- valid_from/valid_to；
- review_status；
- evidence_status；
- verification_requirements；
- provenance reference。

### 4.3 Variable 和 Signal 已没有正式表

迁移 000059 已删除 `variable_definitions`、`variable_signals`、`event_entity_links` 和传导规则等旧表。

依据：`../tidewise-ai/data-service/backend/migrations/000059_retire_data_event_semantics.sql:146`。

删除旧模型本身没有问题，但新的 Signal 语义需要正式 owner：

- Variable 是稳定、受控的变化维度，应有可版本化目录；
- Signal 是带 Anchor、方向、机制、影响周期和生命周期的分析事实；
- Graphiti 只能做投影，不能成为 Signal 唯一事实 owner。

建议 ownership：

| 数据 | 建议 owner | 原因 |
| --- | --- | --- |
| Variable Definition | Data 或正式 Ontology owner | 跨分析复用、稳定词义 |
| Direct/Derived Signal | Reason | 分析产生、有审核生命周期 |
| Signal Transmission Link | Reason | 分析路径，不是主数据拓扑 |
| Analysis Result/Run/Validation | Reason Artifact Store | 执行产物，不是事实实体 |

具体是否与 Data PG 共库需要单独设计门决定，但不能只写进 Neo4j 后失去权威来源。

### 4.4 Storyline 当前不足以承担跨时点判断

当前 Storyline 是可更新主记录，只能直接关联 Event；没有不可变版本、Signal Link、支持/削弱/反驳角色、下一验证点和失效条件。Corporate Storyline 目前也没有 Company anchor。

依据：`../tidewise-ai/data-service/backend/migrations/000066_add_storyline_persistence.sql:24`、`:71`，以及 `../tidewise-ai/data-service/backend/migrations/000067_make_company_independent.sql:105`。

建议补充：

- append-only StorylineVersion；
- Storyline→Event/Signal 的 SUPPORTS、WEAKENS、CONTRADICTS、EXTENDS；
- prior thesis、current thesis、alternative thesis；
- horizon views；
- verification points、falsifiers、next_review_at；
- supersedes version Link；
- Company anchor 恢复为正式可引用关系。

## 5. 推荐的数据类型调整

不需要增加新的顶层领域词汇，仍使用：

```text
Evidence | Event | Entity | Link | Variable | Signal | Storyline
```

需要增加的是 Link subtype、字段合同和执行 Artifact。

### 5.1 Entity

至少覆盖：

- Country、Region、Organization、Company、Security；
- Industry、IndustryChain、ChainNode；
- MarketConcept、Commodity、CommodityIndex、MarketIndex；
- MacroEconomic、GeopoliticRivalry。

### 5.2 Link

#### 主数据事实 Link

- CHAIN_CONTAINS_NODE；
- NODE_INPUT_TO / IS_COMPONENT_OF / DEPENDS_ON；
- COMPANY_OPERATES_AT_NODE；
- COMPANY_ISSUES_SECURITY；
- ENTITY_ASSOCIATED_WITH_CONCEPT；
- COMPANY/ENTITY 位于 Country/Region。

#### Event 事实 Link

- SUBJECT、ACTOR、TARGET、LOCATION、ORIGIN、INVOLVES、TRIGGER_SOURCE。

#### 分析 Link

- EVENT_PRODUCES_SIGNAL；
- SIGNAL_ANCHORED_AT_ENTITY；
- SIGNAL_USES_VARIABLE；
- SIGNAL_TRANSMITS_TO_SIGNAL；
- STORYLINE_SUPPORTS/WEAKENS/CONTRADICTS/EXTENDS。

### 5.3 Link 公共治理字段

长期关系 Link 至少需要：

- `review_status=CANDIDATE|REVIEWED|REJECTED`；
- `evidence_status=VERIFIED_ENTRY|PARTIAL|MISSING`；
- `provenance_refs`；
- `verification_requirements`；
- `valid_from/valid_to`；
- `confidence`；
- `reviewed_by/reviewed_at`。

不建议把这些字段全部强加给产业链拓扑表；可以按 Link subtype 定义属性合同，但查询层需提供统一治理视图。

### 5.4 Variable

Variable 只定义“可发生什么变化”，例如：

- deliverable_supply；
- demand；
- inventory_coverage；
- selling_price；
- input_cost；
- capacity_utilization；
- order_visibility；
- customer_capex；
- policy_restriction_intensity；
- market_attention。

Variable 不保存当前方向。

### 5.5 Signal

Signal 表达：

```text
一个 Event 或上游 Signal
使一个 Anchor 的一个 Variable
在特定时间窗口内出现方向变化
```

最小字段：

- source Event/Signal；
- anchor Entity；
- variable；
- direction；
- mechanism；
- known_at/effective_at；
- onset、peak、decay/end；
- state=PROPOSED|REVIEWED|ACTIVE|DECAYING|EXPIRED|INVALIDATED；
- confidence；
- assumptions、falsifiers、review status。

### 5.6 Storyline

Storyline 不等于 StockTell 的“产业链配置”。产业链配置是事实底图；Storyline 是：

```text
围绕一个 Anchor 和研究问题
持续记录 thesis 如何被新 Event/Signal 确认、削弱或反转
```

### 5.7 执行 Artifact

以下不进入事实图：

- AgentContext；
- AnalysisResult；
- ReasoningTree；
- PublicationRecord；
- ValidationResult；
- RunCard。

## 6. 推荐的 Graphiti 图谱分层

### 6.1 第一层：稳定事实图

```text
IndustryChain ─CONTAINS→ ChainNode
ChainNode ─INPUT_TO/COMPONENT_OF→ ChainNode
Company ─OPERATES_AT→ ChainNode
Company ─ISSUES→ Security
Company/Security ─ASSOCIATED_WITH→ MarketConcept
```

这些关系必须来自 PG 权威数据，不能由 LLM 在分析运行时写入正式图。

### 6.2 第二层：Event 事实图

```text
Event ─SUBJECT/TARGET/LOCATION/ORIGIN/TRIGGER_SOURCE→ Entity
Event ─SUPPORTED_BY→ Evidence Reference
```

Evidence 只用于 provenance。Event Analysis 和 Investment Reasoning 的 Context 从 Event 开始，不返回 Evidence 正文。

### 6.3 第三层：动态影响图

```text
Event ─PRODUCES→ Direct Signal
Signal ─ANCHORED_AT→ Entity
Signal ─USES→ Variable
Signal ─TRANSMITS_TO→ Derived Signal
```

每条 Signal→Signal Link 必须引用真实产业链 topology Link，并记录机制、方向、lag、条件和失效标准。数据库存在拓扑边不代表 Signal 自动传播。

### 6.4 第四层：Storyline 记忆图

```text
StorylineVersion ─ANCHORED_AT→ Entity
StorylineVersion ─SUPPORTS/WEAKENS/CONTRADICTS→ Event/Signal
StorylineVersion(n+1) ─SUPERSEDES→ StorylineVersion(n)
```

Graphiti 保存投影和时态检索能力，权威状态仍由 PG/Reason Artifact owner 管理。

### 6.5 不应建立的边

- `Event ─POSITIVE/NEGATIVE→ Security`；
- `MarketConcept ─证明受益→ Company`；
- `股价同向 ─验证→ 产业关系`；
- `AnalysisResult ─作为事实→ Entity`；
- LLM 临时猜测直接写入正式 Company→ChainNode Link。

## 7. 推荐的 Agent 推理方法

StockTell 把链和标的完全预配置。观潮家需要更强的宏观到微观发现能力，但必须保持相同的事实边界。

### 7.1 Stage 0：PIT 与事实冻结

- 冻结 decision_at；
- 只读取当时已知的 Event、Entity、Link 和 Signal；
- 检查 Event provenance，但不把 Evidence 正文放入 Context；
- 冻结链配置、业务暴露 Link 和 Storyline 版本。

### 7.2 Stage 1：Event 直接解释

由 LLM：

- 理解 5W1H；
- 确认实体角色；
- 选择直接被改变的 Variable；
- 提出 Direct Signal、机制和影响周期；
- 提出候选产业链，不直接输出股票方向。

由工具校验：

- 实体 ID、Event Link、Variable 定义；
- 时间完整性和 Schema；
- 不允许从 Event 直接跳到 Security 结论。

### 7.3 Stage 2：候选产业链发现与 Context 扩展

```text
LLM 提出候选链/节点
→ Tool 从 PG/Graphiti 返回真实 membership 和 topology
→ LLM 比较候选路径
→ 无真实路径则输出 CANDIDATE/UNMAPPED
```

这一步不同于 StockTell 的完全预配置方式，但仍不允许 LLM 发明实体和边。

### 7.4 Stage 3：逐节点多轮传导

每一跳单独判断：

- 上游 Variable 变化如何改变下游 Variable；
- 方向是否保持、反转或被缓冲；
- 传导时滞和持续期；
- 库存、合同、替代、定价权、产能和政策条件；
- 哪个真实 topology Link 支持该路径。

算法只校验边、方向、连续性和字段，不替 LLM 决定经营语义。

### 7.5 Stage 4：公司和证券映射

先从 Node Signal 查询已审核的 Company→ChainNode Link，再查询 Company→Security：

```text
Node Signal
→ Company business exposure
→ operating impact
→ value capture
→ Security mapping
→ expectation/pricing context
```

产品层可以生成 StockTell 风格关系档，但应由正交事实计算：

- reviewed direct operating Link → 直接映射；
- 需要一跳或暴露不纯 → 间接映射；
- 只有 MarketConcept Link → 情绪映射；
- 路径过远 → 弱映射；
- Link 未审核 → 待验证。

关系档只说明距离，不生成投资结论。

### 7.6 Stage 5：Bull/Bear 与结论合成

- Bull Agent 给出主传导和价值捕获；
- Bear Agent 使用同一冻结 Context 找替代解释、缓冲、反向 Signal 和已反映风险；
- Synthesizer 独立输出 short/medium/long；
- 缺 Company Link、估值或市场预期数据时输出 UNMAPPED/UNKNOWN，而不是补猜。

### 7.7 Stage 6：发布护栏

吸收 StockTell 的护栏思想，但不局限于禁词：

- Schema、PIT、ID 和版本校验；
- 每个 Signal 有 Variable、Anchor、机制和完整 impact window；
- 每条传导引用真实 Link；
- Company/Security 映射必须经过审核；
- 事实、推理和假设分层；
- 高置信度需要审核过的关系与足够 Event 依据；
- 固定输出 next checks 和 falsifiers；
- 冻结原始 AnalysisResult，不随后市覆盖。

### 7.8 Stage 7：分层验证

StockTell 的“次日同向”只能作为 Market Reaction。观潮家需要三种验证结果：

| 验证层 | 问题 |
| --- | --- |
| Market Reaction | 市场当日/次日是否同向反应 |
| Operating Validation | 订单、价格、库存、产能、收入、毛利等是否兑现 |
| Thesis Validation | Storyline 的核心机制是否被确认或反驳 |

市场同向率不能自动升级 Company→ChainNode Link，也不能证明 Signal 机制正确。

## 8. 对现有两条 Pipeline 的具体修改

### Event Analysis Pipeline

保留当前职责，但补充：

1. Event→Entity Link 的正式发布；
2. Direct Signal 的正式 owner 与持久化；
3. Signal 必须包含影响周期和验证要求；
4. 允许提出候选链，但不得生成 Company/Security 方向；
5. 未审核关系只进入 review queue。

### Investment Reasoning Pipeline

补充：

1. 只消费 REVIEWED Direct Signal；
2. 读取审核过的 Company→ChainNode 和 Company→Security；
3. 将关系距离、经营影响、价值捕获和市场预期分开；
4. 输出 StockTell 易懂的产品摘要，同时保留结构化推理树；
5. 强制 short/medium/long、next checks 和 falsifiers；
6. 发布后进入三层验证闭环。

## 9. 建议实施优先级

### P0：让一个真实案例具备可执行事实图

1. 通用 Event→Entity Link；
2. Variable Definition；
3. Reason-owned Signal 和 Signal Transmission Link；
4. Company→ChainNode；
5. Company→Security；
6. Link provenance/review/validity；
7. Graphiti 的确定性投影和受控查询。

### P1：跑通一次 Agent 推理

1. Event Analysis 多轮工具；
2. 候选链发现和真实拓扑扩展；
3. 逐节点传导；
4. 公司/证券映射；
5. Bull/Bear；
6. 一句话结论和推理树；
7. 不可变 AnalysisResult。

### P2：持续投研闭环

1. StorylineVersion；
2. 支持/反驳 Signal Link；
3. 验证点监控；
4. Market/Operating/Thesis 三层复盘；
5. 关系人工审阅工作台。

## 10. 最终结论

StockTell 的方法证明：可靠的股票产业链解释首先依赖稳定、经审核、可回溯的关系图，其次才是 LLM 的文字和推理能力。

但我们的目标比 StockTell 更进一步。正确调整不是把所有链和结论写死，而是：

```text
数据库和图谱约束“有哪些真实对象和关系”
LLM 负责理解“本次 Event 为什么以及如何沿这些关系传导”
确定性工具校验“有没有越过事实、时间和权限边界”
人工审核负责“新的长期关系能否进入正式关系图”
```

因此应优先补齐 Event→Entity、Company→ChainNode、Company→Security、Variable/Signal 持久化和关系治理，再搭建多轮 Agent 推理。Storyline 和多周期 Signal 不应删除，它们是观潮家相对 StockTell 支持宏观、中长期和持续 thesis 管理的关键差异。
