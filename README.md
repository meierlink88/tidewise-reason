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

This initialization contains no Agent, Workflow, Semantic Model, storage adapter, or server
behavior yet. Each capability will be added one vertical slice at a time after its public interface
and acceptance test are confirmed.
