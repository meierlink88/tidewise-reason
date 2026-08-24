# 时态知识图谱与推理项目核验

> 核验日期：2026-08-21  
> 证据范围：仅使用项目官方 GitHub 仓库、固定 commit 的 README/源码/测试，以及项目对应论文或官方文档。Stars 为核验当日 GitHub Repository API 快照，会继续变化。

## 先给结论

用户记得的“基于图谱底座、可以按时间维度推理”的项目，**最可能是以下三个之一**：

1. **[CozoDB](https://github.com/cozodb/cozo)（4,092 stars）**：如果记忆点是“图库、Datalog 递归、图算法、向量检索、time travel 都在一个轻量数据库里”，它最符合。它能在某个历史时点上执行递归规则，但这不是未来预测，也不是完整双时态。
2. **[PyReason](https://github.com/lab-v2/pyreason)（348 stars）**：如果记忆点是“图上的时态逻辑、带强度/区间的规则、可解释推理”，它最符合。它是推理库，不是持久化知识图谱平台。
3. **[TerminusDB](https://github.com/terminusdb/terminusdb)（3,388 stars）**：如果记忆点是“Schema 化知识图谱、历史版本、时间区间、Datalog/Prolog 查询”，它最符合。它偏版本化事实底座；复杂递归业务规则和自动物化仍应先做 PoC。

一个重要辨别是：**“带时间”不等于“按时间推理”，而“按时间推理”也不等于“预测未来”。** 当前候选实际分成四类：

- 生产型/可部署的版本化图库：CozoDB、TerminusDB、TypeDB（后者没有原生时态合同）、ChronoGraph；
- 时态逻辑推理库：PyReason；
- Temporal KG 的复杂查询/预测研究代码：TFLEX、TILP、TLogic、TimeTraveler、xERTE；
- LLM + TKG 时间问答：TimeR4、CIK-LLM；
- 动态时态构图：ATOM（原 iText2KG）。它负责把文本变成双时态事实，不负责规则传播或投资预测。

没有一个候选同时开箱即用地提供“事件摄取 + 双时态事实账本 + 产业链递归传播 + 未来窗口预测 + Agent 服务接口”。

## 四类项目逐项核验

### 1. 生产型时态图/规则底座

| 项目 | 固定快照 | 真正的时间语义 | 规则/递归机制 | 对观潮家的判断 |
| --- | --- | --- | --- | --- |
| **CozoDB — 4,092** | [`v0.7.6`](https://github.com/cozodb/cozo/tree/v0.7.6)；当前 [`481af05`](https://github.com/cozodb/cozo/commit/481af058abac9444ea8c9c52c78f096ed4b5bfc4)；[stars API](https://api.github.com/repos/cozodb/cozo) | relation 可选择 `Validity` 历史；`ASSERT/RETRACT` 后可用 `@ "NOW"`、指定时点或 `END` 读取相应状态。[固定 README](https://github.com/cozodb/cozo/blob/481af058abac9444ea8c9c52c78f096ed4b5bfc4/README.md#time-travel)、[validity 测试](https://github.com/cozodb/cozo/blob/481af058abac9444ea8c9c52c78f096ed4b5bfc4/cozo-core/src/data/tests/validity.rs) | 原生 Datalog 递归、安全聚合、图算法；HNSW 结果可以与关系统一，甚至参与递归 Datalog。[固定 README](https://github.com/cozodb/cozo/blob/481af058abac9444ea8c9c52c78f096ed4b5bfc4/README.md#what-is-so-cool-about-datalog) | **最像“图库 + 递归 + time travel”的单体候选**。但没有 ontology、事件抽取、LLM/Agent 层；time travel 也不能直接代表 `observed_at + valid_from/to` 双时态。项目最新稳定版仍为 2023 年的 0.7.6，生产活跃度和升级风险必须验证。 |
| **TerminusDB — 3,388** | [`v12.0.7`](https://github.com/terminusdb/terminusdb/tree/v12.0.7)，[`57f2093`](https://github.com/terminusdb/terminusdb/commit/57f2093baeafd65e16004e84b7b58e0c5cf72858)；[stars API](https://api.github.com/repos/terminusdb/terminusdb) | 每次修改形成不可变 layer/commit，可按历史 commit、branch 查询和 diff/merge；另有 ISO8601、区间和 Allen interval algebra。[固定 README](https://github.com/terminusdb/terminusdb/blob/v12.0.7/README.md)、[官方时间教程](https://terminusdb.org/docs/time-tutorial-patterns/) | WOQL 基于 Prolog/Datalog，支持 unification、closed-world 查询和 graph path。[WOQL 官方说明](https://terminusdb.org/docs/woql-explanation/) | **最适合版本化 Event/Evidence 事实账本 PoC**。系统历史与业务有效期都能表达，但自动递归业务规则、物化派生信号、乱序事件撤回重放需要实测，不能仅按产品宣传推断。 |
| **TypeDB — 4,419** | [`3.12.3`](https://github.com/typedb/typedb/tree/3.12.3)，当前 [`749bc6e`](https://github.com/typedb/typedb/commit/749bc6eea14e3bf3f38e4ce1deaa38c0b208ebbd)；[stars API](https://api.github.com/repos/typedb/typedb) | 没有已核实的一等 time-travel 或双时态合同；时间、修订、有效期需要作为领域实体/属性建模 | TypeQL 3 函数可嵌套、递归、否定并用 tabling 求传递闭包；函数需要在查询中显式调用，不是旧版规则的自动推断物化。[Functions](https://typedb.com/docs/typeql-reference/functions/)、[Functions vs Rules](https://typedb.com/docs/typeql-reference/functions/functions-vs-rules/) | 强 Schema 和产业链递归查询优秀，但不要把“模型里有 timestamp”误称为时态数据库。适合作为类型化事实底座，不是最可能的“时态推理项目”。 |
| **ChronoGraph / Chronos — 54** | [`d860bd5`](https://github.com/MartinHaeusler/chronos/commit/d860bd5092ac2b45356fd9546170fb5a76e03f8e)；[stars API](https://api.github.com/repos/MartinHaeusler/chronos) | ACID、TinkerPop/Gremlin、按 commit timestamp 查询历史、element history 和 branch；本质是 **system-time/content versioning**。[固定 ChronoGraph 文档](https://github.com/MartinHaeusler/chronos/blob/d860bd5092ac2b45356fd9546170fb5a76e03f8e/org.chronos.chronograph/readme.md#L148-L168) | 没有已核实的 Datalog、时态逻辑、link forecasting 或产业传播规则引擎 | 名字很像用户的记忆，但能力更接近可回看历史版本的图库。官方总览也明确不支持分布式和 Graph Computer/OLAP；低 adoption，不应优先于 CozoDB/TerminusDB。[固定总览](https://github.com/MartinHaeusler/chronos/blob/d860bd5092ac2b45356fd9546170fb5a76e03f8e/readme.md#L1-L21) |

这里还存在另一个名为 ChronoGraph 的论文系列实现 [`dfpl/chronograph`](https://github.com/dfpl/chronograph)（11 stars，固定 [`6077466`](https://github.com/dfpl/chronograph/commit/6077466cf20aa92ca84fae3f966d9a1af50fc1c5)）。其 README 将产品称为 Chronoweb，提供 vertex/edge events、遍历、订阅和增量计算服务；它是时态信息扩散分析系统，但关注度和生态都很小，也不像用户记得的高星通用推理平台。[固定 README](https://github.com/dfpl/chronograph/blob/6077466cf20aa92ca84fae3f966d9a1af50fc1c5/README.md)

### 2. 时态逻辑推理库

| 项目 | 固定快照 | 时间与推理机制 | 能力边界 |
| --- | --- | --- | --- |
| **PyReason — 348** | [`v3.6.0`](https://github.com/lab-v2/pyreason/tree/v3.6.0)，[`e1a94af`](https://github.com/lab-v2/pyreason/commit/e1a94af33e1f9d925c9df8284113dd0e14fe8a73)；[stars API](https://api.github.com/repos/lab-v2/pyreason) | 官方定位是 annotated、real-valued、graph-based、temporal logic；输入 graph facts 和 logical rules，在时间步上推理，并强调 explainable inference。[固定 README](https://github.com/lab-v2/pyreason/blob/e1a94af33e1f9d925c9df8284113dd0e14fe8a73/README.md#L10-L35) | **最贴近方向、强度、周期信号传播的规则执行器**，但它是 Python inference software，不是持久数据库、Schema/ontology 管理平台或事件摄取服务。合理角色是接在图/事件账本旁边，而不是单独替代 OpenSPG。 |

### 3. Temporal KG link forecasting 研究代码

这些系统的典型任务不是回答“未来三个月 AI 算力产业链各节点看好还是风险”，而是给定历史四元组后预测某个未来时刻缺失的实体或关系，例如 `(公司A, 采购, ?, t_future)`。它们可作为信号评分模型的研究参考，但不是生产事件底座。

| 项目 | 固定快照 | 实际预测/推理机制 | 分类与边界 |
| --- | --- | --- | --- |
| **TILP — 47** | [`4c3587d`](https://github.com/xiongsiheng/TILP/commit/4c3587d69e2760c42e9d273afd5ecc023bf2eee1)；[stars API](https://api.github.com/repos/xiongsiheng/TILP) | 区间事实 + constrained random walk + `before/after/touching` 等时间算子，端到端学习 temporal logical rules；建模 recurrence、order、relation-pair interval、duration。[固定 README 与规则示例](https://github.com/xiongsiheng/TILP/blob/4c3587d69e2760c42e9d273afd5ecc023bf2eee1/README.md#L1-L77) | ICLR 2023 TKGC/规则学习实验代码。不是数据库、在线摄取或规则治理平台；README 将 time prediction 另指向后续 TEILP，因此不能把 TILP 自身说成完整时间预测产品。 |
| **TLogic — 56** | [`9f6ffa3`](https://github.com/liu-yushan/TLogic/commit/9f6ffa3cc5c112226dc2537983b6bb33d4ef295e)；[stars API](https://api.github.com/repos/liu-yushan/TLogic) | 输入 `subject predicate object timestamp`；从历史图做时间单调随机游走抽取 temporal rules，在查询前窗口 grounding，并按规则置信度与 recency 排候选。[固定 README](https://github.com/liu-yushan/TLogic/blob/9f6ffa3cc5c112226dc2537983b6bb33d4ef295e/README.md#L1-L62)、[AAAI 论文](https://cdn.aaai.org/ojs/20330/20330-13-24343-1-2-20220628.pdf) | AAAI 2022 可解释 inductive link forecasting 原型；批文件/benchmark CLI，不是在线平台。它比纯 embedding 更接近可读时间规则，但规则仍从 benchmark 数据学习，并不等于投研业务规则。 |
| **TimeTraveler / TITer — 42** | 作者仓库 [`JHL-HUST/TITer`](https://github.com/JHL-HUST/TITer) 固定 [`2f79a63`](https://github.com/JHL-HUST/TITer/commit/2f79a63b099d4bb46c9ba707e88fce0aaa9af4ed)；[stars API](https://api.github.com/repos/JHL-HUST/TITer)；[EMNLP 论文](https://aclanthology.org/2021.emnlp-main.655/) | 强化学习 Agent 在历史 KG snapshot 上沿时间事实做多跳路径搜索；relative-time encoding 和时间先验 reward 用于未来 link forecasting | 路径可以解释预测，但它是 2021 年训练/评测原型，没有事实账本、规则治理、增量摄取或生产 serving。 |
| **xERTE — 53** | [`d7a55d1`](https://github.com/TemporalKGTeam/xERTE/commit/d7a55d1c692cc97cdff8dde131093217dc6ea082)；[stars API](https://api.github.com/repos/TemporalKGTeam/xERTE) | 从查询实体迭代扩展时间相关子图，用神经注意力/消息传递为未来实体候选打分，并把 supporting subgraph 作为解释。[固定 README](https://github.com/TemporalKGTeam/xERTE/blob/d7a55d1c692cc97cdff8dde131093217dc6ea082/README.md#L1-L41)、[ICLR 论文](https://openreview.net/forum?id=pGIHq1m7PU) | 这是可解释子图预测，不是符号规则推理；仓库最后提交于 2021 年，不是图库或生产服务。 |

TFLEX 属于相邻但不同的研究任务：它不是未来 link forecasting，而是对已给 TKG 执行**复杂时态查询**。

| 项目 | 固定快照 | 实际机制 | 分类与边界 |
| --- | --- | --- | --- |
| **TFLEX — 45** | [`f648196`](https://github.com/LinXueyuanStdio/TFLEX/commit/f648196db17c6f85c9603bcb7cc02e7b48b12301)；[stars API](https://api.github.com/repos/LinXueyuanStdio/TFLEX) | Temporal Feature-Logic embedding 同时表示 entity set 与 timestamp set，支持一阶逻辑集合运算，并加入 `After/Before/Between` 时间算子；可回答实体或时间。[固定 README](https://github.com/LinXueyuanStdio/TFLEX/blob/f648196db17c6f85c9603bcb7cc02e7b48b12301/README.md#L1-L32)、[NeurIPS 论文](https://openreview.net/forum?id=oaGdsgB18L) | NeurIPS 2023 temporal complex query embedding 实验框架；需要下载约 5GB benchmark 数据并训练模型。它适合研究复杂时间问句，不是生产 KG、规则治理或事件驱动预测服务。 |

### 4. LLM + TKG 时间问答：检索后让 LLM 推理

这类系统最接近“顶层 Codex/LLM + 底层图”的设计，但当前实现仍是论文流水线，不是可直接替代 OpenSPG 的图平台。

| 项目 | 固定快照 | 实际机制 | 分类与边界 |
| --- | --- | --- | --- |
| **TimeR4 — 14** | [`508cc02`](https://github.com/qianxinying/TimeR4/commit/508cc0267e55f24877b136f23f0f3c425f2d37b4)；[stars API](https://api.github.com/repos/qianxinying/TimeR4) | `retrieve → rewrite → retrieve → rerank`：先用 TKG 背景改写问题以显式化时间约束，再按语义与时间检索事实、重排，最终由 LLM 回答。[固定 README](https://github.com/qianxinying/TimeR4/blob/508cc0267e55f24877b136f23f0f3c425f2d37b4/README.md#L1-L36)、[EMNLP 论文](https://aclanthology.org/2024.emnlp-main.394/) | 时间感知的 RAG/TKGQA 研究代码，需要训练 retriever，官方命令使用 A6000 与微调 Llama2。它是时间约束检索 + LLM 问答，不是规则学习、未来预测或持久图库。 |
| **CIK-LLM — 4** | 官方实现 [`6e99843`](https://github.com/gnekt/llm-and-dtkg/commit/6e998434a228dc53d9b42219a12082ddadbc99be)；[stars API](https://api.github.com/repos/gnekt/llm-and-dtkg) | 冻结 LLM；先由 LLM 选关系路径，再从持续更新的 TKG 取证据子图并做 time-aware pruning，将子图符号压缩后放入提示词，让 LLM回答。[固定 README](https://github.com/gnekt/llm-and-dtkg/blob/6e998434a228dc53d9b42219a12082ddadbc99be/README.md)、[PMLR 论文](https://proceedings.mlr.press/v274/maio25a.html) | 概念上最接近“LLM 真正做推理、图负责动态事实”，但仓库只有 4 stars、使用 pickle 数据与分阶段脚本，没有生产数据库、服务、事务或规则治理。更适合借鉴架构，而不是直接选作底座。 |

### 5. 动态时态构图，而非预测引擎

| 项目 | 固定快照 | 时间机制 | 能力边界 |
| --- | --- | --- | --- |
| **ATOM（原 iText2KG）— 957** | [`v1.0.0`](https://github.com/AuvaLab/itext2kg/tree/v1.0.0)，当前 [`9eb8b8f`](https://github.com/AuvaLab/itext2kg/commit/9eb8b8fd0b86567b5f7dc19362ba760c9c52666c)；[stars API](https://api.github.com/repos/AuvaLab/itext2kg) | LLM 将连续文本拆为 atomic facts，抽取 `(subject, predicate, object, t_start, t_end)`；区分 `t_obs`（何时观察/摄取）和 `t_start/t_end`（事实何时有效），再增量合并成动态 TKG。[固定 README](https://github.com/AuvaLab/itext2kg/blob/9eb8b8fd0b86567b5f7dc19362ba760c9c52666c/README.md#L1-L53) | **这是本组最值得借鉴的 Event→双时态事实摄取层**，但不是规则或预测引擎。它依赖 LLM 抽取，resolution 使用相似度合并；仍需外接持久存储、幂等、冲突修订、provenance 和传播执行器。 |

## 对“时间推理”的准确拆分

为了避免选型时把不同能力混在一起，观潮家至少应把时间能力拆成五项：

1. **观察时间**：系统什么时候看到这条证据，即 `observed_at/known_at`；
2. **事实有效时间**：事件或关系在现实中何时成立，即 `valid_from/valid_to`；
3. **历史版本**：数据库在某次提交时是什么样，即 system/transaction time；
4. **时态规则**：如“事件发生后 0–30 天影响上游，30–90 天衰减”；
5. **未来预测**：根据历史图与规则/模型，估计未来未知关系、信号或节点状态。

对应关系是：

- ATOM 明确处理第 1、2 项；
- CozoDB、TerminusDB、ChronoGraph 强在第 3 项，前两者还能让查询/规则在历史切片上运行；
- PyReason 强在第 4 项；
- TFLEX 在带 `Before/After/Between` 的复杂时间查询上训练表示；
- TILP、TLogic、TimeTraveler、xERTE研究第 5 项；
- TimeR4/CIK-LLM 是图检索、时间剪枝与 LLM 问答，不是独立规则或预测器；
- TypeDB 强在 Schema 和递归关系计算，但时间合同需要自己建模。

因此，“有 timestamp filter”或“能读取历史版本”都不能单独证明一个系统具备时态逻辑或预测能力。

## 对事件驱动产业链推理的推荐

若目标仍是由顶层 Codex 类 Agent 驱动，并让 LLM 真正参与逐节点判断，最务实的 PoC 不是直接寻找一个包打天下的项目，而是固定三层合同：

1. **事实层**：双时态 Event/Evidence/Relationship/Revision；候选为 TerminusDB，或在现有 Neo4j/OpenSPG 上自行建模；ATOM 的抽取方式可作为摄取参考。
2. **确定性图计算层**：候选节点遍历、有效期筛选、环路与最大深度、来源追溯；CozoDB/TypeDB 的递归能力最值得对照验证。
3. **判断层**：LLM 根据节点语义、事件证据、传导约束判断方向、强度、周期和失效条件；若需要可复现的数值/时态规则，再引入 PyReason。TLogic/TILP 等模型只适合后续做离线候选评分实验。

### 最小 PoC 排序

1. **CozoDB**：验证一个库能否完成历史切片 + 全产业链递归 + 向量/图混合召回；
2. **TerminusDB**：验证乱序事件、修订、撤回、历史回看和区间查询；
3. **PyReason**：验证带方向、强度、周期的信号是否能产生可解释的逐步规则结果；
4. **ATOM**：只验证从文档抽取 `observed_at` 与 `valid_from/to`，不要把它当预测器；
5. **TLogic**：仅在积累了足够标准化历史四元组后，评估是否能给未来 link 候选增加分数。

## 最终判断

如果用户脑海里的项目是“高星、图数据库、Datalog、递归并支持 time travel”，**大概率是 CozoDB**。如果是“图上的可解释时态逻辑推理”，则更可能是 **PyReason**；如果是“版本化知识图谱和时间区间”，则是 **TerminusDB**。

不建议把 TILP、TLogic、TimeTraveler 或 xERTE 当成 OpenSPG 的直接替代品：它们是面向预制 TKG benchmark 的预测研究代码。也不应把 ATOM 当推理引擎：它真正有价值的是把文本事件整理成双时态图事实。
