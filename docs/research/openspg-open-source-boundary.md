# OpenSPG / KAG 开源边界核查

核查日期：2026-08-17  
重点版本：OpenSPG `v0.8`、KAG `v0.8.0`，并补充截至核查日的官方仓库现状。

## 结论

OpenSPG 不能简单概括为“只有 Admin 前端没开源”。更准确的说法是：

- **OpenSPG 引擎层的大部分核心能力有 Apache-2.0 源码**：SPG Schema、知识构建、KGDSL/逻辑推理、存储和检索适配接口及若干本地实现、核心 Server 和 `/public/v1/*` API 都在 `OpenSPG/openspg`。
- **KAG 0.8 的 Builder/Solver 框架有 Apache-2.0 源码**，包括文档解析、抽取/对齐/索引、图与文本检索、规划、执行、生成、MCP 和 CLI；它不是只有界面的演示壳。
- **官方 8887 端口提供的完整“产品”不能从上述源码等价重建**。缺失的不只是浏览器静态前端源码，还包括 UI 所依赖的一整层 OpenSPGApp Web/BFF、产品业务服务和任务编排源码。
- **官方 Server 二进制还包含 GitHub `v0.8` 没有的厂商适配实现**，至少包括 AIStudio 计算适配和 KGFabric 图存储/搜索适配。它们是可选云/企业适配，不是 Neo4j 本地引擎运行的必需条件，但确实说明官方 JAR 的范围大于公开源码。
- **KAG 0.8 仓库没有发布其架构图所称的 `kag-model`**。官方 README 明确称该版本只发布 kg-builder 和 kg-solver；后来官方另建了 `KAG-Thinker` 仓库，提供训练/推理方法、训练数据和模型下载入口，但它是独立后续发布，不能倒推为 KAG 0.8 已包含模型。

因此应区分两个命题：

1. “OpenSPG/KAG 的核心图谱构建与推理框架是否有源码？”——**是，且源码是实质性的，可以通过 SDK、CLI 和核心 API 使用。**
2. “官方 Docker 中看到的完整 OpenSPG/KAG 产品是否完全开源、可由 GitHub 源码复现？”——**否。UI、产品 BFF/应用服务以及部分厂商适配只出现在官方二进制中。**

## 能力边界

| 能力 | 开源状态 | 可验证证据 | 实际影响 |
| --- | --- | --- | --- |
| SPG Schema 与服务端核心 | 有源码 | [`server` 模块清单](https://github.com/OpenSPG/openspg/blob/v0.8/server/pom.xml#L33-L52)包含 API、Schema、Scheduler、Reasoner、DAO；[核心 HTTP Controller 目录](https://github.com/OpenSPG/openspg/tree/v0.8/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi)包含 Project、Schema、Graph、Query、Reason、Retrieval、Builder、Scheduler 等接口 | 不依赖产品 UI 也能进行项目、Schema、图数据、构建和查询操作 |
| SPG-Builder | 有源码 | 官方说明列出结构化/非结构化知识构建和算子框架；[`builder/core`](https://github.com/OpenSPG/openspg/tree/v0.8/builder/core/src/main/java/com/antgroup/openspg/builder/core)公开逻辑/物理计划、抽取、映射、向量化、融合、链接等实现 | 核心知识构建不是只存在于官方 JAR 的黑盒 |
| KGDSL 与符号推理 | 有源码 | 官方 README 将 KGDSL、逻辑规则推理列为核心能力；[`reasoner`](https://github.com/OpenSPG/openspg/tree/v0.8/reasoner)公开 parser、logical/physical planner、runner、catalog、UDF 等模块 | 本地逻辑推理执行能力有实现源码；公开实现仍可能存在算子覆盖和性能边界，但不是“推理器未开源” |
| Cloudext 接口及常用本地适配 | 有源码 | [`cloudext`](https://github.com/OpenSPG/openspg/tree/v0.8/cloudext)公开 Neo4j、TuGraph、Elasticsearch、Neo4j Search、Redis、MinIO、OSS 等适配以及 graph/search/cache/object-storage/computing-engine 接口 | 官方推荐的 Neo4j + MinIO 本地拓扑可由公开代码支撑 |
| KAG Builder/Solver | 有源码 | [`KAG v0.8.0`](https://github.com/OpenSPG/KAG/tree/v0.8.0/kag)包含 builder、indexer、solver、retriever、LLM/vector/rerank client、MCP/CLI；官方 README 说明其 Builder/Solver 职责和混合推理流程（[架构说明](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md#L157-L165)） | 可在开发者模式中自行配置 LLM/Embedding/Reranker，执行构建和问答；不需要产品 UI 才能使用框架 |
| Web UI 源码 | 未开源 | 官方维护者明确回复“UI codes is not open source”（[Issue #209](https://github.com/OpenSPG/openspg/issues/209#issuecomment-2066134123)）；源码构建 JAR 缺少 `static`、官方 Docker JAR 有静态目录的同类现象也被确认（[Issue #219](https://github.com/OpenSPG/openspg/issues/219#issuecomment-2080420434)）。后续维护者曾称 Web 层计划开源（[Issue #458](https://github.com/OpenSPG/openspg/issues/458#issuecomment-2577335442)），但截至核查日仍有未解决的前端开源请求（[#569](https://github.com/OpenSPG/openspg/issues/569)、[#589](https://github.com/OpenSPG/openspg/issues/589)、[#618](https://github.com/OpenSPG/openspg/issues/618)） | GitHub 源码构建的 Server 首页 404 是预期结果；从官方 JAR 复制静态文件不等于获得可维护的前端源码 |
| OpenSPGApp 产品 Web/BFF | **仅少量基础代码开源，完整实现只在官方二进制中可见** | [`OpenSPG/openspgapp`](https://github.com/OpenSPG/openspgapp)公开仓库最后一笔代码提交是 2023-12-12，`api/http-server`、`api/facade`、`arks/sofaboot` 只有 POM（例如 [`api/http-server/pom.xml`](https://github.com/OpenSPG/openspgapp/blob/master/api/http-server/pom.xml)），公开 Java 代码主要是 account/permission/DAO 基础；而官方 JAR 含完整 `com.antgroup.openspgapp-*` 模块，见下文二进制核查 | UI 依赖的 `/v1/*` 产品 API、登录/权限、项目和应用管理、Schema/数据 UI 适配、模型配置、Builder Job、会话/任务/对话/Chat 等流程不能由当前 `openspgapp` 仓库重建 |
| KAG 专用模型 | **KAG 0.8 未包含；后续有独立发布** | KAG 0.8 README 明确写道“本次发布只涉及” kg-builder、kg-solver，`kag-model` 后续逐步开源（[原文位置](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md#L157-L165)）。KAG 0.8 后续说明称已“适配” KAG-Thinker，而非把模型放进 KAG 仓库（[master 发布说明](https://github.com/OpenSPG/KAG/blob/master/README_cn.md#L60-L65)）；独立的 [`OpenSPG/KAG-Thinker`](https://github.com/OpenSPG/KAG-Thinker)后来提供训练/推理说明、数据集和模型入口 | KAG 框架可接外部通用 LLM；复现特定论文/产品效果还依赖模型、数据、提示词、检索服务和评测条件，不能仅凭 KAG 0.8 仓库保证 |
| AIStudio / KGFabric 适配 | GitHub `v0.8` 无源码，官方 JAR 有字节码 | 官方 README 将 Cloudext 定义为可插拔适配层（[说明](https://github.com/OpenSPG/openspg/blob/v0.8/README.md#L30-L38)）。官方 Server JAR 的固定 digest 核查发现 `cloudext-impl-computingengine-aistudio`、`cloudext-impl-graph-store-kgfabric`、`cloudext-impl-search-engine-kgfabric`，而 [`v0.8 cloudext` 树](https://github.com/OpenSPG/openspg/tree/v0.8/cloudext/impl)没有这些模块 | 这是额外厂商/企业能力，而不是本地 Neo4j 方案的必需核心；不能据此断言本地 Reasoner 不完整，但也不能称官方二进制全部可从 GitHub 重建 |

## 为什么缺失的不只是“Admin 管理后台”

“Admin 后台”容易让人误以为只是账号和权限页面。官方二进制中的 OpenSPGApp 范围明显更大。

对官方镜像 `spg-registry.cn-hangzhou.cr.aliyuncs.com/spg/openspg-server@sha256:fe6708deef9ebb8da8da7b1cb643e83b827769a5be8811961311639aa1f2cb88` 内 JAR 的只读检查显示：

- `BOOT-INF/classes/static/` 有 294 个条目，包括 `index.html` 和编译后的 JS/CSS；
- `com.antgroup.openspgapp-api-http-server` 内有 `ProjectsController`、`AccountController`、`PermissionController`、`SchemasController`、`DatasController`、`BuilderJobController`、`ModelController`、`DialogController`、`TaskController`、`SessionController`、`ChatController`、`AppController`、`StatisticsController` 等；
- 还有 `openspgapp-biz-schema`、`biz-builder`、`biz-reasoner`、`openspgapp-core-reasoner-service`、DAO、API facade/client 等业务与执行模块；
- Reasoner 产品层中包含任务、会话、反馈、统计和 `TaskRunner` 等应用编排实现。

这些模块多数不是 SPG 图推理算法本身，而是把引擎和 KAG 组装成可登录、可配置、可提交任务、可管理知识库和可对话的产品。它们对 **UI 完整可用** 是核心依赖，对 **SDK/CLI 方式使用引擎** 则不是必需。

## 官方 Docker 与源码构建的关系

官方 [`v0.8 docker-compose.yml`](https://github.com/OpenSPG/openspg/blob/v0.8/dev/release/docker-compose.yml)直接引用 `openspg-server:latest`，并没有从 Compose 中重建 Server。公开的 [`server/Dockerfile`](https://github.com/OpenSPG/openspg/blob/v0.8/dev/release/server/Dockerfile)只是把已有的 `target/arks-sofaboot-0.0.1-SNAPSHOT-executable.jar` 加入镜像。因此：

- Compose 能启动完整 UI 产品，不代表组成该 JAR 的全部源码都在 GitHub；
- GitHub `v0.8` 后端 JAR和官方镜像 JAR不是同一内容集合；
- 把官方 `static` 目录叠加到源码后端只能补页面外壳，不能补 OpenSPGApp `/v1/*` BFF 和产品服务；
- 若需要官方 UI 的完整行为，当前可行基线是固定官方 Server 镜像/JAR；若要求完全源码可审计，则应走 `/public/v1/*`、KAG/KNEXT CLI/SDK，或自行实现产品层。

注意：官方 Compose 使用浮动 `latest`，本文的 JAR 清单只对上面明确记录的 digest 成立。该镜像创建时间为 2025-07-03，时间上紧邻 0.8 发布，但官方镜像没有可验证的版本/源码 commit 标签，因此不能把它的每个字节严格归属到某个 Git commit。

## 没有证据支持的更强断言

以下说法目前证据不足，不应写成事实：

- “OpenSPG 的 Schema、Builder 或 Reasoner 核心算法没有开源。”公开仓库存在大量对应实现源码和测试，且本地已能从 `v0.8` 编译并运行核心 API。
- “官方二进制中所有多出来的模块都是本地运行必需的核心。”AIStudio、KGFabric 属于可插拔厂商适配；本地 Neo4j/MinIO 路径不依赖它们。
- “`openspgapp` 完全没有开源。”账号、权限、DAO 等少量基础代码存在；准确表述是该仓库远不足以构建官方产品层。
- “KAG 完全没有模型可用。”KAG 0.8 框架本身支持外部 LLM/Embedding/Reranker，后来也有独立 KAG-Thinker 发布；准确表述是 `kag-model` 不在 KAG 0.8 发布范围内。
- “KAG-Thinker 的发布意味着官方产品和论文效果可完全复现。”这需要另行核对模型许可证、精确权重/数据版本、服务配置和评测协议，不能从仓库存在本身推出。

## 二进制核查方法

以下命令只读取官方镜像内容，用于让上述“只在二进制中可见”的结论可复核：

```bash
docker image inspect \
  spg-registry.cn-hangzhou.cr.aliyuncs.com/spg/openspg-server@sha256:fe6708deef9ebb8da8da7b1cb643e83b827769a5be8811961311639aa1f2cb88

docker run --rm --entrypoint sh \
  spg-registry.cn-hangzhou.cr.aliyuncs.com/spg/openspg-server@sha256:fe6708deef9ebb8da8da7b1cb643e83b827769a5be8811961311639aa1f2cb88 \
  -c 'jar tf /arks-sofaboot-0.0.1-SNAPSHOT-executable.jar'
```

二进制类名只能证明某功能实现存在于发布物，不能替代源码，也不能自动授予反编译、修改或再分发许可。
