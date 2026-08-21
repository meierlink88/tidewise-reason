# Graphiti liquid-cooling demo run — 2026-08-21

## Outcome

The local OpenSPG Server was stopped and its former Neo4j volumes were deleted with explicit user
authorization. A reasoning-owned Neo4j Community 5.26.28 provider and isolated
`graphiti-core==0.29.3` Python runtime were started locally. No UAT resource changed.

The same question used in the OpenSPG evaluation was executed:

> 推理未来12个月AI数据中心液冷服务器产业链各节点的变化趋势

Graphiti ingested one topology Episode and three real Tidewise Atomic Evidence records through the
versioned local Data Service API. The accepted deterministic rebuild contains 27 nodes, including
five ChainNode entities, three Evidence entities, three ResearchEvent entities, three VariableSignal
entities and four fixed-identity Episodes.

The final LLM analysis classified AI芯片、服务器冷板、液冷服务器 and 液冷系统 as 看好, and 数据中心 as
风险 with confidence 0.62. The data-center conclusion weighs broad infrastructure expansion
against the project-specific financing contraction signal. Every node result contains the
transmission path, Evidence IDs, Episode UUIDs, ResearchEvent UUIDs, VariableSignal UUIDs,
counter-evidence, invalidation conditions and confidence. Runtime artifacts are intentionally
ignored under `.runtime/graphiti-demo/`.

## Source Evidence

- `EVD2a67b87e-0eea-5773-ae9c-0acd7d3524bd`: national computing infrastructure is moving toward
  hub-based, scaled deployment and unified scheduling.
- `EVDd50775dc-1ace-51f6-8e17-acaa4e25cb41`: TrendForce forecasts liquid-cooling penetration for AI
  chips at 53% in 2026 and close to 60% in 2027.
- `EVD2e06b439-94cf-5df2-b4a9-8e2b11f3d6a4`: Nvidia reduced its planned guarantee for an OpenAI
  data-center project.

## What Graphiti did

1. Used predefined Pydantic entity and edge types to guide DeepSeek extraction, then exported the
   same Ontology catalog into the Analysis Context used by the final LLM call.
2. Stored raw Episode content, entities, facts, temporal fields and Episode provenance in Neo4j.
3. Deduplicated the stable chain nodes across later Evidence Episodes.
4. Performed hybrid graph, full-text and vector retrieval for four analysis-context queries.

Graphiti did not traverse the whole chain and produce the investment conclusion by itself. The
domain pipeline selected the anchor and horizon, requested the relevant contexts, checked graph
integrity and asked the LLM to analyze every required node.

## Observed seams

The run found three material boundaries that a production domain pipeline must handle:

1. DeepSeek returned JSON Schema descriptions as nested values for custom Pydantic properties.
   Neo4j rejected them, so this compatibility PoC retained type labels while storing direction,
   horizon and mechanism in Signal names, Episode content and fact text.
2. One Signal was attached to the IndustryChain instead of the exact ChainNode, and another was
   missing its `AppliesTo` edge. The pipeline now validates Episode provenance against a versioned
   Evidence-to-anchor acceptance mapping. It no longer derives the canonical endpoint from an LLM-
   generated Signal name, and the alignment check does not decide direction.
3. Graphiti automatically invalidated a broad positive data-center Signal when a later negative
   project-specific Signal arrived. Those facts can coexist and should be aggregated, so the
   pipeline flags this invalidation for domain review and retains the underlying Evidence.

These are evidence that Graphiti is a flexible temporal memory and retrieval layer, not a complete
investment-reasoning engine. Its extraction freedom is useful, but correctness requires a small,
explicit domain validation and analysis pipeline above it.

## Reproduction

```bash
bash scripts/install-graphiti-runtime.sh
bash infra/graphiti/start.sh
bash infra/graphiti/verify.sh
bash scripts/verify-graphiti-contract.sh
bash scripts/test-graphiti-demo.sh
bash scripts/graphiti-demo.sh evidence-smoke
bash scripts/graphiti-demo.sh seed --reset
bash scripts/graphiti-demo.sh analyze
bash scripts/verify-graphiti-demo-runtime.sh
```

The ignored `.runtime/graphiti.env` must first be created from `infra/graphiti/.env.example`. The
Tidewise Data Service and its PostgreSQL provider must be running locally, and the three Evidence
IDs listed above must be available through its authenticated API. `analyze` performs retrieval and
therefore does not require a separate `retrieve` command.

Neo4j Browser is available at `http://127.0.0.1:7474` while the provider is running.
