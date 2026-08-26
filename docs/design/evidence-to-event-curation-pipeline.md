# Evidence→Event Curation Pipeline 设计

> 状态：Draft，待业务和 Data owner 评审
>
> 版本：0.3.0
>
> 日期：2026-08-25
>
> 方法论上游：[事件驱动定性投研方法论 Spec](../specs/event-driven-investment-research-methodology.md)
>
> 下游设计：[事件驱动投研 Agent 真实推理 Demo](./event-driven-reasoning-demo-design.md)
>
> 接收与落库实现：[Event Candidate 接收、去重与发布设计](./event-candidate-resolution-ingestion.md)

## 0. 目的和冻结边界

本 Pipeline 把不可变 Evidence 提炼为可持续更新、可追溯、可用于推理的 Event。它不仅要从
本批 Evidence 中识别事件，还必须判断新材料是在：

- 支持或修订一个历史 Event；
- 描述一个与历史 Event 相关、但现实发生不同的新 Event；
- 仅提供背景、观点或无法核验的 Claim，不形成 Event。

本 Pipeline 解决“现实中发生了什么，以及哪些 Evidence 支持这个 Event”，不解决“它对投资
意味着什么”。

冻结边界：

```text
Event Curation 可以产生或更新
  Event
  Evidence→Event provenance Link
  curation audit

Event Curation 可以只读使用
  已发布历史 Event
  已审核的 Event→Anchor Link
  规范 Entity / Anchor

Event Curation 不得产生
  Event→Anchor Link（由后续 Event Ingestion / Grounding 建立）
  Variable
  Signal / impact window
  Storyline route
  产业链传播
  投资结论
```

Evidence、Event、Entity、Link、Variable、Signal、Storyline 仍是唯一顶层领域数据。批次、候选、
召回结果、匹配决定和审核记录只是 Pipeline 执行产物，不是新的图谱领域对象。

## 1. 目标架构和权威边界

```text
Agent OS 发布 Evidence
          │
          ▼
Data Service / PostgreSQL（事实权威）
  Evidence ── Evidence→Event Link ── Canonical Event
          │                              ▲
          │ 未提炼 Evidence              │ 查询/发布/修订
          ▼                              │
  ┌──────────────────────────────────────┐
  │ Event Curation Module                │
  │ 清洗 → 原子语义 → Event candidate   │
  │      → 历史 Event 召回 → 同一事件判定 │
  │      → 规范化 → 审核 → 原子发布       │
  └───────────────┬──────────────────────┘
                  │ 只读补充召回
                  ▼
  Graphiti：已投影 Event + reviewed direct Anchor Links
                  ▲
                  │ Published Event 投影/修订
                  │
Reasoning Server / Graphiti Event Ingestion
  Event Grounding → Variable / Signal → Investment Reasoning
```

职责：

| 系统/模块 | 职责 |
| --- | --- |
| Data Service / PG | Evidence、Canonical Event、Evidence→Event Link 和发布事务的唯一权威 |
| Event Curation Module | 从 Evidence 形成候选、召回历史 Event、判定同一现实事件、提出新增/合并/修订决定 |
| Graphiti | 提供已投影 Event 的全文/语义图检索和已审核直接 Anchor 邻域；不决定 Event 合并 |
| Reasoning Server | 消费 Published Event，完成 Grounding 和后续投研推理；不读取 Evidence 正文 |
| Artifact/Audit Store | 保存模型、Prompt、规则版本、候选召回、审核决定和重放信息 |

关键原则：

1. Evidence 留存在 Data/PG，不写入 Graphiti；
2. Event 在 PG 原子发布成功前，禁止写入 Graphiti；
3. PG 中的 Event 集合是历史 Event 查重的保底来源，不能只查 Graphiti；
4. Graphiti 投影延迟或 Anchor 漏配不能导致系统重复创建 Event；
5. Graphiti 的候选召回结果只是证据之一，LLM 不能仅凭相似度自动合并 Event。

### 1.1 Evidence 图谱边界

[ADR-0007](../adr/0007-project-only-events-through-native-graphiti-episodes.md) 已确定 Evidence
Episode API 和写入链路退役：Evidence 留在 Data/PG，只有 Data 发布后的正式 Event 进入
Graphiti。历史 Evidence Episode、SQLite 状态和图数据不在本次变更中删除；任何清理仍需
用户单独授权。

## 2. 输入、输出与调用合同

### 2.1 Evidence 逻辑输入

以下是 Pipeline 所需逻辑字段，不在本设计中直接决定 Data 表结构：

```yaml
id: canonical Evidence ID
raw_evidence_id: source document ID | null
source_identity: provider / publisher / filing authority
source_type: filing | policy | news | flash | market_snapshot | research | other
title: string | null
content_or_fragment: immutable text or structured observation
canonical_url_or_locator: string
published_at: timestamp | null
ingested_at: timestamp
language: string | null
content_hash: string
version: string | null
source_grade: controlled value | null
metadata: source-owned scalar metadata
```

Evidence 记录“某来源在某时刻提供了什么”。已有结构化 5W1H、摘要或实体 mention 不会使它
自动成为 Event。

### 2.2 Event 发布输出

Event 必须遵循 Data 权威合同：

```yaml
id: Data-owned canonical Event ID
title: string
summary: string
semantic:
  actors: [string]              # non-empty
  action: string                # non-empty
  objects: [string]             # non-empty
  stage: OCCURRED | ANNOUNCED | EFFECTIVE | IMPLEMENTED | UPDATED | SUSPENDED | TERMINATED | EXPECTED
  jurisdictions: [string]       # may be empty
  effective_at: timestamp | null
  time_precision: INSTANT | DAY | MONTH | QUARTER | YEAR | UNKNOWN
modality: FACT | PLAN | SPEC
occurred_at: timestamp | null
announced_at: timestamp | null
status: ACTIVE | DEPRECATED | ARCHIVED
```

`actors/objects/jurisdictions` 是经事实审核的语义文本，不要求在此阶段产生 Graphiti canonical
Entity ID。`semantic` 同时承担 Event 身份判断，不再维护并行的 5W1H 和 `match_identity`。
Pipeline 可以临时解析这些 mention，查询规范 Anchor 用于历史 Event 召回，但不得把临时结果直接
发布成 Event→Anchor Link，也不得提前创建产业链间接影响。

### 2.3 Evidence→Event provenance Link

一个 Event 必须能回到至少一个合格 Evidence。一个 Evidence 可以拆出多个 Event；多个独立
Evidence 可以支持一个 Event。

```yaml
id: Data-owned Event Evidence Link ID
evidence_id: string
event_id: string
contribution_weight: number  # 0..1
```

Data 当前 Link 只保存 Event、Evidence 和贡献权重。来源独立性、冲突判断和本次提炼执行审计
属于 Curation 执行记录，不得假装成 Data 当前已经拥有的 Link 字段。相同
`(event_id, evidence_id)` 只能存在一次，已有权重不得被静默覆盖。

### 2.4 Pipeline 外部接口

Event Curation 应作为一个深模块对外提供小接口，隐藏向量库、Graphiti 查询、Prompt 和重试
细节：

```text
EventCurationModule.curate(
  evidence_ids,
  curation_as_of,
  policy_version
) -> CurationRunResult
```

`CurationRunResult` 至少返回每个原子语义单元的执行决定：

```yaml
decision: NO_EVENT | NEW_EVENT | SAME_EVENT | RELATED_BUT_DISTINCT | NEEDS_MORE_EVIDENCE | NEEDS_REVIEW
evidence_ids: [string]
matched_event_id: string | null
event_draft: object | null
provenance_drafts: [object]
material_change: boolean | null
conflicts: [object]
audit_ref: string
```

这些 decision 是工作流结果，不是 Event 类型或图谱节点。

## 3. 九道处理工序

### 3.1 Collect and Freeze Evidence

目标：冻结本次处理的不可变输入、时点和来源身份。

动作：

1. 由 Data 查询“未完成 Event Curation”的 Evidence IDs；
2. 读取原文/原子片段、source、发布时间、内容 hash 和版本；
3. 固定 `curation_as_of`，用于回放时的 point-in-time 过滤；
4. 验证 locator 可回到源材料；
5. 记录输入 ID/hash、规则、模型和 Prompt 版本。

这里的“冻结”不是复制测试数据，而是形成可重放的处理快照。若处理失败，Evidence 仍可按
同一输入版本重试。

### 3.2 Clean and Deduplicate Evidence

目标：去掉页面噪声和来源重复，不改变事实语义。

确定性动作：

- HTML/模板噪声处理；
- 编码、空白、时间格式和单位的无损归一；
- 相同 `content_hash`、canonical URL 和同源版本去重；
- 识别同一原公告的转载链和 `source_independence_group`。

LLM/语义辅助动作：

- 提议近重复或改写转载分组；
- 标记文本截断、表格错位和缺页；
- 不把转载数量当成多份独立证据。

本步骤只处理 Evidence 来源重复，不能替代第 5～6 步的历史 Event 身份判定。

### 3.3 Classify and Split Atomic Semantics

目标：把复合 Evidence 拆成可独立审核的最小语义单元，并标记：

- **OBSERVATION**：价格、库存、财务数字或可观察状态；
- **CLAIM**：主体主张、预测、政策表态或媒体引述；
- **OCCURRENCE_CANDIDATE**：已发生、正式宣布或可核验的现实变化候选；
- **CONTEXT_ONLY**：背景内容，不足以形成 Event。

原子 Evidence 无需为了形式再次拆分，但仍需打标。每个单元必须保留 locator；LLM 不得补写
原文没有的主体、时间、数字或因果。

`CONTEXT_ONLY` 直接得到 `NO_EVENT`。OBSERVATION 和 CLAIM 是否形成 Event 取决于现有 Event
业务规则，例如“主体正式发布计划”可以形成 PLAN Event；分析师个人预测不能冒充 FACT。

### 3.4 Form Current-Batch Event Candidates

目标：先在本批 Evidence 内聚合可能描述同一个现实发生的原子单元。

候选边界至少比较：

- 核心主体、动作和对象；
- 发生时间、宣布时间和地域/管辖范围；
- 数值、单位、文件编号和版本；
- modality：事实、计划还是推测；
- 来源是否独立；
- 是否存在直接矛盾。

仅主题相似不能合并。例如“出口许可证收紧”和“年度生产配额下调”即使都涉及稀土，也是
不同现实发生。

### 3.5 Retrieve Historical Event Candidates

目标：对每个本批 Event candidate 召回所有可能对应的历史 Canonical Events，优先保证召回率。

#### 3.5.1 检索表示

Pipeline 为候选 Event 和已发布 Event 生成确定性的匹配文本：

```text
modality | actors | action | objects | stage |
occurred/announced/effective time | jurisdictions | time precision
```

该文本及其 embedding 是检索派生字段，不改变 Event 原文和领域模型。生产环境可以在 Data
维护 `event_match_text` 和向量索引；首个 Demo 可在 PG 结构化缩小范围后，在内存中计算向量。

#### 3.5.2 三路混合召回

```text
historical_candidates =
    PG structured + temporal candidate events
  ∪ Graphiti reviewed direct-anchor neighboring events
  ∪ global Event semantic vector TopK
```

三路职责：

1. **PG 结构化/时间召回**：modality、主体/动作文本、发生或宣布时间窗口、ACTIVE 历史 Event；
2. **Graphiti Anchor 邻域召回**：只使用已经审核的直接 Anchor Link，例如 actor、target、
   jurisdiction/location、直接政策/产业链/节点/公司 Anchor；
3. **全局语义向量兜底**：防止新 Evidence 名称变化、Anchor 未识别或 Graphiti 投影延迟漏召回。

政策文号、公告编号、财报期等精确业务标识首版不进入 Agent OS 合同；待真实误判证明需要后，
再作为可选精确召回通道设计。

当前候选 Event 尚未入图，因此第 3 路召回先执行一次**只读的临时 Anchor Resolution**：用
候选身份语义中的 actors、objects、jurisdictions mention 对已预置的 canonical Entity/Anchor
做全文、向量候选和受控 LLM 匹配，
只接受已有 Anchor ID，再查询这些 Anchor 已关联的历史 Event。这个过程不创建 Entity、Link
或 Episode；临时匹配只写入 curation audit，待 Event 发布后由正式 Grounding Pipeline 重新
审核并建立 Event→Anchor Link。

禁止使用推导出来的“受影响产业链/节点”、Variable、Signal、Storyline 或下游投资结论判断
Event 身份。它们可能主题相同，但不能证明是同一现实发生。

“未过期 Event”不是统一规则。Event 是发生，不会简单过期。召回窗口应由 action/Event
category、发生时间、宣布时间、lifecycle 和精确标识共同决定：

- 重复发生的价格变动、制裁执行、会议或产量调整通常使用较短窗口；
- 同一政策文件、财报期或持续计划可以由精确标识跨越较长窗口；
- lifecycle 用于排除不可用版本，但不能替代现实发生时间。

`curation_as_of` 必须写入 Reasoning 执行审计，并限制本次可使用的 Evidence、Event 和图谱
快照。当前 Data Event 没有 `computed_known_at` 字段，因此第一版只能使用正式发布时间、
`occurred_at`、`announced_at` 和当前可见状态做近似时点过滤，不能宣称已经具备严格 PIT 回放。
若后续要求严格历史评估，必须先由 Data owner 设计并持久化可知时间合同。

#### 3.5.3 Graphiti 的现实能力边界

当前固定 Graphiti 版本的 Episode 查询主要提供全文/BM25，并可使用 reranker；它不是
“Episode content 的原生向量查重服务”。Graphiti 的 Entity/Fact 向量能力不能自动等价为
Event Episode 去重。

因此第一版不把 Event 语义向量检索绑定给 Graphiti：

- PG 是 Canonical Event 保底候选源；
- Graphiti 提供图邻域和补充全文召回；
- Event embedding 由 Event Curation 使用同一 embedding provider 计算，生产索引归 Data owner；
- Graphiti 未来如新增可验证的 Event 向量检索能力，可以替换内部适配器，不改变外部接口。

### 3.6 Resolve Same Real-World Occurrence

目标：由 LLM 综合候选语义，再由确定性门禁和人工审核判定是否为同一现实事件。

#### 3.6.1 判定标准

可以判为 `SAME_EVENT`：

- 核心主体、动作、对象和现实发生相同；
- 时间范围、文件/业务标识和 modality 相容；
- 差异主要来自报道措辞、来源、补充细节或后续确认；
- 新内容可以作为同一 Event 的 provenance 或事实修订表达。

通常必须判为独立 Event：

- 宣布政策与政策正式生效；
- 计划、批准、开工、投产和完成；
- 规则发布与一次具体执法；
- 同类动作在不同日期再次发生；
- 原事件与随后产生的市场价格反应；
- 同一主题下主体、对象、范围或 modality 实质不同。

这些 Event 后续可以进入同一 Storyline，但不能为了故事连续性被合并为一个 Event。

#### 3.6.2 LLM 输入与输出

LLM 只接收：

- 当前候选的原子语义、Event 身份语义草稿和 provenance locator；
- 经过 TopK 限制的历史 Event payload；
- 每个候选的召回路径、时间、直接 Anchor 和精确标识；
- 同一事件判定规则。

LLM 输出结构化建议：

```yaml
decision: SAME_EVENT | NEW_EVENT | RELATED_BUT_DISTINCT | NEEDS_REVIEW
matched_event_id: string | null
same_occurrence_reasons: [string]
material_differences: [string]
new_information: [string]
conflicts: [string]
confidence: number
```

确定性代码负责 schema、PIT、标识冲突、modality、时间和一对多异常门禁。首个 Demo 的
`SAME_EVENT`、冲突修订和“一候选匹配多个历史 Event”必须人工审核。

相似度不能直接等于合并阈值。它只控制送给 LLM/人工的候选范围。

### 3.7 Normalize Event Identity Semantic and Time

目标：根据第 6 步决定，生成新增 Event，或识别历史 Event 是否需要人工修订。

动作：

1. 形成无投资倾向的 title、summary，以及严格的 actors/action/objects/stage/jurisdictions
   身份语义；
2. 确定 `modality=FACT | PLAN | SPEC`；
3. 区分 `occurred_at`、`announced_at`、Evidence `published_at` 和 `ingested_at`；
4. 把本次 `curation_as_of` 和时间判断依据保存到 Reasoning 执行审计，不伪装成当前 Data
   Event 字段；
5. 对 SAME_EVENT 比较新 Evidence 是否造成实质身份语义变化；
6. 删除“利好、利空、上涨空间、推荐”等投资解释性措辞。

时间不确定时进入审核，LLM 不得猜测。公告时间不自动等于生效时间，摄入时间不自动等于
公众最早可知时间。

### 3.8 Verify and Review

目标：在发布前挑战 Event 身份、事实边界和增量更新决定。

审核问题：

1. 每个关键陈述是否能定位到 Evidence？
2. 是现实发生、正式计划、主体 Claim，还是分析者推测？
3. 是否把同主题但不同现实发生错误合并？
4. 是否因为 Graphiti Anchor 相同而过度合并？
5. 是否因为 Graphiti 投影延迟或 Anchor 漏配而错误新建？
6. 多个 Evidence 是否真的独立？
7. 新 Evidence 是仅补 provenance，还是实质修订 Event 身份语义？
8. 是否存在 CONTRADICTING Evidence 或历史 Event 重复？
9. known-at 是否会造成未来信息泄漏？
10. 是否错误产生 Variable、Signal、Storyline 或产业链影响？

首个真实 Demo 要求人工审核后发布。未来自动发布阈值必须根据真实运行评估另行批准。

### 3.9 Publish Atomically and Hand Off

根据决定执行：

| 决定 | PG 动作 | Graphiti 动作 |
| --- | --- | --- |
| NO_EVENT | 记录处理结果，不创建 Event | 无 |
| NEW_EVENT | 创建 Event + Evidence Links | 发布成功后投影新 Event |
| SAME_EVENT，无实质变化 | 无，直接忽略 | 无 |
| SAME_EVENT，有实质变化 | 当前无 Event 修订合同，进入人工审核 | 不写 |
| RELATED_BUT_DISTINCT | 创建新 Event，可在后续另建关系/Storyline | 投影新 Event；本 Pipeline 不建 Storyline |
| NEEDS_REVIEW | 进入审核队列，不发布 | 无 |

新增 Event 的 Data 事务必须完成：

1. 分配 canonical Event ID；
2. 写入 Event payload 和 status；
3. 写入所有 Evidence→Event Links；
4. 任一引用失败时整体回滚；
5. 返回正式 Event aggregate。

run、召回候选、规则/模型版本和判断摘要由 Reasoning 执行存储保存，不能假装与 Data Event
处于同一个 PostgreSQL 事务。

下游只接收：

```text
Event payload
Event ID
Event Evidence Link IDs
```

不得交付 Evidence 正文。Graphiti Event Ingestion 收到 Published Event 后才进行 canonical
Entity/Anchor Grounding。

## 4. LLM、确定性代码和人工职责

| 工作 | LLM | 确定性代码 | 人工审核 |
| --- | --- | --- | --- |
| hash/URL/版本去重 | 不负责 | 负责 | 不需要 |
| 近重复/转载识别 | 提议 | 保留分组依据 | 歧义时 |
| 原子语义分类/拆分 | 提议 | 校验 locator/schema | 首个 Demo 必须 |
| 历史 Event 召回 | 不单独负责 | 三路召回、PIT、TopK | 召回异常时 |
| 同一现实事件判定 | 给出结构化语义判断 | 执行硬门禁 | 首个 Demo 必须 |
| Event 身份语义草稿/差异摘要 | 提议 | 校验字段、时间、单位 | 首个 Demo 必须 |
| Event 新建/修订发布 | 不得执行 | 执行事务和幂等 | 首个 Demo 决定 |
| Variable/Signal/Storyline | 禁止 | 禁止 | 不属于本 Pipeline |

AgentContext 应提供完成当前决策所需的有限上下文，而不是把全图或所有历史 Event 填入
Prompt。推荐一轮召回、一轮同一事件判定、一轮事实规范化/自检；复杂冲突可以追加 reviewer
Agent，但每轮都输出结构化执行产物。

## 5. 内部模块结构

外部保持一个 `EventCurationModule`，内部可以按以下 seam 组织，而不是拆成微服务：

```text
EventCurationModule
├── EvidenceReader
├── EvidenceCleaner
├── AtomicSemanticExtractor
├── CurrentBatchCandidateBuilder
├── HistoricalEventRetriever
│   ├── ExactIdentifierRetriever
│   ├── PgStructuredRetriever
│   ├── GraphitiAnchorRetriever
│   └── EventSemanticRetriever
├── SameOccurrenceResolver
├── EventNormalizer
├── CurationReviewer
└── EventPublisher
```

适配器内部可以变化，但不得把 Graphiti Node/Edge、向量 provider DTO 或 LLM Prompt 泄漏到
Event Curation 的公共接口。

`HistoricalEventRetriever` 的合并结果需要携带：候选 Event ID、召回来源、rank/score、命中
标识、直接 Anchor role、时间窗口和索引版本。`SameOccurrenceResolver` 必须能在不写 Graphiti
的情况下完成决定。

## 6. 状态、幂等与并发

以下是执行状态，不是 Event lifecycle：

```text
RECEIVED
  → CLEANED
  → SPLIT
  → CANDIDATE_FORMED
  → HISTORY_RETRIEVED
  → RESOLVED
  → NORMALIZED
  → REVIEW_REQUIRED
  → PUBLISHED | NO_EVENT | REJECTED

任一步也可以进入 NEEDS_MORE_EVIDENCE 或 FAILED_RETRYABLE
```

规则：

- Evidence 永不因处理失败被覆盖或删除；
- `input hash + policy version + curation_as_of` 构成重放身份；
- 同一 Evidence 版本不能重复新增相同 provenance Link；
- 发布前重新召回 matched Event，避免排队期间重复创建；
- 第一版使用单活动 Resolver；多实例前必须增加共享协调，不能把请求指纹当成 Event 业务身份；
- 一个候选同时强匹配两个历史 Event 时，不自动选一个，进入 `NEEDS_REVIEW`；
- 来源撤回或内容修订不删除历史 Event；当前无版本合同，实质修订进入人工审核；
- Event 实质修订后，已生成的 Signal/推理结果必须进入失效或复核流程。

## 7. 发布门禁

Event 必须同时满足：

- 至少一个可审计 Evidence；
- `action` 非空且现实发生边界单一；
- modality 有原文依据；
- 关键主体、对象、数字、时间没有未披露冲突；
- occurred/announced/known-at 含义未混淆；
- 所有关键陈述有 locator；
- provenance 与 source independence group 完整；
- 历史 Event 三路召回已执行并可审计；
- SAME/NEW 决定通过门禁；
- 未包含 Signal、影响周期、Storyline 或投资结论；
- Event payload 通过 Data Schema；
- 发布事务和审计记录完整。

合法停止结果：`NO_EVENT`、`REJECTED`、`NEEDS_MORE_EVIDENCE`、`NEEDS_REVIEW`。冲突内容作为
`NEEDS_REVIEW` 的原因和 provenance 保留。停止不是失败，也不能为了提高 Event 产量强行发布。

## 8. 第一条真实 Demo

第一条 Demo 不预先制造“正确投资答案”，只验证 Pipeline 能否用真实 Evidence 建立并持续更新
一个边界清晰、可审计的 Event。

执行两轮：

### 第一轮：从真实 Evidence 创建 Event

1. 从现有未提炼 Evidence 选择一个含明确现实发生/正式宣布的记录；
2. 走完清洗、分类、候选构建和三路历史召回；
3. 在历史无相同 Event 时输出 `NEW_EVENT`；
4. 人工审核后由 Data owner 发布；
5. Reasoning Server 消费 Published Event 并投影 Graphiti；
6. Event Ingestion 建立 reviewed direct Event→Anchor Links。

### 第二轮：用后续真实 Evidence 验证增量合并

1. 选择另一来源对同一现实发生的补充报道；
2. 验证 PG 即使在 Graphiti 投影延迟时也能召回第一轮 Event；
3. 验证 Graphiti direct Anchor 和语义向量能提供补充候选；
4. 判断是仅增加 CORROBORATING provenance，还是实质修订 Event；
5. 无实质变化时不得重复投影或创建第二个 Event。

首个 Demo 不评价 Signal 方向、节点结论或后续市场走势。Event Curation 正确性的标准是事实
边界、同一现实事件识别、时间、provenance 和可重放性。

## 9. 测试与观测

### 9.1 必测场景

- 同 hash Evidence 不重复处理；
- 同源转载不计为独立 corroboration；
- 一条复合 Evidence 拆成多个候选；
- 多个独立 Evidence 支持同一 Event；
- Graphiti 投影延迟时仍由 PG 找到历史 Event；
- direct Anchor 漏配时由全局 Event 语义召回兜底；
- 相同宽泛 Anchor 不会把不同现实发生过度合并；
- 政策宣布与正式实施判为两个 Event；
- 同一 Event 的来源补充只新增 provenance；
- 同一 Event 的实质新信息进入 `SAME_EVENT_REVISION/NEEDS_REVIEW`，不覆盖历史 Event；
- 一个候选匹配两个历史 Event 时进入人工复核；
- 分析师预测不会自动发布为 FACT；
- `curation_as_of` 被保存且第一版 PIT 能力限制被明确暴露，不宣称严格回放；
- 发布失败不会留下无 provenance 的 Event；
- Reasoning handoff 不包含 Evidence 正文。

### 9.2 观测指标

- 各阶段输入、通过、拒绝、待审核数量；
- Evidence exact/near duplicate 比例；
- 一个 Evidence 拆分出的候选数；
- 三路召回各自的命中率和最终 SAME_EVENT 覆盖率；
- PG/Graphiti/向量候选集合的交并差异；
- NEW_EVENT、SAME_EVENT、RELATED、REVIEW 的比例；
- SAME_EVENT 中“仅 provenance”与“实质修订”的比例；
- LLM 模型/Prompt/token/延迟/结构化失败；
- 人工推翻了哪些匹配决定或 Event 身份语义字段；
- Event 发布到 Graphiti 可查询的端到端延迟。

## 10. 实现前的数据与接口核验

开始编码前必须由 Data owner 核对：

1. `raw_evidences`、`evidences`、`events`、Evidence→Event Link 的真实 Schema；
2. “未提炼 Evidence”的状态、锁定、重试和完成标记由哪个字段/服务维护；
3. Event create 已有内部事务 use case，但 revise/review 和外部 publish API 当前不存在；
4. Event canonical ID 由 Data 分配；当前没有 version，使用 `status` 表达生命周期；
5. 是否存在文号、披露 ID、财报期等 Event 精确业务标识；
6. Event 当前只能按现有结构化字段和时间查询，没有 `computed_known_at`；
7. Event matching vector 第一版采用内存评估还是 Data-owned pgvector 索引；
8. Graphiti Event 投影如何按正式 Event ID 幂等创建；当前不处理新版本；
9. 新 Data 写 API 应只向 Reasoning Server 返回 Event aggregate，不返回 Evidence 正文。

没有核对 Data owner 前，不在 `tidewise-reason` 创建替代 PG 表或生产直写脚本。

## 11. 实施顺序

本设计通过评审后，按以下顺序实施：

1. 按 ADR-0007 保持 Evidence 不进入 Graphiti；
2. 核对并冻结 Data Evidence/Event/Link 合同；
3. 实现只读 EvidenceReader 和三路 HistoricalEventRetriever；
4. 用真实 Evidence 离线输出候选和召回审计，不发布数据；
5. 实现 AtomicSemanticExtractor、SameOccurrenceResolver 和结构化评审产物；
6. 按[接收与落库实现设计](./event-candidate-resolution-ingestion.md)接通 Data 创建；
7. 接通 Published Event→Graphiti 的新增幂等投影；
8. 完成两轮真实 Demo，再评估自动发布阈值；
9. Event Curation 稳定后，才进入 Event→Variable/Signal Pipeline。

## 12. 待确认问题

1. 严格 PIT 回放是否需要新增 Data-owned 可知时间；当前第一版不依赖不存在的字段？
2. Event 修订未来采用同 ID 新版本、supersedes Link，还是新的 Event；当前统一转人工？
3. 是否需要扩展 Evidence→Event role；当前 Link 只有 `contribution_weight`？
4. Data 是否允许增加 Event matching 派生文本和 pgvector，还是先由独立检索索引承载？
5. 第一版可用的精确业务标识有哪些，按哪类 Event 配置匹配时间窗口？
6. 哪些来源等级和 modality 未来允许自动发布，哪些永久需要人工审核？
7. 已存在 Evidence Episode 暂时保留并由 `episode_kind=EVENT` 查询隔离；后续是否清理需单独决策？
