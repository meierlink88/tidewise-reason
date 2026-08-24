# Graphiti 核心机制与观潮家使用边界

> 调研日期：2026-08-24  
> 本地版本：`graphiti-core==0.29.3`  
> 证据范围：Graphiti 官方文档与 `v0.29.3` 源码。

## 结论

Graphiti 的核心不是“自动推理”，而是把持续到来的文本、消息或结构化记录维护成一个**带来源、事实有效期和历史失效信息的增量知识图谱**，再通过混合检索为 LLM/Agent 提供上下文。

它的主链路可以概括为：

```text
Episode 摄取
  → LLM 抽取实体与事实
  → 实体解析、去重与合并
  → 事实边去重、时间提取与冲突失效
  → 增量写入时态图谱
  → 向量 + BM25 + 图遍历检索与重排
  → Agent 获取上下文后完成业务推理
```

## 核心机制

### 1. Episode：以“本次输入”为摄取和溯源单元

`add_episode` 接收名称、内容、来源说明、来源类型和 `reference_time`。Graphiti 将本次输入保存为 `EpisodicNode`，再从中抽取实体和关系事实。Episode 与抽取出的实体通过 `MENTIONS` 等关系关联，事实边也保存支持它的 Episode ID，因此能够从图事实回溯到输入来源。

Episode 可以是文本、对话消息或 JSON。它代表一次知识摄取，不等同于观潮家业务模型中的 `Event`：一条业务 Event 可以被投影为一个结构化 Episode，但不能因为 Graphiti 创建了 Episode，就认为业务 Event 已完成清洗、审核和定版。

来源：[Adding Episodes](https://help.getzep.com/graphiti/core-concepts/adding-episodes)、[`Graphiti.add_episode`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/graphiti.py)。

### 2. LLM 抽取与软 Schema

Graphiti 使用 LLM 从 Episode 中抽取实体、事实、关系类型、属性和时间。可以使用 Pydantic 模型定义 `entity_types`、`edge_types`，并通过 `edge_type_map` 限定特定实体类型之间允许选择的边类型。

这是一套**抽取约束和提示机制**，不是数据库层的强 Schema，也不是业务主数据合同。如果没有匹配关系，Graphiti 可以退化为通用关系。因此观潮家的实体 ID、类型枚举、关系方向和字段合法性仍需由领域服务确定性校验。

来源：[Custom Entity and Edge Types](https://help.getzep.com/graphiti/core-concepts/custom-entity-and-edge-types/)。

### 3. 实体解析、去重和摘要演化

新实体不会机械地每次创建新节点。Graphiti 会检索候选实体，再由名称、语义和图上下文辅助 LLM 判断是否与已有实体相同；同一实体的事实和摘要可以随新 Episode 增量更新。事实边也会进行去重。

这适合处理新闻中别名、简称和重复表述，但结果具有概率性。公司、产业链节点等关键实体应使用 PG 中稳定 ID 投影和校验，不能把 Graphiti 的自动合并当成唯一主数据解析机制。

来源：[Entities](https://help.getzep.com/entities)、[Adding Fact Triples](https://help.getzep.com/graphiti/working-with-data/adding-fact-triples)。

### 4. 事实中心的双时态模型

Graphiti 的事实边主要包含四个时间：

- `valid_at`：事实在现实世界中开始成立的时间；
- `invalid_at`：事实在现实世界中停止成立的时间；
- `created_at`：系统获知并创建该事实的时间；
- `expired_at`：系统获知该事实已失效的时间。

因此它能区分“事情何时发生”与“系统何时知道”，也能支持补录历史信息和回看某一时点的知识状态。双时态能力主要落在事实边上，并不等于完整的主数据版本管理。

来源：[Graph search temporal fields](https://help.getzep.com/searching-the-graph)、[`EntityEdge`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/edges.py)。

### 5. 增量更新、矛盾识别和旧事实失效

每次加入 Episode 时，Graphiti 只针对本次新增知识进行抽取、解析和图更新，不需要全图重建。新事实与已有事实冲突时，它会尝试识别受影响的旧边，填写 `invalid_at` / `expired_at`，保留旧事实的历史，而不是简单覆盖。

但冲突识别依赖 LLM 和候选召回，所以它是“自动维护能力”，不是事实正确性的最终保证。高风险投研事实仍需保留 PG 权威记录、人工修订状态和可重放投影。

来源：[Graphiti overview](https://help.getzep.com/graphiti/getting-started/overview)、[`edge_operations.py`](https://github.com/getzep/graphiti/blob/v0.29.3/graphiti_core/utils/maintenance/edge_operations.py)。

### 6. 三层图结构与可选社区摘要

Graphiti 的主要结构可以理解为：

```text
Episode：输入内容、来源和摄取时间
   │ mentions / supports
Entity：人、公司、产业链节点、国家、政策等对象
   │ fact edges
Fact：实体之间带时间和来源的关系陈述
```

此外可以构建 Community，对相互关联的实体进行聚类和摘要，用于主题级、全局级召回。Community 是辅助检索能力，不应直接等同于观潮家的 `Storyline`；Storyline 有明确的投研锚点、边界和生命周期，应由业务系统管理后投影。

### 7. 混合检索与重排

Graphiti 将多种召回方式组合使用：

- 向量相似度：寻找语义相近的实体和事实；
- BM25 / 全文检索：匹配名称、术语和关键词；
- 图遍历 / BFS：扩展相邻实体和事实；
- RRF、MMR、Cross-Encoder、节点距离等：融合和重排结果。

它擅长回答“与当前问题最相关的历史事实有哪些”，但 top-k 检索不能保证穷举某条产业链的所有节点。产业链完整拓扑和确定性遍历应由领域查询工具提供。

来源：[Searching](https://help.getzep.com/graphiti/working-with-data/searching)。

### 8. `group_id` 逻辑分组和 Agent 接口

`group_id` 用于把 Episode、实体和事实限定在一个逻辑命名空间中，方便按知识库或租户检索；它不是 Neo4j 的独立 database，也不是物理隔离机制。

Graphiti 还提供 MCP Server，让 Agent 写入 Episode、搜索事实或节点、读取 Episode、添加三元组等。MCP 是通用记忆接口，不包含观潮家的投研传导方法论。

来源：[Graphiti MCP Server](https://help.getzep.com/graphiti/getting-started/mcp-server)。

## Graphiti 不负责什么

Graphiti 本身不负责：

1. 把 Evidence 清洗、核验并定版为业务 Event；
2. 定义观潮家的 Variable、Signal、影响周期和 Storyline 业务语义；
3. 判断一个关系是产业链因果传导还是普通语义关联；
4. 自动完成“宏观事件 → 变量 → 产业链节点 → 投资机会/风险”的完整推理；
5. 保证 LLM 抽取、实体合并和事实失效百分之百正确。

图中的路径只是可检索的事实与关联，不天然构成因果证明。真正的投研推理仍应由 Codex/LLM Agent 在明确的 AgentContext、时间窗口、产业链拓扑、变量信号和正反证据约束下完成。

## 对观潮家的合理分工

```text
观潮家 Event Curation Pipeline
Evidence → 清洗、核验、结构化、实体绑定 → 权威 Event 写入 PG

Graphiti Projection
Event / Entity / Link / Variable / Signal / Storyline
→ Episode + Entity + temporal Fact 投影、增量更新、语义检索

Investment Reasoning Pipeline
确定时间窗口与 Storyline 锚点
→ 精确取得产业链拓扑
→ 从 Graphiti 召回相关 Event / Signal / 历史事实
→ 回查 PG 权威字段
→ Codex/LLM 多轮推导
→ 一句话结论 + 推理树 + 节点周期性影响
```

最终原则是：**PG 管权威事实与业务状态，Graphiti 管时态语义记忆与上下文召回，Codex/LLM Agent 管投研推导。**
