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

- The Compose project is `tidewise-reasoning`; `neo4j` owns the graph provider and `api` owns
  Evidence Episode ingestion.
- Ports 7474 and 7687 bind to loopback.
- The image and Graphiti package are version pinned.
- The Python environment, model credentials, Data Service credential, Graphiti data and generated
  analysis artifacts stay outside Git.
- MySQL and MinIO remain owned by `tidewise-infra`.
- For the original evaluation CLI, Atomic Evidence is read through Data Service's versioned API.
  For the accepted ingestion path, Agent OS pushes the complete record to Reason only after Data
  publication; Reason never enters another service's database or container. ADR 0002 owns this
  newer boundary.
- This local decision does not alter the UAT OpenSPG-specialized Neo4j provider.

Graphiti requires Neo4j 5.26 or later. Neo4j 5.26 is selected over FalkorDB for this first PoC to
minimize backend variability and retain the more mature Cypher, Browser, driver and operational
tooling ecosystem. This is not a claim that Neo4j is always faster than FalkorDB.

## Data contract

The retired liquid-cooling demo has been removed. The formal `ontology` package now owns the
versioned Graphiti extraction types. Its first Evidence Curation version contains Country, Region,
Organization, Industry, Concept, IndustryChain and ChainNode plus their stable foundation links.

The Ontology Catalog is a consumer extraction contract derived from Tidewise Data definitions. It
does not own entity facts, and a caller selects the smallest applicable Entity/Link subset for a
foundation projection, Evidence ingestion or Event ingestion. Evidence remains an Episode rather
than a custom Entity.

The original evaluation contract is frozen in
[ADR 0001](../adr/0001-use-graphiti-for-local-temporal-memory-evaluation.md); published Evidence
Episode delivery is frozen in
[ADR 0002](../adr/0002-ingest-published-evidence-as-graphiti-episodes.md).

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
bash infra/graphiti/start-api.sh
bash infra/graphiti/verify-api.sh
bash scripts/verify-graphiti-contract.sh
bash scripts/test-ontology.sh
bash infra/graphiti/stop-api.sh
bash infra/graphiti/stop.sh
```

Do not run `docker compose down`, `--remove-orphans`, or volume removal as part of normal use.
