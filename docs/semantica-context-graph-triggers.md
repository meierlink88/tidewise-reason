# Semantica ContextGraph 的创建与写入触发方式

依据 Semantica 官方 `Context Graphs` guide 和当前 `main` 源码。

## 结论

Semantica 没有一个由 event、Agent run 或用户问题自动触发 ContextGraph 的全局机制。ContextGraph 由调用方显式创建；图的范围和生命周期也由调用方决定。

官方 guide 明确给出两种 graph construction 方式：

1. 手动构造：调用 `ContextGraph()` 创建空图，再用 `add_node()` / `add_edge()` 写入节点和边。
2. 自动提取工作流：把 `ContextGraph` 作为 `knowledge_graph=` 传入 `AgentContext`，再向 `AgentContext.store()` 传入文档列表，并启用 `extract_entities=True` 或 `extract_relationships=True`。提取过程创建实体节点和关系边。

关键限制：guide 明确说明，向 `store()` 传入单个字符串只保存为 memory item，不触发 graph construction；需要传入文档列表。源码还提供显式 `build_graph()` / `build_from_conversations()`，但同样需要调用方主动调用，不是 Agent run 自动发生。

`load_from_file()` / `AgentContext.load()` 是从已有 JSON/状态恢复图，不是从新事件自动生成图。

因此应用必须自行决定：何时创建一个 ContextGraph、向哪个 graph 写入一批文档、graph_id 对应 run/session/event/case 中的哪一种业务范围、何时保存和销毁。

## 官方依据

- [Context Graphs guide](https://docs.getsemantica.ai/guides/context-graphs/)
- [Context reference](https://docs.getsemantica.ai/reference/context/)
- [AgentContext source](https://github.com/semantica-agi/semantica/blob/main/semantica/context/agent_context.py)
- [ContextGraph source](https://github.com/semantica-agi/semantica/blob/main/semantica/context/context_graph.py)
