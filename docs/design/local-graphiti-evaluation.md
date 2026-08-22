# Local Graphiti Evaluation

## Decision

The active local evaluation uses `graphiti-core==0.29.3` with a dedicated Neo4j Community
5.26.28 provider. The reasoning repository owns this provider because no Tidewise AI application
reads from or writes to Neo4j.

This is not an OpenSPG data migration. The legacy OpenSPG Server container is stopped and removed;
its image, MySQL state and MinIO state remain available. The user explicitly authorized deletion of
the legacy `tidewise-reason_neo4j-data` and `tidewise-reason_neo4j-logs` volumes on 2026-08-21, so
the former OpenSPG ABox is no longer locally recoverable from those volumes.

## Runtime boundaries

- The Compose project is `tidewise-reasoning` and the sole service is `neo4j`.
- Ports 7474 and 7687 bind to loopback.
- The image and Graphiti package are version pinned.
- The Python environment, model credentials, Data Service credential, Graphiti data and generated
  analysis artifacts stay outside Git.
- MySQL and MinIO remain owned by `tidewise-infra`.
- Atomic Evidence is read only through Data Service's versioned `/api/data/v1/evidences` contract;
  the demo does not enter another service's database or container.
- This local decision does not alter the UAT OpenSPG-specialized Neo4j provider.

Graphiti requires Neo4j 5.26 or later. Neo4j 5.26 is selected over FalkorDB for this first PoC to
minimize backend variability and retain the more mature Cypher, Browser, driver and operational
tooling ecosystem. This is not a claim that Neo4j is always faster than FalkorDB.

## Data contract

The demo keeps these concepts separate:

1. `Evidence` is the immutable source record.
2. `ResearchEvent` is the time-scoped occurrence extracted from evidence.
3. `VariableSignal` is a derived, time-bounded interpretation linked to a stable chain node.
4. `AnalysisResult` records the question, as-of time, retrieved context and conclusion; it is not
   silently treated as new evidence.

Graphiti supplies temporal graph memory and retrieval. The domain analysis pipeline still owns
scope selection, horizon filtering, evidence conflict handling and the final LLM reasoning prompt.

Pydantic types are the versioned local Ontology Catalog. They constrain ingestion, and the pipeline
exports their JSON Schema plus relation endpoint signatures into the Analysis Context. A production
selector should include only the types related to the detected anchor; this bounded demo includes
its complete five-entity/seven-relation catalog because all types are relevant.

Episode identities are UUIDv5 values derived from a fixed namespace and Evidence identities. A
plain `seed` clears and rebuilds only the dedicated `neo4j` Graphiti group; `seed --reset` clears the
entire dedicated local evaluation database. Generated context and result artifacts carry the same
content-derived run ID, graph fingerprint and Episode set, so verification rejects stale output.
Every node result must structurally cite its Evidence, Episode, ResearchEvent and VariableSignal;
free-text transmission paths are not accepted as the provenance contract.

The authoritative cross-service timeout, retry, error, compatibility and recovery decisions are
frozen in [ADR 0001](../adr/0001-use-graphiti-for-local-temporal-memory-evaluation.md).

The first DeepSeek V4 Flash compatibility run keeps custom entity and edge type labels but does not
ask Graphiti to persist custom Pydantic properties. The provider returned JSON Schema descriptions
as nested property values, which Neo4j correctly rejected. Direction, horizon and mechanism remain
in Episode content and extracted fact text until a validated structured-output adapter is added.

## Lifecycle

Prerequisites are Python 3.12.11 through `uv`, Docker, and the locally running Tidewise Data Service
at `127.0.0.1:9011`. Create `.runtime/graphiti.env` from `infra/graphiti/.env.example`; populate the
Neo4j password, LLM, embedding and Data Service credentials; protect the file with mode `0600`.
Then use service-scoped commands:

```bash
mkdir -p .runtime
cp infra/graphiti/.env.example .runtime/graphiti.env
chmod 0600 .runtime/graphiti.env
# Replace every placeholder in .runtime/graphiti.env before continuing.
bash scripts/install-graphiti-runtime.sh
bash infra/graphiti/start.sh
bash infra/graphiti/verify.sh
bash scripts/verify-graphiti-contract.sh
bash scripts/test-graphiti-demo.sh
bash scripts/graphiti-demo.sh evidence-smoke
bash scripts/graphiti-demo.sh seed --reset
bash scripts/graphiti-demo.sh analyze
bash scripts/verify-graphiti-demo-runtime.sh
bash infra/graphiti/stop.sh
```

Do not run `docker compose down`, `--remove-orphans`, or volume removal as part of normal use.
