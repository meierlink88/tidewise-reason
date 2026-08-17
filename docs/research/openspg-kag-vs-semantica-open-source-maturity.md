# OpenSPG/KAG 与 Semantica 的开源成熟度对比

> 调研日期：2026-08-17  
> 比较基线：OpenSPG `v0.8`、KAG `v0.8.0`、Semantica `v0.6.5`。  
> 范围：只评价公开仓库中可以检查、构建和部署的内容；不把 GitHub stars 当作成熟度证据。

## 结论

不能用一个总分准确概括两者：

- **作为一个完整、可自行修改和部署的开源产品，Semantica 的成熟度更高。** 后端、REST API、CLI、MCP、Docker 和 React Explorer UI 都在同一公开仓库中，wheel 也会携带 UI 静态文件。
- **作为专业知识图谱的语义建模、知识构建和规则推理内核，OpenSPG + KAG 更成熟、更深。** OpenSPG 的 SPG-Schema、Builder、KGDSL/逻辑与物理执行层以及 KAG 的 Builder/Solver 不是展示性壳层，而是较大规模的实质实现。
- **Semantica 还不能仅凭 README 的广泛功能列表视为生产成熟。** 它是创建于 2025 年的年轻项目，当前仍为 `0.6.5`；公开主 CI 没有运行 Python 后端测试，并且部分被宣传为完整能力的代码仍明确包含 placeholder 或未实现路径。
- **OpenSPG 的短板不是单纯“没有前端源码”。** 官方 8887 产品还缺少公开的 OpenSPGApp BFF、项目/账户/权限/配置、任务和会话编排等业务层，导致 GitHub 源码不能等价重建官方完整产品。

因此，如果问题是“哪个公开仓库更像一个完整可控的 OSS 产品”，答案是 **Semantica**；如果问题是“哪个语义知识图谱/规则推理技术底座更成熟”，答案是 **OpenSPG + KAG**。

## 分维度判断

| 维度 | OpenSPG `v0.8` + KAG `v0.8.0` | Semantica `v0.6.5` | 判断 |
|---|---|---|---|
| 开源边界完整性 | 引擎与 KAG 核心开放，但官方 UI、BFF 和业务编排不完整 | Python 后端、API、CLI、MCP、Docker、Explorer UI 均公开 | Semantica 明显领先 |
| 语义建模深度 | SPG-Schema、概念/实体/事件模型、属性图语义增强、可编程算子 | OWL、SHACL、SKOS、ontology 模块广，但部分能力仍在快速补齐 | OpenSPG 领先 |
| 规则/图推理深度 | KGDSL parser、逻辑计划、物理计划、runner、UDF、warehouse 分层完整 | Datalog 有实质实现，但 Rete/SPARQL 等部分路径仍很浅或为 placeholder | OpenSPG 明显领先 |
| KAG/RAG 能力 | Schema 约束构建、知识与 chunk 互索引、逻辑形式引导的检索和多跳问答 | ingestion、graph/vector store、agent context、provenance 覆盖广 | 取决于场景；专业问答更偏 OpenSPG/KAG |
| UI 与自托管体验 | 官方产品 UI 不能由 GitHub 等价重建 | Explorer 源码公开，Docker 和 wheel 都包含 UI | Semantica 明显领先 |
| 发布活跃度 | OpenSPG 最新稳定版为 2025-06；KAG `0.8.0` 之后有少量提交，但无新稳定版 | 2025-11 至 2026-08 有密集发布，最新 `0.6.5` | Semantica 领先 |
| 测试证据 | 有 Java/Scala/Python 测试，但 OpenSPG CI 使用 `-DskipTests`，KAG CI 的 pytest 步骤被注释 | 有大量 Python 测试文件，但主 CI 不执行 pytest，只跑 3 组前端测试并构建包 | 两者都不成熟；Semantica 测试面更广，但缺少门禁 |
| CI/安全/发布供应链 | 基础 CI、CLA、许可证检查，Actions 版本较旧 | CodeQL、Bandit、Semgrep、Safety、pip-audit、Checkov、Action SHA pin、PyPI OIDC/provenance | Semantica 领先 |
| 稳定性与历史验证 | OpenSPG 仓库历史更长，核心规模和企业技术血缘更强 | 项目不到两年、未到 1.0，仍在高速修补 API/安全边界 | OpenSPG 核心领先 |
| 社区与治理 | 多名核心贡献者，但发布和主仓开发已放缓 | 活跃、PR 多，但提交高度集中于一名维护者，bus factor 风险较高 | 各有风险 |

## 关键事实与边界

### Semantica 的强项

Semantica 的公开仓库包含完整的产品表面：

- `semantica/` Python 包；
- `explorer/` React/TypeScript UI；
- REST server、worker、CLI、MCP 入口；
- Dockerfile 与 Compose；
- 文档、cookbook、贡献指南、安全政策和发布流水线。

其 [README](https://github.com/semantica-agi/semantica) 展示了 ingest、parse、normalize、extract、KG、ontology、reasoning、provenance、graph/vector store 和 Explorer 的统一产品形态。公开 [CI workflow](https://github.com/semantica-agi/semantica/blob/v0.6.5/.github/workflows/ci.yml) 还明确检查 Explorer 静态文件是否被打进 wheel，这一点正好是当前 OpenSPG GitHub 交付缺少的。

Semantica 的发布和安全工程也较现代：[Releases](https://github.com/semantica-agi/semantica/releases) 显示从 `v0.0.1` 到 `v0.6.5` 的密集迭代；仓库还有多种静态扫描、依赖审计以及基于 OIDC 的 PyPI 发布流程。

### Semantica 的成熟度警告

这些优点不能直接推导为“所有内核都已成熟”：

1. `v0.6.5` 的公开 CI 没有 `pytest`、Python coverage、lint、mypy 或多 Python 版本矩阵；它只验证 Python 3.11 下的包构建、三组前端测试和 UI 打包。
2. 仓库虽然有大量测试，但“有测试文件”和“每个 PR 都由这些测试门禁”是两回事。
3. [Rete 实现](https://github.com/semantica-agi/semantica/blob/v0.6.5/semantica/reasoning/rete_engine.py) 中的 alpha 条件匹配和 beta join 仍是简化占位逻辑；其他存储、SPARQL 推理、embedding provider 和 CLI 路径也可见 placeholder 或 `NotImplementedError`。
4. 项目版本仍未到 1.0，虽然 `pyproject.toml` 自我标记为 `Production/Stable`，但这只是项目声明，不是独立生产验证。
5. `v0.6.5` 发布说明集中修复了认证缺失、Cypher/SPARQL 注入、SSRF、pickle RCE、XXE 和 DoS 等问题。积极修复是好信号，但这些问题直到近期才暴露，也说明服务安全边界仍在收敛。
6. `SECURITY.md` 的支持版本仍停留在旧的 `0.2.x`，与当前 `0.6.5` 不一致。

因此，更准确的定位是：**Semantica 是功能覆盖广、开源体验好、迭代很快的年轻平台，而不是已经被充分证明的生产级知识推理内核。**

### OpenSPG/KAG 的强项

[OpenSPG](https://github.com/OpenSPG/openspg) 的公开代码包含 Schema、Builder 和 Reasoner 的实质实现。Reasoner 不是单文件规则示例，而是包含 KGDSL parser、逻辑计划、物理计划、runner、UDF、catalog 和 warehouse 的多模块 Java/Scala 系统。KAG 公开的 Builder、Indexer、Solver、KNEXT、MCP 和 CLI 则围绕 OpenSPG 形成专业领域知识库的构建与问答链路。

[KAG README](https://github.com/OpenSPG/KAG) 将其目标明确限定为专业领域知识库的逻辑推理与事实问答，核心包括知识/Chunk 互索引、Schema 约束构建和逻辑形式引导的混合推理。这个范围比 Semantica 的“通用上下文、决策、治理、连接器”更窄，但在该核心问题上更深。

### OpenSPG/KAG 的成熟度警告

1. [OpenSPG `v0.8`](https://github.com/OpenSPG/openspg/releases/tag/v0.8) 发布于 2025-06-29，公开仓库之后基本没有继续演进；[KAG `v0.8.0`](https://github.com/OpenSPG/KAG/releases/tag/v0.8.0) 也没有更新的稳定版。
2. OpenSPG CI 构建时使用 `-DskipTests`；KAG 的 CI 只跑格式检查，pytest 步骤被注释。因此两者公开 CI 也不能证明后端回归测试持续通过。
3. 官方 Compose 使用的完整 server JAR 与 GitHub 可编译 server JAR 不等价。公开源码缺少的不只是管理后台静态资源，还包括 UI 所依赖的 OpenSPGApp BFF、账户/权限/项目/配置、任务与会话编排，以及部分产品适配器。
4. KAG `0.8` 文档明确当时只开放 kg-builder 和 kg-solver，kag-model 未包含；后续推理产品线也发生了独立演进。
5. 所以“核心引擎开放”成立，“官方整套产品可以从 GitHub 完整重建”不成立。

## 对 Tidewise 的选择建议

若目标是尽快拥有一套可以完全掌控源码、带 UI、API、Docker 和基础治理能力的开源工作台，Semantica 更适合进入 PoC 候选。

若目标是承载 Tidewise 已设计的 TBox、领域 Schema、知识构建和确定性规则/多跳推理，OpenSPG/KAG 的核心模型仍更匹配，不应仅因官方 UI 不开放就直接替换。

更稳妥的技术决策是：

- 将 **OpenSPG/KAG** 视为“较成熟但产品层不完整开放的专业语义/推理引擎”；
- 将 **Semantica** 视为“完整开放、交付体验较好但内核仍在快速成熟的通用图与 AI 治理平台”；
- 在替换前用同一组 Tidewise 数据验证 Schema 约束、实体消歧、规则表达、解释链、增量更新和查询正确性，而不是只比较 README、stars 或 UI。

## 一手资料

- [OpenSPG repository](https://github.com/OpenSPG/openspg)
- [OpenSPG v0.8 release](https://github.com/OpenSPG/openspg/releases/tag/v0.8)
- [KAG repository](https://github.com/OpenSPG/KAG)
- [KAG v0.8.0 release](https://github.com/OpenSPG/KAG/releases/tag/v0.8.0)
- [Semantica repository](https://github.com/semantica-agi/semantica)
- [Semantica releases](https://github.com/semantica-agi/semantica/releases)
- [Semantica v0.6.5 CI](https://github.com/semantica-agi/semantica/blob/v0.6.5/.github/workflows/ci.yml)
- [Semantica v0.6.5 Rete source](https://github.com/semantica-agi/semantica/blob/v0.6.5/semantica/reasoning/rete_engine.py)
- [Semantica security policy](https://github.com/semantica-agi/semantica/blob/main/SECURITY.md)

