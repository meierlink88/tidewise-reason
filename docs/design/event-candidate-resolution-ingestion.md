# Event Candidate 接收、去重与发布设计

- Status: Implemented
- Version: 1.0.0
- Date: 2026-08-25
- Scope: Reasoning Server 接收 Agent OS 已提炼的 Event Candidate，完成历史 Event 判定、Data
  Service 发布，以及 Graphiti Event 投影；重复 Event 直接忽略
- Upstream: Agent OS Evidence→Event 提炼工序（本设计暂不实现）
- Methodology: [Evidence→Event Curation Pipeline](./evidence-to-event-curation-pipeline.md)

## 1. 结论

Reasoning Server 应提供一个异步的 **Event Candidate Resolution** 深模块。Agent OS 只提交一条
原子 Event Candidate 和至少一个已经由 Data Service 发布的 `evidence_id`。Event 的 `semantic`
直接表达用于判断 Event 身份的结构化语义。Reasoning Server 隐藏 Graphiti 检索、规则、LLM 比较、Data 调用、重试
和投影细节。

处理结果有两条主要路径：

1. **命中历史 Event**：返回已匹配 Event ID 后结束；不新建 Event、不追加 Evidence Link、
   不写 Graphiti。
2. **形成新 Event**：先由 Data Service 在同一 PostgreSQL 事务中创建 Event 与
   `event_evidence_links`，取得正式 `EVT...` ID；随后 Reasoning Server 把该正式 Event 异步、
   幂等投影到 Graphiti。

Data Service 始终是 Event 与 Evidence Link 的唯一权威。Graphiti 是历史候选召回和推理图谱，
不能先于 Data 创建 Event，也不能分配 Event ID。

## 2. 本期边界

### 2.1 本期负责

- 接收和冻结 Agent OS 传来的 Event Candidate；
- 校验 Evidence ID、Event 原子性、时间和 Data Event 合同；
- 从 Graphiti 召回历史 Event，并用 Data 只读结果弥补投影延迟；
- 基于统一规则与 LLM 语义判断 Event 是否重复；
- 对新 Event 调用 Data Service 创建 Event 与 Evidence Link；
- 对重复 Event 直接忽略，不产生任何外部写入；
- 获取正式 Event ID 后投影 Graphiti；
- 持久化执行状态、判定摘要、重试状态和跨系统关联 ID。

### 2.2 本期不负责

- Agent OS 如何从 Evidence 提炼 Event Candidate；
- Variable、Signal、影响周期、Storyline 和投研结论；
- 自动修改历史 Event 核心事实；
- 自动创建 Graphiti 中不存在的 Entity；
- 从 Event 自由抽取并持久化任意 Fact；
- 把 Evidence 正文再次写入 Graphiti。

`EventCandidate` 和执行状态都是工作流 DTO，不是新的投研领域对象，也不在
Graphiti 中创建同名节点。

## 3. 系统职责

| 系统 | 职责 |
| --- | --- |
| Agent OS | 以后负责 Evidence→Event 提炼；提交单一现实动作的 Candidate 和对应 Evidence IDs |
| Reasoning Server | 候选接收、历史召回、同一事件判断、发布编排、Graphiti 投影与执行审计 |
| Data Service | Event、Atomic Evidence、`event_evidence_links` 的唯一权威；分配正式 ID并保证事务 |
| Graphiti | 已发布 Event 的历史候选召回、标准 Entity 邻域和下游推理图谱 |

Reasoning Server 不直接写 Data PostgreSQL。Data Service 不负责语义去重；它只执行 Reasoning
Server 已做出的 `CREATE_NEW` 决定并校验领域约束。

## 4. 对外 API

### 4.1 接收 Candidate

```http
POST /api/reason/v1/event-candidates
Authorization: Bearer <agent-os-service-token>
Content-Type: application/json
```

推荐返回 `202 Accepted`。历史检索、LLM 比较和跨服务发布可能耗时，且需要持久化重试；异步
接口可以先可靠接纳输入。它是 Event Candidate 资源，不使用 `/jobs` 命名。

```json
{
  "event": {
    "title": "美国扩大对华 HBM 出口限制",
    "summary": "美国政府宣布扩大对中国高带宽内存产品的出口限制。",
    "semantic": {
      "actors": ["美国政府"],
      "action": "扩大出口限制",
      "objects": ["HBM"],
      "stage": "ANNOUNCED",
      "jurisdictions": ["中国"],
      "effective_at": null,
      "time_precision": "DAY"
    },
    "modality": "FACT",
    "occurred_at": "2026-08-25T00:00:00Z",
    "announced_at": "2026-08-25T00:00:00Z"
  },
  "evidence_ids": [
    "EVD00000000-0000-0000-0000-000000000000"
  ]
}
```

可靠接纳后返回：

```json
{
  "submission_id": "evt-submission-00000000-0000-0000-0000-000000000000",
  "status": "ACCEPTED",
  "status_url": "/api/reason/v1/event-candidates/evt-submission-00000000-0000-0000-0000-000000000000",
  "replayed": false
}
```

硬性约束：

- Agent OS 不提交 Candidate ID。Reasoning 在可靠接纳后生成内部 `submission_id`；
- Agent OS 不提交 `curation_as_of`。Reasoning 以服务端 `accepted_at` 作为本次在线处理时点；
- Reasoning 对“规范化 Event payload + 排序后的 Evidence IDs”计算请求指纹。完全相同的重试
  返回原 `submission_id`；新增 Evidence 或 Event 内容变化会形成新提交并重新判定；
- `evidence_ids` 至少一项，每项必须是 Data Service 已存在的正式 `EVD...` ID，且不得重复；
- `event.semantic` 直接采用 Event 身份语义，不再重复提交 5W1H 和 `match_identity` 两套结构；
- `actors`、`action`、`objects`、`stage` 必填；`actors/objects` 至少一项，字符串不能为空；
- `jurisdictions` 允许空数组，`effective_at` 允许 `null`；
- `stage` 为受控值 `OCCURRED | ANNOUNCED | EFFECTIVE | IMPLEMENTED | UPDATED | SUSPENDED |
  TERMINATED | EXPECTED`；
- `time_precision` 为受控值 `INSTANT | DAY | MONTH | QUARTER | YEAR | UNKNOWN`；
- `event` 只能描述一次现实动作，不能把多步因果链或多次政策阶段合在一条 Event 中；
- `status` 不由 Agent OS 提交，新 Event 由 Data Service 固定创建为 `ACTIVE`；
- 时间统一使用带时区 ISO-8601，服务内部规范化为 UTC。

`business_identifiers` 原本用于政策文号、交易所公告编号、监管案件号或财报期等精确匹配。
它能降低跨来源同一 Event 的误判，但不是每类 Event 都有。第一版从 Agent OS 合同中移除，
后续有真实误判证据时再单独设计，不阻塞当前流程。

### 4.2 查询处理结果

```http
GET /api/reason/v1/event-candidates/{submission_id}
Authorization: Bearer <agent-os-service-token>
```

```json
{
  "submission_id": "evt-submission-00000000-0000-0000-0000-000000000000",
  "status": "SUCCEEDED",
  "decision": "NEW_EVENT",
  "event_id": "EVT00000000-0000-0000-0000-000000000000",
  "event_created": true,
  "evidence_link_result": "CREATED",
  "graph_projection_status": "SUCCEEDED",
  "decision_summary": {
    "reason_codes": ["NO_SAME_OCCURRENCE_FOUND"],
    "matched_event_ids": []
  },
  "accepted_at": "2026-08-25T12:00:01Z",
  "completed_at": "2026-08-25T12:00:07Z"
}
```

API 不返回模型的隐藏思维链，只返回可审计的提交 ID、结构化判断项和简短理由。

### 4.3 状态与决定

执行状态：

```text
ACCEPTED → RESOLVING → SUCCEEDED                         # SAME_EVENT，直接忽略
                     └→ PUBLISHING → PROJECTING → SUCCEEDED
                     └→ NEEDS_REVIEW
                     └→ FAILED_RETRYING | FAILED
```

业务决定：

| decision | 含义 | Data 动作 | Graphiti 动作 |
| --- | --- | --- | --- |
| `SAME_EVENT` | 同一次现实动作 | 无，直接忽略 | 无 |
| `NEW_EVENT` | 新现实动作 | 创建 Event + Evidence Links | 投影新 Event |
| `RELATED_BUT_DISTINCT` | 主题相关但动作/阶段/时点不同 | 与 `NEW_EVENT` 相同 | 投影新 Event |
| `NEEDS_REVIEW` | 证据不足或候选冲突 | 不写 | 不写 |
| `SAME_EVENT_REVISION` | 同一动作但核心事实需修订 | 本期不自动执行，转人工 | 不写 |

当前 Data Event 没有版本字段和外部修订合同，因此第一版不能把 `SAME_EVENT_REVISION` 静默
处理成覆盖旧 Event 或创建“v2”。

### 4.4 OpenAPI 与 Swagger

本项目已经使用 FastAPI，框架默认生成：

```text
GET /openapi.json  # OpenAPI 3 合同
GET /docs          # Swagger UI
GET /redoc         # ReDoc
```

因此不引入第二套 Swagger 框架或手写一份容易漂移的 OpenAPI YAML。Pydantic 请求/响应模型、
FastAPI route、受控 enum、错误响应和 Bearer security scheme 是运行时合同源。

实施使用 Pydantic 请求/响应模型、稳定 `operation_id` 和 FastAPI route 作为唯一
运行时合同源。按当前决定不额外提交手写 OpenAPI 或生成快照，避免两份合同漂移。

## 5. 去重原则与流程

### 5.1 唯一身份原则

两个 Event 只有在描述**同一个主体、同一次现实动作、同一个直接作用对象、同一个事件阶段和
同一个发生时点/业务对象**时，才是同一 Event。措辞、来源和补充细节不同不改变 Event 身份。

判断辅助问题：如果把两个描述合并，会不会丢掉一个可以独立定位时间的现实动作？会丢掉，
就是两个 Event；不会丢掉，才可能是同一 Event 或同一 Event 的补充。

例如“宣布限制”“限制正式生效”“扩大限制范围”“撤销限制”是不同阶段或动作，即使主体和
对象相同也不能去重。

### 5.2 候选召回

召回用于减少 LLM 比较范围，不直接决定合并：

1. 根据 `occurred_at/announced_at`、modality 和动作类型计算业务时间窗口；
2. 使用 Graphiti Event Episode 全文/BM25 查询标题、摘要和规范化 Event 身份语义；
3. 若 Candidate 的 mention 能只读匹配到现有标准 Anchor，补充查询这些 Anchor 邻接的历史
   Event；此步骤不得创建 Entity 或 Link；
4. 使用 Data Service 现有 Event 读取接口按时间窗口补召回，覆盖“Data 已成功、Graphiti 尚未
   投影”的窗口；
5. 合并、按正式 Event ID 去重并截断候选集，再进入逐对判断。

Graphiti 0.29.3 没有 Episode 原生向量字段，因此第一版不假设“Event Episode 已自动向量化”。
全文、结构化时间和图邻域足以完成首版召回。若后续增加 Event 向量索引，它仍只是召回通道，
不能代替同一现实动作判断。

### 5.3 候选判定

每一对 Candidate 与历史 Event 先经过确定性否决，再交给 LLM：

1. 主体是否相同或可规范化为同一主体；
2. 动作是否为同一次动作，而不是同主题的另一次动作；
3. 直接对象是否相同；
4. 阶段是否相同；
5. 时间是否指向同一次发生；
6. 已知业务标识是否冲突；
7. 是否存在无法安全合并的核心事实冲突。

LLM 必须输出受控 JSON：

```json
{
  "decision": "SAME_EVENT",
  "same_actor": true,
  "same_action": true,
  "same_object": true,
  "same_stage": true,
  "same_occurrence_time": true,
  "material_conflicts": [],
  "reason_codes": ["SAME_REAL_WORLD_OCCURRENCE"],
  "summary": "不同来源描述同一次宣布动作。"
}
```

任一核心项无法确定、候选之间形成矛盾票决，或 LLM 输出不符合合同，结果均为
`NEEDS_REVIEW`，不能通过降低相似度阈值强行自动发布。

### 5.4 并发保护

第一版保持一个活动 Resolver Worker，并在最终 Data 写入前重新召回一次候选，防止排队期间
已有 Event 被创建。请求指纹只能防止完全相同的请求重放，不能阻止两个不同 Candidate 并发
描述同一现实事件。

如果以后部署多个 Resolver 实例，必须先引入共享协调锁或 Data 侧的 Event identity reservation；
仅靠 Graphiti 查询无法提供跨实例唯一性保证。

## 6. Data Service 必须补充的合同

当前 Data Service 只有 Event 读取 API；虽然内部 `event.UseCase.Create` 已能事务创建 Event、
Evidence Link、Actor Link 和 Asset Link，但没有开放外部 Event 写入。因此实施前需要先在
Data Context/ADR 中确认以下最小写合同。

### 6.1 创建新 Event

```http
POST /api/data/v1/events
Authorization: Bearer <reason-service-token>
X-Request-ID: <trace-id>
```

请求只包含目标 Data Event 合同字段；其中新的 `semantic` 结构须先完成 Data Schema 迁移：

```json
{
  "publication_key": "evt-submission-00000000-0000-0000-0000-000000000000:create",
  "event": {
    "title": "...",
    "summary": "...",
    "semantic": {
      "actors": ["美国政府"],
      "action": "扩大出口限制",
      "objects": ["HBM"],
      "stage": "ANNOUNCED",
      "jurisdictions": ["中国"],
      "effective_at": null,
      "time_precision": "DAY"
    },
    "modality": "FACT",
    "occurred_at": "2026-08-25T00:00:00Z",
    "announced_at": "2026-08-25T00:00:00Z"
  },
  "evidence_ids": [
    "EVD..."
  ]
}
```

Data 必须：

- 校验全部 Evidence ID 已存在；
- 分配正式 Event ID 和 Event Evidence Link ID；
- 在一个 PostgreSQL 事务内创建 Event 和全部 Evidence Links，第一版内部统一写
  `contribution_weight=1.0`；
- 任一 Evidence 无效时整体失败；
- 返回创建后的 Event aggregate，至少包含正式 Event ID 和 Evidence Link IDs。

### 6.2 安全重试

Reasoning 与 Data 之间没有分布式事务。Data 写成功但响应丢失时，Reasoning 必须能够使用同一
请求身份重试并取回同一个 Event ID，否则可能创建重复 Event。

这里需要的是**传输幂等身份**，不是已退役的 Event Dedupe Key，也不把语义去重责任转移给
Data。建议 Event 创建接口使用请求体中的 `publication_key`，其值由 Reasoning 从内部
`submission_id` 确定性派生；Data 原子保存该调用身份和结果。`X-Request-ID` 只用于链路追踪，
不能承担幂等语义。“同一 publication key + 同一 payload 返回同一结果、同一 key + 不同
payload 返回 409”是实现前的硬性验收条件。该能力会重新引入最小发布记录，需要 Data ADR
明确它只负责安全重放，不是 Event 业务身份，也不负责语义去重。

## 7. Graphiti 投影

只有 Data 返回正式 Event ID 后，才创建 Event Episode：

```text
episode_kind      = EVENT
domain_object_id  = EVT...
name              = EVT...
source            = EpisodeType.json
source_description= Published canonical Event from Data Service
content           = Data 返回 Event 的规范 JSON
group_id           = neo4j
```

投影规则：

- Episode UUID 从正式 Event ID 确定性派生；同一 Event 重试不得创建第二个 Episode；
- Graphiti 内容只来自 Data 返回的正式 Event，不以 Agent OS Candidate 作为权威快照；
- 使用 Graphiti 标准 `add_episode()` 完成实体抽取、解析、上下文实体创建、Fact 抽取、去重与
  时态失效；LLM 创建的上下文 Entity 不得获得权威 `data_object_id`；
- Event 身份语义随 Data 正式 Event 一起投影，不维护第二份 `match_identity`；
- 原生 Fact 只表达 Event 直接支持的事实，不得把 Variable、Signal、Storyline、投资影响或
  预测写成 Event Fact；这些内容由后续 Event Analysis 和 Storyline Reasoning 负责；
- Graphiti 失败不回滚 Data Event。Reasoning 持续重试投影，并把状态暴露为
  `FAILED_RETRYING`；Data 中的 Event 仍然有效。

命中 `SAME_EVENT` 时不新增 Event Episode，也不更新 Data 或 Graphiti；本次 Candidate 仅在
Reasoning 执行记录中保留判定结果。

## 8. Reasoning Server 模块结构

遵循现有 `ingestion/episcode/` 结构，建议新增：

```text
ingestion/episcode/event/
  api.py                 # POST/GET HTTP 适配，不含去重规则
  contracts.py           # Agent OS DTO、状态 DTO
  module.py              # EventCandidateModule 深接口与状态编排
  store.py               # Candidate、payload hash、决定、Data/Graph 状态
  worker.py              # 单活动 Resolver Worker、lease、retry
  resolution/
    retriever.py         # Graphiti + Data 历史候选召回
    policy.py            # 确定性身份规则与决策聚合
    comparator.py        # LLM 受控比较
  data/
    client.py            # Data Event create 适配器
    contracts.py         # Data wire DTO，不复用 Agent OS DTO
  graphiti/
    projector.py         # 正式 Event 的 Graphiti 原生 Episode 投影
    retriever.py         # Event Episode 全文/邻域查询
```

模块对外只暴露：

```python
EventCandidateModule.accept(candidate) -> Acceptance
EventCandidateModule.get(submission_id) -> ResolutionStatus
```

API、Graphiti、Data Client 和 LLM 不互相直接调用，所有流程都由 `module.py` 编排。这样后续
Agent OS 提炼方式变化时，只要继续满足 Candidate 合同，就不影响去重和发布内部实现。

## 9. 一致性与失败处理

| 失败位置 | 系统行为 |
| --- | --- |
| 请求校验失败 | 不接纳，返回 400/422 |
| 完全相同 payload 重试 | 根据请求指纹返回原 `submission_id`，不重复执行 |
| Graphiti 召回失败 | Data 时间窗口召回可降级；两路均不可用则重试，不盲目发布 |
| LLM 超时/非法输出 | 有界重试，随后 `NEEDS_REVIEW` |
| Data 4xx | `FAILED` 或 `NEEDS_REVIEW`，不写 Graphiti |
| Data 超时/5xx | 使用同一传输幂等身份重试，不能换请求身份 |
| Data 成功、Reason 崩溃 | 重放同一 Data 请求，恢复同一 Event ID |
| Graphiti 投影失败 | Data 不回滚，持久化 Event ID 后持续重试 |
| Graphiti 已存在同 ID 同内容 | 幂等成功 |
| Graphiti 已存在同 ID 不同内容 | 停止覆盖并进入人工检查 |

Reasoning 本地 Store 至少持久化：`submission_id`、Candidate 原文、规范请求指纹、`accepted_at`、状态、候选 Event IDs、
结构化决定摘要、正式 Event ID、Data 请求身份、Graphiti 投影状态、attempt 和 lease。第一版沿用
单实例 SQLite 可以成立；多副本前必须迁移到共享持久化与共享协调机制。

## 10. 验收场景

1. 新 Candidate 携带一个有效 Evidence，Data 同事务得到一个 Event 和一个 Evidence Link，随后
   Graphiti 只有一个 `episode_kind=EVENT` Episode；
2. 两个不同来源 Evidence 描述同一主体、动作、对象、阶段和时点，第二次返回同一 Event ID，
   Data 和 Graphiti 均无新增或更新；
3. “宣布限制”和“限制生效”返回两个 Event IDs；
4. 相同 Event 与 Evidence IDs 重试返回原 `submission_id`，不增加 Event、Evidence Link 或
   Graphiti Episode；
5. Data 创建成功后 Graphiti 临时不可用，API 状态显示投影重试；恢复后自动完成且 Data 中不
   增加第二个 Event；
6. Graphiti 投影延迟期间，相同现实事件再次到达，Data 只读补召回能避免重复创建；
7. Candidate 缺少 Evidence ID、Evidence 不存在、Event 身份语义不完整或包含多次动作时拒绝发布；
8. 同一现实动作出现核心事实修订时进入 `SAME_EVENT_REVISION/NEEDS_REVIEW`，不覆盖旧 Event。
9. `/openapi.json` 包含 Event Candidate 请求、状态响应、受控 enum、Bearer security 和全部错误
   响应；本地 `/docs` 可以完成交互验证。

## 11. 实施顺序

1. 评审并冻结本设计中的 Event Candidate、同一事件判断和 Evidence Link 语义；
2. 在 Data Service 先设计并实现 Event 创建与安全重试合同；
3. 在 Reasoning Server 先冻结 Pydantic/OpenAPI 合同快照，再实现 Candidate API、持久化状态机
   和 Data Client；
4. 实现 Graphiti/Data 历史召回与确定性去重规则；
5. 接入受控 LLM comparator，完成重复/新 Event 的端到端验收；
6. 实现 Data-first 的受控 Graphiti Event Projector 和失败恢复；
7. 用真实 Evidence IDs 完成上述八个场景；
8. 最后再设计 Agent OS 的 Evidence→Event 提炼工序，使其产出本合同需要的 Candidate。

## 12. 已确认变更与实施前决策

已确认：

- Event `semantic` 改为本设计的身份语义结构，替代尚未成熟的严格六键 5W1H；实施时同步更新
  Data migration、Context、ADR、OpenAPI 和读写代码；
- Agent OS 请求不携带 Candidate ID、`curation_as_of`、`business_identifiers` 或
  `contribution_weight`；
- Data 内部创建 `event_evidence_links` 时，第一版统一写入 `contribution_weight=1.0`。

实施决策：

1. Data Service 已接受 `publication_key` + 最小发布记录，它仅负责传输幂等；
2. `SAME_EVENT_REVISION` 第一版统一 fail closed 到 `NEEDS_REVIEW`，不覆盖历史 Event；
3. Reasoning API 第一版限定单活动 Resolver Worker；
4. ADR-0005 已明确 Event-only Graphiti 主链路和 ADR-0002 的 supersede 范围。
