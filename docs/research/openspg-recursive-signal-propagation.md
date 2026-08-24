# OpenSPG 递归多跳与产业链信号传导可行性

## 结论先行

OpenSPG **原生支持有界的递归多跳图遍历**，并且原生的概念因果推理器能够将一个事件按已注册的 `leadTo` 概念规则递归传导。因此，对“从某个 Event/Signal 出发，找到产业链上所有可达节点”这件事，**不需要修改 OpenSPG 内核**。

但两个边界必须说清：

1. KGDSL 的 `repeat(min,max)` 是**有界变长路径展开**，不是 Datalog 式的无界递归/固定点求值。官方源码将路径从 1 层展开到用户给定的 `upper` 层；对“有限节点、最好是 DAG 的产业链”足够，但不应宣称为任意深度或完整固定点语义。证据：[`PatternMatchPlanner.buildBoundVarLenExpand`](https://github.com/OpenSPG/openspg/blob/v0.8/reasoner/lube-logical/src/main/scala/com/antgroup/openspg/reasoner/lube/logical/planning/PatternMatchPlanner.scala#L279-L297)。
2. OpenSPG 提供“寻路、路径约束、路径属性归约、派生节点/边”的机制，但**没有内置投研专用的方向、强度、时延、周期、条件、多路径冲突聚合算法**。这些必须由观潮家建模成图边属性和可执行的领域规则/算法。

对当前 `tidewise-reason` 的约束（只使用官方 `openspg-server:latest`，不注入 JAR 或 KAG wheel），最稳妥的架构是：**OpenSPG 负责图和有界多跳查询，外部 Signal Propagation Service 负责领域计算，通过 OpenSPG 的 HTTP API 读写图，KAG 负责问题规划与结果表达**。这是非侵入式的，不需要改官方镜像。

## 一、OpenSPG 原生的两种“递归多跳”

### 1.1 查询时：KGDSL `repeat(min,max)` 有界变长路径

OpenSPG KGDSL 可以从起始节点展开一到 N 层同类关系：

```text
GraphStructure {
  A [IndustryChainNode, __start__='true']
  B [IndustryChainNode]
  A->B [transmitsTo] repeat(1,10) as path
}
Rule {
}
Action {
  get(A.id, B.id, __path__)
}
```

官方测试明确验证了：

- `repeat(1,10)` 枚举可达终点；
- 不加最长/最短约束时可返回全部匹配路径；
- `__path__` 可返回路径上的节点和边；
- `group(A).keep_shortest_path(path)` / `keep_longest_path(path)` 可保留最短/最长路径；
- `path.edges().constraint(...)` 可对每一步边的前后属性施加约束；
- `path.edges().reduce(...)` 可将整条路径的边属性累积成一个值。

直接证据：[`KgReasonerTransitiveTest`](https://github.com/OpenSPG/openspg/blob/v0.8/reasoner/runner/local-runner/src/test/java/com/antgroup/openspg/reasoner/runner/local/main/transitive/KgReasonerTransitiveTest.java#L105-L303)、[`RepeatReduce`](https://github.com/OpenSPG/openspg/blob/v0.8/reasoner/udf/src/main/java/com/antgroup/openspg/reasoner/udf/builtin/udf/RepeatReduce.java)。

例如，若产业链边有 `coefficient`，可以用原生 reduce 计算路径乘积：

```text
pathStrength = path.edges().reduce(
  (acc, edge) => acc * edge.coefficient,
  1.0
)
```

官方测试已用持股比例实现同样的多跳累乘，这证明“沿路径累乘传导系数”是原生表达式可承载的计算，不需要自定义 Java UDF。同一 `reduce` 机制从表达能力上也可以累加时延或累积方向符号；但具体投研公式是观潮家的领域设计，不是 OpenSPG 官方预置能力。

**边界：** `repeat` 必须有上界。源码中 `for (i <- 1 to ...upper)` 明确是按上界展开物理/逻辑计划，因此它不是“直到不再产生新事实”的通用固定点引擎。

### 1.2 入图时：概念分类 + `leadTo` 递归传导

OpenSPG 还有另一套原生机制：写入 Event 时先把它分类到 Concept，再沿 Concept 之间已注册的 `leadTo` 规则生成下一个 Event，然后对新 Event 继续分类和传导。

官方供应链例子是：

```text
产品价格上涨事件
  -> 下游公司成本上涨事件
  -> 下游公司利润下降事件
```

`CausalConceptReasoner.propagate()` 在产生下一个 Event 后，查找该 Event 对应 Concept 的下一条 `leadTo`，并再次调用 `propagate()`，因此这部分是真正的递归调用。证据：[`CausalConceptReasoner`](https://github.com/OpenSPG/openspg/blob/v0.8/builder/core/src/main/java/com/antgroup/openspg/builder/core/reason/impl/CausalConceptReasoner.java)、[`ReasonProcessor`](https://github.com/OpenSPG/openspg/blob/v0.8/builder/core/src/main/java/com/antgroup/openspg/builder/core/reason/ReasonProcessor.java)、[官方 SupplyChain `concept.rule`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/schema/concept.rule)、[官方供应链说明](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/supplychain/README_cn.md)。

OpenSPG HTTP `writerGraph` 在 `enableLeadTo=true` 时会执行 `ReasonProcessor`，并将派生记录写回图存储。证据：[`GraphController.writerGraph`](https://github.com/OpenSPG/openspg/blob/v0.8/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi/GraphController.java#L165-L220)。

**重要限制：** 这是“沿已注册 Concept 因果规则的递归”，不等于通用 Datalog 固定点。当因果概念图存在环时，当前源码未显示通用的 visited-set 或最大深度保护；实际领域模型应保持因果规则 DAG，或在外部执行器中加循环与深度防护。这一点是对源码的工程推断，不是官方承诺。

## 二、投研信号传导中，哪些原生支持，哪些需要扩展

| 能力 | OpenSPG 原生情况 | 观潮家需要做的事 |
| --- | --- | --- |
| 从锚点遍历全部可达节点 | 支持 `repeat(1,N)` | 限定关系类型、最大深度、方向、起点和 `asOfTime` |
| 返回完整路径 | 支持 `__path__` | 将路径转成投研证据链 |
| 沿路径筛选关系 | 支持 `edges().constraint(...)` | 定义产能、库存、替代性、锁价等适用/失效条件 |
| 路径属性累积 | 支持 `edges().reduce(...)` | 定义方向符号、传导系数、时延等的领域公式 |
| 最长/最短路径 | 原生 UDAF | 判断投研上应保留“最强”还是“全部”路径 |
| 派生 Event/Signal/edge | `Action` 可创建节点和边；`leadTo` 可递归 | 设计幂等 ID、规则版本、来源信号和生效/失效时间 |
| 时间过滤/算术比较 | KGDSL 有时间/算术 UDF 和 Constraint | 建模 event time、known time、effective interval、horizon |
| 信号方向 | 可作为属性及规则参与计算 | 方向语义、反转条件和不确定性需自定义 |
| 强度、弹性、衰减 | 通用算术表达可承载部分简单公式 | 无投研内置模型；需自定义、回测和版本化 |
| 时延、持续周期 | 可保存和计算已给定值 | “一个事件会影响多久”的估计模型不是 OpenSPG 内置能力 |
| 多 Event/多路径聚合与冲突 | 通用 `group/sum/avg/...` 可做基础聚合 | 需定义时间重叠、去重、相关性、置信度、阈值和冲突政策 |
| 循环、组合爆炸与固定点 | `repeat` 只是有界展开 | 产业链尽量 DAG，并实现 visited-set、最大深度、强度截止和路径去重 |

因此，“在 OpenSPG 上实现整条产业链递归分析”的答案是 **能**，但应将它拆成两层：

`repeat` 重复的是同一个声明边模式，不是无类型地混合遍历所有边。因此投研图最好统一建模成 `transmitsTo` 关系，再用 `mechanism` 属性区分需求拉动、成本传导、供给约束、替代和互补；否则需要分别查询多种边并在外部合并。

```text
OpenSPG 原生层
  有界多跳遍历 + 路径返回 + 基础约束/归约 + 派生事实写回

观潮家领域层
  传导状态机 + 时间演化 + 多路径聚合 + 冲突处理 + 幂等/版本/回放
```

## 三、为什么不建议把整个传导执行器都写成 KGDSL

对简化 Demo，可以用一次 `repeat + reduce` 直接算出每条路径的累积方向、强度和时延。但生产投研通常还需要：

- 一个节点同时接收多个 Event 和多条相关路径；
- 不同信号有不同开始、峰值和失效时间；
- 同一源事件在分叉后又汇合，不能当成独立证据重复计数；
- 某个节点的结果可能改变后续边的适用条件；
- 需要幂等、版本、回放、校准、规则审计和中间状态观测。

这已经不只是“图路径算术”，而是一个领域状态机。将它全部压入 KGDSL 会使规则难测试、难回测和难升级。更合理的分工是：KGDSL 用于找候选子图/路径和基础确定性规则，外部服务负责复杂的传导状态和聚合。

## 四、非侵入式扩展能力的事实边界

### 4.1 外部服务直接通过 OpenSPG HTTP API：确定可行，首选

OpenSPG Server 官方对外提供：

- `POST /public/v1/reason/run`：提交 `projectId + dsl + params` 执行 KGDSL；
- `POST /public/v1/graph/upsertVertex`：写节点；
- `POST /public/v1/graph/upsertEdge`：写边；
- `POST /public/v1/graph/writerGraph`：写子图，并可通过 `enableLeadTo` 触发概念因果传导。

证据：[`ReasonController`](https://github.com/OpenSPG/openspg/blob/v0.8/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi/ReasonController.java)、[`GraphController`](https://github.com/OpenSPG/openspg/blob/v0.8/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi/GraphController.java)。

因此外部 Signal Propagation Service 可以：

1. 调用 `/reason/run` 取回 Event/Signal 对应的产业链可达路径；
2. 在自己的进程中执行方向、强度、延迟、时间衰减、适用条件和多路径聚合；
3. 通过 `upsertVertex/upsertEdge` 写回 `DerivedSignal` / `PropagationResult` / `derivedFrom` / `affects` 等可溯源事实；
4. KAG 在问答时检索这些结果和证据链。

这个方案不修改 OpenSPG JAR、KAG wheel 或官方镜像，只使用官方 API，与当前 `AGENTS.md` 的限制完全相容。

### 4.2 自定义 KAG Python Executor：框架支持，但对当前镜像约束不是首选

KAG 有 `ExecutorABC` 和 registry，从框架上支持用户实现并注册新 Executor；官方 v0.8 也宣称提供多 Executor 扩展机制。证据：[`ExecutorABC`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/interface/solver/executor_abc.py)、[KAG v0.8.0 release](https://github.com/OpenSPG/KAG/releases/tag/v0.8.0)。

但要让嵌入 `openspg-server` 的 KAG 进程加载新 Python 类，通常必须把模块放入可导入路径、挂载代码或替换安装包。虽然这是 KAG 的正常开发者扩展方式，但它与当前仓库“不注入 KAG wheel/运行时代码”的约束存在张力。这是对部署机制的工程推断；不建议作为当前首选。

### 4.3 KAG MCP Executor：有官方扩展点，但 v0.8 不是直接连远程 HTTP MCP

KAG v0.8 有官方 `mcp_executor`，它接收 `.py/.js` MCP 脚本的 `store_path`，然后以 stdio 子进程运行；`main_solver` 也会从应用配置的 `mcp_servers` 创建 MCP executors。`download_data()` 还写有 HTTP URL 下载分支，但 v0.8 `__init__` 在初始化 `kag_project_config` 之前就调用了 `download_data()`；因此 HTTP `store_path` 不应在未实测前被当成可靠能力。官方例子使用的是本地相对脚本路径。证据：[`McpExecutor`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/executor/mcp/mcp_executor.py)、[`MCPClient`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/executor/mcp/mcp_client.py)、[`main_solver.get_pipeline_conf`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/main_solver.py#L95-L143)、[官方 Google Web Search MCP 例子](https://github.com/OpenSPG/KAG/tree/v0.8.0/kag/examples/google_web_search_mcp)。

需要精确区分：

- **确定支持**：由 KAG 启动一个可访问的 `.py/.js` MCP 脚本，让它作为 Planner 可选的 Executor；官方例子验证的是本地脚本路径。
- **不能直接宣称支持**：v0.8 的 `MCPClient` 仅检查 `.py/.js` 并使用 `stdio_client`，这段源码没有直接连接远程 HTTP/SSE MCP Server 的实现。
- **可行的折中**：一个很薄的官方 MCP 脚本只负责调用独立部署的 Propagation HTTP Service。这不替换 KAG wheel，但仍然要把该脚本作为应用配置/对象存储资源交给 KAG，且需在当前 OpenSPG UI/API 中验证具体的上传和 `mcp_pipeline` 配置路径。

综合判断：MCP 适合让 KAG 自动选择传导工具；但它不应成为传导计算的唯一入口。核心服务仍应保持独立 HTTP API，便于事件入图、批处理、回测和人工触发。

## 五、对 tidewise-reason 的可实施架构

```text
Event Ingestion / Research Analysis Request
                  |
                  v
       Signal Propagation Service       <- 观潮家自主模块
       - horizon/asOfTime
       - visited/maxDepth
       - direction/strength/lag/duration
       - conditions/invalidators
       - path dedup & multi-signal aggregation
          |                       |
          | POST reason/run       | optional upsert results
          v                       v
      Official OpenSPG Server (unchanged image)
      - Schema / ABox
      - repeat(1,N) path expansion
      - path constraint/reduce
      - derived Signal/evidence storage
          ^
          |
      KAG Solver / OpenSPG Application
      - understand question
      - select horizon/anchor
      - retrieve graph + evidence
      - optionally call propagation through MCP/thin tool
      - explain conclusion
```

### 建议的分阶段落地

1. **Demo 阶段**：不新增运行时组件。在 Schema 中定义一种产业链传导边，属性包含 `direction/coefficient/lagDays/durationDays/validFrom/validTo`；用 `repeat(1,10) + __path__ + reduce` 验证从一个起点覆盖所有下游节点。
2. **第一版领域执行器**：新建独立 Propagation Service，通过 HTTP 调 OpenSPG；初期只实现有界 BFS/DAG 传导、时间衰减、强度阈值、简单加权聚合和证据路径。
3. **KAG 接入**：先由 Tidewise 应用编排同时调用 KAG 和 Propagation Service；如果后续确认 OpenSPG 产品模式的 MCP 上传/配置路径稳定，再增加薄 MCP adapter 让 Planner 自动调用。
4. **物化策略**：不必把每次问答的所有中间值都写回图。只物化需要跨查询复用、审计或影响后续事件的 DerivedSignal；即时路径得分可仅存于本次 AnalysisRun。

## 六、一个适合当前 Demo 的设计草图

建议将“产业链关系”和“某次传导结果”分开：

```text
(IndustryChainNode)-[transmitsTo]->(IndustryChainNode)
transmitsTo {
  mechanism,
  direction,          // +1 / -1 / conditional
  coefficient,
  lagDays,
  durationDays,
  validFrom,
  validTo,
  conditionRef,
  evidenceRef,
  ruleVersion
}

(Event)-[produces]->(VariableSignal)
VariableSignal {
  variable,
  direction,
  strength,
  startAt,
  peakAt,
  endAt,
  confidence,
  asOfTime,
  derivationVersion
}

(AnalysisRun)-[derived]->(NodeImpact)
NodeImpact {
  nodeId,
  horizon,
  direction,
  score,
  confidence,
  pathIds,
  sourceSignalIds,
  asOfTime,
  expiresAt
}
```

执行时以 Signal 的锚定节点作为 `__start__`，用 `repeat(1,maxDepth)` 取路径，再由领域执行器按路径顺序生成每个 NodeImpact。这样 OpenSPG 不只是被动存图，它真正执行了语义受限的多跳寻路和基础规则；同时复杂投研算法仍能够独立回测、升级和审计。

## 七、事实与工程推断汇总

### 官方源码直接确认的事实

- KGDSL 支持带上下界的 `repeat(min,max)` 变长路径。
- 路径可以返回、约束、reduce，并保留最长/最短路径。
- Concept causal reasoner 会递归执行后续 `leadTo` 规则。
- `writerGraph(enableLeadTo=true)` 会触发推理并写回派生记录。
- OpenSPG 对外有 Reasoner 和 Graph 读写 HTTP API。
- KAG 有可注册 Executor 接口和 MCP Executor。
- KAG v0.8 MCP Client 的当前实现是运行 `.py/.js` stdio MCP 脚本，而不是直连远程 HTTP/SSE MCP。

### 基于上述事实的工程推断

- 有限/DAG 产业链的全节点遍历可用 OpenSPG 原生能力完成。
- 生产级多信号时态传导不宜全部压入 KGDSL；应用外部领域执行器补足。
- 通过 OpenSPG HTTP API 实现外部执行器，是当前官方镜像约束下侵入性最小、可测性和可升级性最好的方案。
- MCP 是可选的 KAG 编排适配层，不应与核心传导引擎绑死。

## 参考基线

- OpenSPG `v0.8`，本次源码审计 commit: `ceeb3ef549df79ca4c4878e7ff452c73584991f3`。
- KAG `v0.8.0`，本地官方 checkout commit: `de777280584fec0c3d888804eaafa86f169f13db`。
- 官方仓库：[OpenSPG/openspg](https://github.com/OpenSPG/openspg)、[OpenSPG/KAG](https://github.com/OpenSPG/KAG)。
