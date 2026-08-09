# Semantica Context Graph: Semantic Search and Cross-Graph Navigation

Source checked: Semantica's current Context Graph guide and the corresponding
`AgentContext` / `ContextGraph` implementation on the `main` branch (2026-08-09).

## Semantic Search via AgentContext

This is hybrid retrieval, not graph construction. `AgentContext` first finds
textually similar memories through its vector store. When an `anchor_node` is
supplied, it then looks up each candidate's hop distance from that node in the
ContextGraph and blends the semantic score with a graph-proximity score. A
`max_hops` value also acts as a neighborhood filter.

A candidate must be associated with a graph node ID for proximity blending to
work. The implementation looks for `result.id` or `metadata.node_id` / `id` /
`memory_id`. A bare string passed to `context.store()` becomes a memory item and
does not itself construct the graph. The guide therefore assumes an already
populated graph and omits an explicit memory-to-node association in its short
example.

## Cross-Graph Navigation

This links two separate in-memory `ContextGraph` instances without merging them.
`link_graph()` registers an exit node in graph A and an entry node in graph B;
`navigate_to()` follows one registered bridge; `cross_graph_path()` performs a
BFS across ordinary edges and registered bridges.

It is not database federation or a Neo4j cross-database join. Live Python object
references back the links. Link metadata can be serialized, but after loading
the graphs the references must be restored with `resolve_links()`.

In the guide's exact code the bridge is `APT29 -> SolarWinds`, so the implemented
shortest path to Treasury is `APT29 -> SolarWinds -> Treasury`. The printed
comment `APT29 -> SUNBURST -> SolarWinds -> Treasury` would require the bridge to
start at `SUNBURST`; it does not match the shown code.

## Sources

- https://docs.getsemantica.ai/guides/context-graphs/
- https://github.com/Hawksight-AI/semantica/blob/main/semantica/context/agent_context.py
- https://github.com/Hawksight-AI/semantica/blob/main/semantica/context/context_graph.py
