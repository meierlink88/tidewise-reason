# 开源知识图谱与推理引擎短名单

> 核验日期：2026-08-21  
> 证据：仅使用项目官方 GitHub 仓库、官方文档、源码与测试。Stars 为当日 GitHub Repository API 快照，会继续变化。  
> 筛选标准：至少覆盖“图/事实存储、Schema/ontology、规则/递归、时态、溯源”中的两项。版本优先采用最新稳定 tag，并同时给出固定 commit。

## 结论

**用户最可能记得的项目是 [`Cognee`](https://github.com/topoteretes/cognee)，当前约 30,165 stars。** 它的界面、知识图谱、ontology、时态记忆、provenance 和 Agent/MCP 定位看起来与 OpenSPG/Graphiti 很接近，也是候选中关注度最高的。

但要先纠正一个容易误判的点：**Cognee 不是通用规则推理引擎。** 它所说的 graph reasoning，主要是 LLM 抽取、图结构组织、图/向量检索和给 Agent 提供关联上下文；在审计的 v1.5.0 核心代码中没有发现类似 KGDSL、Datalog、Jena Rule、固定点传导或业务规则求值器。

如果用户记得的是“真正能写递归规则的图库”，更可能是：

1. **TerminusDB**：版本化知识图谱 + Schema + WOQL/Datalog + 时间区间；
2. **TypeDB**：强类型关系模型 + TypeQL 递归函数；
3. **Apache Jena**：RDF/OWL + 通用前向/后向规则引擎 + 推导路径。

对观潮家而言，没有一个项目同时完整替代 OpenSPG、KAG、Graphiti 和顶层 Agent。更合理的比较对象分成三层：

- **真正规则/递归推理底座**：Apache Jena、TypeDB、TerminusDB、Rulewerk/Soufflé、PyReason；
- **符号 AI 研究平台**：OpenCog AtomSpace / Hyperon；
- **LLM + KG / Agent 上下文平台**：Cognee、TrustGraph。它们不能因为 README 写了 reasoning 就被当作业务规则引擎。

## 分层短名单

| 层级 | 项目与当前 stars | 固定版本/快照 | 已核实能力 | 不具备或需要自建 | 对事件驱动投研的判断 |
| --- | --- | --- | --- | --- | --- |
| LLM + KG / Agent memory | **[Cognee](https://github.com/topoteretes/cognee) — 30,165** | [`v1.5.0`](https://github.com/topoteretes/cognee/tree/v1.5.0)，commit [`2169926`](https://github.com/topoteretes/cognee/commit/2169926457d739a2efbffb39d7d068c8ee573789) | 图/向量存储可换；RDF/OWL ontology resolver；Temporal Graph/recall；W3C PROV-O 风格 provenance；MCP/Agent memory | 没有通用 Datalog/KGDSL/固定点规则执行；事件传导仍由 Agent 或外部执行器完成 | **适合做 Graphiti 的竞争者**，负责文档、事件记忆、时态召回和溯源；不应单独承担产业链逐节点规则传播 |
| LLM + KG / Agent context | **[TrustGraph](https://github.com/trustgraph-ai/trustgraph) — 2,585** | [`v2.8.15`](https://github.com/trustgraph-ai/trustgraph/tree/v2.8.15)，commit [`3cb6439`](https://github.com/trustgraph-ai/trustgraph/commit/3cb6439603e9f5fe3454d037c961149062d58c7a) | RDF/OWL/SKOS/SHACL ontology、graph/vector/document 管道、fact-level provenance、GraphRAG/OntologyRAG、Agent 编排与 MCP | “Reasoning path”是被检索进上下文的图路径；未发现业务规则、Datalog 或递归推导引擎 | 适合做完整 Agent context 平台，但部署组件较多；投研传播逻辑仍需领域 Tool/Agent |
| 类型化演绎数据库 | **[TypeDB](https://github.com/typedb/typedb) — 4,419** | [`3.12.3`](https://github.com/typedb/typedb/tree/3.12.3)，commit [`ae8b88a`](https://github.com/typedb/typedb/commit/ae8b88ad9f20bacc09cf81ec991d7a81c72aaa2d) | 强类型 Entity/Relation/Attribute、继承/接口/基数约束；TypeQL 函数支持嵌套、递归、否定和 tabling，可计算传递闭包 | TypeDB 3 已用函数替换 TypeDB 2 的规则；需要显式调用，结果按查询计算而非自动物化；无原生投研时态/provenance 合同 | **很适合稳定产业链 Schema 和精确全链递归查询**；Event 双时态、Evidence lineage、DerivedSignal 生命周期仍需建模 |
| 图/向量/Datalog 数据库 | **[CozoDB](https://github.com/cozodb/cozo) — 4,092** | [`v0.7.6`](https://github.com/cozodb/cozo/tree/v0.7.6)；当前 main commit [`481af05`](https://github.com/cozodb/cozo/commit/481af058abac9444ea8c9c52c78f096ed4b5bfc4) | 事务型关系数据库；以 Datalog 查询隐式图，支持递归、安全聚合、图算法、向量 HNSW 与 Datalog 统一、可选 relation time travel | 没有 ontology/LLM/Agent/文档摄取平台；Schema 不是 OpenSPG 式领域本体；官方仍说明 1.0 前不保证语法/API/存储兼容，最新稳定版发布于 2023-12 | **适合验证“同一底座完成精确递归 + 向量召回 + 历史查询”**，但生产活跃度和版本稳定性必须先评估 |
| 版本化时态知识图谱 | **[TerminusDB](https://github.com/terminusdb/terminusdb) — 3,388** | [`v12.0.7`](https://github.com/terminusdb/terminusdb/tree/v12.0.7)，commit [`57f2093`](https://github.com/terminusdb/terminusdb/commit/57f2093baeafd65e16004e84b7b58e0c5cf72858) | JSON/JSON-LD document + graph；Schema constraints；Git-like branch/commit/diff/merge；WOQL 的 Datalog/Prolog unification、path 查询；Allen interval algebra 和时间推理 | 不提供 KAG/Codex 式 LLM Planner；官网对“rule inference”的表述比公开示例更宽，复杂递归/物化规则必须 PoC 验证 | **本短名单中最值得做投研数据底座 PoC 的候选**：版本、时间、Schema 与审计很匹配；需补 Agent MCP 和事件传导规则层 |
| Semantic Web 规则平台 | **[Apache Jena](https://github.com/apache/jena) — 1,411** | [`jena-6.2.0`](https://github.com/apache/jena/tree/jena-6.2.0)，commit [`d0676a2`](https://github.com/apache/jena/commit/d0676a2c402ead68a133596f4ac5977be64dd251) | RDF store/TDB、SPARQL、Ontology API、RDFS/OWL reasoner、通用规则引擎；支持 forward、backward、hybrid；可记录 `RuleDerivation` 推导路径 | 没有原生 LLM/Agent 编排；双时态、事件有效期和金融数据合同需自行建模；Java/RDF 工程门槛较高 | **确定性规则与可解释推导最成熟**；适合做规则侧车或语义底座，但不是开箱即用投研平台 |
| Datalog 规则执行器 | **[Soufflé](https://github.com/souffle-lang/souffle) — 1,149** / **[Rulewerk](https://github.com/knowsys/rulewerk) — 36** | Soufflé [`2.5`](https://github.com/souffle-lang/souffle/tree/2.5)，commit [`5682a9f`](https://github.com/souffle-lang/souffle/commit/5682a9f12e2668ecdd26348fe63cc508bc0fcf47)；Rulewerk [`v0.9.0`](https://github.com/knowsys/rulewerk/tree/v0.9.0) | Soufflé 将 Datalog 编译为并行 C++，支持递归和 provenance；Rulewerk/VLog 支持 facts、existential rules、stratified negation、查询，并可读 RDF/转换 OWL | 不是在线图数据库、文档检索或 Agent 平台；时态/溯源数据模型需业务定义；Rulewerk 活跃度和 stars 低 | 适合成为独立 Signal Propagation Executor；不适合作为 OpenSPG/Graphiti 的完整替代 |
| 时态图逻辑执行器 | **[PyReason](https://github.com/lab-v2/pyreason) — 348** | [`v3.6.0`](https://github.com/lab-v2/pyreason/tree/v3.6.0)，commit [`e1a94af`](https://github.com/lab-v2/pyreason/commit/e1a94af33e1f9d925c9df8284113dd0e14fe8a73) | annotated、real-valued、graph-based、temporal logic；以初始 facts + logical rules 在图上推理；强调 explainable inference | 不是持久化知识图谱/ontology 管理平台；数据规模、并发、规则治理和生产运维需验证 | **最贴近“外部产业链信号传导执行器”**；可与 Graphiti/Cognee/TerminusDB 搭配，而非单独承担所有存储与检索 |
| 符号 AI / 超图 | **[OpenCog](https://github.com/opencog/opencog) — 2,474**；AtomSpace 992；Hyperon 270 | OpenCog snapshot [`ae68bda`](https://github.com/opencog/opencog/commit/ae68bda779f16571bb017b8d3ea56ff8f50a822f)；AtomSpace [`c8d633b`](https://github.com/opencog/atomspace/commit/c8d633bf272b838c2132c21b7c8ddf169a18dd22)；Hyperon [`v0.2.10`](https://github.com/trueagi-io/hyperon-experimental/tree/v0.2.10) | AtomSpace 是内存 hypergraph/metagraph KR、查询和 graph rewriting；OpenCog 有 URE/PLN；Hyperon 以 MeTTa 表达模式匹配、重写和多种 inference | 不是常规业务知识图谱产品；持久化需额外模块；学习、部署和建模复杂，Hyperon 仍是 experimental | 研究价值高，但不适合作为当前投研系统的首个生产底座 |

## 关键事实核验

### Cognee：为何“像”，又为何不是规则引擎

Cognee v1.5.0 的确已经不只是简单向量 RAG：

- [`RDFLibOntologyResolver`](https://github.com/topoteretes/cognee/blob/v1.5.0/cognee/modules/ontology/rdf_xml/RDFLibOntologyResolver.py) 能读取 RDF/OWL ontology，做类/个体匹配与子图获取；
- [`temporal_graph`](https://github.com/topoteretes/cognee/tree/v1.5.0/cognee/tasks/temporal_graph) 抽取 Event/Entity 并构建时态图，[`temporal_retriever.py`](https://github.com/topoteretes/cognee/blob/v1.5.0/cognee/modules/retrieval/temporal_retriever.py) 提供时间召回；
- [`ProvenanceEntry`](https://github.com/topoteretes/cognee/blob/v1.5.0/cognee/modules/provenance/models/ProvenanceEntry.py) 保存 source quote、valid interval、checksum chain、derived-from、revision 与 invalidation；相关能力有集成/单测；
- [README](https://github.com/topoteretes/cognee/blob/v1.5.0/README.md) 明确支持本地图、Neo4j/Neptune、向量库、MCP 和 Agent memory。

但这套源码的主路径是 `add → cognify → memify/remember → search/recall`。所谓 ontology grounding 是让抽取结果对齐 ontology，所谓 graph reasoning 是利用图关系检索和组织上下文。仓库中出现的 `rule_engine.py` 位于 benchmark adapter，并不是 Cognee 通用运行时规则引擎。[`logistics benchmark rule_engine.py`](https://github.com/topoteretes/cognee/blob/v1.5.0/cognee/eval_framework/benchmark_adapters/logistics_system_utils/rule_engine.py)

因此：**Cognee 可以竞争 Graphiti/KAG 的记忆与图文召回位置，不能直接替代 OpenSPG KGDSL 或观潮家的产业传导执行器。**

### TypeDB：当前版本仍能递归，但不再是旧式自动规则

TypeDB 3.12.3 的 Schema 和 TypeQL 函数都存于数据库。官方文档说明函数可以嵌套、递归和带否定；递归函数使用 tabling 终止环，并给出 transitive closure 示例。[TypeQL Functions](https://typedb.com/docs/typeql-reference/functions/)、[Queries as Functions](https://typedb.com/docs/core-concepts/typeql/queries-as-functions/)

同时，官方迁移文档明确说 TypeDB 3 的 functions 替换 TypeDB 2 rules：函数必须在查询中显式调用，不会像旧 inference toggle 那样让所有查询自动看到推断实例，也不会预先物化全部结果。[Functions vs Rules](https://typedb.com/docs/typeql-reference/functions/functions-vs-rules/)、[2.x → 3.x 差异](https://typedb.com/docs/reference/typedb-2-vs-3/diff/)

这对投研反而可能是优点：每次 AnalysisRun 可以显式指定 `as_of/horizon/rule_version` 并调用递归函数，避免旧派生信号无条件污染当前图。但 Signal 是否持久化、何时失效仍由观潮家负责。

### CozoDB：把递归图查询与向量检索放进同一个 Datalog 数据库

CozoDB 是事务型关系数据库，但使用 Datalog 表达查询和隐式图。官方明确支持递归、安全聚合、PageRank 等图算法；HNSW 向量检索可以直接参与 Datalog unification，甚至用于递归 Datalog。relation 还可以选择开启 time travel，在历史时点查询数据。[固定版 README](https://github.com/cozodb/cozo/blob/v0.7.6/README.md)、[当前官方仓库](https://github.com/cozodb/cozo)

它的优势是底层能力组合紧凑，适合精确产业链闭包、图算法、相似检索和历史查询。但它没有 OpenSPG Schema、Graphiti Episode、Cognee Agent memory 或现成 LLM pipeline；官方还明确说明 1.0 前不保证兼容性。因此它应作为底层数据库 PoC 候选，而不是现成投研平台。

### TerminusDB：最接近“版本化 Event + 时间推理”的数据库

TerminusDB v12.0.7 README 和官方文档能确认：

- JSON/JSON-LD document 与图关系共存，Schema 可约束文档；
- 每次变更形成 immutable layer/commit，可按 branch 或历史 commit 查询，支持 diff/merge；
- WOQL 是基于 Prolog 的 Datalog 查询语言，有 unification、closed-world 语义和图 path；
- v12 提供 ISO8601 时间类型、Allen interval algebra、range 查询和多步时间谓词组合。

来源：[固定版 README](https://github.com/terminusdb/terminusdb/blob/v12.0.7/README.md)、[WOQL 解释](https://terminusdb.org/docs/woql-explanation/)、[WOQL 执行世界/历史 layer](https://terminusdb.org/docs/woql-getting-started/)、[时间处理教程](https://terminusdb.org/docs/time-tutorial-patterns/)。

边界是：公开文档最充分展示的是 Datalog 查询、unification、path 和时间谓词；“任意业务规则自动物化/递归维护”的产品能力不能只根据一句 marketing 文案推断。PoC 必须实际验证递归传导、规则版本、乱序 Event 和撤回重放。

### Apache Jena：真正规则推理的成熟基线

Jena 的 inference subsystem 将 base RDF + ontology + rules 绑定成 `InfModel`，内置 RDFS/OWL reasoner 和通用规则引擎，支持 forward、backward、hybrid。开启 derivation logging 后，`InfModel.getDerivation()` / `RuleDerivation` 可以递归解释某个 inferred triple 来自哪些规则和源 triple。[官方 inference 文档](https://jena.apache.org/documentation/inference/index.html)、[`RuleDerivation`](https://jena.apache.org/documentation/javadoc/jena/org.apache.jena.core/org/apache/jena/reasoner/rulesys/RuleDerivation.html)

这是真正规则推理，不是“把检索图路径放入 LLM prompt”。它的不足不是推理能力，而是缺少面向 Agent、事件摄取、双时态和投研分析的产品层。

## 对事件驱动产业链分析的适配排序

### 第一组：值得做底座 PoC

1. **TerminusDB**：最适合验证 Event/Evidence 的版本化、时间窗口、历史回看和 Datalog 查询。
2. **TypeDB**：最适合验证强产业链 Schema、关系约束和全链递归函数。
3. **CozoDB**：最适合验证 Datalog 递归、向量召回、图算法和历史查询能否由单一轻量底座承担。
4. **Cognee**：最适合验证 Agent memory、文档/事件抽取、temporal recall 与 provenance；规则传播要外置。

### 第二组：适合作为规则/信号执行器

1. **PyReason**：直接表达带时间和实值注解的图规则，最贴近方向、强度、周期信号。
2. **Apache Jena**：成熟规则、OWL/RDFS 和 derivation trace，适合确定性规则与审计。
3. **Soufflé / Rulewerk**：适合大规模 Datalog 或存在规则，但要自行封装在线服务和数据合同。

### 第三组：不是当前首选

- **TrustGraph**：完整 Agent context/RAG 平台，但与顶层 Codex Agent 的编排职责重叠，且没有已核实的业务规则引擎。
- **OpenCog/Hyperon**：表达力和研究价值高，工程复杂度远超当前 PoC 需要。

## 推荐验证方式

不要迁移完整 ReasonSmoke UI。先固定同一套领域 Tool 合同与 10 条 Event：

```text
upsert_event(event, evidence, valid_time, known_time, revision)
get_chain_nodes(anchor)
get_active_events(anchor, as_of, horizon)
run_propagation(anchor, as_of, horizon, rule_version)
explain_signal(signal_id)
retract_event(event_id, revision)
replay(anchor, as_of)
```

分别验证：

- TerminusDB 是否能正确保留版本、时态和撤回历史；
- TypeDB 是否能用一个递归函数覆盖全部节点并处理环；
- Cognee 是否能稳定召回时间窗口内的 Event、Evidence 和 provenance；
- PyReason/Jena 是否能输出逐步推导链，而不是只给最终标签；
- 顶层 Codex Agent 在不更换提示词的情况下，能否消费相同 Tool 输出。

## 最终判断

一句话回答“是不是还有一个高星、类似的项目”：

> **大概率是 Cognee，但 Cognee 更接近 Graphiti/KAG 的 Agent memory 与 GraphRAG 层，不是 OpenSPG/Semantica 的通用规则引擎。**

若以观潮家事件驱动投研为目标，真正值得追加 PoC 的组合是：

> **TerminusDB 或 TypeDB 作类型化/版本化事实底座，PyReason 或 Jena 作确定性规则侧车，Cognee 只作为 Agent 记忆与文档检索候选。**
