# OpenSPG 0.8 + KAG 0.8.0 纯开源推理闭环边界

## 结论

**能。** OpenSPG v0.8 和 KAG v0.8.0 的公开源码足以完成一次“用户自然语言问题/推理命题 → LLM 规划 → 图谱、规则、Chunk 混合检索与推理 → LLM 答案生成 → 证据与过程输出”的计算闭环。**完成这条推理链不必须使用未开源的 OpenSPGApp BFF 和官方 UI。**

但应区分“推理计算闭环”和“官方产品体验闭环”：

- CLI/Python SDK 能用纯开源组件闭环；
- KAG 还公开了可通过 stdio/SSE 启动的 MCP server，其 `qa_pipeline(query)` tool 直接执行 Solver 并返回答案；
- OpenSPG 提供开源的底层图查询和确定性规则推理 HTTP API；
- KAG 0.8.0 本身没有将自然语言 Solver Pipeline 包装成一个可独立部署的通用 QA HTTP 服务，需要自己加一层很薄的 API 适配；
- 想直接复用官方 8887 页面、账户/项目管理、会话任务和流式展示，则依赖未开源产品层，或者必须自行实现等价应用层。

## 公开源码中的完整计算链

1. **问题入口**：官方 DomainKG 例子直接把用户 `query` 传给 `SolverPipelineABC.from_config(...).ainvoke(...)`，同时使用 `TraceLogReporter`。例子文档明确将 `python qa.py` 列为“执行 QA 任务、生成答案”步骤。证据：[qa.py](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/domain_kg/solver/qa.py)、[DomainKG README](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/examples/domain_kg/README_cn.md)。
2. **LLM 规划**：`KAGLFStaticPlanner` 把原始问题和可用 Executor schema 传入 LLM，产生任务计划；对依赖前序结果的子问题还会再用 LLM 改写。证据：[KAGLFStaticPlanner](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/planner/lf_kag_static_planner.py)。
3. **计划执行**：`KAGStaticPipeline` 生成 task DAG，按依赖分组执行 Retriever、Math、Deduce 和 Output 等 Executor，再把 Context 交给 Generator 生成最终答案。证据：[KAGStaticPipeline](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/pipeline/kag_static_pipeline.py)。
4. **图检索与规则推理**：KAG 的 `OpenSPGSearchAPI` 和 `OpenSPGGraphApi` 通过公开 KNEXT client 调用 OpenSPG 的 schema/search/graph/reason 端点；OpenSPG v0.8 公开 server 中存在 `/public/v1/reason/run`、`/public/v1/reason/thinker` 和 `/public/v1/reason/schema`。证据：[OpenSPGGraphApi](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/tools/graph_api/impl/openspg_graph_api.py)、[OpenSPGSearchAPI](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/tools/search_api/impl/openspg_search_api.py)、[ReasonController](https://github.com/OpenSPG/openspg/blob/v0.8/server/api/http-server/src/main/java/com/antgroup/openspg/server/api/http/server/openapi/ReasonController.java)。
5. **LLM 语言推理**：`KagDeduceExecutor` 能根据上下文执行 entailment、judgement、extract 和 choice 等操作；这一层使用可配置的 LLM client，不要求官方未发布的 `kag-model`。证据：[KagDeduceExecutor](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/executor/deduce/kag_deduce_executor.py)、[OpenAI/vLLM client](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/llm/openai_client.py)、[Ollama client](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/common/llm/ollama_client.py)。
6. **答案和证据**：`LLMIndexGenerator` 汇总每个 task 的结果、检索的 Chunk 和图数据，为文档生成引用 ID，再调用 LLM 生成最终答案；`TraceLogReporter` 可在本地返回 decomposition、thinking、generator input、answer 和 references，无需产品 BFF。证据：[LLMIndexGenerator](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/generator/llm_index_generator.py)、[TraceLogReporter](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/reporter/trace_log_reporter.py)。

KAG 官方自述也与源码结构一致：`kg-solver` 组合规划、推理和检索，集成图谱推理、逻辑计算、Chunk 检索和 LLM 推理；0.8.0 已发布 `kg-builder` 和 `kg-solver`，未发布的是 `kag-model`。证据：[KAG v0.8.0 README](https://github.com/OpenSPG/KAG/blob/v0.8.0/README_cn.md#5-%E6%8A%80%E6%9C%AF%E6%9E%B6%E6%9E%84)。

## CLI / SDK / API / UI 的闭环判定

| 形态 | 纯开源是否可闭环 | 精确边界 |
| --- | --- | --- |
| Python 脚本/终端 | **可以** | 官方例子以 `python qa.py` 完成问题到答案。但 `kag` 命令自身没有通用交互式 `qa` 子命令；其子命令主要是 info、builder、benchmark 和 MCP server。 |
| Python SDK | **可以** | 直接构造 `SolverPipelineABC` 并调用 `ainvoke(query, reporter=...)`，返回答案；`TraceLogReporter` 返回本地过程与引用。 |
| MCP | **可以** | 公开的 `kag mcp-server` 可注册 `qa_pipeline(query)` tool，内部调用已开源 Solver Pipeline 并返回 answer。证据：[KagMcpServer](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/mcp/server/kag_mcp_server.py)。 |
| HTTP API | **底层可以，自然语言 QA 需薄适配层** | OpenSPG 公开 HTTP API 已覆盖 schema、graph、search、KGDSL reason 和 thinker；KAG 0.8.0 未自带把整个 Solver 发布为通用 HTTP 服务的 server。 |
| 官方 Web UI | **不可以** | 公开仓库没有官方 KAG 前端及其所需的完整 OpenSPGApp BFF；不能用纯开源源码原样复刻 8887 产品交互。 |

## 未开源部分中，哪些是必需的

### 不是推理计算闭环的必需项

- 官方 KAG UI、登录、账户、权限、项目列表和配置页；
- OpenSPGApp 的会话/任务持久化与产品级调度；
- 官方 UI 使用的 `/public/v1/reasoner/dialog/report/*` 流式上报接口：KAG 公开 client 和 `OpenSPGReporter` 会调用这类接口，但纯本地闭环可以改用已开源的 `TraceLogReporter`。`OpenSPGReporter.do_report()` 在未配置 host 时也直接返回。证据：[OpenSPGReporter](https://github.com/OpenSPG/KAG/blob/v0.8.0/kag/solver/reporter/open_spg_reporter.py)。

### 必需，但并非“未开源产品代码”

- 一个可用的 OpenSPG v0.8 开源 server 和图/搜索存储；
- 一个已提交 schema 并建好索引的知识库；
- 可调用的 chat LLM；可使用 OpenAI-compatible/vLLM 服务或 Ollama 本地模型；
- 混合检索通常还需要 embedding/vectorizer，可以是外部 API，也可以是本地模型；
- 知识的质量、Schema/规则定义、Prompt 和模型能力决定命题最终能否被正确证明；“管线能跑完”不等于“任意命题都能得到正确答案”。

## 对“推理命题”的两种理解

- 如果命题已经是结构化的 subject/predicate/object 或 KGDSL，OpenSPG 的开源 `thinker` / `reason/run` 就能执行确定性规则推理，LLM 不是必需。
- 如果命题是自然语言问题，KAG 开源 Solver 负责用 LLM 规划和改写、调用 OpenSPG/检索/语言推理等 Executor，再用 LLM 将结果与引用组合为答案。这就是纯开源部分已能完成的 LLM 参与闭环。

## 研究限制

本结论基于 OpenSPG `v0.8` 与 KAG `v0.8.0` tag 的官方源码和示例进行静态链路核对；本次没有配置真实 LLM/embedding 密钥并运行完整问答。
