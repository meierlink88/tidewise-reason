# Tidewise Agent OS Context Map

```text
Agent Runtime
    |
    | versioned Semantic Runtime contract
    v
Semantic Runtime
    |
    v
Generated graph and vector projections
```

| Context | Owns | Does not own |
| --- | --- | --- |
| Agent Runtime | Agents, Workflows, prompts, model access, run state | Semantic definitions, graph/vector projections, authoritative business facts |
| Semantic Runtime | Semantic Model publication, validation, retrieval, reasoning, provenance, decision support | Agent orchestration, model-provider credentials, authoritative business facts |

The contexts do not import each other's implementation packages or read each other's persistence.
