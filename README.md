# Tidewise Agent OS

Tidewise Agent OS is organized as two independently owned runtimes:

```text
External event
      |
      v
Agent Runtime (Agno AgentOS, LLM, Agent/Workflow orchestration)
      |
      | versioned contract
      v
Semantic Runtime (LinkML, Semantica, validation, retrieval, reasoning)
      |
      v
Neo4j and Qdrant projections
```

## Initial structure

```text
contracts/                     Runtime-to-runtime contracts
deploy/                        Deployment definitions
services/
  agent-runtime/               Agno-based Agent Runtime
  semantic-runtime/
    semantic-model/            Authoritative LinkML source
    src/                       Semantica-based runtime implementation
```

The initial runtime slice provides storage connectivity and health/readiness interfaces. It does
not yet define an Agent, Workflow, or domain Semantic Model. Those capabilities will be added one
vertical slice at a time after their public interfaces and acceptance tests are confirmed.

## One-click local runtime

Start the complete local stack:

```bash
./agent-os up
```

The command generates a local Neo4j password under the ignored `.runtime/` directory, builds both
Runtime images, starts all dependencies, and returns only after every health check passes.

| Runtime | URL | Purpose |
| --- | --- | --- |
| Semantic Runtime | <http://127.0.0.1:8100/health> | Semantica, Neo4j, and Qdrant readiness |
| Semantica Explorer | <http://127.0.0.1:8000> | Local diagnostic UI over generated ContextGraph state |
| Agent Runtime | <http://127.0.0.1:8200/docs> | Agno AgentOS interface |
| Agent readiness | <http://127.0.0.1:8200/ready> | Agent Runtime to Semantic Runtime contract check |
| Neo4j Browser | <http://127.0.0.1:7474> | Local graph database UI |
| Qdrant Dashboard | <http://127.0.0.1:7433/dashboard> | Isolated Agent OS vector database UI |

Operational commands:

```bash
./agent-os status
./agent-os logs
./agent-os down
./agent-os reset --yes
```

`down` preserves named-volume data. `reset --yes` removes only this Compose project's volumes.
Host bindings are loopback-only and are intended for local development, not production exposure.
