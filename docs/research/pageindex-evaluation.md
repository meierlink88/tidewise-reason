# PageIndex 作为观潮家推理引擎的适配性评估

> 调研时间：2026-08-11
>
> PageIndex 锁定版本：[`d375c00a5a6a45bb5caeca31790f777e222c154a`](https://github.com/VectifyAI/PageIndex/tree/d375c00a5a6a45bb5caeca31790f777e222c154a)，包版本 `0.2.9`、状态 `Alpha`
>
> Mafin2.5-FinanceBench 锁定版本：[`1c890d5e0fd9929953d38282614555847727011d`](https://github.com/VectifyAI/Mafin2.5-FinanceBench/tree/1c890d5e0fd9929953d38282614555847727011d)
>
> FinanceBench 锁定版本：[`cc39aeb4afdf33909ee1412188bf89035950c2eb`](https://github.com/patronus-ai/financebench/tree/cc39aeb4afdf33909ee1412188bf89035950c2eb)

本文只使用项目官方仓库、官方文档/博客、官方 benchmark 仓库和 benchmark 原始仓库。为避免把产品宣称当成已验证事实，证据分为：

- **[官方说明]**：官方 README、文档或博客中的产品说明/宣称；
- **[源码事实]**：在上述锁定提交中可以直接复核的实现；
- **[工程判断]**：基于前两类证据，对观潮家架构适配性的判断。

## 一、结论

**PageIndex 不适合作为观潮家的核心“推理引擎”，不应替换 OpenSPG + KAG；它适合作为长文档 evidence retriever（证据检索器）做受控 PoC。**

PageIndex 的核心能力是把 PDF/Markdown 转成类似目录的层级树，让 LLM 或 Agent 沿树选择章节、读取页面，再基于原文作答。其“reasoning”主要是**查询时的 LLM 导航、证据选择和答案生成**，不是领域本体、结构化事实、规则、事件/时序、因果链或可演绎证明意义上的推理。[官方 README 的两阶段说明](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/README.md#L46-L73)与[官方框架说明](https://pageindex.ai/blog/pageindex-intro)均支持这一定位。

它最有价值的使用场景是年报、招股书、公告、研报、法规、合同和技术手册等长文档：先找出可追溯的章节/页码，再把证据交给 Tidewise Agent/KAG。它当前不提供 OpenSPG/KAG 所承担的领域 schema、实体关系、事实融合、规则推理和跨源知识治理能力。

建议的组合边界是：

```text
长 PDF / Markdown ──> OCR/解析 ──> PageIndex ──> 章节/页码/原文证据 ──┐
                                                                  ├─> Tidewise Agent ──> 带引用回答
结构化数据/实体关系/事件/规则 ──> OpenSPG + KAG ──> 可治理事实与推理 ──┘
```

PageIndex 的输出只能作为**候选证据**；若要写入权威知识图谱，仍需经过结构化抽取、实体对齐、来源与时间标注、冲突处理和验证，不能把模型生成答案直接当作事实。

## 二、适配性速览

| 能力 | OSS 当前适配性 | 判断 |
|---|---:|---|
| 单份长文档的章节/页码定位 | 高 | 是 PageIndex 的核心能力，值得 PoC |
| 单文档跨章节问答 | 中高 | Agent 可反复选页取证，但效果依赖模型与文档结构 |
| 原文页码/章节可追溯 | 中高 | 树节点和页面内容可返回；最终引用正确性仍需验收 |
| 中文文档、复杂表格、扫描件 | 未知 | 无官方语言矩阵和中文/扫描件公开质量 benchmark |
| 多文档检索与跨文档推理 | OSS 低 | 官方说明单文档是默认；需另做文档路由/向量检索 |
| 百万文档统一索引 | OSS 不具备 | 仅 Enterprise PageIndex File System 宣称具备，未开源、无可复现实验 |
| 领域本体、实体关系、事实融合 | 不具备 | 不能替代 OpenSPG |
| 规则、时序、因果和可解释演绎 | 不具备 | 不能替代 KAG 的知识推理职责 |
| 完整本地 retrieval/chat 服务 | 不具备 | `0.2.9` 本地 SDK 只覆盖索引、树和页面读取 |
| 直接生产自托管 | 中低 | Alpha；缺服务化、鉴权、队列、HA、增量更新等生产设施 |

## 三、它到底是什么

### 3.1 核心抽象

PageIndex 把文档转成层级 JSON 树。节点通常包含标题、节点 ID、起止页、摘要/描述、正文或子节点。查询时，模型先看树而不是整个文档，选择相关节点，再按节点映射回原始页面/文本。[官方框架文章](https://pageindex.ai/blog/pageindex-intro)把过程描述为：查看目录、选择章节、提取信息、判断证据是否充分，不充分则继续搜索，最后回答。

这是一种**文档结构索引 + Agentic retrieval**。它与知识图谱推理的差别在于：

- PageIndex 的节点主要表示文档章节，不是经过 schema 约束的领域实体/关系；
- PageIndex 的边主要表示目录层级，不代表可演绎的业务语义；
- 查询过程由 LLM 选择节点和生成答案，不提供确定性规则执行或证明语义；
- 输出的可解释性来自“查了哪些页/章节”，不是完整的事实推导链。

### 3.2 标准 PDF 建索引流程

锁定提交中的 classic pipeline 可概括为：

1. 用 PyPDF2 提取逐页文本和 token 统计；
2. 检查文档前部是否存在目录；
3. 如果目录包含页码，用 LLM 将目录转成结构并校准印刷页码与 PDF 物理页码；
4. 如果没有可用目录，把页面按约 20k token 分组、相邻组重叠一页，让 LLM 生成或延续层级结构；
5. 让 LLM 检查标题和起始页，修复失败项；
6. 对超过页数/token 阈值的大节点递归细分；
7. 可选生成文档描述和节点摘要。

这些步骤可在 [`page_index_classic.py` 的目录识别/无目录生成流程](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/page_index_classic.py#L516-L723)和[最终树构建流程](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/page_index_classic.py#L1127-L1280)中复核。

因此，“no chunking”应精确理解为：**不把固定 embedding chunk 作为最终检索单位**。标准建树内部仍会因上下文窗口把页面分批，并且使用重叠页面；不能把宣传语理解成整个系统完全不分批。

当前默认配置记录了 `gpt-4o-2024-11-20` 索引模型、`gpt-5.6-luna` 摘要模型、`gpt-5.4` 检索模型，以及 20 个目录页、每节点 10 页、每节点 20k token 等阈值；这些是仓库默认值，不是硬编码的唯一模型。[配置源码](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/config.yaml#L1-L13)

### 3.3 PageIndex Flash

Flash 是预览中的快速 PDF 建树路径。它用版面/字体等启发式规则生成初始层级结构，因此**结构生成本身可以不用 LLM**；但默认摘要仍需要 LLM，完整优化还包含确定性合并和 LLM 扩展。[Flash README](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/flash/README.md#L1-L50)和[公开 API](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/flash/api.py#L71-L124)显示其接受 PDF 路径或 `BytesIO`。

Flash 适合降低标准 pipeline 的 LLM 建树成本，但启发式布局解析对不同模板、表格密度、扫描质量和语言的稳健性仍需要在观潮家的真实材料上验证。

### 3.4 Markdown

Markdown pipeline 根据 `#` 到 `######` 标题和粗体标题生成树，输出以行号为定位基础；它与 PDF pipeline 是不同入口。[Markdown 标题解析](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/page_index_md.py#L32-L68)、[Markdown 主流程](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/page_index_md.py#L192-L280)

## 四、检索与“推理”流程

### 4.1 开源仓库真正提供的检索方式

最简单的官方 tree-search 教程把整棵树放进一个 prompt，要求模型返回 `thinking` 和 `node_list`，然后由应用读取所选节点。[官方 tree-search 示例](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/examples/tutorials/tree-search/README.md#L1-L25)

最新本地 Agent demo 暴露三个工具：

- 获取文档元数据；
- 获取不带全文的完整树；
- 获取指定页面范围的内容。

Agent 被提示尽量选择紧凑页段、读取证据，并在必要时继续调用工具。编排和最终作答由外接的 OpenAI Agents SDK 完成，而不是 PageIndex 本身的本地 retrieval/chat 引擎。[Agent demo 源码](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/examples/agentic_vectorless_rag_demo.py#L1-L86)

这说明 OSS 中完整的问答链实际上是：

```text
PageIndex 建树/读页 + 外部 Agent 框架 + 外部 LLM + 应用自建答案/引用约束
```

### 4.2 本地 SDK 的关键缺口

`0.2.9` 在锁定提交中刚加入 local mode。本地客户端可同步提交文档、读取树、读取页文本并做文档 CRUD，但明确不支持本地 `chat_completions`、folder 和旧 retrieval API。[客户端模式分发](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/client.py#L33-L68)、[未实现的本地能力](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/client.py#L251-L319)

因此，不能把 PyPI SDK 的“local mode”理解成一个已完成的本地 RAG/推理服务。它目前更接近索引和证据访问库；生产级检索编排、回答、引用校验、并发控制、服务化和可观测性都要由接入方补齐。

### 4.3 Cloud 的高级检索未在 OSS 完整开源

官方教程称 dashboard/retrieval API 会组合 LLM tree search 与 value-function MCTS，但对应的高级实现未出现在锁定仓库中；教程也写明更多细节将后续发布。[LLM Tree Search 文档](https://docs.pageindex.ai/tutorials/tree-search/llm)

此外，官方 Hybrid Tree Search 文档说明其会对每个节点再分块，用 embedding/vector search 给节点打分，并把 value-based search 与 LLM search 合并；该方法还是 Retrieval API 的默认方式。[Hybrid Tree Search 文档](https://docs.pageindex.ai/tutorials/tree-search/hybrid)

所以“vectorless”也必须限定范围：

- 简单 LLM tree search 可以不依赖向量库；
- PageIndex 的 Cloud/Hybrid 默认检索路径会使用 chunk、embedding 和 vector search；
- “no vector database / no chunking”不是所有 PageIndex 产品形态都满足的系统级事实。

Cloud Chat API 可针对一个或多个文档 ID 返回回答和引用，但官方把 Chat API 标为 beta，旧 retrieval 接口处于 deprecated 状态。[API Reference](https://docs.pageindex.ai/api-reference)、[Cloud chat 客户端实现](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/cloud_api.py#L179-L238)

### 4.4 多文档检索

官方文档明确指出 PageIndex 默认面向单文档。对于文档集合，官方给出三种路由思路：

- 用 metadata + SQL 做确定性筛选；
- 对小型文档集，用文档 description + LLM 选文档；
- 把文档内容分块、embedding 后放入向量数据库，先做语义文档选择。

参见[文档搜索总览](https://docs.pageindex.ai/tutorials/doc-search)、[metadata 路由](https://docs.pageindex.ai/tutorials/doc-search/metadata)、[description 路由](https://docs.pageindex.ai/tutorials/doc-search/description)和[semantic 路由](https://docs.pageindex.ai/tutorials/doc-search/semantics)。也就是说，多文档路由和跨文档推理不是 OSS tree index 自动解决的问题。

官方 PageIndex File System 博客宣称可用 virtual nodes、query-dependent trees 和 dynamic flattening 把百万文档组织成单一索引，但同时明确这些能力属于 Enterprise release。仓库没有对应实现，也没有可复现的规模/质量 benchmark。[PageIndex File System 官方说明](https://pageindex.ai/blog/pageindex-filesystem)

## 五、模型、依赖与部署边界

| 项目 | OSS 本地路径 | Cloud / Enterprise |
|---|---|---|
| 运行形态 | Python 库和 CLI；不是开箱即用的 HTTP 推理服务 | 托管 API；Enterprise 宣称 VPC/on-prem |
| LLM | 标准 pipeline 必需；Flash 结构生成可不使用，但默认摘要/完整优化需要 | 由托管服务提供 |
| 模型接入 | 无 provider 前缀时走 OpenAI；`provider/model` 形式走 LiteLLM | PageIndex API key |
| 文档存储 | 每文档 JSON 文件和 manifest | 闭源托管实现 |
| 向量数据库 | 简单本地 tree-search 不必需 | Hybrid Retrieval 会使用 embedding/vector search |
| OCR | 本地只有 PyPDF2 文本提取，不是真正 OCR | 官方宣称 enhanced OCR，但实现未开源 |
| 生产设施 | 未提供本地鉴权、队列、分布式任务、HA、限流和服务监控 | 具体能力/边界需商务与安全评审 |

仓库依赖包括 LiteLLM、OpenAI SDK、PyPDF2、pypdfium2、requests、YAML、dotenv 等。[`requirements.txt`](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/requirements.txt#L1-L11)；项目元数据声明 `python >=3.7`、`Development Status :: 3 - Alpha`。[`pyproject.toml`](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pyproject.toml#L1-L50)

LLM 调用层对普通模型直接使用 OpenAI SDK，对带 provider 前缀的模型使用 LiteLLM，并带重试逻辑。[模型调用源码](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/utils.py#L39-L147) 这提供了模型可替换性，但不能保证任意本地模型都能稳定遵守复杂 JSON 输出和树修复 prompt。

标准建树、摘要和 Agent 查询都会向模型发送文档文本。**[工程判断]** 对含未公开经营数据、个人信息或受授权限制材料的场景，如果不是在自托管、合规的 OpenAI-compatible/LiteLLM provider 内运行，就必须把外发文本、日志留存、数据区域和供应商训练政策纳入安全评审。

官方 README 宣称 Enterprise 支持 VPC/on-prem，但这不是 MIT 仓库已经提供的部署物。[部署说明](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/README.md#L79-L84)

## 六、输入、输出与 API

### 6.1 OSS CLI / Python

CLI 要求在 `--pdf_path` 与 `--md_path` 中二选一，可选择 Flash，并将结果写为 JSON。[CLI 使用说明](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/README.md#L147-L208)

主要输入输出如下：

| 入口 | 输入 | 输出/行为 | 边界 |
|---|---|---|---|
| classic PDF | PDF 路径或 `BytesIO` | `doc_name`、可选 `doc_description`、`structure` 树 | 文本提取依赖 PyPDF2；标准流程依赖 LLM |
| Flash PDF | PDF 路径或 `BytesIO` | 快速层级树，可选摘要/优化 | preview；布局启发式需按模板验证 |
| Markdown CLI | Markdown 文件 | 基于标题和行号的结构树 | 未接入当前 local client 的 document submit |
| local SDK submit | PDF 文件路径 | 同步建树并存本地，返回 document ID | PDF only；长文档可能耗时数分钟 |
| local SDK read | document ID、页范围 | 文档元数据、树、页文本 | 不含本地 chat/retrieval |
| Cloud SDK/API | 上传 PDF、document ID、query | 托管处理、tree/chat/retrieval、引用 | beta/deprecated 状态和闭源实现需单独核验 |

本地 store 为逐文档目录中的 `tree.json`、`pages.json`、`doc.json` 和全局 manifest，没有数据库事务、索引分片或高可用语义。[本地存储源码](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/local_store.py#L69-L144)

本地 submit 只接受 PDF，并同步完成索引；其所谓 OCR 内容实际来自 PyPDF2 文本提取。因此图片型/扫描型 PDF 在本地不会凭空得到可检索文字。[local API 源码](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/local_api.py#L48-L139)、[客户端 PDF 文本提取](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/client.py#L165-L181)

官方 Cloud 文档当前以 PDF 文档处理为主，并另有 Markdown tree endpoint。[Document Processing](https://docs.pageindex.ai/sdk/documents)、[API Reference](https://docs.pageindex.ai/api-reference) 主仓库没有 DOCX、HTML、TXT 或结构化数据库 ingestion pipeline。

示例中的 vision RAG 是先把 PDF 页渲染成图片，再让外部视觉模型阅读 PageIndex 选出的页面；它不等于 PageIndex 原生支持图片文档理解。

## 七、可扩展性与规模

### 7.1 有利因素

- 树是简单 JSON，容易接成 Tidewise Agent 的工具，也容易保存 node/page provenance；
- LiteLLM 为多模型/自托管 OpenAI-compatible endpoint 提供了接入面；
- 检索 prompt 可注入领域偏好，允许 Agent 多轮选择章节和页面；
- classic、Flash、Markdown 可针对不同文档来源分别试验。

### 7.2 当前 OSS 边界

- 本地存储是单机 JSON 文件，不是 corpus search engine；
- 每次 submit 生成新 document ID，没有正式的原位增量更新/版本合并语义；
- 多文档路由要另建 metadata、description 或向量索引；
- 没有本地 HTTP 服务、任务队列、租户隔离、鉴权、HA、备份恢复和规模压测；
- 大量异步 LLM 摘要调用会带来 provider 并发限制、成本和尾延迟；
- 树质量依赖文档结构与模型输出，错误可能在章节边界、页码映射、摘要和查询导航中累积。

相关开放 issue 也显示这些仍是现实集成风险，而非已解决的产品契约：

- [#316：增量更新诉求](https://github.com/VectifyAI/PageIndex/issues/316)；
- [#323：大 PDF/context limit 用户报告](https://github.com/VectifyAI/PageIndex/issues/323)；
- [#283：并发调用/rate limit 用户报告](https://github.com/VectifyAI/PageIndex/issues/283)；
- [#199：本地模型 JSON 输出兼容性用户报告](https://github.com/VectifyAI/PageIndex/issues/199)；
- [#240：缺少 security policy](https://github.com/VectifyAI/PageIndex/issues/240)。

这些 issue 是用户报告和未关闭需求，不能单独证明所有版本必然复现；但它们应进入 PoC 的失败注入与验收范围。

## 八、格式与语言支持

可由公开实现确认的范围是：

- **文本型 PDF**：classic 与 Flash；
- **Markdown**：独立 CLI/pipeline；
- **扫描 PDF**：本地没有真正 OCR，Cloud 虽宣称 enhanced OCR，但实现和质量不可复核；
- **图片/图表视觉理解**：依赖示例中外接的视觉模型，不是核心 pipeline 自带；
- **DOCX/HTML/TXT/数据库记录**：主项目没有原生 ingestion。

官方没有发布受支持语言矩阵，也没有中文、繁体中文、混排、RTL 或跨语言检索的公开质量 benchmark。Flash 实现包含多语言字符/方向处理，模型层也可能使用多语言模型，但这只说明“技术上可尝试”，不能据此承诺中文效果。

FinanceBench 与仓库主要示例均为英文。因此，观潮家的中文公告、扫描件、复杂财务表、脚注和中英混排材料必须单列测试，不能从英文 FinanceBench 分数外推。

## 九、Benchmark：已宣称什么，能验证什么

### 9.1 Mafin2.5-FinanceBench 的 98.7%

PageIndex 官方博客宣称 Mafin 2.5 在 FinanceBench 上达到 98.7%。[官方 benchmark 博客](https://pageindex.ai/blog/Mafin2.5)

锁定的 Mafin 仓库中可复核到：

- `result_gpt4o.json` 和 `result_deepseekv3.json` 各有 150 条结果；
- 每个结果文件的标签计数为 `AL=136`、`BE=6`、`MVA=5`、`NAL=2`、`SEDC=1`；
- 按仓库口径把除 `NAL` 外均视为正确，即 `148 / 150 = 98.67%`；
- 仓库提供答案、标签、人类复核 CSV 和 evaluator，但**没有发布 Mafin 的索引、检索、生成 pipeline 代码，也没有逐题检索 trace/证据 artifact**。

结果与标签可在 [`result_gpt4o.json`](https://github.com/VectifyAI/Mafin2.5-FinanceBench/blob/1c890d5e0fd9929953d38282614555847727011d/result_gpt4o.json)、[`result_deepseekv3.json`](https://github.com/VectifyAI/Mafin2.5-FinanceBench/blob/1c890d5e0fd9929953d38282614555847727011d/result_deepseekv3.json)及[人类评估说明](https://github.com/VectifyAI/Mafin2.5-FinanceBench/blob/1c890d5e0fd9929953d38282614555847727011d/human_evaluations/README.md#L1-L18)中复核。

这个数字不能直接视为独立可复现的 PageIndex 检索准确率，原因包括：

1. **只覆盖公开样本 150 题。** FinanceBench 原始仓库说明完整数据集有 10,231 题，开源的是 150 题样本，完整集需另行申请。[FinanceBench 原始 README](https://github.com/patronus-ai/financebench/blob/cc39aeb4afdf33909ee1412188bf89035950c2eb/README.md#L7-L18)、[FinanceBench 论文](https://arxiv.org/abs/2311.11944)
2. **成功定义经过扩展。** 136 条与原答案和方法对齐；另外 6 条被标为 benchmark error、5 条为 multiple valid approaches、1 条为相同证据但不同结论，这些也被计入有效结果。[Mafin 人类评估说明](https://github.com/VectifyAI/Mafin2.5-FinanceBench/blob/1c890d5e0fd9929953d38282614555847727011d/human_evaluations/README.md#L1-L18)
3. **evaluator 口径宽松。** prompt 接受合理的替代解释、额外正确信息等；hybrid 评估对多个 judge 结果采用 OR 逻辑。[评估器源码](https://github.com/VectifyAI/Mafin2.5-FinanceBench/blob/1c890d5e0fd9929953d38282614555847727011d/eval.py#L35-L113)
4. **系统不可端到端复现。** 结果文件可以复核，但没有 Mafin 的检索/生成实现，无法从原文重新跑到 98.7%。
5. **任务代表性有限。** Mafin README 自己指出 benchmark 存在错误/歧义，且主要是简单单文档检索，缺少多文档推理。[Mafin README](https://github.com/VectifyAI/Mafin2.5-FinanceBench/blob/1c890d5e0fd9929953d38282614555847727011d/README.md)

因此，98.7%适合作为“该方法在公开 FinanceBench 样本上有潜力”的证据，不足以证明中文投研、多文档事件链、扫描件、实时更新或生产规模的效果。

### 9.2 Flash 工程 benchmark

Flash README 列出 9 份 PDF，从 9 页到 1,098 页、约 8.7k 到 158.7 万输入 token，并给出 end-to-end 优化/摘要的运行统计。[Flash benchmark 表](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/pageindex/flash/README.md#L52-L69)

该表能说明团队测试过不同长度文档，但没有完整公开模型、硬件、复现脚本和逐阶段质量指标；它也不是 retrieval/answer accuracy benchmark，不能用于证明检索质量。

### 9.3 仍缺失的证据

公开材料没有提供以下可复现结果：

- 中文、繁体中文、中英混排和跨语言检索；
- 扫描件 OCR、复杂财务表格、图表/脚注；
- 多文档、跨年度、事件/因果链推理；
- 百万文档 OSS 规模、并发和更新性能；
- PageIndex 与 BM25、向量/混合 RAG、KAG 在同一观潮家数据集上的对照；
- evidence page recall、citation precision、索引成本和查询成本的系统评测。

## 十、许可证、活跃度与成熟度

### 10.1 许可证

主仓库使用 [MIT License](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/LICENSE)，允许在保留版权和许可声明的前提下使用、修改和分发。

但 MIT 只覆盖公开仓库代码，不能自动推定 Cloud、Enterprise、PageIndex File System、托管 OCR/MCTS 等闭源能力采用相同授权。若 PoC 依赖这些能力，需要另行确认价格、数据处理协议、SLA、退出/迁移和模型供应商条款。

### 10.2 活跃度与发布状态

- 锁定的 main HEAD 是 2026-08-11 合入 local mode 的 [`d375c00`](https://github.com/VectifyAI/PageIndex/commit/d375c00a5a6a45bb5caeca31790f777e222c154a)，说明项目仍在快速迭代；
- 包元数据为 `0.2.9` 且标注 Alpha；PyPI 在调研快照时稳定版仍为 `0.2.8`，另有 `0.3.0.dev3` 预发布，仓库 HEAD 与已发布稳定包并不完全同步。[PyPI release history](https://pypi.org/project/pageindex/#history)
- GitHub Releases 当时主要是 `v0.3.0.dev2/dev3` 开发标签。[Releases](https://github.com/VectifyAI/PageIndex/releases)
- 当前测试 workflow 覆盖 Python 3.10/3.13 和可选 Agent 框架组合，HEAD 对应 action 成功；但测试以单元/模拟为主，没有真实 LLM 的端到端检索质量门禁。[测试 workflow](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/.github/workflows/tests.yml)、[HEAD CI run](https://github.com/VectifyAI/PageIndex/actions/runs/31498444170)
- 调研快照中仓库仍有较多开放 issue/PR，结合 Alpha 版本，应按快速变化的上游依赖管理，而不是稳定内核。

官方没有发布 PageIndex 学术论文；README 推荐引用的是 PageIndex 官方博客文章，而非同行评审或 arXiv 论文。[官方 Citation 段落](https://github.com/VectifyAI/PageIndex/blob/d375c00a5a6a45bb5caeca31790f777e222c154a/README.md#L272-L290)

## 十一、建议的受控 PoC

### 11.1 PoC 目标

只验证一个明确假设：**PageIndex 能否比现有基线更稳定、低成本地从观潮家长文档中找出正确证据页/章节。** 不把 PoC 目标扩展成替换 OpenSPG/KAG，也不先验接受官方问答准确率或 Enterprise 规模宣称。

### 11.2 样本

建议选 30–50 份有人工可核验答案和证据页的代表性材料，覆盖：

- 英文 SEC/港股年报与中文公告、研报、法规；
- born-digital PDF、扫描 PDF、复杂表格、图表、脚注和中英混排；
- 直接定位题、跨章节组合题、数值计算题；
- 同公司跨年度以及跨公司/跨来源问题；
- 有目录、无目录、错误目录和超长文档。

### 11.3 对照组

至少与下列路径在同一题集上对照：

- BM25/全文检索；
- 当前向量或 hybrid RAG；
- 当前 KAG 检索/推理链；
- PageIndex classic；
- PageIndex Flash；
- PageIndex + Tidewise Agent（仅把树/页内容暴露为工具）。

### 11.4 核心指标

| 类别 | 指标 |
|---|---|
| 证据质量 | evidence page Recall@K、Precision@K、章节边界正确率、引用覆盖率 |
| 答案质量 | 人工盲评正确率、引用支持率、无依据结论率、数值/单位正确率 |
| 鲁棒性 | 建树失败率、JSON/模型输出失败率、扫描/表格/无目录分层成功率 |
| 性能 | 索引 p50/p95、查询 p50/p95、并发退化、超长文档完成率 |
| 成本 | 每文档索引 token/金额、每问题 token/金额、重试成本、缓存收益 |
| 运维 | 重建与版本切换时间、更新/删除一致性、故障恢复、可观测性 |
| 安全 | 文本外发范围、日志/缓存留存、密钥管理、供应商数据条款 |

### 11.5 通过后的集成方式

如果 PoC 通过，只把 PageIndex 封装为窄接口，例如：

```text
index(document_version) -> tree_id
search(tree_id, query) -> candidate node_ids/page_ranges
fetch(tree_id, page_range) -> immutable source text + provenance
```

接口中必须保留 `document_id`、文档版本/hash、node ID、页码、原文片段、模型/索引版本和时间戳。Tidewise Agent 负责跨工具编排；OpenSPG/KAG 继续负责实体、关系、事实治理与推理。这样即使未来更换 PageIndex，也不会把其内部树结构或 Cloud API 扩散成系统核心耦合。

### 11.6 当前本地基线与接入 seam

当前仓库中的完整 Tidewise Schema 仍是未提交到 OpenSPG 的人工审核候选，且尚无 PostgreSQL ABox 事实导入；基础验收也只覆盖 Web 和 KAG/KNEXT CLI，不覆盖模型问答质量。参见本地 [`README.md`](../../README.md)和[`local-openspg-kag.md`](../design/local-openspg-kag.md)。因此 PoC 应分两层验收：

1. 先独立比较 PageIndex 与现有 Chunk/全文/向量路径的证据页召回和引用准确率；
2. 等最小 `Schema -> ABox -> Event -> Rule -> KAG Solver` 链路成立后，再比较“图事实/规则”与“图事实/规则 + PageIndex 文档证据”，不把两种尚未对齐的能力做失真的总分对比。

项目规范要求保持官方 OpenSPG/KAG 0.8 拓扑，除非先记录实验。因此首选把 PageIndex 放在 Tidewise Agent 后的外部 `DocumentEvidenceRetriever`，不修改当前 Compose。若需进入 KAG Solver，可基于 [`RetrieverABC`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/interface/solver/retriever_abc.py#L22-L59) 封装适配器；但 KAG 0.8 的 [`ChunkData.to_dict()`](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/interface/common/model/retriever_data.py#L1046-L1067) 不会传播 `properties`，PoC 必须专门验证 `document_id/node_id/page/source_revision` 不在 merger/generator 链路中丢失。

### 11.7 本地源码验证

本次在仓库外的临时 checkout 中用隔离 Python 3.12 环境安装了锁定提交的依赖，运行官方测试得到 `74 passed, 1 warning`。这证明当前 HEAD 的单元/模拟测试可通过，但不是真实 LLM、中文金融文档、检索质量或生产并发验证。

## 十二、最终决策

**决策：不采用 PageIndex 替换 OpenSPG + KAG；批准其以“长文档 evidence retriever”身份进入受控 PoC。**

采用它的理由是层级文档索引、页级证据访问和 Agent 工具形态与长报告检索高度契合；限制它的理由是：本地 retrieval/chat 尚未实现、OSS 只有单机 JSON 存储且 PDF local submit 不含真正 OCR、多文档/百万规模能力不在开源版、公开 benchmark 不能端到端复现，且它本身不提供知识图谱和规则/时序推理语义。

只有当自有题集证明它在 evidence recall、citation precision、成本、延迟和失败率上相对现有基线有实质收益，并通过数据安全与版本锁定评审，才进入产品集成；否则保留 OpenSPG/KAG 主链，不增加新的生产依赖。
