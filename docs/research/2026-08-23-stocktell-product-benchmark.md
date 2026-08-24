# StockTell 产品与方法论对标研究

> 调研日期：2026-08-23
>
> 资料范围：仅使用 StockTell 官方公开页面。
>
> 目的：判断当前 Event → Signal → Storyline → 产业链/节点投研推理设计是否需要调整。

## 1. 结论

StockTell 是当前产品的高度相关标杆，但不是可以原样照搬的完整预测方法论。

当前设计的主体方向无需推翻：

```text
Evidence 清洗为 Event
→ Event Analysis：实体、Variable、Direct Signal、影响周期、Storyline 路由
→ Investment Reasoning：产业链/节点传导、公司/证券映射、结论与推理树
```

需要调整的是实施优先级和产品表达：

1. 把“事件到产业链节点、公司和证券的稳定映射关系”提升为第一优先级；
2. 把关系距离、影响方向、置信度和投资意义分开，不能混成一个“利好/利空”标签；
3. 每个结论必须同时给出后续验证点和失效条件；
4. 在两条推理 Pipeline 后增加不可改写的发布、观察和复盘闭环；
5. Storyline 保留为中长期研究记忆，但前台优先表达“今日触发”和“长期定位”；
6. Signal 保留为内部时态推理对象，前台可显示为“变化判断/影响状态”，不要求用户理解领域术语。

StockTell 最值得吸收的是产品闭环和关系治理，而不是它的次日同向统计或静态规则推理。

## 2. StockTell 实际解决的问题

StockTell 将产品定义为产业链投资理解工具，核心问题是：一个全球事件如何传导到产业链、环节和相关公司，以及公司属于直接、间接、情绪还是待验证映射。其公开框架为：

```text
全球事件
→ 产业链传导
→ 环节变化
→ 股票映射
→ 关系类型
→ 验证点
```

它明确不把自己定位为新闻聚合、选股或交易工具，而是帮助用户区分真实业务关系与市场情绪联想。[关于 StockTell](https://www.stocktell.me/about)

### 2.1 每日产品输出

公开日报把一次分析稳定拆成四段：

1. 这次变了什么；
2. 影响哪条产业链；
3. A 股如何映射；
4. 后续验证什么。

历史判断保留原貌，不随后续行情改写。[日报示例](https://www.stocktell.me/daily/2026-08-21)

### 2.2 执行流程

官方方法页描述的执行逻辑是：

```text
盘前捕获海外异常与全球事件
→ 按人工校准关系归入产业链和环节
→ LLM 生成链级说明，规则提供方向兜底
→ 按审核过的关系模型映射国内标的
→ 绑定真实来源
→ 结构、禁词和行情校验
→ 发布
→ 收盘后自动记录结果并进入复核
```

产业链环节、公司映射、关系档和引用链接不由 AI 临时创造；AI 主要负责文字归纳和候选推理，未经人工审核的生成内容不能获得最高置信度。[数据来源与方法](https://www.stocktell.me/methodology?from=footer)

这说明 StockTell 本质上是“稳定关系底图 + 每日事件触发 + 受约束的 LLM 表达”，不是让 LLM 自由遍历全图后直接生成股票结论。

## 3. 最核心的领域能力

### 3.1 关系档是核心基础设施

StockTell 使用以下关系分类：

| 关系档 | 含义 |
| --- | --- |
| 触发源 | 海外公司或事件源，不是国内映射标的 |
| 直接映射 | 传导路径短且业务入口明确，仍需订单、客户、收入和毛利验证 |
| 间接映射 | 相关但隔层或业务暴露不纯 |
| 情绪映射 | 主题相关，但缺少直接业务传导 |
| 弱映射 | 关系较远，只作外围观察 |
| 待验证 | 存在线索，但证据不足或尚未审核 |

关系档表示业务和传导距离，不等于受益强度，更不等于股价方向。[关系说明](https://www.stocktell.me/relations)

### 3.2 产业逻辑与市场行为分离

链页将事件触发、产业链传导、资金行为和事后复盘分开展示，并强调资金流不等于基本面验证。[AI 产业链页](https://www.stocktell.me/chain/ai)

个股页又把长期产业链定位与当日事件触发分开，同时列出关系档、上下游位置、待核验披露项、财务状态和 ETF 暴露。[个股页示例](https://www.stocktell.me/stock/300502)

### 3.3 验证点是结论的一部分

StockTell 不止输出“相关公司”，还说明下一步应检查订单、客户、收入占比、毛利率、产能、资本开支或商业化进展。因果链页还展示逐步传导、置信度、反转条件和容易误判的环节。[因果链示例](https://www.stocktell.me/insight/ai-infra)

### 3.4 产品闭环

产品形成五个互相连接的入口：

```text
今日推理
→ 产业链页
→ 股票池/个股页
→ 自选跟踪
→ 日报归档与复盘
```

股票池可按产业链、上下游、板块、概念和关系档筛选；自选页按产业链聚合用户标的的今日触发和验证点。[股票池](https://www.stocktell.me/stocks) [自选](https://www.stocktell.me/watchlist)

## 4. 对当前设计的调整

### 4.1 两条推理 Pipeline 保留

当前职责划分是合理的：

- Event Analysis 回答“这个 Event 直接改变了什么”；
- Investment Reasoning 回答“这些变化如何传到目标产业链、节点和可投资载体”。

StockTell 的流程验证了这一结构。它只是没有公开建模独立的 Signal 和 Storyline，而是把相似信息压缩在每日判断、链状态和历史归档中。

### 4.2 将稳定业务映射 Link 提升为 P0

当前系统若缺少 ChainNode → Company 和 Company → Security 的真实关系，即使 Event 和 Signal 推理正确，也无法可靠回答“哪些标的是直接关系、哪些只是概念映射”。

无需发明新的顶层对象，可以扩展 `Link` 类型和属性：

```text
ChainNode --COMPANY_EXPOSED_AT--> Company
Company   --ISSUES-------------> Security
Entity    --MAPPED_TO----------> MarketConcept / Index / CommodityIndex
```

业务暴露 Link 至少需要：

- `mapping_class`：DIRECT / INDIRECT / SENTIMENT / WEAK / PENDING；
- `business_basis`：产品、客户、收入、产能或供应关系依据；
- `evidence_status`：已接入披露、部分待核验、待补来源；
- `verification_points`：下一步应核验的公开信息；
- `review_status`、`reviewed_at` 和有效期；
- 来源或 Evidence 审计引用。

LLM 可以提出候选 Link，但不能自行把候选升级成正式长期关系。

### 4.3 四个维度必须正交

系统需要明确分开：

| 维度 | 回答的问题 |
| --- | --- |
| 关系距离 | 公司与产业链节点离得多近 |
| 影响方向 | Event/Signal 对变量产生上升、下降还是不确定影响 |
| 推理置信度 | 事实与传导链有多可靠 |
| 投资意义 | 是否存在价值捕获、预期差和风险收益空间 |

“直接映射”不等于“利好”；“经营改善”也不等于“股价仍有上涨空间”。

### 4.4 Signal 保留，但作为内部对象

StockTell 前台使用“升温、承压、分歧”等语言，但缺少明确的中长期作用窗口。我们的 Signal 应继续表示：

```text
某 Event 导致某 Entity 的某 Variable
在何时开始、向哪个方向变化、何时达到峰值、何时衰减、什么条件会失效
```

例如：

```text
Event：某国限制稀土原料出口
Entity：稀土精矿节点
Variable：可交付供给
Signal：DOWN
onset：立即
peak：1—3 个月
decay/end：替代供应恢复或限制解除后
```

用户看到的是“稀土精矿短中期供应趋紧”，系统内部仍用 Signal 保持时间、机制和可审计性。

### 4.5 Storyline 保留，但降低前台概念负担

StockTell 的“长期定位 + 今日触发 + 不可改写日报 + 复盘”实际承担了 Storyline 的部分功能。我们的 Storyline 更适合继续作为后台的跨时点研究记忆：

```text
上一版 thesis
→ 新 Event / Signal
→ 本轮变化
→ 支持和反驳因素
→ 验证点与失效条件
→ 下一版 thesis
```

前台不必要求用户理解 Storyline，可以分别显示“今日触发”“长期逻辑”“发生了什么变化”。

### 4.6 Evidence 不进入推理 Context，但证据链不能断

当前“从 Event 开始推理”的边界仍然成立。Evidence 清洗、去重、拆分和审核后发布 Event，Codex 默认只消费 Event。

但 Event 和稳定映射 Link 必须保留 provenance、来源角色、发布时间和核验状态，产品端才能解释事实从哪里来。必要时由独立核验工具回看 Evidence，而不是让主推理绕过 Event 直接从原文生成 Signal。

### 4.7 增加分析后的验证闭环

这不是第三条 LLM 推理 Pipeline，而是两条 Pipeline 之后的自动化工序：

```text
冻结原始结论
→ 到达验证时点
→ 回填市场、订单、财报、产能或政策结果
→ 区分市场同向、经营验证和 thesis 验证
→ 标记 CONFIRMED / WEAKENED / CONTRADICTED / UNKNOWN
→ 进入人工复核
→ 更新关系或 Storyline，新版本不覆盖旧结论
```

## 5. 不应照搬的部分

### 5.1 次日同向不是因果验证

StockTell 的复盘主要统计事件后国内标的是否同向，并明确承认这不是基本面验证，也不能预测未来。[复盘页](https://www.stocktell.me/track)

我们的系统必须把三种结果分开：

- 市场反应是否同向；
- 产业/公司经营变量是否被验证；
- 原投资 thesis 是否成立。

### 5.2 不能只覆盖盘前短期触发

StockTell 的主场景偏隔夜海外事件到当日 A 股映射，缺少显式的短、中、长期影响窗口。我们的宏观、政策、产业和公司事件需要保留 Signal 周期与 Storyline 记忆。

### 5.3 不能完全依赖静态映射

StockTell 的关系模型高度依赖人工预配置。我们的 Agent 应当能够语义发现候选产业链和传导路径，但所有正式实体身份、产业链拓扑和长期业务暴露仍需经过确定性校验与审核。

### 5.4 必须强化 Event 去重

2026-08-21 日报中，美光和迈威尔相关判断存在近义重复条目。这反向证明 Evidence → Event 工序必须做事件归一化、聚类和去重，否则同一事实会被重复计入推理上下文。[日报示例](https://www.stocktell.me/daily/2026-08-21)

### 5.5 不把市场标签包装成机构事实

“抢筹、洗盘、弱势共振”等规则标签最多属于市场行为观察，不应成为产业链传导或机构意图的事实依据。

## 6. 调整后的目标闭环

```text
0. Event Curation
Evidence → 清洗/拆分/去重/核验 → Event

1. Event Analysis
Event → Entity → Variable → Direct Signal + impact window
      → Storyline routing candidate

2. Investment Reasoning
新 Event + Active Signals + Storyline + 产业链拓扑 + 稳定业务映射
→ 受影响产业链与节点
→ 节点经营影响
→ Company 价值捕获
→ Security / Concept / Index 映射
→ 预期差或 UNKNOWN
→ 一句话结论 + 结构化推理树 + 验证点 + 失效条件

3. Publish & Validate
冻结当时结论 → 观察市场与经营结果 → 分类复盘 → 更新 Storyline/关系版本
```

## 7. 实施优先级建议

1. 先用一个真实 Event 跑通 Event Curation 和 Event Analysis；
2. 同时补齐案例需要的 ChainNode → Company → Security 稳定 Link；
3. 把真实产业链及节点、Event、Variable、Signal、Storyline 投影到 Graphiti；
4. 让 Codex 输出“影响链/节点 + 公司映射 + 一句话结论 + 推理树 + 验证点”；
5. 保存原始结果并做一次真实复盘；
6. 跑通后再扩展宏观、地缘和中长期 Storyline，不先建设大而全的规则库。

## 8. 最终判断

StockTell 证明了用户真正购买的不是图谱、Signal 或 Agent 本身，而是一个每天可阅读、能回到产业链结构、能解释公司关系、并可继续验证的判断结果。

因此，现有设计应从“推理模型优先”调整为“结论产品闭环优先”，但不应删除 Signal、Storyline 或多周期推理。它们正是当前设计相对 StockTell 能够支持宏观到微观、中长期影响和持续 thesis 管理的关键能力。
