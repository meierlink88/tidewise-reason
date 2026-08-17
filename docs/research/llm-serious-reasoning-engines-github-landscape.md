# GitHub 上的 LLM 严肃推理引擎候选

> 调研日期：2026-08-17  
> 目标：寻找接近 OpenSPG + KAG 的开源项目，即同时重视领域语义、可重复推理、证据链和 LLM 问答，而不是普通 RAG 或多智能体模拟。  
> 已知排除基线：Semantica 与 MiroFish；详细原因见本仓库已有对比文档。

## 结论

GitHub 上目前仍没有一个成熟、开放、可自托管的项目，可以完整替代 OpenSPG + KAG 的四层闭环：

1. 受 Schema/TBox 约束的知识构建；
2. 长期 ABox、文档和证据的统一管理；
3. 确定性规则、图查询或形式逻辑推理；
4. LLM 驱动的检索、问题分解和答案生成。

最值得继续看的不是一个项目，而是三组候选：

- **最接近完整产品形态：OpenBKN Foundry、TrustGraph、TigerGraph GraphRAG。** 它们有数据接入、语义层、Agent/LLM 和运行面，但各自缺少 OpenSPG/KAG 式的完整形式推理，或存在许可证、后端锁定问题。
- **最可信的严肃推理内核：TypeDB、Nemo、OWLAPY、PyReason。** 它们在强类型、Datalog、OWL/SWRL 或开放世界时序逻辑上更扎实，但都不是开箱即用的 KAG 产品。
- **最值得借鉴的 LLM Solver：GRASP、GFM-RAG。** 它们擅长图上的问题分解、SPARQL 生成或多跳召回，但不负责权威知识建模与规则治理。

因此，对 Tidewise 最稳妥的方向不是立即替换 OpenSPG/KAG，而是：

- 先用 **OpenBKN Foundry** 做“完整平台替代”的对照 PoC；
- 用 **Nemo 或 PyReason** 给现有 OpenSPG/KAG 增加确定性/时序规则 sidecar；
- 用 **GRASP 或 GFM-RAG** 做 KAG Solver 的 challenger；
- 用 **OWLAPY** 做 TBox 一致性、OWL 推理和公理解释的离线校验层。

## 什么才算“严肃推理”

本次不把项目自称的 `reasoning` 直接当作推理能力。候选至少需要满足下列若干项：

| 能力 | 验收含义 |
|---|---|
| 领域语义 | Schema、ontology、类型、关系签名或约束是运行时合同，不只是 prompt 文本 |
| 可重复计算 | 同一事实集和规则集应得到可重复结果；关键结论不能完全由 LLM 自由生成 |
| 多步推理 | 支持规则链、递归查询、多跳图遍历、问题分解或显式搜索 |
| 解释与溯源 | 能指出使用了哪些事实、规则、图路径、查询和原始来源 |
| 时间与冲突 | 能表达事实有效期、事件变化、不一致或冲突，而不是静态 chunk 集合 |
| 可治理运行面 | 可自托管、可测试、可观察、许可证允许实际业务使用 |

仅有向量召回、community summary、ReAct 循环、LLM chain-of-thought 或图可视化，不足以成为 OpenSPG/KAG 同类引擎。

## 第一组：接近完整平台的候选

### 1. OpenBKN Foundry：产品形态最接近，优先做完整平台 PoC

[OpenBKN Foundry](https://github.com/openbkn-ai/bkn-foundry) 把业务语义组织为 Business Knowledge Network，公开仓库包含 Context Loader、数据虚拟化、工具执行、访问控制与 BKN Trace。其 README 明确使用 `Object → Action → Rule → Constraint` 表达可解释决策，并强调行动前风险评估、执行拦截和事后审计。

与 OpenSPG/KAG 相似的地方：

- ontology-driven 的业务对象、关系、逻辑、风险和动作模型；
- 结构化与非结构化数据的统一上下文；
- 面向 Agent 的 SDK、CLI、Skill 和 API；
- 规则、约束、权限和证据链是平台对象，而非单次 prompt；
- 有 Kubernetes 部署、认证、组织/角色、审计和 Trace 服务。

主要风险：

- 该 GitHub 仓库创建于 2026 年 5 月，公开历史仍短；README 基准主要是项目方自测，不能替代 Tidewise 数据集验收。
- 它更像“业务语义与安全执行平台”，公开材料没有证明其具备 OpenSPG KGDSL、OWL-DL 或完整 Datalog 那样的形式推理语义。
- 仓库是逐文件多许可证。部分上游文件是 Apache-2.0，OpenBKN 新模块使用带附加条件的 [OpenBKN License](https://github.com/openbkn-ai/bkn-foundry/blob/main/LICENSE-OPENBKN.txt)，限制未经授权的共享多租户托管、商业 entitlement 绕过和部分品牌修改。选型前必须完成逐组件许可证清单。
- 后端部署较重，完整安装以 Kubernetes 为中心，不适合仅凭 Docker Compose 快速替换当前本地环境。

**判断：** 当前“外形最像企业版 OpenSPG/KAG 替代品”的候选，但首先应验证规则语义、许可证边界和最小部署成本，不能直接定为替换方案。

### 2. TrustGraph：开放标准、ontology 和 provenance 很强，形式规则较弱

[TrustGraph](https://github.com/trustgraph-ai/trustgraph) 是 Apache-2.0 的自托管 Context Graph/GraphRAG 平台，公开代码覆盖 ontology-guided extraction、RDF/SPARQL、多个图/向量后端、Agent 编排、API、CLI、Workbench 与 Kubernetes/Compose 部署。

它最有价值的能力是证据治理。官方 [Query-Time Explainability 规范](https://github.com/trustgraph-ai/trustgraph/blob/master/docs/tech-specs/query-time-explainability.md) 把一次 GraphRAG 查询表示为 PROV-O 活动，记录召回边、LLM 选中的边、选择理由、合成答案和从边到 chunk/page/document 的来源链。仓库还有 extraction provenance、ontology extraction 与相关单元/集成测试。

但源码和规范显示，其主要“推理”仍是：

1. 从问题抽取概念；
2. 召回子图；
3. 由 LLM 选择相关边并给出理由；
4. 由 LLM 合成答案。

其 [ontology 规范](https://github.com/trustgraph-ai/trustgraph/blob/master/docs/tech-specs/ontology.md) 描述了 OWL-inspired 类、属性和约束，但当前公开实现证据更强的是 ontology-guided extraction 与查询，而不是完整 OWL/Datalog 物化或规则计划器。

**判断：** 若优先级是全开源、自托管、W3C provenance 和可观察 GraphRAG，TrustGraph 很值得 PoC；若核心是可执行因果/业务规则，它需要 Nemo、PyReason 或其他规则内核补齐。

### 3. TigerGraph GraphRAG：可用产品面较完整，但后端锁定

[TigerGraph GraphRAG](https://github.com/tigergraph/graphrag) 在 2026 年已演进到 `v2.0.1`。官方 README 显示它支持：

- schema-aware KG 构建与严格 Schema 模式；
- 自定义或自动生成 ontology；
- 向量、图查询、community 等混合召回；
- Planned/Reactive 两种 agentic 检索；
- Trace Logs、引用、管理 UI、API 和 Docker/Kubernetes 部署；
- 将自然语言问题匹配到预先批准的 GSQL 查询，再执行确定性查询。

“LLM 负责理解问题，已批准查询负责执行”的边界比自由生成 Cypher 更适合严肃场景，也比普通 GraphRAG 更接近 KAG 的受控 Solver。

主要问题是：GraphRAG 仓库虽为 AGPL-3.0，但官方只支持 TigerGraph 4.2+ 作为图和向量后端；TigerGraph 数据库本身不是可从该 GitHub 仓库重建的开放引擎。项目 README 还说明 Agentic engine 和非 Hybrid Search 路径以 self-service/as-is 方式提供。

**判断：** 如果可以接受 TigerGraph 后端和许可证，它是产品完成度较高的对照组；如果目标是完全开放、可替换存储的推理内核，它不合适。

## 第二组：可信的推理内核

### 4. TypeDB：强类型语义数据库，适合替换语义底座，不是 KAG 成品

[TypeDB](https://github.com/typedb/typedb) 是 MPL-2.0 的强类型数据库。TypeQL 能表达实体、关系、属性、角色、继承、基数和值约束。TypeDB 3 用可嵌套、递归、可否定的 [TypeQL functions](https://typedb.com/docs/typeql-reference/functions/) 表达计算；官方明确说明这些函数推广了 Datalog 风格逻辑程序，并替代 TypeDB 2 的 rules/inference。

优势：

- Schema 在写入时执行约束，不只是给 LLM 看；
- n-ary relation、角色和继承比普通属性图语义更强；
- 递归函数适合供应链路径、归属、可达性和派生关系；
- 数据库、语言、驱动和社区历史远长于大多数 2025/2026 GraphRAG 项目。

边界：

- TypeDB 3 的函数需要显式调用，不再像 TypeDB 2 规则那样静默补全数据；迁移时必须重新设计推理合同。
- 它不提供 KAG 的文档解析、实体消歧、chunk/knowledge 互索引和完整问答 Solver。
- TypeDB Studio 有 LLM Agent mode，但那是自然语言生成/修复 TypeQL 的工具面，不等于 KAG 产品。

**判断：** 如果愿意重做数据模型和 Solver，TypeDB 是最可信的“强语义数据底座”替代候选；它不是低成本替换。

### 5. Nemo：活跃、清晰的 Datalog/RDF 规则 sidecar

[Nemo](https://github.com/knowsys/nemo) 是 TU Dresden Knowledge-Based Systems 团队维护的 Rust 规则引擎。官方 README 将其定位为面向 RDF/SPARQL 的 Datalog rule engine，支持：

- stratified negation；
- 数值、比较和算术数据类型；
- aggregate；
- existential rules / tuple-generating dependencies；
- CSV、RDF、SPARQL endpoint 输入和多种 RDF 输出；
- CLI、Python、JavaScript/WASM 绑定。

截至调研日，仓库最新 tag 为 `v0.10.1`，主分支 CI 连续通过，且有多名长期贡献者。官方同时明确提示仍处于 heavy development、release 应视为 unstable。

**判断：** Nemo 不含 LLM、文档抽取和 UI，但作为 OpenSPG ABox 旁的确定性规则执行器，比许多“全栈 AI 推理平台”的规则实现更可信。适合验证供应链传导、关系闭包、规则派生和批量物化。

### 6. OWLAPY：LLM 知识构建与标准本体推理的桥

[OWLAPY](https://github.com/dice-group/owlapy) 由 Paderborn University DICE 团队维护，MIT 许可。它把 OWLAPI、RDF 和 Python/ML 生态连接起来，并新增 AGen-KG：用 LLM 从大文档中分块、合并并生成 ontology/KG。

其严肃推理价值包括：

- OWL class expression、TBox/ABox、SWRL rule 的 Python API；
- HermiT、Pellet、Openllet、JFact、ELK 等标准 reasoner 同步；
- 公理 justifications 和 contrastive explanations；
- OWL 表达式到 Description Logic/SPARQL 的转换；
- reasoner 性能基准与明确的语义边界。官方文档特别说明 Structural/RDFLib reasoner 是 closed-world/structural，并非正式 entailment；标准 OWL 2 DL 语义应使用 HermiT/Pellet 等同步 reasoner。

**判断：** 它不是在线问答平台，但非常适合把 Tidewise TBox 投影做一致性检查、分类、派生和解释。OWL-DL 推理不宜直接放入每条事件的高频热路径。

### 7. PyReason：最贴近事件与时序影响链的规则组件

[PyReason](https://github.com/lab-v2/pyreason) 是 BSD-2-Clause 的开放世界时序图逻辑引擎。其 [论文](https://arxiv.org/abs/2302.13482) 和文档说明它基于 generalized annotated logic，在图上执行带时间、区间/实值标注的规则，并生成完整可解释推理 trace。

这与 Tidewise 的 Variable Signal、时点/时段事实、影响传播和置信区间比普通 Datalog 更贴近。仓库持续发布，调研日已有 `v4.0.0b1`，近期兼容性与性能 workflow 有成功记录。

边界是：PyReason 是 Python 推理库，不负责大型知识库、文档解析、实体对齐、服务治理或 LLM Solver；当前 beta 主版本也需要稳定性验证。

**判断：** 适合作为“事件信号 → 规则影响链 → trace”的 sidecar PoC，不适合作为 OpenSPG 全量图存储替代。

## 第三组：LLM Solver 与多跳检索 challenger

### 8. GRASP：已有 KG 上的可审计 SPARQL/QA Agent

[GRASP](https://github.com/ad-freiburg/grasp) 是 Freiburg University 团队在 ISWC 2025 发布的 Generic Reasoning and SPARQL Generation across Knowledge Graphs。它让 LLM 通过工具迭代搜索 entity、property、literal 和 graph shape，生成 SPARQL 或自然语言答案，并能输出完整交互 trace、运行服务和在 KGQA 数据集上评估查询结果。

与通用 text-to-SPARQL 相比，GRASP 的价值是让模型逐步探索 KG，而不是一次性看到巨大 Schema 后猜查询。它还支持自定义 SPARQL endpoint 和 OpenAI-compatible 本地模型。

**判断：** 很适合作为 KAG Solver challenger，直接连接现有 RDF/SPARQL 图或 QLever；它不做权威 Schema、知识构建和规则物化。

### 9. GFM-RAG / G-reasoner：多跳图召回组件，不是规则引擎

[GFM-RAG](https://github.com/RManLuo/gfm-rag) 用预训练 graph foundation model 在图索引上做单步多跳召回，能输出捕获的 reasoning paths，并允许直接导入 `nodes.csv`、`relations.csv`、`edges.csv`。截至调研日，仓库已发布 34M 的 G-reasoner 模型和代码。

**判断：** 值得与 KAG retrieval 做准确率、token 和延迟对比，但其“reasoning”主要指学习式图检索，不是确定性规则、ontology entailment 或可验证证明。

### 10. Youtu-GraphRAG：研究价值高，但许可证直接排除生产使用

[Youtu-GraphRAG](https://github.com/TencentCloudADP/youtu-graphrag) 有 schema-guided knowledge tree、问题分解、并行子问题、IRCoT 反思和 reasoning trace，在研究型 GraphRAG 中完成度较高。

但是其 [LICENSE](https://github.com/TencentCloudADP/youtu-graphrag/blob/main/LICENSE) 明确要求只能用于 academic purposes，并禁止任何 commercial 或 production use。

**判断：** 可以阅读算法和在隔离研究环境中复现，不应进入 Tidewise 生产 PoC shortlist，也不能作为商业产品底座。

## 观察名单：能力画像好，但成熟度不足

### Open Ontologies

[Open Ontologies](https://github.com/fabio-rovai/open-ontologies) 是 2026 年出现的 Rust/MCP ontology engine，公开能力覆盖 RDF/SPARQL、SHACL、OWL-RL/OWL-DL、lineage、版本、alignment、action schema、causal certification 和 PDDL planner。其 [reasoning 文档](https://github.com/fabio-rovai/open-ontologies/blob/main/docs/reasoning.md) 声称实现原生 Rust SHOIQ tableaux，并列出 RDFS、OWL-RL、OWL-RL-ext、OWL-DL 四种 profile；主分支近期 CI 为绿色。

风险同样明显：项目历史很短，主要由单一维护者贡献；核心存储是 in-memory Oxigraph；没有被广泛独立验证的生产负载；Studio 的 Agent sidecar 当前强绑定 Claude SDK。它适合做 TBox 工具实验，不宜直接承载 Tidewise 长期 ABox。

### pg-ripple

[pg-ripple](https://github.com/trickle-labs/pg-ripple) 是 PostgreSQL 18 Rust 扩展，README 和源码目录覆盖 RDF/SPARQL、SHACL、Datalog、时序事实、proof tree、what-if inference、规则冲突、LLM 自然语言解释与 RAG。若这些能力稳定，它的画像非常接近“严肃推理数据库”。

但该仓库创建于 2026 年 4 月，调研时只有极小社区，绝大多数提交来自一人；三个月内 tag 已到 `v0.128.0`，版本增长速度与实际稳定性不能等同；公开 Actions 最近看不到可信的绿色主分支全套运行，多条依赖 PR 为 failure 或 action-required。只能放观察名单，必须从源码构建并独立跑 W3C、Datalog、恢复和并发测试后再评价。

### OpenCog Hyperon / MeTTa、Scallop

- [OpenCog Hyperon](https://github.com/trueagi-io/hyperon-experimental) 的 Atomspace + MeTTa 能表达图重写、逻辑和神经符号组合，但官方仍明确称 active pre-alpha，离企业知识产品较远。
- [Scallop](https://github.com/scallop-lang/scallop) 是基于 Datalog 和 provenance semiring 的可微逻辑语言，适合研究概率/神经符号推理，不负责企业知识构建和在线问答产品。

## 明确不应误判为替代品的项目

| 项目类型 | 代表 | 为什么不是 OpenSPG/KAG 同类 |
|---|---|---|
| 文档 GraphRAG | Microsoft GraphRAG、LightRAG | 图主要服务召回和摘要，没有权威 TBox 与可治理规则执行 |
| 时序 Agent memory | Graphiti、Cognee | 重点是记忆、检索和上下文演化；ontology/provenance 在增强，但确定性规则仍不是核心合同 |
| 多智能体模拟 | MiroFish/OASIS | 生成情景和社会行为，不是长期权威事实库与形式推理器 |
| KG 路径研究代码 | ToG/ToG-2/ToG-3 | 验证 LLM 沿 KG 搜索路径，缺少完整数据、Schema、治理和运行面 |
| 通用 Agent framework | LangGraph、AutoGen、CrewAI | 负责流程编排，不提供知识语义和推理正确性 |
| LLM inference server | vLLM、SGLang、OpenReasoningEngine | 优化模型推理吞吐，不是知识推理引擎 |

## 对 Tidewise 的 PoC 优先级

### P0：保留 OpenSPG/KAG 基线

继续把当前系统作为基线，固定同一批 TBox、ABox、规则和问答集。没有基线就无法判断新项目的“回答更自然”是否牺牲了事实、规则和可解释性。

### P1：四条小而独立的 challenger

1. **OpenBKN Foundry**：验证完整平台替代形态，重点检查 BKN Lang、规则/约束实际执行、Trace 和许可证清单。
2. **Nemo 或 PyReason sidecar**：验证现有 OpenSPG 数据导出后，规则链和时序影响链能否给出稳定派生与 trace。
3. **GRASP Solver**：在同一知识图谱上对比 KAG Solver 的多跳正确率、查询可执行率和 token 成本。
4. **OWLAPY TBox gate**：对 schema projection 做一致性、subsumption、派生和 justification 验证，不进入在线热路径。

TypeDB 应作为单独的中长期数据模型实验，而不是与上述四项混在一个短 PoC 中；它会触发较大的 Schema、数据导入和查询重写成本。

## 统一验收集

每个候选必须使用同一份 Tidewise fixture 和问题集，至少测量：

| 类别 | 必测指标 |
|---|---|
| Schema | 类型、关系签名、基数、枚举、继承、非法写入拒绝率 |
| 实体与事实 | 实体消歧 precision/recall、来源保留率、重复合并错误率 |
| 规则 | 规则链正确率、递归/否定/冲突行为、同输入确定性 |
| 时间 | valid time、transaction time、事件顺序、过期事实和更正 |
| 问答 | 简单事实、多跳、规则题、否定题、缺失信息拒答、答案引用 |
| 解释 | 每个结论能否回溯到事实、规则/查询、原始文档和版本 |
| 增量 | 单事件写入到可查询/可推理的延迟，重建范围和错误恢复 |
| 性能 | 导入吞吐、p50/p95/p99、并发、峰值内存、token 与模型成本 |
| 运维 | 单机/集群部署、备份恢复、权限、审计、升级和失败可见性 |
| 法务 | 代码、镜像、模型、数据、UI 和商业部署的逐组件许可证 |

推荐增加三类“反向题”：

- 图中没有证据时必须明确拒答；
- 规则前提缺一项时不得推出结论；
- 新事实撤销或过期后，旧派生必须能被撤销、重算或标记失效。

## 最终排名

| 目的 | 首选 | 次选 | 不建议 |
|---|---|---|---|
| 完整平台替代对照 | OpenBKN Foundry | TrustGraph | Youtu（许可证禁止生产） |
| 强语义数据底座 | TypeDB | 继续 OpenSPG | 普通属性图 + prompt Schema |
| 确定性规则 | Nemo | TypeDB functions | 只让 LLM“按规则思考” |
| 时序影响链 | PyReason | Nemo + 显式时间谓词 | 静态 GraphRAG |
| OWL/TBox 校验 | OWLAPY | Open Ontologies（观察） | 把 OWL 当标签字典 |
| KG 问答 Solver | GRASP | GFM-RAG | 自由生成查询且无执行/trace |
| 全开源 provenance GraphRAG | TrustGraph | OpenBKN Trace | 仅返回模型 chain-of-thought |

一句话建议：**短期不换 OpenSPG/KAG；用 OpenBKN 做完整平台对照，用 Nemo/PyReason、OWLAPY、GRASP 分别挑战规则、TBox 和 Solver。只有这些 challenger 在同一验收集上明显胜出，才讨论重构主干。**

## 一手资料

- [OpenBKN Foundry repository](https://github.com/openbkn-ai/bkn-foundry)
- [OpenBKN License](https://github.com/openbkn-ai/bkn-foundry/blob/main/LICENSE-OPENBKN.txt)
- [TrustGraph repository](https://github.com/trustgraph-ai/trustgraph)
- [TrustGraph query-time explainability](https://github.com/trustgraph-ai/trustgraph/blob/master/docs/tech-specs/query-time-explainability.md)
- [TigerGraph GraphRAG repository](https://github.com/tigergraph/graphrag)
- [TypeDB repository](https://github.com/typedb/typedb)
- [TypeDB functions and rules](https://typedb.com/docs/typeql-reference/functions/functions-vs-rules/)
- [Nemo repository](https://github.com/knowsys/nemo)
- [Nemo documentation](https://knowsys.github.io/nemo-doc/)
- [OWLAPY repository](https://github.com/dice-group/owlapy)
- [PyReason repository](https://github.com/lab-v2/pyreason)
- [PyReason paper](https://arxiv.org/abs/2302.13482)
- [GRASP repository](https://github.com/ad-freiburg/grasp)
- [GFM-RAG repository](https://github.com/RManLuo/gfm-rag)
- [Youtu-GraphRAG repository and license](https://github.com/TencentCloudADP/youtu-graphrag)
- [Open Ontologies repository](https://github.com/fabio-rovai/open-ontologies)
- [pg-ripple repository](https://github.com/trickle-labs/pg-ripple)

## 调研限制

本报告核验了官方仓库、源码树、许可证、公开 CI、release/tag、官方文档与论文，但没有在 Tidewise fixture 上实际部署所有候选，也没有把项目方自报基准当作独立性能结论。GitHub 活跃度与版本状态会变化；进入 PoC 时应固定 commit、镜像 digest、模型和依赖锁文件。
