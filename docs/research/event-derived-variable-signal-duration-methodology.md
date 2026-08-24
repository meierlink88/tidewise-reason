# Event 派生 Variable Signal 起效与持续周期估计方法

> 研究日期：2026-08-21  
> 适用范围：事件驱动的产业链 / 投研分析  
> 证据边界：只采用标准组织、政府技术文档及原始学术论文；本文中的落地设计均标为工程建议。

## 一句话结论

不能仅凭一段 Event 文本可靠地“猜出持续 3 个月”。周期是 **Event × 分析锚点 × 传导机制 × 市场状态** 的联合属性。同一事件对“上游订单”“中游库存”“下游毛利”和“股票价格”会产生不同的起效时间和衰减曲线。

推荐把周期推导设计为：

```text
明确披露期限
  > 合同 / 政策 / 产能 / 库存等确定性约束
  > 同类事件的经验响应曲线或生存分布
  > 专家情景先验
  > LLM 候选假设（不得直接发布为最终周期）
```

LLM 适合抽取日期、识别机制、匹配规则和生成待验证假设；最终时间区间应由证据、规则或经历史校准的统计模型计算，并持续接受新事实的失效检验。

## 1. 先定义“周期”究竟是什么

### 1.1 周期属于锚点信号，不属于 Event 本身

分析锚点至少应为：

```text
产业链节点 + 变量 + 地域/市场 + 主体范围
```

例如“某晶圆厂停产”不是一个可直接使用的周期结论，它可以同时派生：

- `晶圆厂.output`：停产日起立即下降；
- `芯片设计公司.inventoryRisk`：库存缓冲消耗后才上升；
- `服务器厂商.componentCost`：采购或合同重定价后才变化；
- `相关公司.stockPrice`：信息首次公开时即可能反应。

供应链中的订单信息会受需求信号处理、配给博弈、批量订货和价格波动影响，并可能在向上游传播时放大。因此，不能把“产业链每经过一跳固定增加 N 天”当作通用规律；传导规则需要按变量和机制建模。[Lee、Padmanabhan、Whang（1997）](https://doi.org/10.1287/mnsc.43.4.546)

### 1.2 不存一个 duration，存一条有不确定性的影响曲线

令 `s_A(h)` 表示 Event 被当前时点知晓后第 `h` 个时间单位，对锚点 `A` 的预期影响强度。工程上至少区分：

- `knownAt`：市场或系统何时能够知道事件，防止未来信息泄漏；
- `effectiveAt`：事件在现实世界何时开始实施；
- `onset`：锚点变量首次出现有意义影响；
- `peakAt`：影响峰值；
- `end/halfLife`：影响跌回非实质水平或衰减一半的时间；
- `direction/magnitude`：方向与随时间变化的幅度；
- `invalidationConditions`：哪些新事实会使推导失效。

W3C OWL-Time 将时间点、具有起止边界的区间、duration 以及区间重叠等关系明确分开，适合作为图谱时间字段与窗口相交规则的语义参考。[W3C Time Ontology in OWL](https://www.w3.org/TR/owl-time/)

### 1.3 用“实质性阈值”定义起止，而不是让模型自由描述

为每个锚点变量设业务阈值 `δ_A`。定义：

```text
onset = 首次满足 |s_A(h)| >= δ_A 的时点
end   = 最后满足 |s_A(h)| >= δ_A 的时点
```

阈值可以是产量变化、价格变化、毛利影响或风险概率变化。没有统一阈值时，“持续多久”没有可重复的答案。还必须区分：

- **无显著影响**：置信区间内的影响低于阈值；
- **证据不足**：无法估计；
- **尚未起效**：预计未来会超过阈值，但当前尚未达到。

## 2. 六层周期估计方法

### 2.1 第一层：事件明确披露的期限

优先读取官方公告、合同、政策或经营数据中的：开始日、结束日、生效日、分阶段里程碑、数量、续约/终止条款和恢复条件。

工程建议：LLM 只把原文抽成候选字段，并保留逐字段证据片段；日期解析器检查时间顺序、时区、单位和“预计/最迟/至少/可能延期”等模态词。披露的是 **事件约束期**，不一定等于每个锚点的影响期，后续仍要叠加库存、交付、合同和响应滞后。

### 2.2 第二层：结构化的机制 / 传导估计

为每种 `事件类型 → 锚点变量` 建机制模板，将传导路径拆成可观测的阶段：

```text
事件实施
  -> 库存或在手订单缓冲
  -> 采购 / 排产 / 运输 lead time
  -> 合同重定价或替代供应切换
  -> 锚点变量响应
  -> 恢复、去库存或产能爬坡后的衰减
```

每条边保存延迟分布 `L_i` 和响应核 `K_i(h)`。多跳的起效延迟由各阶段延迟相加；完整影响曲线应由事件强度曲线与各阶段响应核逐层卷积，而不是简单给每一跳复制同一个有效期。

日本大地震的企业网络研究实证记录了冲击同时沿供应商和客户关系传播，并用生产网络一般均衡模型估计直接与间接影响。这支持按网络方向、路径和锚点分别估计，而不是给全产业链一个统一周期。[Carvalho 等（2021）](https://doi.org/10.1093/qje/qjaa044)

当输入只有范围时，例如库存覆盖 `20–35 天`、替代认证 `30–60 天`，输出也必须是范围。若不同输入相关，需保留相关性，不能假设独立；NIST 的不确定性指南也提醒，忽略协方差或模型设定错误会使传播结果失真。[NIST Engineering Statistics Handbook：Propagation of Error](https://www.itl.nist.gov/div898/handbook/mpc/section5/mpc55.htm)

### 2.3 第三层：历史同类事件的动态响应

有足够数量的可比事件与锚点时间序列时，以历史数据校准机制先验：

| 方法 | 估计对象 | 适合回答 | 主要限制 |
|---|---|---|---|
| 金融事件研究 | 事件窗内异常收益 | 信息何时被证券价格吸收 | 主要衡量市场定价，不等于产量、订单或利润的现实影响期；事件重叠会污染结果 |
| 分布滞后模型 | 各滞后期系数 `β_h` | 影响何时开始、峰值、衰减及累计效应 | 需处理趋势、季节性、自相关、反向因果和滞后长度选择 |
| Local Projection | 每个未来 horizon 的响应 | 不同 horizon 的影响曲线及置信区间 | 仍依赖冲击识别与可比样本，远期区间通常更宽 |
| 生存 / hazard 模型 | 信号尚未失效的概率 `S(h)` | “还能持续多久”及不同条件下的失效风险 | 必须明确定义终止事件；撤回、替代和恢复可能形成竞争风险 |

MacKinlay 的经典事件研究把金融事件研究定义为使用事件附近的证券价格衡量公司价值影响，因此它更适合作为“市场价格信号”的周期证据，不能直接替代实体产业变量的周期估计。[MacKinlay（1997）](https://www.jstor.org/stable/2729691)

分布滞后模型直接估计 `y_t = α + Σ β_h x_{t-h} + ε_t` 的滞后响应；多项式分布滞后用约束减少高维滞后系数，但约束形状和误差自相关会影响结论。[McDowell（2004），Stata Journal](https://www.stata-journal.com/article.html?article=st0065)

Jordà 的 Local Projection 在每个预测 horizon 分别回归响应，可获得逐期 impulse response 和逐点/联合推断，并比从一个完整动态系统远期外推更不易受模型错设影响。[Jordà（2005），American Economic Review](https://doi.org/10.1257/0002828053828518)

当历史样本中很多信号在观察结束时仍然有效，普通平均持续时长会产生删失偏差。应以 survival function `S(h)=P(T>h)` 表示尚未结束概率，或以 Cox 模型用事件类型、节点、库存状态、政策强度等协变量解释失效 hazard；Cox 原始论文就是针对含删失的 failure time 与协变量建模。[Cox（1972）](https://doi.org/10.1111/j.2517-6161.1972.tb00899.x)；[NIST 对 survival function 的定义](https://www.itl.nist.gov/div898/handbook/apr/section1/apr122.htm)

如果只能知道“上季度仍有效、本季度已失效”，这是区间删失而不是一个精确结束日；可使用 Turnbull 的分组、删失和截断数据非参数分布估计，避免人为把季度末当成真实终点。[Turnbull（1976）](https://doi.org/10.1111/j.2517-6161.1976.tb01597.x)

### 2.4 第四层：情景范围与不确定性传播

样本不足时，不给虚假的精确日期，而是形成条件化情景：

```text
乐观 / 基准 / 悲观
或 onsetP10 / onsetP50 / onsetP90
   endP10   / endP50   / endP90
```

输入来自披露范围、机制参数、历史分布和明确标注的专家先验。用 Monte Carlo 将各输入分布通过机制模型传播到 onset、peak 和 end 的输出分布；JCGM 101:2008 正式给出了通过数学模型传播输入概率分布并形成输出覆盖区间的 Monte Carlo 框架。[BIPM/JCGM 101:2008](https://doi.org/10.59161/JCGM101-2008)

短期 / 中期 / 长期筛选不应只比较两个点日期。更稳妥的筛选量是：

```text
P(信号的实质影响区间与分析窗口 W 相交)
以及 E[W 内的平均/累计影响强度]
```

远期、多跳、低样本信号应自然得到更宽区间和更低置信度，而不是因为 LLM 语言肯定就获得高置信度。

### 2.5 第五层：在线监控、修订与失效

信号是带版本的预测，不是一次生成后永久有效。建议状态机为：

```text
anticipated -> active -> decaying -> expired
                    \-> invalidated / superseded
```

至少在以下情形重估或失效：事件撤回；生效日延期/提前；产量、价格、库存、订单等关键观测持续偏离预测带；替代供给、政策、技术或竞争格局改变；出现方向相反且证据等级更高的新事件。

小幅但持续的模型偏离可用 CUSUM 等顺序监控。NIST 说明 CUSUM 通过累计相对基准均值的偏差来检测过程均值漂移，并可设置误报、漏报和希望检测的最小变化幅度。[NIST Engineering Statistics Handbook：CUSUM](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc323.htm)

### 2.6 第六层：历史回测与持续校准

每个事件类型 × 锚点变量 × 市场状态建立历史 cohort，按当时可知信息重放，避免使用后来才公布的数据。至少评估：

- onset / peak / end 的绝对误差；
- P50、P80、P90 区间的实际覆盖率；
- 信号有效日误报率和漏报率；
- 各 horizon 的方向、幅度与累计影响误差；
- 按事件类型、产业链层级、地区和市场状态分组后的稳定性。

只有经过样本外校准的方法才可提升 `confidence`；单次专家判断或 LLM 表述不能据此升级。

## 3. LLM 的合适角色与禁止边界

### 适合交给 LLM

- 从公告中抽取显式时间、条件、数量与模态词，并定位原文证据；
- 将 Event 分类到机制模板，提出受影响锚点和传导路径候选；
- 生成检索历史类比事件所需的结构化标签；
- 发现相互矛盾的来源、遗漏条件和潜在失效触发器；
- 在规则 / 统计模型给出结果后，生成可读解释。

### 不应交给 LLM 独立决定

- 没有依据时直接输出“持续 6 个月”；
- 执行多跳时间加总、概率传播和窗口筛选；
- 用语言相似性代替可比事件定义与因果识别；
- 把股票价格事件窗当作订单、收入或产能影响期；
- 覆盖明确披露、确定性规则、统计模型或审核结论。

NIST 将生成式模型“自信地产生错误内容”定义为 confabulation，并建议用经验证的方法评估能力、记录业务规则和领域知识、核验输出来源与引文，且不要从狭窄或轶事式测试外推能力。因此 LLM 的周期结果应是 `LLM_HYPOTHESIS`，必须经证据或模型门禁后才能成为正式 Variable Signal。[NIST AI 600-1，第 2.2 节及 MS-2.3/MS-2.5](https://doi.org/10.6028/NIST.AI.600-1)

## 4. 推荐的数据契约

```yaml
VariableSignal:
  anchor: {nodeId: string, variable: string, geography: string, subjectScope: string}
  direction: UP | DOWN | MIXED | NONE
  knownAt: timestamp
  effectiveAt: timestamp | interval
  onset: {p10: timestamp, p50: timestamp, p90: timestamp}
  peakAt: {p10: timestamp, p50: timestamp, p90: timestamp}
  end: {p10: timestamp, p50: timestamp, p90: timestamp, openEnded: boolean}
  magnitudeCurve: curveRef
  materialityThreshold: value
  confidence: {source: number, mechanism: number, empirical: number, overall: number}
  basis:
    type: DISCLOSED | CONTRACTUAL | MECHANISTIC |
          DISTRIBUTED_LAG | LOCAL_PROJECTION | SURVIVAL |
          EXPERT_SCENARIO | LLM_HYPOTHESIS
    evidenceIds: []
    ruleOrModelVersion: string
  assumptions: []
  invalidationConditions: []
  status: ANTICIPATED | ACTIVE | DECAYING | EXPIRED |
          INVALIDATED | SUPERSEDED
  lastEvaluatedAt: timestamp
```

`confidence` 不应只是一个由 LLM 生成的分数。建议把来源可靠度、机制完备度、历史校准质量分别保存，综合分数由确定性规则计算。

## 5. 推荐的实际推导流程

```text
1. Event 抽取：发生了什么、何时知晓、何时生效、显式期限与条件
2. 锚点展开：对每个“节点 + 变量”分别生成候选信号
3. 证据优先：先采用明确披露与合同/政策硬约束
4. 机制计算：叠加库存、订单、交付、产能、定价等延迟与响应核
5. 经验校准：用同类事件的 distributed-lag / local-projection / survival 结果更新参数
6. 情景传播：输出 onset/peak/end 分布，而非单一日期
7. 窗口评分：计算与短、中、长期窗口的重叠概率和窗口内影响强度
8. 持续监控：新 Event 或实际变量偏离时重估、失效或被新版本替代
9. 回测校准：按当时可知数据检验区间覆盖率与误报/漏报
```

最关键的产品判断是：**LLM 可以帮助回答“可能通过什么机制、应查哪些证据”，但不能仅凭语义常识可靠回答“具体持续多久”。** 当没有披露、机制参数或可比历史时，正确输出是“区间很宽 / open-ended / 证据不足”，而不是制造一个看起来精确的期限。

## 参考来源

1. W3C, [Time Ontology in OWL](https://www.w3.org/TR/owl-time/).
2. Lee, Padmanabhan & Whang (1997), [Information Distortion in a Supply Chain: The Bullwhip Effect](https://doi.org/10.1287/mnsc.43.4.546).
3. Carvalho et al. (2021), [Supply Chain Disruptions: Evidence from the Great East Japan Earthquake](https://doi.org/10.1093/qje/qjaa044).
4. MacKinlay (1997), [Event Studies in Economics and Finance](https://www.jstor.org/stable/2729691).
5. McDowell (2004), [From the help desk: Polynomial distributed lag models](https://www.stata-journal.com/article.html?article=st0065).
6. Jordà (2005), [Estimation and Inference of Impulse Responses by Local Projections](https://doi.org/10.1257/0002828053828518).
7. Cox (1972), [Regression Models and Life-Tables](https://doi.org/10.1111/j.2517-6161.1972.tb00899.x).
8. Turnbull (1976), [The Empirical Distribution Function with Arbitrarily Grouped, Censored and Truncated Data](https://doi.org/10.1111/j.2517-6161.1976.tb01597.x).
9. NIST, [Reliability or Survival Function](https://www.itl.nist.gov/div898/handbook/apr/section1/apr122.htm), [Propagation of Error](https://www.itl.nist.gov/div898/handbook/mpc/section5/mpc55.htm), [CUSUM Control Charts](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc323.htm).
10. BIPM/JCGM (2008), [JCGM 101:2008 — Propagation of distributions using a Monte Carlo method](https://doi.org/10.59161/JCGM101-2008).
11. NIST (2024), [Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile, NIST AI 600-1](https://doi.org/10.6028/NIST.AI.600-1).
