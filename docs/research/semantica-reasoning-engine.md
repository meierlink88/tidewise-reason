# Semantica 推理原理与实现边界

> 调研日期：2026-08-21  
> 源码基线：Semantica `main`，commit [`c5d382e`](https://github.com/semantica-agi/semantica/tree/c5d382ee81edc0727d07907c932970c762ec33bd)；最新正式版为 [`v0.6.6`](https://github.com/semantica-agi/semantica/releases/tag/v0.6.6)。  
> 证据范围：官方仓库 README、架构文档、源码与测试；不采用第三方介绍。

## 结论

Semantica 不是 KAG 那样的“LLM 推理驾驶系统”，也不是 MiroFish 那样的多智能体仿真引擎。它当前更准确的定位是：

> **知识图谱/上下文图基础设施 + 轻量符号规则引擎 + Datalog + 时态计算 + 决策与推理溯源。**

它的主要推理原理是把事实和规则变成可计算的符号，再通过前向链、后向链或 Datalog 不动点计算产生新事实。LLM 不是这一内核的必需条件。它另有一个可选 `GraphReasoner`，但该组件只是把调用方提供的图转成文本，一次性提交给 LLM 回答，并没有实现 KAG 式的查询规划、任务 DAG、检索器选择和多步工具执行。

从当前源码判断，真正比较完整、能够明确说明算法行为的推理能力是：

1. `Reasoner` 的简单 IF–THEN 前向/后向规则推理；
2. `DatalogReasoner` 的递归 Horn 规则与半朴素不动点求值；
3. 基于 Allen 区间代数的确定性时态计算；
4. 对人工记录的决策和因果边进行图遍历、影响评分与溯源。

README 同时宣传 Rete、SPARQL、溯因和“因果推理”，但当前对应实现的成熟度差异很大：Rete 和 SPARQL 仍有明确的占位逻辑；所谓因果分析主要是遍历用户已声明的因果边，并辅以“共享实体 + 时间先后”的启发式关系，不是结构因果模型、因果发现、干预或反事实推理。

## 一、整体执行架构

官方架构描述的全链路是：

```text
数据源
  → Ingest / Parse / Normalize / Split
  → 实体、关系、事件抽取
  → 冲突检测与实体去重
  → Knowledge Graph / Context Graph
  → Ontology / Reasoning / Provenance / Decisions
  → Enriched KG
  → 图存储、向量存储、导出、REST、MCP、CLI、Explorer
```

来源：[官方 README 的 Architecture](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/README.md#architecture)、[ARCHITECTURE.md](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/ARCHITECTURE.md)。

这里需要区分“平台模块齐全”和“自动推理流水线”两个概念。Semantica 提供 ingestion、KG、ontology、reasoning、provenance、context 等独立模块，但不存在一个类似 KAG Solver 的统一 Planner，自动理解自然语言问题、拆解任务并逐步调用这些模块。应用需要自己选择：

- 如何把数据转成图和事实；
- 调用哪一种 Reasoner；
- 注入哪些规则；
- 是否把派生事实写回图；
- 是否再调用 LLM 生成自然语言答案。

## 二、真正的符号推理内核

### 2.1 简单规则引擎：前向链和后向链

高层 `Reasoner` 用字符串保存事实，例如：

```text
Produces(cable_company, power_cable)
UsesMaterial(power_cable, copper)
```

规则采用简化的自然语言外壳：

```text
IF Produces(?company, ?product)
AND UsesMaterial(?product, ?material)
THEN IndirectlyUses(?company, ?material)
```

这里的“自然语言”不是 LLM 理解，而是固定语法解析：代码用正则识别 `IF ... AND ... THEN ...`，再用 `?变量` 做字符串模式匹配和绑定。

- **前向链**：反复扫描规则和事实；条件全部匹配就实例化结论，并把新结论立刻加入工作内存；直到没有新事实或达到默认 50 轮上限。
- **后向链**：从目标结论出发寻找可能生成它的规则，递归证明每个前提，默认最大深度 10。
- `InferenceResult` 保存本轮使用的规则、直接前提和规则置信度，可用于解释；但置信度没有沿多跳前提执行统一的概率传播。

来源：[`Reasoner`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/reasoner.py)、[对应测试](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/tests/reasoning/test_reasoner.py)。

这是一套可用但较轻量的内存规则引擎，不等于 OpenSPG 中包含 KGDSL、逻辑计划、物理计划、算子和图存储集成的完整 Reasoner 栈。

### 2.2 Datalog：当前最扎实的多跳推理实现

`DatalogReasoner` 接受 Horn 子句：

```prolog
ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
```

它把事实按谓词建立索引，并采用自底向上的**半朴素求值**：每轮只把上一轮新增的 delta 事实至少放入一个规则体位置参与匹配，持续产生新事实，直至不动点。递归规则因此能够计算任意有限图上的多跳可达关系。

它还可以把 `ContextGraph` 的节点转换成一元事实、把边转换成二元事实，然后对派生事实进行带变量查询。官方测试覆盖了递归祖先、三跳可达、双条件 join、变量绑定和 ContextGraph 导入。

来源：[`DatalogReasoner`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/datalog_reasoner.py)、[`test_datalog_reasoner.py`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/tests/reasoning/test_datalog_reasoner.py)。

需要保留的边界是：这是 Python 进程内的事实集合和规则求值，不是直接把复杂规则下推到 Neo4j、RDF store 或分布式执行引擎；源码也没有为 Datalog 派生事实提供完整的逐跳 proof trace API。

### 2.3 时态推理

`TemporalReasoningEngine` 是确定性的纯 Python 时间区间计算，支持 Allen 区间关系，例如 `before`、`after`、`meets`、`overlaps`、`during`、`contains`、`starts`、`finishes` 和 `equals`，并提供：

- 某一时点哪些事实有效；
- 区间合并与间隙分析；
- 时间覆盖率；
- 实体时间线；
- 双时态事实的追溯覆盖。

来源：[`semantica/kg/temporal_reasoning.py`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/kg/temporal_reasoning.py)。

它能回答“事实在什么时间有效、区间是否重叠”，但不会自动判断“某事件影响将持续三个月”。影响周期仍必须由数据、规则、统计模型或 LLM 另行产生，然后由时态引擎计算。

## 三、所谓“因果推理”实际是什么

Semantica 将每次决策记录为图节点，并允许调用方显式创建三种边：

```text
CAUSED
INFLUENCED
PRECEDENT_FOR
```

随后通过 BFS/DFS 或图数据库查询遍历这些边，回答：

- 哪些决策导致了当前决策；
- 当前决策影响了哪些后续决策；
- 根因和先例是什么；
- 多跳链路的置信度如何衰减。

多跳链置信度采用边权连乘；影响评分还会组合实体重叠、类别相同和 30 天内的时间接近度。若没有显式因果边，`trace_decision_causality()` 会把“引用同一实体且发生得更早”的决策当作潜在原因。

来源：[`ContextGraph.add_causal_relationship()`、`trace_decision_causality()` 和 `_calculate_decision_influence_score()`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/context/context_graph.py)、[`CausalChainAnalyzer`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/context/causal_analyzer.py)。

因此，“因果”在这里主要意味着**已经记录的因果语义边及其图分析**。它没有从观测数据中学习因果结构，也没有看到结构因果模型、`do()` 干预、潜在结果估计或反事实模拟。共享实体与时间先后的启发式最多表示“可能相关/可能在先”，不能单独证明因果。

## 四、LLM 在哪里参与

可选的 `GraphReasoner` 会：

1. 把传入的所有实体和关系格式化为文本；
2. 拼进一个固定提示词；
3. 要求 LLM 严格依据图上下文回答；
4. 返回模型生成的字符串。

来源：[`GraphReasoner`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/graph_reasoner.py)。

该实现没有：

- 自动实体链指；
- 按问题选择子图；
- 逻辑形式规划；
- 子问题 DAG；
- Retriever / Math / Deduce 等执行器；
- 多轮工具调用和结果回填。

所以它更接近“把图谱上下文塞给一次 LLM 调用”，而不是 KAG Solver。图太大时，调用方必须自己先检索和裁剪子图。

Semantica 的官方说明也明确限定了可解释性边界：它解释的是提交给模型的上下文、模型输出、适用政策和外部执行轨迹，而不是重建 LLM 内部的 chain-of-thought。来源：[README 的 explainability 声明](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/README.md#graph-native-infrastructure-for-context-and-accountable-ai-systems)。

## 五、宣传能力与当前实现的差距

| README/架构中的名称 | 当前源码实际情况 | 判断 |
| --- | --- | --- |
| Forward chaining / backward chaining | 固定 IF–AND–THEN 语法、字符串统一、内存迭代/递归证明 | 有实质实现，但语法和执行规模较轻量 |
| Datalog | Horn 规则、索引、半朴素不动点、递归、多跳和变量查询 | 当前最可信的符号多跳能力 |
| Rete network | `AlphaNode._matches()` 和 `BetaNode._can_join()` 当前都无条件返回 `True`；多条件网络传播也没有形成完整 join 链 | 仍是框架/占位，不能按生产 Rete 评估 |
| SPARQL reasoning/execution | `execute_query()` 即使配置 triplet store 也返回空结果；`_has_type()` 无条件返回 `True` | 主要是查询注释和结果后处理骨架，不是真正 SPARQL 执行器 |
| Abductive reasoning | 根据规则结论是否匹配观察值生成候选，再用固定启发式分数排序 | 简单候选反推，不是完整假设搜索或概率溯因 |
| Causal reasoning | 显式因果边遍历 + 共享实体/时间先后的启发式 + 图指标 | 是因果关系记录与分析，不是因果发现/干预/反事实 |
| Fully explainable | 简单 Reasoner 能保存直接规则和前提；ExplanationGenerator 将已有 proof/result 格式化为路径和文本 | 是系统层溯源；不能解释 LLM 内部推理，Datalog 也缺完整 proof trace |

源码依据：[`rete_engine.py`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/rete_engine.py)、[`sparql_reasoner.py`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/sparql_reasoner.py)、[`abductive_reasoner.py`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/abductive_reasoner.py)、[`explanation_generator.py`](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/explanation_generator.py)。

## 六、与 OpenSPG + KAG、MiroFish 的区别

| 系统 | 主要知识载体 | 主要推理机制 | LLM 角色 | 会不会自主组织自然语言多步任务 |
| --- | --- | --- | --- | --- |
| OpenSPG | 受 Schema 约束的语义知识图谱 | KGDSL、图查询、规则和算子执行 | OpenSPG 原生规则不依赖 LLM | OpenSPG 单独不会 |
| KAG | OpenSPG 图、Chunk、索引和外部结果 | Planner → 任务 DAG → Retriever/Executor → Generator | 理解、规划、语义演绎和生成 | 会，是其核心价值 |
| Semantica | ContextGraph/KG、决策、事实、溯源 | 简单规则、Datalog、时态运算、图遍历；另有一次性 LLM 图问答 | 可选抽取和图上下文回答 | 当前没有 KAG 式统一 Planner |
| MiroFish | Zep 图谱/记忆、Agent 状态和模拟日志 | 多个 LLM Agent 在 OASIS 环境中多轮互动，观察群体涌现 | 决定各 Agent 行为并生成报告 | 有仿真调度，但不是符号规则推理 |

最关键的分类是：

```text
OpenSPG ≈ 深一些的语义图谱与规则推理底座
KAG     ≈ 面向自然语言问题的 LLM 推理编排层
Semantica ≈ 广覆盖的图谱、上下文、规则和治理工具箱
MiroFish  ≈ LLM 多主体情景仿真应用
```

因此 Semantica 与 OpenSPG 的重叠远大于它与 KAG 的重叠。它的 `GraphReasoner` 不能直接视为 KAG 替代品；它也不会像 MiroFish 那样让主体交互并从群体行为中生成预测。

## 七、对事件驱动产业链分析的含义

假设图中已经有：

```text
Event → A 节点 → B 节点 → C 节点
```

Semantica 不会仅凭这条拓扑自动判断事件对每个节点是利好还是利空。应用仍需提供可执行语义，例如：

```prolog
positive(B) :- positive(A), positively_transmits(A, B).
negative(B) :- positive(A), negatively_transmits(A, B).
```

或者使用简单 `Reasoner` 的 IF–THEN 规则。Datalog 可以沿十个节点递归传播，不需要逐节点手写十条规则，但必须事先建模关系的传播方向、符号、有效条件和时间约束。

Semantica 的优势是可以把：

- 事件、产业链和派生结论存入图；
- 使用 Datalog 做确定性多跳传播；
- 使用时态模块过滤仍然有效的信号；
- 保存来源、规则和决策轨迹；
- 再把有界子图交给 LLM 解释。

它当前不能自动替代的部分是：

- 从自然语言投研命题生成完整任务计划；
- 自动选择图检索、规则、数值计算和文档证据；
- 自动判断尚未建模的产业传导机制；
- 以可靠方法预测事件影响周期；
- 通过主体行为模拟市场反应。

若观潮家使用 Semantica，需要自行实现一层接近 KAG 的投研编排器；若继续使用 OpenSPG + KAG，则 Semantica 更适合作为“完整开源的 ContextGraph/决策溯源设计参考”，而不是直接替换现有推理链路。

## 一手资料索引

- [Semantica 官方仓库与 README](https://github.com/semantica-agi/semantica/tree/c5d382ee81edc0727d07907c932970c762ec33bd)
- [官方架构图](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/ARCHITECTURE.md)
- [简单 Reasoner](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/reasoner.py)
- [DatalogReasoner](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/datalog_reasoner.py)
- [Datalog 官方测试](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/tests/reasoning/test_datalog_reasoner.py)
- [时态推理](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/kg/temporal_reasoning.py)
- [LLM GraphReasoner](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/graph_reasoner.py)
- [ContextGraph 决策与因果链](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/context/context_graph.py)
- [ReteEngine](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/rete_engine.py)
- [SPARQLReasoner](https://github.com/semantica-agi/semantica/blob/c5d382ee81edc0727d07907c932970c762ec33bd/semantica/reasoning/sparql_reasoner.py)

