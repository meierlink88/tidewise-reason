# 事件驱动股票投研 Agent Harness 方法论

> 研究日期：2026-08-22
>
> 研究对象：[`HKUDS/Vibe-Trading`](https://github.com/HKUDS/Vibe-Trading)、[`AI4Finance-Foundation/FinRobot`](https://github.com/AI4Finance-Foundation/FinRobot)、[`K-Quant/K-Quant`](https://github.com/K-Quant/K-Quant)
>
> 源码基线：Vibe-Trading [`1907e47d`](https://github.com/HKUDS/Vibe-Trading/tree/1907e47d31d72f34bc2c87e0e5c4f750c83da59d)、FinRobot [`01ed4083`](https://github.com/AI4Finance-Foundation/FinRobot/tree/01ed408326f1d4ec2460596dee10858faf0f69af)、K-Quant [`1280959c`](https://github.com/K-Quant/K-Quant/tree/1280959c47166e5d94fa3fa028a0ac5dead64133)
> 证据边界：项目事实仅来自三个官方仓库的 README、源码与配置。本文提出的融合架构是基于这些证据的工程推导，不代表三个项目的官方设计。本文讨论研究辅助和风险识别，不讨论自动交易执行。

## 结论

目标不应是复刻三个项目，也不应让一个“大模型投研 Agent”从新闻直接生成买卖结论。更合理的目标是建设一套与 Codex、Claude Code、Agno 等运行时解耦的 **Investment Research Agent Harness**：

```text
Graphiti 时点事实与证据
    ↓
事件归一化与事实/观点隔离
    ↓
宏观 → 中观 → 微观传导路径候选
    ↓
板块 / 概念 / 商品 / 个股 × 短中长期研究合同
    ↓
确定性计算 + 统计模型 + LLM 解释/反驳
    ↓
PIT 验真、事件研究、回测、压力测试
    ↓
人工审批后的研究结论与监控任务
    ↓
真实结果归因 → 校准规则、模型和方法论
```

三个项目应被提炼为三个互补的控制面：

| 项目 | 最值得提炼的控制面 | 不应误用为 |
|---|---|---|
| Vibe-Trading | 假设生命周期、可重放 run card、PIT/前视防护、统计验真、风险与权限门禁 | 宏观到产业链的因果知识引擎 |
| FinRobot | Lead + 专项 Agent 编排、确定性数值计算与 LLM 叙述分离、多空辩论与 Judge 综合 | 经时点回测校准的事件预测器 |
| K-Quant | 动态时序知识构建、关系投影为模型输入、增量学习、图关系解释 | 可直接投入生产的 Agent 运行时或完整 PIT 平台 |

一句话概括融合原则：**Graphiti 管“当时已知什么”，K-Quant 范式管“关系怎样随时间进入模型”，FinRobot 范式管“谁负责分析、谁负责计算、谁负责质疑”，Vibe-Trading 范式管“结论如何被验真、重放、否决和持续监控”。**

## 1. 三个项目真正值得借鉴什么

### 1.1 Vibe-Trading：把投研变成可证伪的研究流程

Vibe-Trading 的核心启发不是它提供多少数据源或因子，而是把“研究想法”变成有状态、有证据、有实验记录的对象。

其 `Hypothesis` 对象记录 thesis、universe、signal definition、data sources、run cards 和 invalidation notes，并使用 `exploring / testing / validated / rejected / monitoring` 生命周期；回测结果与 Monte Carlo、Bootstrap、Walk-Forward 验证能够链接回假设。[假设对象与生命周期](https://github.com/HKUDS/Vibe-Trading/blob/1907e47d31d72f34bc2c87e0e5c4f750c83da59d/agent/src/hypotheses/registry.py#L20-L26) · [假设字段](https://github.com/HKUDS/Vibe-Trading/blob/1907e47d31d72f34bc2c87e0e5c4f750c83da59d/agent/src/hypotheses/registry.py#L82-L112) · [链接回测和稳健性结果](https://github.com/HKUDS/Vibe-Trading/blob/1907e47d31d72f34bc2c87e0e5c4f750c83da59d/agent/src/hypotheses/registry.py#L282-L327)

其 backtest run card 保存配置哈希、可选策略源码哈希、数据源、标量指标、警告、产物清单和 validation，使结论可以追溯到当次输入和实现，而不只是保留一段 Agent 对话。[run card 结构与哈希](https://github.com/HKUDS/Vibe-Trading/blob/1907e47d31d72f34bc2c87e0e5c4f750c83da59d/agent/backtest/run_card.py#L25-L94)

验真不是只看收益率。项目提供随机排列检验、Sharpe Bootstrap 置信区间和分段 Walk-Forward 一致性检查。[统计验证入口](https://github.com/HKUDS/Vibe-Trading/blob/1907e47d31d72f34bc2c87e0e5c4f750c83da59d/agent/backtest/validation.py#L1-L10) · [Monte Carlo](https://github.com/HKUDS/Vibe-Trading/blob/1907e47d31d72f34bc2c87e0e5c4f750c83da59d/agent/backtest/validation.py#L29-L113) · [Bootstrap Sharpe](https://github.com/HKUDS/Vibe-Trading/blob/1907e47d31d72f34bc2c87e0e5c4f750c83da59d/agent/backtest/validation.py#L136-L197) · [Walk-Forward](https://github.com/HKUDS/Vibe-Trading/blob/1907e47d31d72f34bc2c87e0e5c4f750c83da59d/agent/backtest/validation.py#L208-L285)

项目还把写操作和交易操作视为高风险边界，要求显式批准，并强调 mandate、order gate、halt、fail-closed 和 audit log。[Agent 安全边界](https://github.com/HKUDS/Vibe-Trading/blob/1907e47d31d72f34bc2c87e0e5c4f750c83da59d/AGENT_CONTRIBUTOR_GUIDE.md#L41-L55) · [写操作门禁](https://github.com/HKUDS/Vibe-Trading/blob/1907e47d31d72f34bc2c87e0e5c4f750c83da59d/AGENT_CONTRIBUTOR_GUIDE.md#L98-L110)

应借鉴：

- `Hypothesis` 是一级持久对象，不是聊天过程中的临时文字；
- 每个判断必须链接证据、计算产物、回测和失效条件；
- 结论允许进入 `rejected`，失败研究也要保留；
- 数字结论必须来自本次工具结果或确定性计算；
- 研究默认只读，任何外部写入、发布、告警扩散和交易执行另设审批。

不能直接照搬：

- 它的主干更偏市场数据、因子、策略和回测，并未原生定义“地缘政治/政策 → 国家/区域 → 商品/产业节点 → 公司”的语义传导合同；
- 假设登记和 run card 能证明“做过什么”，不能证明自然语言因果链本身正确；
- 通用持久记忆不能替代 Graphiti 的双时点事实、冲突事实和实体关系治理。

### 1.2 FinRobot：让 Agent 负责判断，让代码负责数字

FinRobot 当前官方 README 把桌面版研究流描述为 Lead Agent 编排数据、分析、建模、综合和报告五类角色，再由 bull、bear、judge 三个角色完成对抗式审议。[多 Agent 结构](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/README.md#L67-L89)

更重要的是，它明确提出 **Deterministic Compute, LLM Narration**：DCF、DDM、LBO、WACC、可比公司和 Monte Carlo 等数字由 Python 计算路径产生，LLM 只负责推理、综合、解释和写作，产物保留 provenance。[数值与叙述分离](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/README.md#L91-L103) 官方 README 也将系统概括为 9 个 Agent、7 条研究流水线、30 个纯 Python 计算算子和多数据源 failover。[代码库能力快照](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/README.md#L104-L113)

仓库中的旧版 AutoGen 工作流同样体现“Agent 配置 + profile + toolkit + proxy”的组合方式，并提供单 Agent、RAG、Shadow 和带 Leader 的多 Agent 形态。[Agent 与工具注册](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/finrobot/agents/workflow.py#L22-L103) · [多 Agent 基类](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/finrobot/agents/workflow.py#L269-L349) · [带 Leader 的多 Agent](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/finrobot/agents/workflow.py#L397-L421)

公司研究管线会先抓取财务数据，生成预测、DCF 和同行比较，再由专门 Agent 形成投资逻辑、风险、估值与报告。[公司研究管线](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/README.md#L163-L186) `ValuationEngine` 在代码中实现 EV/EBITDA、同行比较和 DCF，并综合多种估值结果；`SensitivityAnalyzer` 对收入增长、利润率和置信区间做确定性分析。[估值引擎](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/finrobot_equity/core/src/modules/valuation_engine.py#L30-L47) · [DCF 与估值综合](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/finrobot_equity/core/src/modules/valuation_engine.py#L203-L327) · [敏感性分析](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/finrobot_equity/core/src/modules/sensitivity_analyzer.py#L29-L61)

应借鉴：

- 将“采集事实、建模、估值、反方审议、最终综合”拆成不同责任主体；
- LLM 不计算价格目标、异常收益、暴露权重、概率或估值，最多选择参数并解释计算结果；
- Bull 和 Bear 使用同一事实包独立工作，Judge 必须读取双方以及验证 Agent 的产物；
- 研究报告是结构化计算与证据的视图，不是权威事实存储。

不能直接照搬：

- 公开 equity pipeline 以单公司财务、新闻、同行和报告为中心，宏观到产业链的跨层传播不是主干；
- 代码中的新闻/催化剂处理主要依靠关键词、来源启发式和固定权重，例如事件类型、情绪、影响等级与概率由规则组合得到，适合原型，不足以成为生产事件本体或概率校准器。[催化剂分类和权重](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/finrobot_equity/core/src/modules/catalyst_analyzer.py#L111-L174) · [加权影响](https://github.com/AI4Finance-Foundation/FinRobot/blob/01ed408326f1d4ec2460596dee10858faf0f69af/finrobot_equity/core/src/modules/catalyst_analyzer.py#L265-L300)
- 公司财务预测和 DCF 属于情景模型，不等价于经过 PIT 横截面或事件窗口回测的证券收益预测；
- 多 Agent 辩论提高观点覆盖，不天然提高预测准确率，必须由独立验真层裁决。

### 1.3 K-Quant：把动态知识投影成可学习、可解释的关系

K-Quant 把平台分为动态金融知识库、量化投资和 XAI/评估三部分。动态知识模块包括演化知识抽取、时序记录链接与冲突消解、基于时序模式规则的动态更新；量化模块将 KB 关系提取为 relational matrix，作为股票预测的另类数据，再提供动态 ensemble 和增量学习；解释模块寻找关系图中最相关的股票并评估预测与解释模型组合。[K-Quant 总体设计](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/README.md#L10-L67)

它的知识单元采用 `(entity1, relation, entity2, timestamp)` 四元组；HiDy 数据按 Macro、Meso、Micro、Others 四个分支组织，包含多类实体与关系。[HiDy 层级与四元组](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/README.md#L105-L115) 公司关系抽取也显式输出带 timestamp 的公司关系。[动态关系抽取合同](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/extraction/README.md#L1-L4)

其 DART 融合代码会在时间邻近和文本相似条件下合并事件，并结合来源、领域丰富度、来源支持情况计算 veracity/confidence；这证明“相同事件聚合”和“事实可信度”应是独立步骤，而不是由一次 LLM 摘要隐式完成。[事件去重条件](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/fusion/DART.py#L195-L232) · [多来源支持与置信初始化](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/fusion/DART.py#L287-L358)

知识更新使用时序随机游走和规则置信度：路径只允许沿不晚于当前时间的边移动，候选分数同时考虑规则 support/confidence 与时间差。[时序路径约束](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/knowledge%20update/temporal_walk.py#L43-L114) · [规则和时间衰减评分](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/knowledge%20update/score_functions.py#L4-L59)

模型侧提供 MLP、GRU、LSTM、GAT 等基础模型，以及 HIST、RSR、relation-GAT、KEnhance 等知识增强模型；关系模型直接读取 `stock2stock_matrix` 的关系维度，预测后计算 IC、Rank IC 并可进入 Qlib/Backtrader 回测。[模型与关系输入](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/Model/model_pool/README.md#L32-L47) · [关系矩阵进入模型](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/Model/model_pool/exp/learn.py#L126-L158) · [预测与回测](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/Model/model_pool/README.md#L64-L84) 它还提供动态 ensemble、梯度增量学习和 DoubleAdapt，用于处理市场分布漂移。[ensemble 与增量学习](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/Model/model_pool/README.md#L86-L117)

应借鉴：

- 事件、实体和关系必须带时间，图谱要允许演化而非只存当前真值；
- 将图关系投影为按决策时点生成的稀疏关系张量或路径特征，训练模型不直接依赖在线图遍历；
- 图关系既是预测输入，也是解释输入；解释应能回到“哪些关系、哪些邻居、哪些路径贡献了结果”；
- 关系、事件效应和模型权重都需要衰减、增量更新和漂移监控。

不能直接照搬：

- 四元组只有一个 timestamp，不能完整表达“现实何时发生”和“系统何时知道”两个时间轴；
- 现有关系矩阵示例将同行、合作、供应、持股等关系拼接成数组，但没有定义面向宏观政策、商品、产业链节点和不同证券类型的统一传导语义。[关系矩阵构建示例](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/GraphDatabase/build_relation_data.py#L138-L231)
- README 明确提示知识增强模型训练和推理需要保持相同关系文件结构，动态知识需要手动覆盖更新文件，说明其公开工程尚不是自动化的双时点特征平台。[动态关系文件限制](https://github.com/K-Quant/K-Quant/blob/1280959c47166e5d94fa3fa028a0ac5dead64133/Model/model_pool/README.md#L79-L84)
- 它是研究代码，不提供 Codex/Claude Code/Agno 所需的工具权限、审批、会话恢复和 Agent 产物治理。

## 2. 融合后的分层架构

建议使用六层架构。LLM 只能跨层调用受控工具，不能绕过事实、计算和验证层直接产生最终评级。

```text
┌────────────────────────────────────────────────────────────┐
│ L6 交付与监控：研究结论、风险状态、失效条件、再研究触发器 │
├────────────────────────────────────────────────────────────┤
│ L5 审议与治理：Bull / Bear / Risk / Judge / 人工审批       │
├────────────────────────────────────────────────────────────┤
│ L4 验真与预测：事件研究、PIT 回测、横截面模型、估值、压力测试│
├────────────────────────────────────────────────────────────┤
│ L3 传导与暴露：宏观→中观→微观路径、资产映射、多周期假设    │
├────────────────────────────────────────────────────────────┤
│ L2 事件语义：去重、归一化、事实/主张/观点/假设隔离         │
├────────────────────────────────────────────────────────────┤
│ L1 Graphiti：原始证据、双时点事实、实体身份、冲突与版本历史 │
└────────────────────────────────────────────────────────────┘
```

### L1：Graphiti 是知识与数据基础设施，不是收益预测模型

Graphiti 应保存：原始文档和片段、来源、实体身份、事件、关系、观测值、修订历史、冲突记录、Agent 产物引用。它回答的是：

- 在 `decision_at` 时刻系统已经知道哪些内容？
- 这些内容来自哪里、何时发布、是否被修订或反驳？
- 某事件与哪些国家、区域、产业节点、商品、公司、证券相连？

Graphiti 官方将其定位为可增量更新的 temporal Context Graph，支持实体、关系、事实失效以及时间、全文、语义和图检索；MCP 工具也显式区分 episode 的摄入时间和事件参考时间，并让事实携带 `valid_at / invalid_at`。[Graphiti Overview](https://help.getzep.com/graphiti/getting-started/overview) · [Graphiti MCP Server](https://github.com/getzep/graphiti/blob/main/mcp_server/src/graphiti_mcp_server.py)

但 Graphiti 的摄入时间不天然等于资本市场最早可知时间。例如历史公告今天补录时，`ingested_at` 是今天，公告的 `known_at` 却应是历史发布日期；存在盘中、盘后、地区和交易所差异时还需更细的可用性规则。因此 `published_at / known_at / decision_at` 应作为投研领域合同显式保存和校验。Graphiti 不直接回答“未来收益是多少”。收益预测属于 L4，观点综合属于 L5。

### L2：事件层必须分离事实、主张、观点和推导

禁止把一段 LLM 总结同时当作事实和投资结论。建议至少分成六类对象：

| 对象 | 含义 | 是否可以被后续覆盖 |
|---|---|---|
| `SourceObservation` | 来源在某时刻说了什么，保留原文与 URI | 不覆盖，只追加 |
| `EventFact` | 经归一化、可定位时间和实体的事实 | 不覆盖；用版本和有效期修订 |
| `Claim` | 公司、政府、媒体、分析师等主体的主张 | 不提升为事实；记录主张者 |
| `Interpretation` | Agent 对事实含义的解释 | 可竞争、可撤销 |
| `Hypothesis` | 可验真的传导或收益假设 | 有生命周期和失效条件 |
| `Forecast` | 针对资产和 horizon 的概率/区间输出 | 到期后冻结并评分 |

事实对象至少需要两个时间：

- `valid_at / event_start / event_end`：现实世界发生或有效的时间；
- `published_at / known_at / ingested_at`：市场和系统最早能知道的时间。

任何 `as_of=T` 查询只能读取 `known_at <= T` 的观察、当时有效的实体映射和截至 T 已发布的修订。事后更正不能回写成“当时已知”。

### L3：从事件到资产的传导不是一条边，而是一组可竞争路径

统一传导骨架：

```text
Event
  → 国家/区域约束或激励
  → 利率 / 汇率 / 财政 / 监管 / 贸易 / 能源 / 物流 / 供需机制
  → 商品或产业链节点
  → 板块 / 概念 / 公司经营暴露
  → 收入 / 成本 / 产能 / 库存 / 订单 / 资本开支 / 风险溢价
  → 证券价格、波动、流动性和可持有性
```

每条 `TransmissionPath` 必须携带：

```yaml
path_id: path_...
decision_at: 2026-08-22T10:00:00+08:00
source_event_ids: [evt_...]
steps:
  - from: country_policy
    relation: changes_export_constraint
    to: chain_node
    direction: negative
    lag_range: [0d, 30d]
    persistence: medium
    condition: "替代来源未能在窗口内放量"
    evidence_ids: [obs_...]
confidence: 0.62
counter_path_ids: [path_...]
falsifiers:
  - "主要替代供应商交付周期恢复到历史区间"
```

方向、强度和时滞不能只由 LLM 给一个分数。正确流程是：LLM 提出候选路径，图查询确认实体和关系，确定性代码计算暴露，历史事件研究校准方向/窗口，验证 Agent 输出置信区间和缺失证据。

### L4：预测必须是“对象 × horizon × 指标”的可评分合同

“利好”“长期看好”无法验真。每个 Forecast 至少定义：

- 研究对象与可交易标识；
- `decision_at` 和允许使用的数据快照；
- horizon 和到期日；
- 预测指标、benchmark 和中性化方式；
- 点预测、区间或概率分布；
- 基准模型；
- 传导路径、证据和关键假设；
- 失效条件；
- 事后评分规则。

### L5-L6：多 Agent 负责形成审议记录，不替代证据和模型

Agent 的最终产物应是“基于哪些事实、通过哪些路径、在哪个 horizon、相对于什么 benchmark、有什么概率和风险”的研究合同。人类审批的是合同和证据，不是 Agent 的隐藏思维过程。

## 3. Agent DAG、工具权限与审批

### 3.1 建议 DAG

```text
Trigger / Research Request
          │
          ▼
Research Director ───────────────┐
          │                      │
          ▼                      │
PIT Guardian + Event Curator     │
          │                      │
   ┌──────┴─────────┐            │
   ▼                ▼            │
Macro/Policy     Storyline       │
Analyst          Resolver        │
   └──────┬─────────┘            │
          ▼                      │
Industry-Chain Mapper            │
          │                      │
   ┌──────┼────────┬────────┐    │
   ▼      ▼        ▼        ▼    │
Sector  Concept  Commodity Company Exposure
Agent   Agent    Agent     Agent  │
   └──────┴────────┴────────┘    │
          │                      │
   ┌──────┴──────────┐           │
   ▼                 ▼           │
Quant Validator   Fundamental/   │
                  Valuation      │
   └──────┬──────────┘           │
      ┌───┴────┐                 │
      ▼        ▼                 │
    Bull      Bear               │
      └───┬────┘                 │
          ▼                      │
Risk & Falsification             │
          │                      │
          ▼                      │
Judge / Research Synthesizer ◄───┘
          │
          ▼
Human Approval → Publish / Monitor
                         │
                         ▼
                    Outcome Scorer
```

关键依赖规则：

- `PIT Guardian` 失败，所有下游 fail closed；
- `Industry-Chain Mapper` 必须同时输出主路径和至少一条反向/替代路径；
- 多资产 Agent 只计算本对象暴露，不直接读取彼此最终评级，避免结论串扰；
- `Bull` 与 `Bear` 使用相同冻结事实包并行工作；
- `Judge` 只有在 Quant、Bull、Bear、Risk 都完成后才能运行；
- 任何“证据不足”都应成为合法终态，不强制生成评级。

### 3.2 Agent 不是人格 Prompt，而是可测试的执行合同

每个 Agent 应以版本化配置定义：

```yaml
agent_id: industry_chain_mapper
version: 1.0.0
objective: "生成事件到产业节点和公司的候选传导路径"
input_schemas: [FactPacketV1, EntitySnapshotV1]
output_schema: TransmissionPathSetV1
allowed_tools:
  - graphiti.search_as_of
  - graphiti.get_neighbors_as_of
  - exposure.calculate
  - artifact.read
denied_tools:
  - graphiti.write_fact
  - publish.external
  - broker.*
budgets:
  max_tool_calls: 20
  max_wall_seconds: 300
completion_gates:
  - every_path_has_evidence
  - every_path_has_falsifier
  - counter_path_count_gte_1
```

Codex、Claude Code 和 Agno 只需实现同一 Agent/Tool/Artifact 协议；方法论不应绑定某个框架的 memory 或 chain-of-thought 格式。

### 3.3 权限分级

| 等级 | 能力 | 默认审批 |
|---|---|---|
| R0 | 读取冻结事实包和本地研究产物 | 自动 |
| R1 | Graphiti `as_of` 查询、行情/公告/宏观数据读取 | 自动，审计 |
| C1 | 确定性计算、特征物化、回测、压力测试 | 自动，资源限额 |
| W1 | 写入 Interpretation/Hypothesis/Forecast/Monitor | 自动或批量审批；不能写 EventFact |
| W2 | 修改事实归一化、实体合并、来源评级 | 数据管理员审批 |
| E1 | 对外发布研究、发送大范围告警 | 人工审批 |
| E2 | 交易或资金相关操作 | 不属于本 Harness；独立系统和授权 |

Agent 永远不能直接修改已确认 `EventFact`。它只能提出 `FactCandidate`，由确定性校验和数据治理流程审核后进入事实层。

## 4. 多周期研究方法

不同 horizon 对同一事件可以方向相反。不得用一份“综合看多/看空”覆盖全部周期。

下表窗口是初始研究模板，不是全局硬编码。实际 horizon 必须按“事件类型 × 传导变量 × 研究对象 × 市场机制”配置；同一事件对商品现货、公司订单、利润和证券价格的起效与衰减时间通常不同。

| 周期 | 典型窗口 | 主要机制 | 重点输出 | 核心验真 |
|---|---|---|---|---|
| 短期 | 0-5 个交易日 | 意外度、关注扩散、流动性、仓位、交易制度 | 异常收益/波动概率、事件衰减半衰期、跳空和回撤风险 | 事件研究、AR/CAR、成交与滑点、next-open |
| 中期 | 1-3 个月 | 订单、库存、价格传导、盈利预期修正、政策执行 | 行业中性超额收益、盈利修正、节点景气状态 | Walk-Forward、横截面 IC/Rank IC、分层组合 |
| 长期 | 6-36 个月 | 产能、资本开支、技术替代、市场份额、ROIC、估值重估 | 情景现金流、可持有条件、永久损失风险 | 情景估值、敏感性、基本面兑现、回撤/稀释/治理 |

建议同一研究对象输出三个独立 Forecast：

```yaml
short_term:
  horizon: 5_trading_days
  target: benchmark_adjusted_return
  probability_positive: 0.58
  decay_half_life_days: 2.0
medium_term:
  horizon: 60_trading_days
  target: industry_neutral_excess_return
  expected_range: [-0.04, 0.09]
long_term:
  horizon: 24_months
  target: thesis_state
  states: {strengthening: 0.35, unchanged: 0.40, weakening: 0.25}
```

这些数值必须由已登记的统计/估值工具生成。LLM 可以解释，不可以凭语言直接填写。

## 5. 板块、概念、商品与个股的统一研究合同

### 5.1 公共合同

```yaml
research_id: research_...
object:
  type: chain_node | sector | stock_concept | commodity_index | company_stock
  canonical_id: ...
  tradable_id: ...
decision_at: ...
universe_snapshot_id: ...
fact_packet_id: ...
event_ids: [...]
transmission_paths:
  main: [...]
  counter: [...]
exposure:
  method: ...
  value: ...
  confidence: ...
horizons:
  short: ForecastV1
  medium: ForecastV1
  long: ForecastV1
market_pricing:
  benchmark: ...
  valuation_or_positioning: ...
risks: [...]
falsifiers: [...]
missing_evidence: [...]
validation_artifacts: [...]
status: exploring | testing | validated | rejected | monitoring | stale
method_versions:
  agent_specs: {...}
  model_ids: [...]
  prompt_hashes: [...]
  tool_versions: {...}
```

### 5.2 各对象的差异化必填项

| 对象 | 必填暴露与状态 | 特有风险 |
|---|---|---|
| 产业链节点/板块 | 产能、产量、库存、价格、开工率、交付周期、供需缺口、上下游议价 | 替代技术、扩产快于需求、口径过宽 |
| 股票概念 | 成分股 PIT 快照、纯度、业务收入暴露、覆盖广度、重叠度、拥挤度 | 概念漂移、主题炒作、成分事后调整 |
| 商品指数 | 现货/期货口径、库存、期限结构、产区、运输、汇率和政策暴露 | 基差、合约换月、行政干预、地域错配 |
| 公司个股 | 收入/成本/产能/客户/供应商/地区暴露、财务质量、估值、流动性、治理 | 估值已反映、融资稀释、客户集中、执行失败 |

“可持有”不应是永久标签，而是带期限和条件的研究状态：

- `candidate`：存在可验证假设，证据和估值尚未通过门禁；
- `research_hold`：中长期 thesis 仍成立，价格与风险条件处于合同范围；
- `watch`：方向可能正确但时点、估值或证据不足；
- `risk`：关键路径正在弱化或尾部风险超过阈值；
- `invalidated`：预先登记的 falsifier 已发生；
- `stale`：事实、估值或模型超过新鲜度 SLA，禁止继续沿用旧结论。

## 6. Graphiti 中的数据边界与投影方式

### 6.1 建议保存的核心对象

- `SourceDocument / SourceObservation`
- `EventFact / EventCluster / Storyline`
- `Country / Region / Policy / Institution`
- `Commodity / CommodityIndex`
- `IndustryChain / ChainNode / Sector / StockConcept`
- `Company / Security`
- `MetricObservation`
- `Claim / Interpretation / Hypothesis / Forecast`
- `TransmissionPath / ExposureSnapshot`
- `ResearchRun / ValidationArtifact / Outcome`

### 6.2 Graphiti 中必须禁止的混写

- 不把 `LLM: 某政策利好光伏` 写成 EventFact；
- 不把证券涨跌后的归因倒写为事件发生时已知的事实；
- 不用 Storyline 当前最终摘要覆盖历史版本；
- 不把概念当前成分股用于历史回测；
- 不让模型预测结果反向提高源事实的可信度；
- 不把 Agent 共识当成统计显著性。

### 6.3 模型投影而不是在线图遍历

训练/回测时从 Graphiti 生成不可变 `FeatureSnapshot`：

```text
(security_id, decision_date)
  ├─ event_type × direction × decay features
  ├─ storyline persistence / novelty / contradiction features
  ├─ macro-country-region exposure features
  ├─ upstream/downstream path exposure features
  ├─ commodity price/inventory features
  ├─ concept breadth/purity/crowding features
  └─ company fundamental/valuation features
```

同时生成当日稀疏关系张量：

```text
R[t, source_asset, target_asset, relation_type]
```

K-Quant 已证明将关系矩阵作为 relation-GAT 等模型输入是可行范式，但本系统应按 `decision_at` 每日生成并版本化关系快照，而不是覆盖一个“最新关系文件”。

## 7. 验真、回测与持续监控

### 7.1 四级验真阶梯

1. **事实验真**：来源身份、发布时间、实体消歧、重复事件、冲突、修订和引用完整性。
2. **传导验真**：路径每一步是否有证据；方向、时滞和条件是否来自历史或确定性暴露计算；是否存在替代路径。
3. **预测验真**：事件窗口、横截面、Walk-Forward、随机对照、Bootstrap、成本和容量测试。
4. **组合验真**：相关性、集中度、尾部风险、回撤、流动性和不同宏观 regime 的稳定性。

### 7.2 必须预注册的实验

每次验证前冻结：

- 事件族定义和 inclusion/exclusion；
- `known_at` 规则和执行时点；
- universe 的 PIT 成分；
- benchmark 和行业/风格中性化；
- label horizon；
- 交易成本、滑点、涨跌停/T+1 等市场约束；
- train/validation/test 或滚动窗口；
- baseline、主要指标和通过阈值；
- 多重检验控制；
- 失败条件。

Vibe-Trading 的假设生命周期、validation 与 run card 可以直接转化为上述研究治理结构，但事件信号、产业链暴露和 Graphiti 快照必须由本系统补齐。

### 7.3 最小对照矩阵

每个事件驱动模型至少比较：

| 实验 | 输入 |
|---|---|
| B0 | 价格/成交/基础风险因子 |
| B1 | B0 + 事件特征 |
| B2 | B0 + 产业链/概念关系特征 |
| B3 | B0 + 事件 + 关系传导 |
| B4 | B3 + LLM Interpretation 特征 |
| Placebo | 打乱事件时间或实体映射 |

只有 B3 对 B1/B2/B0 在样本外稳定增量，才能说明“事件经过产业链传导”提供了额外价值；如果只有 B4 有效，还必须排查语言模型是否使用了事后信息或市场价格暗示。

### 7.4 监控闭环

每个已发布研究结论生成 `MonitorContract`：

```yaml
monitor_id: monitor_...
research_id: research_...
refresh_sla: 1d
triggers:
  - new_event_on_storyline
  - source_claim_retracted
  - path_confidence_drop_gt_0.15
  - commodity_inventory_cross_threshold
  - earnings_revision_cross_threshold
  - valuation_exit_range
  - forecast_expired
on_trigger:
  - freeze_new_fact_packet
  - rerun_affected_subgraph
  - compare_thesis_diff
  - require_approval_if_rating_changes
```

Forecast 到期后必须生成 `OutcomeCard`，记录真实结果、benchmark、误差、路径是否兑现、哪个 Agent/模型贡献或误导了结论。结果用于校准事件族、路径先验和模型，不允许删除失败样本。

## 8. 必备产物，而不是只保存对话

| 产物 | 作用 |
|---|---|
| `fact_packet.json` | 冻结 `decision_at` 时可知事实和来源 |
| `event_card.json` | 事件归一化、范围、意外度、持续性和冲突 |
| `transmission_paths.json` | 主路径、反路径、证据、时滞与 falsifier |
| `exposure_snapshot.parquet` | 多资产确定性暴露 |
| `feature_snapshot.manifest.json` | PIT 特征和关系张量版本 |
| `research_contract.json` | 对象 × horizon 的统一研究定义 |
| `forecast_card.json` | 概率、区间、基准、到期与评分规则 |
| `validation_run_card.json` | 配置/数据/代码/模型哈希与结果 |
| `bull_memo.md / bear_memo.md` | 同一事实包上的独立论证 |
| `risk_register.json` | 风险、触发器、缓解和 owner |
| `decision_memo.md` | Judge 综合与未解决分歧 |
| `monitor_contract.json` | 后续监控 SLA 和再研究触发 |
| `outcome_card.json` | 到期验真和误差归因 |

每个产物都应带 `run_id`、输入产物 ID、schema 版本、工具版本、模型 ID、prompt hash、生成时间和内容哈希。这样切换 Codex、Claude Code 或 Agno 时，研究合同仍可重放。

## 9. 分阶段落地

### 阶段 0：先建立事实与时间门禁

目标：任何研究都能回答“当时系统知道什么”。

- 给 Event、Storyline、关系和指标补齐 `valid_at` 与 `known_at`；
- 建立 SourceObservation、EventFact、Claim、Interpretation、Hypothesis 边界；
- 提供 Graphiti `search_as_of`、`neighbors_as_of`、`snapshot` 三类只读工具；
- 实现 FactPacket 冻结和引用校验；
- 禁止 Agent 直接写事实。

验收：随机抽取历史日期，无法检索到其后发布或修订的数据。

### 阶段 1：单事件、单跳、多资产研究合同

目标：先做可验真的窄闭环。

- 选择 3-5 类高质量事件，如政策发布、制裁/关税、产能事故、价格调整、业绩预告；
- 只做 Event → ChainNode/Commodity → Company/Security 的一跳或两跳传播；
- 生成板块、概念、商品和个股四类合同；
- 建立短期事件研究和中期横截面 baseline；
- 输出 Vibe 式 hypothesis/run card。

验收：B1/B2/B3/Placebo 对照可自动重跑，全部输入满足 PIT。

### 阶段 2：Agent DAG 与对抗审议

目标：引入 FinRobot 式角色分工，但保持确定性计算边界。

- 上线 Director、PIT Guardian、Event Curator、Chain Mapper、Exposure、Quant、Bull、Bear、Risk、Judge；
- 所有 Agent 采用结构化输入输出和工具白名单；
- 估值、收益、暴露、概率和风险指标只由工具产生；
- 结论变化需人工审批；
- 对 Codex、Claude Code、Agno 运行同一 golden cases，比较产物而不是比较隐藏思维链。

验收：任何 Agent 失败都能局部重跑；Judge 无法绕过缺失上游产物生成结论。

### 阶段 3：时序关系模型和增量学习

目标：引入 K-Quant 式关系张量和漂移适应。

- 每日从 Graphiti 生成 PIT 关系快照和路径特征；
- 比较非图模型、静态关系模型和时序关系模型；
- 引入事件/关系衰减、模型漂移监控和滚动重训；
- 图解释输出必须回链到原始证据和路径，不只输出邻居权重。

验收：关系模型在多个滚动窗口、市场 regime 和成本假设下对基线有稳定样本外增量。

### 阶段 4：长周期 thesis 与持续学习

目标：将研究变成持续更新的决策支持系统。

- 长期 Forecast 绑定情景财务、估值和可持有条件；
- MonitorContract 自动检测新事件、反驳、估值和基本面变化；
- OutcomeCard 校准事件族、路径时滞、Agent 可靠度和模型权重；
- 建立研究方法版本晋级：shadow → experimental → validated → production；
- 生产晋级必须通过合规、数据许可、PIT、回放和人工审批门禁。

## 10. 最终方法论

这套系统的核心不是“让 LLM 更会分析股票”，而是把投资研究改造成一条受约束的知识生产线：

1. **事件先成为有来源、有双时点、有冲突记录的事实对象；**
2. **事实通过可竞争、可证伪的宏观—产业—公司传导路径连接到资产；**
3. **板块、概念、商品和个股使用同一研究合同，但保留各自暴露和风险字段；**
4. **短、中、长期分别预测和评分，不用一个模糊评级覆盖所有周期；**
5. **LLM 提出路径、调用工具、解释和反驳，数值由代码和统计模型计算；**
6. **每个结论必须经过 PIT、事件研究、样本外回测、压力测试和反方审议；**
7. **Graphiti 保存事实与研究谱系，Agent 运行时可以替换；**
8. **失败假设、反例和真实结果进入长期记忆，持续校准而不是被删除。**

因此，最值得从三个项目继承的不是具体页面、模型或框架，而是三条纪律：

- 从 K-Quant 继承“知识必须随时间演化，并能投影成模型输入与解释”；
- 从 FinRobot 继承“Agent 分工明确，代码算数字，LLM 写解释”；
- 从 Vibe-Trading 继承“假设必须可证伪、可回测、可重放、可否决、可监控”。

这三条纪律共同构成面向 Codex、Claude Code、Agno + Graphiti 的股票投研 Agent Harness。
