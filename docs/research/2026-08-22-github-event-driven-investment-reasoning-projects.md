# GitHub 股票投研、事件驱动与预测分析项目调研

> 调研时间：2026-08-22 11:11（Asia/Shanghai）  
> 目标：寻找可用于股票投研，尤其是“事件 → 产业链/公司基本面 → 预测 → 回测”闭环的高星开源项目。  
> 范围：项目筛选不以 Graphiti 或当前技术栈为维度；现有图谱只在最后作为可消费的数据基础讨论。  
> 来源：仅使用项目官方 GitHub 仓库、README、源码目录、Release 和 GitHub REST API。Stars 是抓取时点快照，会继续变化。

## 结论

截至调研时，GitHub 上**没有一个高星、成熟项目同时完成**以下全链路：

1. 从公告、新闻和宏观信息中识别金融事件；
2. 沿产业链、公司、概念和地域关系推导影响范围与方向；
3. 把事件及其传导转化为可训练的时点特征；
4. 预测未来超额收益、基本面或产业节点指标；
5. 在严格 point-in-time、含交易成本的环境中回测；
6. 生成带证据和不确定性的投研解释。

高星项目通常只覆盖其中一层：Qlib 侧重预测与回测，FinGPT 侧重金融文本理解，RD-Agent 侧重因子/模型自动研发，FinRobot 与 TradingAgents 侧重 LLM 投研编排，OpenBB 侧重数据接入，FinRL/TradeMaster 侧重交易策略与强化学习。真正把**时序金融知识图谱与股票预测**放在同一框架内的 K-Quant、YiJinJing、FGSMP 等项目，社区规模和工程成熟度反而较低。[Qlib](https://github.com/microsoft/qlib) · [FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) · [K-Quant](https://github.com/K-Quant/K-Quant)

因此，最合适的路线不是整体引入某个“股票 Agent”，而是复用一组相互独立的能力：

- **预测与回测主干：Qlib**；
- **事件文本理解：FinGPT 的任务定义、数据处理和模型作为 baseline**；
- **事件效应校准：EventStudy 思路或同等的 Python 实现**；
- **时点安全的 LLM/Agent 回测：FINSABER**；
- **因子与模型自动研发：RD-Agent，待基线稳定后再接入**；
- **基本面报告与多角色审议：FinRobot 或 TradingAgents，只作为解释/挑战层，不作为预测事实来源**；
- **图关系进入预测的设计参考：K-Quant 与 Qlib HIST，不直接把低成熟度仓库当生产底座**。

## 先区分两个容易混淆的“事件驱动”

GitHub 量化项目中的 `event-driven` 有两种完全不同的含义：

| 含义 | 例子 | 是否解决本次问题 |
|---|---|---|
| 业务事件驱动预测 | 财报预警、扩产、制裁、事故、价格变化，经公司/产业链传导后预测未来影响 | 是 |
| 软件事件循环驱动交易/回测 | 市场开盘、收盘、Bar、订单和成交事件触发策略代码 | 只解决回测执行，不理解业务事件 |

例如 qf-lib 自称 event-driven backtester，指的是回测架构模拟市场开收盘等事件，并不等于它能理解财报、产业链或政策事件。[qf-lib README](https://github.com/quarkfin/qf-lib#what-is-qf-lib)

本调研把“真正事件驱动预测”定义为：项目能将新闻、公告或结构化事件作为可观测输入，估计其对未来收益、风险或基本面的方向、幅度、期限或概率。仅有 LLM 讨论、新闻摘要、情绪标签、交易 Agent 或软件事件循环，不视为完整事件预测。

## GitHub 快照与成熟度

下表按项目对当前目标的适配度分组，不按 stars 机械排序。`最近推送` 是 GitHub API 的 `pushed_at`，只能证明仓库近期有引用更新，不能单独证明发布质量；有 Release 的项目同时列出最新正式版本。

### 核心候选

| 项目 | Stars | 许可 | 最近推送 / Release | 真正覆盖的层次 | 判断 |
|---|---:|---|---|---|---|
| [microsoft/qlib](https://github.com/microsoft/qlib) | 47,818 | MIT | 2026-07-23；[v0.9.7](https://github.com/microsoft/qlib/releases/tag/v0.9.7) | 监督学习、市场动态、预测、组合、回测、评估、PIT 数据 | **P0：预测与回测主干** |
| [AI4Finance/FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) | 21,129 | MIT | 2026-08-02；[v1.0.0](https://github.com/AI4Finance-Foundation/FinGPT/releases/tag/v1.0.0) | 金融情绪、关系、NER、标题分析、新闻+基本面的方向预测实验 | **P0：事件理解 baseline** |
| [microsoft/RD-Agent](https://github.com/microsoft/RD-Agent) | 14,304 | MIT | 2026-08-04；[v0.8.0](https://github.com/microsoft/RD-Agent/releases/tag/v0.8.0) | 基于 Qlib 的因子与模型联合自动研发、报告因子提取 | **P1：自动研发层** |
| [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | 31,423 | MIT | 2026-08-21；以仓库当前版本为准 | 自然语言研究、PIT 数据、假设→信号→回测、证据与运行记录 | **P1：投研工作流与审计参考** |
| [AI4Finance/FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) | 7,828 | Apache-2.0 | 2026-07-27；[desktop-v0.1.0](https://github.com/AI4Finance-Foundation/FinRobot/releases/tag/desktop-v0.1.0) | 基本面预测、DCF、同行对比、多 Agent 投研报告 | **P1：研究与解释层** |
| [K-Quant/K-Quant](https://github.com/K-Quant/K-Quant) | 84 | Apache-2.0 | 2025-12-06；无 Release | 时序金融知识库、关系矩阵、股票预测、解释与评估 | **设计最贴近，工程成熟度不足** |
| [waylonli/FINSABER](https://github.com/waylonli/FINSABER) | 143 | Apache-2.0 | 2026-08-05；[v2.0.1](https://github.com/waylonli/FINSABER/releases/tag/v2.0.1) | 新闻/公告/LLM 策略的 PIT、滑点、流动性和成本回测 | **P0：Agent 预测验真层** |
| [sipemu/eventstudy](https://github.com/sipemu/eventstudy) | 11 | AGPL-3.0 | 2026-06-26；无 GitHub Release | AR/CAR/AAR/CAAR、多因子、日内、面板 DiD 事件研究 | **P0 方法参考，不是预测模型** |
| [Nixtla/neuralforecast](https://github.com/Nixtla/neuralforecast) | 4,249 | Apache-2.0 | 2026-08-17；[v3.2.1](https://github.com/Nixtla/neuralforecast/releases/tag/v3.2.1) | 带外生变量的概率时序预测 | **P1：产业节点数值预测** |
| [AI4Finance/FinRL-X](https://github.com/AI4Finance-Foundation/FinRL-Trading) | 3,582 | Apache-2.0 | 2026-05-02；[v1.0.0](https://github.com/AI4Finance-Foundation/FinRL-Trading/releases/tag/v1.0.0) | 选股、配置、风控、回测、纸面/实盘执行 | **P2：信号之后的组合层** |
| [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | 99,184 | Apache-2.0 | 2026-07-18；[v0.3.1](https://github.com/TauricResearch/TradingAgents/releases/tag/v0.3.1) | 新闻/宏观/情绪/基本面/技术多 Agent 辩论和投资决定 | **高星研究编排，不是预测内核** |
| [OpenBB/OpenBB](https://github.com/OpenBB-finance/OpenBB) | 72,129 | AGPL-3.0 | 2026-07-30；2026-04 ODP Release | 多数据源统一 Python/REST/MCP 接入 | **数据层，不是推理或预测模型** |

Stars、许可识别、归档状态和最近推送来自抓取时的官方 GitHub API：[Qlib API](https://api.github.com/repos/microsoft/qlib)、[FinGPT API](https://api.github.com/repos/AI4Finance-Foundation/FinGPT)、[RD-Agent API](https://api.github.com/repos/microsoft/RD-Agent)、[Vibe-Trading API](https://api.github.com/repos/HKUDS/Vibe-Trading)、[FinRobot API](https://api.github.com/repos/AI4Finance-Foundation/FinRobot)、[K-Quant API](https://api.github.com/repos/K-Quant/K-Quant)、[FINSABER API](https://api.github.com/repos/waylonli/FINSABER)、[EventStudy API](https://api.github.com/repos/sipemu/eventstudy)、[NeuralForecast API](https://api.github.com/repos/Nixtla/neuralforecast)、[FinRL-X API](https://api.github.com/repos/AI4Finance-Foundation/FinRL-Trading)、[TradingAgents API](https://api.github.com/repos/TauricResearch/TradingAgents)、[OpenBB API](https://api.github.com/repos/OpenBB-finance/OpenBB)。OpenBB 的 GitHub API 没有正确识别 SPDX，但仓库 README 明确声明 AGPLv3。[OpenBB License 说明](https://github.com/OpenBB-finance/OpenBB#3-license)

## 按适配度排序的详细判断

### 1. Qlib：最值得直接复用的预测与回测底座

Qlib 是本次候选中工程成熟度、股票预测能力和可回测性最均衡的项目。官方框架同时覆盖数据、监督学习、市场动态建模、强化学习、策略执行、组合分析、在线服务和回测；`qrun` 能串起数据集、训练、预测、IC 分析和组合回测。官方文档还单列 Point-In-Time database，适合防止财务数据与事件数据穿越。[Qlib README](https://github.com/microsoft/qlib#framework-of-qlib) · [Qlib 文档目录](https://github.com/microsoft/qlib/blob/main/docs/index.rst) · [Qlib workflow 示例](https://github.com/microsoft/qlib/blob/main/examples/workflow_by_code.py)

Qlib 也不是纯 OHLCV 框架。它允许自定义 DataLoader、DataHandler、Dataset、模型和策略；官方 benchmark 中包含 HIST——一个通过 concept-oriented shared information 做股票趋势预测的图模型入口。因此，产业链、公司概念和事件传播特征可以先投影为 Qlib 每日特征或关系矩阵，再进入 LightGBM、GRU、Transformer、HIST 等模型，而无需把图数据库直接嵌进训练循环。[Qlib Data Layer](https://github.com/microsoft/qlib/blob/main/docs/component/data.rst) · [Qlib HIST benchmark](https://github.com/microsoft/qlib/tree/main/examples/benchmarks/HIST)

它没有解决的部分：事件抽取、事件本体、产业链因果方向、Storyline 合并和证据解释。Qlib 只会学习我们喂进去的时点特征与标签之间的统计关系。因此它应成为**预测/回测主干**，而不是事件推理引擎。

### 2. FinGPT：最适合借鉴事件文本理解，但不能直接充当因果预测器

FinGPT 官方模型与数据覆盖金融情绪、金融关系抽取、标题涨跌分类、NER 和问答；关系抽取标签中还明确包含 `product/material produced`、`manufacturer`、`industry`、`subsidiary`、`headquarters location` 等关系，这些任务对把公告和新闻转为 Event、Company、ChainNode 关系很有参考价值。[FinGPT README：instruction datasets and models](https://github.com/AI4Finance-Foundation/FinGPT#instruction-tuning-datasets-and-models)

FinGPT-Forecaster 以 ticker、历史新闻窗口和最新基本面为输入，生成分析并预测下一周股价方向，证明它确实尝试了“新闻+基本面→方向预测”，而不只是金融问答。[FinGPT-Forecaster](https://github.com/AI4Finance-Foundation/FinGPT/tree/master/fingpt/FinGPT_Forecaster)

但其局限也很明确：

- Forecaster 是单股、新闻窗口驱动的 LLM 预测实验，不是产业链传导模型；
- 模型输出的解释不等于经过事件研究校准的因果效应；
- 其关系类型和训练数据可用作 baseline，但我们的事件本体、中文产业链术语和时点边界仍需自行构建与评估；
- 不应直接把它生成的涨跌理由写回权威事件事实。

最合理的复用层次是：使用其任务拆分、数据格式、评测集构造和开源模型作为事件抽取/情绪/关系 baseline，再与自有 schema 做监督微调或蒸馏。

### 3. RD-Agent：适合在事件特征稳定后自动做因子和模型研发

RD-Agent(Q) 官方定位是基于 Qlib 的数据中心型量化多 Agent 框架，自动进行因子与模型联合优化；它提供 `fin_quant`、`fin_factor`、`fin_model`，也能从财报中提出并实现因子。[RD-Agent Finance Quant Agent](https://github.com/microsoft/RD-Agent/blob/main/docs/scens/quant_agent_fin.rst) · [RD-Agent README](https://github.com/microsoft/RD-Agent#-run-the-application)

它对当前目标的价值不是实时回答“这个事件利好谁”，而是：

- 基于已经 point-in-time 化的事件/产业链特征，自动提出组合、变换和交互项；
- 让候选因子进入固定训练、验证、测试和回测区间；
- 联合搜索模型与特征，而非只让 LLM 写一段主观看法。

RD-Agent 默认量化场景仍围绕 Qlib 日频 price/volume 和预计算 factor 文件，不能直接读取一个动态事件图就得到可靠预测。[RD-Agent factor data template](https://github.com/microsoft/RD-Agent/blob/main/rdagent/scenarios/qlib/experiment/factor_data_template/README.md) 因此应在特征合同、标签与验收指标稳定后再启用，否则 Agent 只会自动化放大数据泄漏、错误标签或无效研究空间。

### 4. Vibe-Trading：内容适配度很高，但更像研究工作台而非单一预测模型

Vibe-Trading 把自然语言研究、point-in-time 数据、研究假设、信号生成、回测和证据记录放在同一工作流中，并覆盖 A/H/美股等研究场景。它对当前项目最有价值的不是替代现有图谱或预测模型，而是借鉴“假设 → 可计算信号 → 走样本外回测 → 保存证据与运行记录”的投研闭环。[Vibe-Trading README](https://github.com/HKUDS/Vibe-Trading)

它仍然是一个快速演进的综合平台，能力覆盖面与现有基础设施重叠较多，也不能因为支持 Agent 和回测就直接推定其内置研究结论有效。建议优先评估其研究合同、PIT 约束、walk-forward 验证和审计记录设计，暂不整体接管现有运行时。

### 5. K-Quant：与“时序知识 → 股票预测”最接近，但只能作为设计和算法参考

K-Quant 的公开设计几乎正面对应本次问题：

- 动态金融知识抽取、时间记录链接、冲突解决与动态更新；
- 知识实例表示为 `(entity1, relation, entity2, timestamp)`；
- 把知识库关系导出为 relational matrix，作为股票预测的 alternative data；
- 提供动态图 ensemble、增量学习、关系图解释和投资组合评估；
- 量化模块建立在 Qlib 上。[K-Quant README](https://github.com/K-Quant/K-Quant)

这说明“先维护时序关系，再投影成每日关系矩阵和特征送入 Qlib”是有公开研究先例的。它尤其值得参考：

- HiDy 的 Macro/Meso/Micro 层级设计；
- 时间四元组与冲突处理；
- 图关系矩阵生成方式；
- 关系图解释器如何指出影响预测的关联公司。

但它只有 84 stars、没有正式 Release，最近推送为 2025-12-06，README 和目录更接近研究平台/论文代码，不足以替代 Qlib、Graphiti 或生产特征平台。结论是：**复用方法和模型，不整体接管运行时**。

### 6. FINSABER：最适合验证 LLM/Agent 的投资预测是否真的有效

FINSABER-2 不是预测模型，而是为传统、机器学习和 LLM 投资策略提供统一评测的框架。它显式处理执行时点、复权 OHLC、滑点、流动性上限、订单拒绝、结构化结果和 LLM 成本；LLM 策略默认 `next_open`，并要求没有精确时间戳的新闻/公告最早在下一交易决策使用，从而避免同日收盘价穿越。[FINSABER README](https://github.com/waylonli/FINSABER) · [LLM-style strategy 与 execution settings](https://github.com/waylonli/FINSABER#implement-an-llm-style-strategy)

这正好可以验证以下 challenger：

- 单纯 LLM 看新闻；
- LLM + Storyline；
- LLM + 产业链邻居；
- 规则/统计事件信号；
- Qlib 模型；
- Agent 辩论后的最终评级。

它不负责训练事件模型，也不负责大规模图查询，但非常适合成为“Agent 说得好听是否等于可交易增量”的验真层。

### 7. EventStudy：用来学习事件影响分布，不是用来直接预测下一只股票

sipemu/eventstudy 实现了经典与现代金融事件研究，包括 Market/Fama-French/Carhart/GARCH 等回报模型，AR、CAR、AAR、CAAR，多种参数/非参数检验，日内事件研究，以及面板 DiD 和 Sun-Abraham 方法。[EventStudy README](https://github.com/sipemu/eventstudy)

它最适合回答：

- 某类事件在不同窗口的平均异常收益是多少；
- 影响何时开始、何时衰减；
- 产业链上游/下游或不同暴露度公司的 CAR 是否显著不同；
- 同类事件在不同市场状态、国家或行业中是否稳定；
- Storyline 的首次事件、确认事件和反转事件是否有不同效应。

它**不能**回答单一新事件下一定涨跌多少；事件研究估计的是历史分布和统计显著性。由于该仓库是 R + AGPL-3.0 且 stars 很低，生产实现可以借鉴方法后在自有 Python 统计层重新实现，是否直接复用代码需单独做许可证判断。

### 8. FinRobot：最适合复用基本面投研和报告工作流

FinRobot 当前公开的 equity research pipeline 能抓取利润表、资产负债表和现金流，执行三年财务预测、DCF 和同行比较，再由八类 Agent 形成投资逻辑、风险与估值报告。[FinRobot README](https://github.com/AI4Finance-Foundation/FinRobot)

它与 Company、IndustryChain、Storyline 的结合点很直接：把图谱中经证据验证的事件、产业链暴露和节点趋势作为额外研究工具输入，再让 Agent 解释这些信息如何影响收入、成本、资本开支和估值假设。

但 FinRobot 的核心是投研自动化与报告生成，不是经过 point-in-time 横截面回测的事件预测器。三年预测、DCF 或 Agent 共识只能作为假设和解释，必须由 Qlib/FINSABER/事件研究层独立验真。

### 9. NeuralForecast：适合预测产业节点指标，不适合直接吃原始事件图

NeuralForecast 提供 30 多种神经时序模型，支持静态、历史和未来外生变量、概率预测、趋势/季节/外生变量解释以及自动模型选择。[NeuralForecast README](https://github.com/Nixtla/neuralforecast)

它适合的目标不是“让模型读新闻”，而是预测：

- 产业节点价格、产量、库存、开工率、交付周期；
- 公司收入、毛利率、订单和资本开支；
- 某类事件的日/周发生强度；
- 地区供给风险或物流指标。

Event/Storyline/ChainNode 必须先编码为按时间对齐的外生变量，例如事件计数、严重度、置信度、传播权重和暴露度。若这些未来外生变量在预测时并不知道，必须严格作为 historical exogenous 使用，不能把事后确认的 Storyline 状态泄漏到未来窗口。

### 10. TradingAgents：高星并不等于有可靠的事件预测模型

TradingAgents 用 LangGraph 组织基本面、情绪、新闻、技术、研究员、交易员、风控和 Portfolio Manager。新闻 Agent 会解释全球新闻与宏观事件，研究员进行多空辩论，最终输出投资决定；最新版本还保存决策日志，并在未来取得真实收益后生成反思。[TradingAgents README](https://github.com/TauricResearch/TradingAgents)

它的价值是多角色研究流程、状态机和 challenge 机制，不是底层预测算法。官方明确提示结果依赖 LLM、温度、时段和数据质量，并具有非确定性。[TradingAgents disclaimer](https://github.com/TauricResearch/TradingAgents#tradingagents-framework) 因此建议只借鉴：

- 分析角色和反方审议；
- 风险 Agent 与 Portfolio Manager 的职责分离；
- 决策日志、事后收益和反思闭环；
- 将自有事件/产业链工具接入 Agent 的接口方式。

不要用它替代时点特征、监督模型、事件效应统计和回测。

### 11. OpenBB：可作为外部数据适配层，但不是本次核心推理方案

OpenBB 的 Open Data Platform 是“connect once, consume everywhere”的数据接入层，可把专有、授权和公开数据统一暴露给 Python、REST、MCP、Excel 和研究面板。[OpenBB README](https://github.com/OpenBB-finance/OpenBB)

如果后续需要统一接入行情、财务、宏观和另类数据，它值得评估；但它本身不提供事件因果传导或股票预测模型。其 AGPLv3 以及各数据供应商的独立授权边界也需要在服务化使用前评估。[OpenBB License](https://github.com/OpenBB-finance/OpenBB#3-license)

## 可作为补充或 baseline 的项目

| 项目 | Stars / 维护 | 能做什么 | 为什么不是首选 |
|---|---|---|---|
| [google-research/timesfm](https://github.com/google-research/timesfm) | 28,078；2026-07-14；Apache-2.0 | 通用时序 foundation model、点/分位数预测、外部协变量 | 非金融、非事件、非关系推理；适合作为数值零样本 baseline |
| [AI4Finance/FinRL](https://github.com/AI4Finance-Foundation/FinRL) | 16,064；2026-07-13；MIT | 金融强化学习环境、数据和策略 | 事件与产业链不是核心；先有可靠信号后才有必要做 RL |
| [TradeMaster](https://github.com/TradeMaster-NTU/TradeMaster) | 3,043；2025-06-04；Apache-2.0 | 多资产市场模拟、13+ RL 算法、评估 | 更偏交易与执行；最近 Release 仍是 2023 年 v1.0.0 |
| [qf-lib](https://github.com/quarkfin/qf-lib) | 954；2026-08-05；Apache-2.0 | 活跃的事件循环回测、避免 look-ahead、报告 | “event-driven”是软件架构，不是业务事件预测 |
| [FinMem](https://github.com/pipiku915/FinMem-LLM-StockTrading) | 945；2024-08-18；MIT | 分层记忆、多源信息、LLM 决策 | 记忆思路与 Storyline 接近，但维护停滞且不是校准预测器 |
| [PIXIU](https://github.com/The-FinAI/PIXIU) | 883；2025-03-04；MIT | 金融 LLM、NLP/股票涨跌数据集和评测 | 主要是数据与 benchmark；子数据集许可各异 |
| [Temporal Relational Stock Ranking](https://github.com/fulifeng/Temporal_Relational_Stock_Ranking) | 527；2021-03-04；AGPL-3.0 | 行业/Wikidata 股票关系 + 时序排名模型 | TensorFlow 1.x 时代论文代码，数据与维护过旧 |
| [ProsusAI/finBERT](https://github.com/ProsusAI/finBERT) | 2,214；2022-09-09；Apache-2.0 | 金融情绪分类 | 只是一项文本标签；FinGPT 覆盖面更广 |

以上 stars、许可与最近推送同样来自官方 API：[TimesFM](https://api.github.com/repos/google-research/timesfm)、[FinRL](https://api.github.com/repos/AI4Finance-Foundation/FinRL)、[TradeMaster](https://api.github.com/repos/TradeMaster-NTU/TradeMaster)、[qf-lib](https://api.github.com/repos/quarkfin/qf-lib)、[FinMem](https://api.github.com/repos/pipiku915/FinMem-LLM-StockTrading)、[PIXIU](https://api.github.com/repos/The-FinAI/PIXIU)、[Temporal Relational Stock Ranking](https://api.github.com/repos/fulifeng/Temporal_Relational_Stock_Ranking)、[FinBERT](https://api.github.com/repos/ProsusAI/finBERT)。

## 明确排除或只观察的项目

### ai-hedge-fund：高星演示，不应误判成成熟预测引擎

[virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) 有 62,979 stars、MIT 许可且近期仍更新，但 README 明确称其为 proof of concept、教育和研究用途，不用于真实交易。它展示 Buffett、Munger 等角色化 Agent 以及回测界面，适合产品演示，不足以证明事件预测有效。[官方 README](https://github.com/virattt/ai-hedge-fund)

### TradingAgents-CN：高星但许可边界不适合作为通用开源底座

[hsliuping/TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN) 有 31,301 stars，但 GitHub API 未识别统一 SPDX；项目 README 说明当前采用混合许可，`app/` 和 `frontend/` 属于需商业授权的专有部分。它对 A 股数据和中文 UI 有参考价值，但不能把 stars 等同于可自由商用的完整开源栈。[官方许可说明](https://github.com/hsliuping/TradingAgents-CN#-重要版权声明与授权说明)

### FGSMP：问题定义很贴近，但无许可且长期停止维护

[melodyqxuan/FGSMP](https://github.com/melodyqxuan/FGSMP) 的论文代码直接用历史行情、新闻和细粒度事件标签预测二元股价走势，问题定义非常相关；但只有 4 stars、无明确许可证，最近推送停留在 2021-03-12，不能直接复用到商业项目。[FGSMP README](https://github.com/melodyqxuan/FGSMP)

### YiJinJing：概念闭环很完整，当前仍是低成熟度 notebook 项目

[CUEB-QF-ZQS/YiJinJing](https://github.com/CUEB-QF-ZQS/YiJinJing) 声明实现“金融事件抽取 → 时序多模态异构图 → MEHGT → 股票/行业短期趋势”，与目标高度重合；但只有 13 stars，核心实现大量位于 notebook，最近推送为 2025-12-06。适合放入算法观察名单，不适合作为生产基础设施。[YiJinJing README](https://github.com/CUEB-QF-ZQS/YiJinJing/blob/main/README_en.md)

## 推荐组合

### 推荐 A：可审计、可回测的主线

这是最推荐的组合：

1. 自有事件与产业链数据负责权威事实、时间和证据；
2. 借鉴 FinGPT 做事件类型、实体关系、情绪和严重度 baseline；
3. 用 EventStudy 方法估计不同事件族的历史异常收益、方向、期限和置信区间；
4. 将事件、Storyline、产业链传播和基本面暴露投影为 point-in-time 日/周特征；
5. 用 Qlib 训练横截面排名、未来超额收益或基本面预测模型，并完成组合回测；
6. 用 FINSABER 单独评测 LLM/Agent 策略，防止把文字表现误当投资能力；
7. 基线稳定后再让 RD-Agent 自动搜索因子和模型。

这条路线把“事实、统计、预测和解释”分开，最符合投研可复现要求。

### 推荐 B：研究报告与投委会式挑战层

在推荐 A 的输出之上增加 FinRobot 或 TradingAgents：

- FinRobot 负责财务预测、DCF、同行比较和长报告；
- TradingAgents 负责多空辩论、风险审查和 Portfolio Manager 决策；
- Agent 只能读取带 `as_of`、来源和模型版本的事实/预测；
- Agent 的观点写入独立 ResearchOpinion，不回写 Event 或 Company 权威事实；
- 每次观点在 FINSABER 或 Qlib 中留存事后收益与失效原因。

这能利用 LLM 自主研究能力，同时避免让 LLM 直接成为不可校准的价格预测器。

### 推荐 C：图关系预测实验

如果希望验证产业链关系是否带来显著增量：

1. 参考 K-Quant，把 Company、ChainNode、IndustryChain、StockConcept 的时点关系导出为每日稀疏关系矩阵；
2. 在 Qlib 中对比无图 baseline、概念关系、产业链一跳、产业链多跳衰减和事件动态图；
3. 先复现 Qlib HIST，再逐步替换其 concept matrix；
4. 用滚动窗口检验 IC、RankIC、行业中性超额收益、换手、最大回撤和跨市场稳定性；
5. 只有在图特征产生稳定样本外增量后，才考虑更复杂的 GNN/动态图模型。

## 如何消费当前已有数据

现有 Graphiti 只是基础设施；真正可复用的是其中的领域数据和时间语义。建议不要让训练模型在线遍历图，而是建立独立、可重放的 Feature Projection：

| 当前数据 | 可投影的预测特征示例 |
|---|---|
| Event | 类型、情绪、严重度、置信度、来源等级、新颖度、`event_at`、`known_at`、衰减值 |
| Storyline | 阶段、持续时长、事件密度、确认/反转次数、来源一致性、最近更新时间 |
| Company | 行业、规模、估值、财务修正、供应链暴露、事件敏感度历史 |
| ChainNode / IndustryChain | 上下游方向、跳数、替代性、集中度、瓶颈度、供需状态、传播衰减 |
| StockConcept | 概念暴露权重、概念拥挤、同概念事件强度、概念内相对强弱 |
| Country / Region | 政策、制裁、汇率、物流、地缘事件强度及公司地域暴露 |

最低数据合同应至少包含：

- `event_at`：事件真实发生时间；
- `known_at`：系统/市场最早可知时间；
- `valid_from` / `valid_to`：关系或状态有效期；
- `source_id` / `source_quality`：证据与质量；
- `entity_id` 与证券映射；
- `revision_id`：后续修订不能覆盖历史视图；
- `feature_as_of`：训练和回测实际使用的快照时间。

没有 `known_at`、历史版本和 point-in-time 截面，再好的 Qlib、RD-Agent 或 LLM 都会把未来修订、事后 Storyline 和最终关系状态泄漏到历史样本中。

## 最终排序

按当前目标的综合适配度排序：

1. **Qlib**：生产级候选，承接特征、预测、组合和回测；
2. **FinGPT**：事件理解与金融文本模型 baseline；
3. **FINSABER + EventStudy 方法**：分别验证 Agent 策略和校准事件效应；
4. **Vibe-Trading**：研究合同、PIT、假设到回测和审计闭环的高星参考；
5. **RD-Agent**：在特征与回测合同稳定后自动做因子/模型研发；
6. **K-Quant + Qlib HIST**：图关系进入股票预测的直接设计参考；
7. **FinRobot**：公司基本面、估值和报告自动化；
8. **NeuralForecast**：产业节点、公司经营指标和事件强度的概率预测；
9. **TradingAgents**：研究挑战、风险审查和决策日志，不作为预测事实源；
10. **OpenBB**：需要扩充外部数据源时再评估；
11. **FinRL-X/FinRL/TradeMaster**：可靠 alpha 产生后再用于配置和执行研究。

一句话结论：**现在最值得做的不是安装一个高星“股票推理模型”，而是用现有事件/产业链数据构建 point-in-time 特征，以 Qlib 为预测回测主干，以事件研究校准影响，以 FINSABER 验真 LLM 策略，再让 FinRobot/TradingAgents 负责解释与挑战。**
