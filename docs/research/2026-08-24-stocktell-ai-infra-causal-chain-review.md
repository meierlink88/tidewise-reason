# StockTell AI 基础设施因果链与观潮家推理方法调整

> 调研日期：2026-08-24
>
> 一手案例：[AI 推理基础设施 · 因果链](https://www.stocktell.me/insight/ai-infra)
>
> 目的：逐节点拆解 StockTell 的推导理由，判断观潮家在数据、图谱和 Agent 推理机制上还缺少什么。

## 1. 结论

观潮家当前 Event→Signal→节点的主体方向正确，现有方法也已经覆盖影响周期、逐跳机制、缓冲、替代、反方和失效条件。

StockTell 案例揭示的主要缺口不是再增加“利好/利空算法”，而是以下六点：

1. Event 与产业节点之间存在多个非节点的中介 Driver Signal；
2. 因果结构通常是共同驱动后的多分支，不是单条产业链的线性遍历；
3. 每条结构边还需要受控的 Variable→Variable 传导语义；
4. 关键假设需要形成条件门，而不只是附在结论后的风险文本；
5. 节点需要动态因果角色和 Event-specific 排序；
6. 每一跳需要独立的机制依据、审核状态和验证指标。

不需要增加新的顶层领域对象。上述能力可以继续由 Event、Entity、Link、Variable、Signal、Storyline 表达；需要扩展 Link subtype、Signal 合同和 Reasoning Tree Artifact。

## 2. StockTell 案例的总推导结构

示例 Event 包含两个变化：

- AI 数据中心需求/业绩强于预期；
- 新模型使单位推理成本下降。

StockTell 没有直接从 Event 跳到光模块、HBM 或液冷，而是先经过两个总假设：

```text
单位推理成本下降
→ AI 使用量可能增加
→ 总 token/推理工作负载增加
→ 云厂采购更多算力并扩建数据中心
```

然后从“算力集群扩大”分叉：

```text
算力集群扩大
├─ scale-out 网络流量增加 → 光模块/高速互连
├─ 加速卡数量与单卡内存增加 → HBM/服务器内存
├─ GPU 与 HBM 集成要求提高 → 先进封装
├─ 机柜功率密度提高 → 液冷
├─ 总用电和供电约束提高 → 数据中心供配电
├─ 近距离 scale-up 互连增加 → 高速铜连接
├─ 服务器出货增加 → 服务器/算力代工
└─ 传统风冷/低速互连被替代 → 负向 Signal
```

国产算力芯片没有被放在直接经营传导分支中，而被标为海外 AI 景气和国产替代的情绪映射，需要自己的订单验证。[StockTell 因果链](https://www.stocktell.me/insight/ai-infra)

## 3. 逐节点推导理由

| 节点 | StockTell 的推导理由 | 真正需要判断的 Variable/机制 | 关键反例或验证点 |
| --- | --- | --- | --- |
| 光模块/高速互连 | 大规模集群需要高速机器间通信，800G/1.6T 随 scale-out 放量 | cluster_scale、interconnect_bandwidth、port_count、speed_mix、order_visibility | 云厂 capex、速率路线、订单、收入占比 |
| HBM/服务器内存 | 加速卡必须配套高带宽和大容量内存 | accelerator_shipments、memory_per_accelerator、HBM_attach_rate、capacity | HBM 与 DDR5 不能混同；看产品结构、产能和订单 |
| 先进封装/封测 | GPU 与 HBM 需要 2.5D/CoWoS 等集成，封装产能可能成为瓶颈 | packaging_intensity、capacity_utilization、lead_time、yield | 扩产兑现、稼动率、客户结构；国产环节存在兑现时滞 |
| 先进封装材料 | 封装扩产再向材料端传导，隔着客户认证和放量周期 | qualified_demand、customer_certification、material_usage、lag | 不能从“封装景气”直接外推全部材料；看客户导入和收入 |
| 液冷/温控 | 机柜功率密度接近或超过风冷边界，液冷从可选变刚需 | rack_power_density、cooling_requirement、liquid_cooling_penetration | 使用密度、部署节奏和订单是否兑现 |
| 高速铜连接 | 机柜内短距 scale-up 连接增加，但与光互连存在路线竞争 | short_reach_bandwidth、distance、copper_share、optical_substitution | 不同距离/速率下光铜边界；客户验证 |
| 数据中心电力 | 用电由成本项变为能否上电的容量约束 | total_power_demand、available_power、power_delivery_capacity、order_backlog | 数据中心用电、供配电订单；向本地设备厂传导距离较远 |
| 国产算力芯片 | 主要是国产替代关注度，不是海外 Event 的直接供货受益 | market_attention、domestic_substitution_orders | 必须用国产订单和收入兑现验证，不得冒充直接经营 Signal |
| 服务器/算力代工 | 服务器出货跟随云厂 capex 和加速卡部署 | server_shipments、capex、order_visibility | 云厂/芯片厂出货与代工订单 |
| 传统风冷/低速互连 | 新架构对旧技术形成替代 | substitution_pressure、legacy_share | 替代节奏并非立即发生，需观察存量与新建比例 |

这个案例的“节点理由”都包含四层：

```text
物理或业务机制
→ 受影响 Variable
→ 必要条件/替代关系
→ 可观察验证指标
```

只保存一段自由文本 `mechanism`，不足以稳定支持 Agent 多轮推理和机器校验。

## 4. 当前方法已经具备的能力

当前 Methodology Spec 已经规定：

- 一个 Event 可以生成多个方向不同的 Signal；
- 每个 Signal 有 Anchor、Variable、方向、机制和影响周期；
- 每跳记录 lag、缓冲、替代、反向条件和 duration basis；
- 不允许全局固定衰减或固定延迟；
- LLM 负责语义判断，工具只校验 ID、Schema、时间和真实 Link；
- Investment Reasoning 需要经营影响、价值捕获、反方和多周期输出；
- Evidence 不进入下游 AgentContext。

依据：`docs/specs/event-driven-investment-research-methodology.md` 第 6、8、14、15 节。

因此不需要推翻两条 Pipeline，也不应改成 StockTell 的静态热力图检索。

## 5. 必须补充的元素

### 5.1 中介 Driver Signal

当前推理树容易写成：

```text
Event → 某 ChainNode Direct Signal → 沿 topology 传播
```

但 StockTell 案例真正的前半段是：

```text
Event
→ inference_unit_cost DOWN
→ usage_volume UP（条件性）
→ total_compute_demand UP
→ cloud_capex UP
→ cluster_scale UP
→ 多个节点分支
```

这些 Signal 不一定锚定某个 ChainNode，可以锚定 IndustryChain、Market、Company group 或其它正式 Entity。

调整：允许 Direct/Derived Signal 在进入产业链节点前形成中介 Driver Signal；不得要求 Event 的第一个 Signal 必须锚定 ChainNode。

### 5.2 分支型 Reasoning Tree

StockTell 明确说明光模块、HBM、液冷、电力是被共同 Driver 带动的并列分支，不是硬串成：

```text
光模块 → HBM → 封装 → 液冷 → 电力
```

调整：推理树必须支持一个上游 Signal 同时产生多个下游 Signal，并记录：

- `common_driver_signal_id`；
- `branch_id`；
- 每个分支独立的 mechanism、condition、lag 和 confidence；
- 分支之间的互补、竞争或无直接因果关系。

如果多个分支重新汇合，结构实际上是 DAG；产品仍可渲染为树，但 canonical Artifact 不应强制单父节点。

### 5.3 Variable→Variable 传导合同

现有 `industry_chain_graph_edges` 有 relation type、mechanism 和 condition_note，但同一拓扑边可能支持多种不同的变量传导：

```text
上游供给下降 → 下游输入成本上升
上游价格上升 → 下游毛利下降或售价上升
上游产能提升 → 下游可交付供给上升
```

调整：增加一个 Link subtype/persistence contract，可暂称 `Edge Variable Transmission`，但它不是新的顶层领域对象。

最小字段：

- topology_link_id；
- source_variable_id；
- target_variable_id；
- default_polarity；
- mechanism_summary；
- required_conditions；
- buffers；
- substitutions；
- lag_basis；
- verification_metrics；
- provenance_refs；
- review_status。

它只向 LLM提供经审核的机制候选，不自动计算 Signal。

### 5.4 非 topology 的 Signal 传导 grounding

当前 Spec 要求跨 Entity 的每条 Signal Link 必须引用产业链 topology Link。这个规则对节点→节点有效，但不能覆盖：

```text
推理成本 → 使用量
使用量 → 云厂 capex
云厂 capex → 集群规模
```

调整 Signal Transmission Link 的 grounding：

```text
grounding_kind =
  SAME_ANCHOR_VARIABLE
  ENTITY_RELATION
  CHAIN_TOPOLOGY
  REVIEWED_MECHANISM
  EXPLICIT_HYPOTHESIS
```

- CHAIN_TOPOLOGY 必须引用真实 IGE；
- ENTITY_RELATION 必须引用正式 Entity Link；
- REVIEWED_MECHANISM 必须引用受控机制合同；
- EXPLICIT_HYPOTHESIS 只能保持低/中置信并进入验证队列；
- 不能因为没有 topology Link 就由 LLM 自由造边。

### 5.5 条件门与反事实分支

本案例最重要的假设不是“AI 更便宜”，而是：

```text
使用量增幅是否足以超过单位成本下降幅度？
```

若只是节省支出而使用量不增长，总算力和 capex 未必上升。

调整：把关键假设建成 Reasoning Tree 中的条件门：

```text
Condition Gate: demand_elasticity / workload_growth
├─ 成立 → compute demand UP
├─ 不成立 → compute demand STABLE/DOWN
└─ 未知 → 两个 Scenario 并存
```

Condition Gate 是 Analysis Artifact 中的节点类型，不进入事实图，不需要增加领域顶层数据。

### 5.6 节点动态因果角色

相同 ChainNode 在不同 Event 下承担的角色不同。建议每次 Analysis Result 动态输出：

- PRIMARY_DEMAND_RECEIVER；
- REQUIRED_COMPLEMENT；
- BOTTLENECK；
- INFRASTRUCTURE_CONSTRAINT；
- SUBSTITUTE/COMPETING_ROUTE；
- SENTIMENT_ONLY；
- DISPLACED/NEGATIVE_EXPOSURE；
- NO_CLEAR_IMPACT。

这是运行时判断，不应写成 ChainNode 永久属性。

### 5.7 Event-specific Delta 与排序

StockTell 最有价值的自我约束是：如果“推理成本下降”“训练集群大单”“国产替代政策”三个 Event 都产生同一张节点热力图，那么系统只是检索预制图谱，而不是真正推理。

调整：Analysis Result 增加：

- event_relevance；
- causal_distance；
- evidence_completeness；
- transmission_strength；
- node_priority；
- why_this_event_changes_the_baseline。

排序不是收益预测，而是本次 Event 对节点的因果相关性和验证优先级。

### 5.8 每跳机制依据与验证指标

Evidence 不进入 AgentContext 的原则可以保留，但每条正式 topology/mechanism Link 必须带：

- reviewed mechanism statement；
- provenance IDs；
- source role/status；
- verification metrics；
- last_reviewed_at；
- confidence；
- missing evidence。

Agent 读取审核后的机制和来源状态，不读取 Evidence 正文。核验工具可通过 provenance ID 回查 Evidence。

## 6. 对 Pipeline 的调整

### 6.1 Event Analysis Pipeline

保持只生成 Event 直接支持的 Signal，但允许直接 Signal 锚定：

- IndustryChain；
- ChainNode；
- Commodity/Index；
- Company 或其它正式 Entity；
- 不必强制直接落到最终受影响节点。

例如本案例的 Direct Signal 应优先是：

```text
inference_unit_cost DOWN
```

而 `liquid_cooling_demand UP` 应是后续条件性 Derived Signal。

### 6.2 Investment Reasoning Pipeline

建议增加以下明确步骤：

```text
1. Identify Event Delta
2. Build Mediating Driver Signals
3. Evaluate Critical Condition Gates
4. Expand Candidate Chain/Node Context
5. Build Parallel Transmission Branches
6. Classify Node Causal Roles
7. Compare Complement/Substitute/Displaced Branches
8. Rank Event-specific Node Relevance
9. Produce Horizon Views, Counterfactuals and Checks
```

### 6.3 Agent 分工

现有角色可保留，但 Industry Chain Analyst 至少分两轮：

1. Driver/Branch Planner：提出共同 Driver、分支和条件门；
2. Node Mechanism Analyst：逐节点解释 Variable、机制、lag、缓冲和替代；
3. Bear/Risk Analyst：专门尝试关闭条件门或证明需求没有兑现；
4. Synthesizer：比较分支，不把所有节点压成同方向。

不要求模型公开隐藏思维链，只保存结构化陈述、对象引用、假设、条件和结论。

## 7. 图谱需要新增什么

### 静态事实/机制底图

```text
IndustryChain → ChainNode
ChainNode → ChainNode topology
ChainNode → applicable Variable
Topology Link → reviewed Variable Transmission candidate
Entity → Entity business/dependency relation
```

### 动态推理图

```text
Event → Direct Signal
Signal → Variable
Signal → Anchor Entity
Signal → Derived Signal
```

Signal Link 支持同 Anchor 变量推导、正式 Entity Relation、产业 topology、审核机制和显式假设五类 grounding。

### 只保存在 Artifact 的结构

```text
Condition Gate
Scenario Branch
Node Causal Role
Event-specific Ranking
Reasoning DAG
```

## 8. 第一版 Demo 应如何验证

不能只验证“能否输出一条看起来合理的 AI 基础设施链”。至少使用同一条产业链运行三个不同 Event：

1. 推理成本下降；
2. 训练集群大单/资本开支上修；
3. 国产替代政策。

期望差异：

- 推理成本下降：先经过使用弹性条件门，偏光互连/服务器/HBM；
- 训练集群大单：需求更直接，先进封装/HBM/电力权重更高；
- 国产替代政策：国产算力芯片从情绪映射变成直接政策/订单候选，其它海外映射降权。

这个对比不预设每个节点固定答案，只检验 Agent 是否根据 Event delta 改变共同 Driver、分支、节点角色和验证点。

## 9. 最终判断

StockTell 案例证明，成熟的节点推理不是“沿产业链边扩散一个正负值”，而是：

```text
Event Delta
→ 中介 Driver Signal
→ 关键条件门
→ 多个并行传导分支
→ 节点 Variable 变化
→ 瓶颈/互补/替代/情绪等动态角色
→ Event-specific 节点排序
→ 验证指标和反事实
```

观潮家现有方法论已经具备大部分治理基础。真正需要修改的是：放宽 Signal Link 只能由产业 topology grounding 的限制、补充中介 Driver、分支 DAG、条件门、Variable Transmission 合同和 Event-specific 差异性验收。
