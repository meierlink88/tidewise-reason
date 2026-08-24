# Evidence→Event Curation Pipeline 设计

> 状态：Draft，进入实现前评审
>
> 版本：0.1.0
>
> 日期：2026-08-24
>
> 方法论上游：[事件驱动定性投研方法论 Spec](../specs/event-driven-investment-research-methodology.md)
>
> 下游设计：[事件驱动投研 Agent 真实推理 Demo](./event-driven-reasoning-demo-design.md)

## 0. 目的和冻结边界

本设计定义如何把已有 Evidence 清洗、拆分、核验并发布成下游唯一允许使用的 Event。
它解决的是“哪些来源材料足以形成哪些事实 Event”，不是“这个 Event 对投资意味着什么”。

冻结边界：

```text
Evidence Curation 可以产生
  Event + Evidence→Event provenance

Evidence Curation 不得产生
  Event Anchor Link
  Variable
  Signal / impact window
  Storyline route
  产业链传播
  投资结论
```

Event Curation 输出规范 5W1H 文本和时间。Event 进入 Graphiti 后，Graphiti Ingestion 才把
5W1H 中进入推理路径的 mention 匹配到规范 Anchor 并建立 reviewed Event Anchor Link。

Evidence、Event、Entity、Link、Variable、Signal、Storyline 仍是唯一顶层领域数据。本设计
中的清洗批次、候选、审核记录和运行状态都是执行产物，不是新的图谱事实类型。

## 1. 系统位置和权威边界

```text
Data Service / PostgreSQL
  raw_evidences / evidences
        │
        ▼
  Event Curation Pipeline
  清洗、去重、拆分、归一、核验、发布
        │
        ├── Evidence（不可变）
        ├── Event（事实权威）
        └── Evidence→Event Link（provenance 权威）
        │
        ▼ Published Event contract

Reasoning Server
  Graphiti Ingestion / Anchor Grounding
        │
        ▼
  Event Analysis / Investment Reasoning
```

职责：

| 系统 | 职责 |
| --- | --- |
| Data Service / PG | Evidence、Event、provenance 的读取、审核和事务发布 |
| Event Curation Pipeline | LLM 辅助清洗/拆分/归一，确定性校验和人工发布 |
| Reasoning Server | 只消费已发布 Event，不读取 Evidence 正文 |
| Graphiti | Event 入图、Anchor Grounding、下游时态语义关系和检索 |
| Artifact/Audit Store | 保存模型、Prompt、规则、输入 ID、审核决定和重放信息 |

Reasoning Server 不得为了 Demo 方便直接修改 Data PostgreSQL。生产 Event 发布能力由 Data
owner 提供；本仓库可以先实现只读合同、隔离评估夹具和发布产物校验器。

## 2. 输入与输出合同

### 2.1 Evidence 逻辑输入

以下是 Pipeline 所需的逻辑字段，不在本设计中直接决定 Data 表结构：

```yaml
id: canonical evidence ID
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

Evidence 记录“来源在某时刻提供了什么”。已有结构化摘要、实体 mention 或行情字段不会使其
自动成为 Event。

### 2.2 Event 发布输出

Event 必须遵循现有 Data 权威合同：

```yaml
id: Data-owned canonical Event ID
title: string
summary: string
semantic:
  who: string | null
  what: string
  when: string | null
  where: string | null
  why: string | null
  how: string | null
modality: FACT | PLAN | SPEC
occurred_at: timestamp | null
announced_at: timestamp | null
lifecycle: ACTIVE | DEPRECATED | ARCHIVED
computed_known_at: timestamp
provenance_audit_ref: string
```

`who/what/where` 是被事实审核过的语义文本，不要求在此阶段完成 Graphiti canonical Entity
ID。Pipeline 可以保留 mention 边界和原文 locator 供后续 grounding 审计，但不能提前创建
产业链间接影响。

### 2.3 Evidence→Event provenance Link

一个 Event 必须能回到至少一个合格 Evidence。一个 Evidence 可以拆出多个 Event；多个独立
Evidence 可以支持一个 Event。

Provenance Link 至少需要表达：

```yaml
evidence_id: string
event_id: string
role: PRIMARY | CORROBORATING | CONTEXT | CONTRADICTING
claim_locator: page / paragraph / field / timestamp | null
source_independence_group: string
known_at_basis: published_at / disclosed_at / received_at policy reference
curation_run_id: string
```

`role` 是 Link 属性或 Link type 的受控语义，不产生新的顶层类型。用于发布事实的 PRIMARY
和 CORROBORATING Evidence 必须保留；CONTRADICTING Evidence 不得被删除或隐瞒。

## 3. 七道处理工序

### 3.1 Collect and Freeze Evidence

目标：冻结本次处理的不可变输入和来源身份。

动作：

1. 读取 Evidence ID、原文/片段、source、发布时间和内容 hash；
2. 验证 locator 可回到源材料；
3. 固定 Evidence 版本，禁止清洗过程覆盖原文；
4. 记录本次 curation run 的输入 ID、hash、规则、模型和 Prompt 版本。

门禁：缺少不可变内容、来源身份或可审计 locator 时不得发布正式 Event。

### 3.2 Clean and Deduplicate

目标：去掉页面噪声和重复传播，但不改变事实语义。

确定性动作：

- HTML/模板噪声处理；
- 编码、空白、时间格式和单位的无损归一；
- 相同内容 hash 去重；
- canonical URL、转载链和 source independence group 校验。

语义辅助动作：

- 近重复和改写转载候选；
- 同一原始公告被多家媒体转述的聚类候选；
- 文本截断、表格错位和缺页提示。

转载数量不得冒充独立证据数量。重复 Evidence 仍可保留来源记录，但不能重复提高 Event
可信度。

### 3.3 Split Observations, Claims and Occurrences

目标：把复合 Evidence 拆成可独立审核的最小语义单元。

至少区分：

- **Observation**：来源观察到的指标、库存、价格、财务数字或状态；
- **Claim**：可识别主体提出的主张、指引、预测、政策表态或媒体引述；
- **Occurrence candidate**：已经发生、正式宣布或可核验的现实变化；
- **Context only**：背景知识，不足以单独形成 Event。

示例：一篇新闻同时写“配额下降、进口收缩、价格上涨、分析师预计继续上涨”，必须拆成
多个单元；不得直接发布为一个“稀土全面利好”Event。

LLM 可以提出拆分边界和类型候选，但每个单元必须保留原文 locator，不得补写原文没有的
数字、主体、时间或因果关系。

### 3.4 Form Event Candidates

目标：判断哪些单元描述同一个现实发生，并形成候选 Event 边界。

关系不是一一对应：

```text
一个复合 Evidence → 多个 Event candidate
多个独立 Evidence → 一个 Event candidate
一个未确认 Claim → 零个正式 Event
```

候选合并至少比较：

- 核心发生或宣布动作；
- 主体与客体文本；
- 发生/宣布时间；
- 地域和政策范围；
- 数值、单位和版本；
- 来源是否独立；
- 是否存在直接矛盾。

仅主题相似不能合并。例如“出口许可证收紧”和“年度生产配额下调”即使都涉及稀土，也应是
两个 Event。

### 3.5 Normalize Event 5W1H and Time

目标：把候选发布成统一、无投资倾向的事实表达。

动作：

1. 形成 title、summary 和严格 5W1H；
2. 确定 `modality=FACT | PLAN | SPEC`；
3. 区分 `occurred_at`、`announced_at`、Evidence `published_at` 和 `ingested_at`；
4. 依据版本化 PIT 规则计算 `computed_known_at`，保存计算依据；
5. 初始化 Event lifecycle；
6. 删除“利好、利空、上涨空间、推荐”等投资解释性措辞。

时间不得互相替代：公告发布时间不自动等于现实生效时间；系统摄入时间不自动等于公众最早
可知时间。时间不确定时保存不确定性并进入审核，不得由 LLM 猜测。

财报文件本身不是一个完整经营 Event。“公司发布财报”可以是 Event；具体数字仍是
Observation；跨期指标发生实质变化时，可以按规则形成独立 State Change Event。

### 3.6 Verify and Review

目标：在发布前挑战候选 Event 的事实边界。

审核问题：

1. Event 的每个关键陈述是否能定位到 Evidence？
2. 是真实发生、正式计划、主体 Claim，还是分析者推测？
3. 一条复合材料是否仍混入多个独立发生？
4. 多个 Evidence 是否真的独立，而不是同源转载？
5. 数字、单位、主体、时间和范围是否一致？
6. 是否存在 CONTRADICTING Evidence？
7. 5W1H 是否加入 Evidence 不支持的因果或投资判断？
8. known-at 是否会导致未来信息泄漏？
9. 是否错误生成 Variable、Signal、Storyline 或产业链影响？

第一条真实 Demo 要求人工审核后发布。后续自动发布阈值必须基于真实运行数据另行评审，
不能在本设计中先假定 LLM 置信度足以替代事实审核。

### 3.7 Publish Atomically and Hand Off

目标：事务性发布 Event 与 provenance，并向下游交付最小合同。

同一发布事务必须完成：

1. 分配或确认 Data canonical Event ID；
2. 写入 Event payload 和 lifecycle；
3. 写入所有 Evidence→Event provenance Links；
4. 写入 curation run、规则/模型版本和审核决定；
5. 生成 `provenance_audit_ref`；
6. 产生可幂等消费的 Published Event 通知或读取版本。

交给 Reasoning Server 的内容只有：

```text
Event payload
Event ID
computed_known_at
provenance_audit_ref
Event version / content hash
```

不得交付 Evidence 正文、摘要或片段。Graphiti Ingestion 根据 Published Event 5W1H 开始
Anchor Grounding。

## 4. LLM、确定性代码和人工职责

| 工作 | LLM | 确定性代码 | 人工审核 |
| --- | --- | --- | --- |
| 页面噪声清理候选 | 可以 | 必须保证原文/hash 不变 | 异常时 |
| 精确 hash/URL 去重 | 不负责 | 负责 | 不需要 |
| 近重复/转载候选 | 提议 | 保存分组依据 | 歧义时 |
| Claim/Observation/Occurrence 拆分 | 提议 | 校验 locator/Schema | 首个 Demo 必须 |
| 5W1H 草稿 | 提议 | 校验字段、时间、长度 | 首个 Demo 必须 |
| 时间和单位 | 不得猜测 | 解析、规范和 PIT 校验 | 冲突时 |
| 是否发布 Event | 不得单独决定 | 执行门禁 | 首个 Demo 决定 |
| Variable/Signal/Storyline | 禁止 | 禁止 | 不属于本 Pipeline |

LLM 输出始终是候选。Prompt 中的置信度不能代替 provenance、来源独立性、时间和人工审核。

## 5. 工作流状态和失败处理

以下是执行状态，不是 Event domain lifecycle：

```text
RECEIVED
  → CLEANED
  → SPLIT
  → NORMALIZED
  → REVIEW_REQUIRED
  → PUBLISHED | REJECTED

任一步也可以进入 NEEDS_MORE_EVIDENCE 或 FAILED_RETRYABLE
```

规则：

- Evidence 永不因清洗失败被覆盖或删除；
- 重试必须使用 input hash + curation policy version 保证幂等；
- 新 Evidence 可以支持现有 Event、触发 Event 修订或形成新 Event；
- 来源撤回或关键内容修订时，不删除历史 Event，按 Data lifecycle 规则修订或失效，并保留
  原 provenance；
- 下游已经生成 Signal 时，Event 修订必须触发 Graphiti 投影和受影响分析失效/复核。

## 6. 发布门禁

Event 必须同时满足：

- 至少一个可审计 Evidence；
- `what` 非空且边界单一；
- modality 有依据；
- 关键主体、对象、数字、时间没有未披露冲突；
- occurred/announced/known-at 的含义未混淆；
- 所有关键陈述有 claim locator；
- provenance Link 与 source independence group 完整；
- 未包含 Signal、影响周期、Storyline 或投资结论；
- Event payload 通过 Data Schema；
- 发布事务和审计记录完整。

以下结果是合法停止：

- `REJECTED`：不是独立 Event、属于观点或无法核验；
- `NEEDS_MORE_EVIDENCE`：事实边界可能成立，但当前来源不足；
- `CONTEXT_ONLY`：可保留为 Evidence 背景，不发布 Event；
- `CONFLICTED`：来源对关键事实直接矛盾，等待审核，不强行合并。

## 7. 第一条真实纵向 Demo

第一条 Demo 不准备标准答案，只验证 Pipeline 能否从现有真实 Evidence 发布一个边界清晰、
可审计的 Event。

执行顺序：

1. 从现有 `evidences` 中选择一个含有明确现实发生或正式宣布的候选；
2. 读取其 raw source、发布时间、内容 hash 和 source identity；
3. 执行清洗、去重和复合语义拆分；
4. 形成一个或多个 Event candidates；
5. 人工审核 5W1H、modality、时间和 provenance；
6. 由 Data owner 发布或生成隔离的待发布合同；
7. Reasoning Server 只读取 Published Event payload；
8. Graphiti Ingestion 建立 Episode 和 reviewed Event Anchor Links；
9. 再开始 Variable/Direct Signal Pipeline。

首个 Demo 验收只看：

- 是否正确拆分复合 Evidence；
- Event 是否忠实于来源而没有投资解释；
- 时间和来源是否可审计；
- 下游是否完全不读取 Evidence 内容；
- Graphiti 是否能基于 Event 5W1H 找到规范直接 Anchor。

不以 Signal 方向、节点结论或市场后来走势评价 Event Curation 正确性。

## 8. 实现接口边界

Event Curation 的逻辑端口：

```text
EvidenceReader
  读取不可变 Evidence 与 source metadata

EvidenceCleaner
  产生清洗文本和重复候选，不覆盖 Evidence

EvidenceSplitter
  产生带 locator 的 Observation / Claim / Occurrence candidates

EventNormalizer
  产生 Event 5W1H、modality 和时间候选

CurationReviewer
  执行门禁并记录审核决定

EventPublisher
  事务性发布 Event + provenance + audit reference
```

这些是接口职责，不要求成为六个微服务。第一版应在 Data owning application 内形成一条可
重试 Pipeline；Reasoning Server 只需要 `PublishedEventReader` 和 Event contract validator。

实现前必须先在 Data owner 中核对：

1. `raw_evidences`、`evidences`、`events` 和 provenance 的真实字段与约束；
2. 是否已有 Event create/review/publish API 或事务 service；
3. Evidence 内容、source metadata 和版本如何读取；
4. Event canonical ID 和 lifecycle 由谁生成；
5. 撤回、修订和重复 Event 的现有规则；
6. 当前 API 是否能只返回 Event payload 和 audit reference，而不泄露 Evidence 内容。

没有核对 Data owner 前，不在 `tidewise-reason` 内创建替代 PG 表或直写脚本。

## 9. 测试与观测

首轮需要的测试 seam：

- 同 hash Evidence 不重复形成 Event；
- 同源转载不计为独立 corroboration；
- 一条复合 Evidence 能拆成多个候选；
- 多个独立 Evidence 能支持一个 Event；
- 分析师预测不会自动发布为 FACT Event；
- `published_at` 不会覆盖 `occurred_at`；
- Event 每个关键陈述能回到 locator；
- 发布事务失败不会留下无 provenance 的 Event；
- Reasoning handoff 不包含 Evidence 内容；
- 重试不会重复发布同一个版本。

运行观测至少记录：

- 各阶段输入、通过、拒绝和待审核数量；
- exact/near duplicate 比例；
- 一个 Evidence 拆分出的候选数；
- 一个 Event 的独立来源数；
- LLM 模型、Prompt、token、延迟和失败；
- 人工修改了哪些 5W1H 或时间字段；
- 发布到 Graphiti 可查询的端到端延迟。

## 10. 当前缺口与下一步

当前设计依据记录：PostgreSQL 已有 `raw_evidences` 和 `evidences`，Event 表和 Evidence Link
合同存在，但尚无正式 Event 数据；Event authoring/publish API、实体 Link 和完整审核工作流
仍需在 Data owner 核实。

下一步只做设计核验，不立即写数据：

1. 在 Data 仓库核对 Evidence/Event/provenance 实际 Schema 和 service；
2. 用一个真实 Evidence 手工走完七阶段，验证逻辑字段是否足够；
3. 固定第一版 Published Event contract 和审核门禁；
4. 决定第一版由 Data CLI、内部 API 还是审核 UI 发布；
5. 再拆实现任务，不在 Reasoning Server 中绕过 Data owner。

## 11. 待确认问题

1. `computed_known_at` 使用公众最早可知时间还是本系统实际摄入时间，二者如何同时保留？
2. PRIMARY、CORROBORATING、CONTRADICTING provenance 是 Link type 还是 Link role？
3. 哪些 source grade 和 Event modality 可以在未来自动发布，哪些必须人工审核？
4. Event 修订是同 ID 新版本、supersedes Link，还是 lifecycle 更新？
5. 行情 Observation 派生 State Change Event 的第一版确定性阈值由谁维护？
6. Data 当前是否已有可复用的 review queue 和操作审计模型？
