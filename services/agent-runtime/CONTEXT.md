# Agent Runtime Context

**Agent Runtime**:
The Agno AgentOS environment that owns Agent definitions, Workflows, model access, prompts, run
state, tools, and calls to the Semantic Runtime interface.

**Semantic Runtime Client**:
The consumer-owned adapter that invokes a pinned Semantic Runtime contract. It never imports the
Semantic Runtime implementation or accesses Neo4j/Qdrant directly.

**Agent Run**:
A durable execution record for one Agent or Workflow invocation. It may reference a Semantic Model
release but cannot modify that release.

**Readiness**:
`GET /ready` succeeds only when the typed Semantic Runtime v1 health contract is reachable and
valid. Agno's `GET /health` remains process liveness.
