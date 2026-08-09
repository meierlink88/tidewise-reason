# Semantica Ontology 是否供 AI Agent 使用

核对基线：Semantica 官方仓库 `main` commit `e90bd048e18ff81d5a1e30a2a95e1be469bd2c23`，以及当前 Tidewise 部署的 `semantica==0.6.0`。

## 结论

Semantica 明确把 ContextGraph、GraphRAG、memory、decision tools 和 KG tools 定位为 AI Agent 可消费能力；Ontology 也有一个面向 MCP Client 的 `semantica://ontology/schema` 资源定义。这证明“让调用方 Agent 读取语义模型”属于产品意图。

但当前实现没有把导入的 Ontology 自动注入 Agent prompt/context，也没有让 NER 或 Agno Knowledge ingestion 自动受 Ontology 约束。Agno 五个集成组件没有 Ontology 参数或 Ontology tool；MCP 的 ontology schema resource 在 0.6.0 中还不可用。因此直接的 Ontology-to-Agent 集成目前是不完整的。

## Semantica 内部对 Ontology 的显式使用

Ontology 并非只被维护。`OntologyEngine` 明确支持：

- 从数据或文本生成 Ontology；
- 从 Ontology 生成 SHACL；
- `validate_graph(..., ontology=...)` 验证 KG；
- Ontology evaluation；
- OWL/RDF export；
- SKOS concept search；
- alignment 存储与 alignment-aware URI query expansion。

这些都是显式 API 调用，不是全局自动 pipeline hook。

官方资料：

- <https://docs.getsemantica.ai/reference/ontology/>
- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/semantica/ontology/engine.py>
- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/semantica/triplet_store/query_engine.py>

## 官方 Agent 集成实际暴露的能力

Agno 官方集成列出五个组件：

- `AgnoContextStore`；
- `AgnoKnowledgeGraph`；
- `AgnoDecisionKit`；
- `AgnoKGToolkit`；
- `AgnoSharedContext`。

它们面向 memory、ContextGraph、GraphRAG、decision 和 KG construction。`AgnoKGToolkit` 的七个工具是 extract entities、extract relations、add/query graph、find related、infer facts、export subgraph。源码没有 Ontology、SHACL、SKOS 或 vocabulary 参数/工具。

官方资料：

- <https://docs.getsemantica.ai/integrations/agno/>
- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/integrations/agno/kg_toolkit.py>
- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/integrations/agno/knowledge_graph.py>

## MCP 中最直接的 Ontology-to-Agent 证据及缺口

MCP resource registry 定义了：

`semantica://ontology/schema` — “Full ontology schema from the OntologyManager (concept hierarchy and constraints).”

这类 MCP resource 可由 Claude 等 MCP-compatible AI client 读取，因此是官方源码中最直接的 Ontology 给 Agent 使用的设计证据。

但 handler 尝试执行：

```python
from semantica.ontology import OntologyManager
```

当前 0.6.0 和官方 main 的 `semantica.ontology` 均没有导出或实现该 `OntologyManager`。handler 捕获异常后只返回 `{"message": "Ontology manager not available"}`。本地运行中的 0.6.0 已通过 import 实测确认失败。

此外，MCP tool registry 没有 Ontology / SHACL tool；只有 extraction、graph、decision、reasoning、export 等工具。

官方资料：

- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/mcp/resources/registry.py>
- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/mcp/tools/__init__.py>
- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/mcp/README.md>

## 另一个未实现的表述

`ContextRetriever` docstring 列出 “Ontology-aware context retrieval”，但类的构造参数、`retrieve()` 和其余源码没有 Ontology loader、Ontology filter、class expansion 或 SHACL logic。该表述目前不是可确认的实现能力。

源码：

- <https://github.com/semantica-agi/semantica/blob/e90bd048e18ff81d5a1e30a2a95e1be469bd2c23/semantica/context/context_retriever.py>

## 当前可行的 Agent 消费路径

1. 将 Ontology classes / concepts 与业务实体放入同一个 ContextGraph，Agent 通过通用 `query_graph` / `find_related` 遍历；这只是通用图查询。
2. Agent 显式调用 Explorer REST 的 ontology search、SKOS、SHACL 或 alignment endpoints；Semantica 当前没有现成 Agno Ontology toolkit。
3. 应用直接调用 `OntologyEngine` / `OntologyValidator`，把验证或推理结果作为 bounded context 返回 Agent。
4. 修复并配置 MCP ontology resource 后，由 MCP Agent 读取 schema；0.6.0 原样不可用。

## 当前 Tidewise 状态

当前 `Agent Runtime` 没有注册 Agent、Workflow、Semantica KG Toolkit 或 Ontology tool。它对 `Semantic Runtime` 唯一的消费合同是 `/health`。因此当前运行栈中没有任何 AI Agent 在读取 Ontology。

依据：

- `services/agent-runtime/src/tidewise_agent_runtime/app.py`
- `services/agent-runtime/src/tidewise_agent_runtime/semantic_client.py`
- `contracts/semantic-runtime-v1.yaml`
