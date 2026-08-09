# One-click Agent OS Runtime v1

## Outcome

`./agent-os up` builds and starts an isolated local stack in which:

- Semantic Runtime is reachable on `http://127.0.0.1:8100`;
- Semantica Explorer is reachable on `http://127.0.0.1:8000`;
- Agent Runtime is reachable on `http://127.0.0.1:8200`;
- Semantic Runtime has verified live connections to Neo4j and Qdrant;
- Agent Runtime readiness verifies the versioned Semantic Runtime health contract.

## Ownership and dependency direction

- Semantic Runtime owns the Neo4j and Qdrant adapters and their lifecycle.
- Agent Runtime calls Semantic Runtime over HTTP and never imports its implementation or connects
  to Neo4j/Qdrant.
- Semantica Explorer is a diagnostic process over its own generated ContextGraph JSON. Semantica
  0.6.0 does not automatically wire Explorer to the external Neo4j/Qdrant adapters.
- Neo4j records, Qdrant vectors, and Explorer ContextGraph JSON are rebuildable projections, not
  authorities for Tidewise business facts.

## Frozen interfaces

| Interface | Owner | Success | Safe failure |
| --- | --- | --- | --- |
| `GET :8100/health` | Semantic Runtime | HTTP 200 with Semantica, Neo4j, and Qdrant status | HTTP 503; no fabricated readiness |
| `GET :8000/api/health` | Semantica Explorer | HTTP 200 from Explorer | container remains unhealthy |
| `GET :8200/health` | Agent Runtime/Agno | HTTP 200 process liveness | container restart policy applies |
| `GET :8200/ready` | Agent Runtime | HTTP 200 only when Semantic Runtime contract is usable | HTTP 503 with bounded reason |

The provider contract is `contracts/semantic-runtime-v1.yaml`. Agent Runtime owns a typed consumer
for the exact response and fails closed on a non-200 or malformed response.

## Persistence and credentials

- Named Docker volumes hold Neo4j, Qdrant, Explorer, and Agent Runtime state.
- `./agent-os up` creates a random Neo4j password in `.runtime/stack.env` with user-only file
  permissions. The file is ignored by Git.
- No provider credential or generated runtime state is committed.
- Qdrant is not authenticated in this localhost-only v1 stack and must not be exposed publicly.

## Ports

Qdrant uses host ports `7433/7434` by default to avoid colliding with the existing Tidewise local
Qdrant on `6333/6334`; containers still use Qdrant's native `6333/6334` ports. All host ports can be
overridden in `.runtime/stack.env`.

## Rollback and reset

- `./agent-os down` stops the stack without deleting data.
- `./agent-os reset` stops the stack and removes only this Compose project's named volumes after an
  explicit confirmation flag.
- The stack never changes the existing Tidewise PostgreSQL, Neo4j, or Qdrant instances.

## Non-goals

- publishing ObjectType definitions or facts;
- making Explorer the production semantic interface;
- configuring an LLM or defining an Agent/Workflow;
- production authentication, TLS, high availability, backup, or external exposure.
