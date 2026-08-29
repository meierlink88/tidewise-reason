# Tidewise Reason

Tidewise Reasoning Server and its Graphiti temporal graph provider. The standalone FastAPI service
owns Event Candidate resolution and formal Event projection. Tidewise Data remains the
authoritative owner of Evidence, Event and canonical domain facts.

## Start

```bash
mkdir -p .runtime
cp infra/graphiti/.env.example .runtime/graphiti.env
chmod 0600 .runtime/graphiti.env
# Replace every placeholder before continuing.
bash scripts/install-graphiti-runtime.sh
bash infra/graphiti/start.sh
bash infra/graphiti/start-api.sh
```

## Services

The Reasoning Server port is deliberately fixed in Compose and is not configurable through the
private runtime environment.

| Service | Local address |
| --- | --- |
| Reasoning API | <http://127.0.0.1:8890> |
| Swagger UI | <http://127.0.0.1:8890/docs> |
| OpenAPI document | <http://127.0.0.1:8890/openapi.json> |
| Neo4j Browser | <http://127.0.0.1:7474> |

## Stop

```bash
bash infra/graphiti/stop-api.sh
bash infra/graphiti/stop.sh
```

These service-scoped commands do not remove Neo4j or Reasoning Server state volumes. Do not run
unscoped `docker compose down`, `--remove-orphans`, or volume-removal commands in this repository.

## Graphiti Ontology

The formal Graphiti extraction types live in [`ontology/`](ontology/). The
`reasoning-ontology/v4` catalog mirrors selected Tidewise Data entity and stable-link contracts and
contains no authoritative facts. Evidence does not enter Graphiti.

```bash
bash scripts/test-ontology.sh
bash scripts/verify-graphiti-contract.sh
```

Authoritative fact imports are explicit projections, not Event Episodes. The first projection
validates the complete Country API response against the local `Country`, `Region` and
`CountryInRegion` Pydantic ontology before Graphiti receives any write:

```bash
bash scripts/project-country-regions.sh plan
bash scripts/project-country-regions.sh run --limit 1
bash scripts/project-country-regions.sh run --replace
bash scripts/project-country-regions.sh verify
```

The implementation lives in [`projection/`](projection/). It uses stable Tidewise Data IDs,
deterministic Graphiti UUIDs and the fixed Neo4j Community `neo4j` group. Canonical facts use
Graphiti's public `nodes.entity.save_bulk` / `edges.entity.save_bulk` Namespace APIs and embeddings
but deliberately bypass LLM entity resolution, so same-name entities of different authoritative
types cannot merge. A limited run is only a provider
smoke test; `--replace` explicitly rebuilds only this fixed group, and `verify` compares it with the
full current Data API result.

Industry and Concept use separate authoritative projections because the current Data doctype defines
an Industry hierarchy but no direct Industry-to-Concept fact. The Industry projection validates the
complete hierarchy and writes `Industry` plus `IndustryHasParent`:

```bash
bash scripts/project-industries.sh plan
bash scripts/project-industries.sh run --replace
bash scripts/project-industries.sh verify
```

The Concept projection independently writes only canonical `Concept` nodes:

```bash
bash scripts/project-concepts.sh plan
bash scripts/project-concepts.sh run --replace
bash scripts/project-concepts.sh verify
```

Both use scoped replacement within the shared `neo4j` group. They preserve
Country, Region and `CountryInRegion` facts, and do not infer an Industry-to-Concept relationship.

IndustryChain is projected only after the canonical Industry and Concept targets exist. The
projection reads all Data-owned chains plus their typed `mapped_to_industry` and
`mapped_to_concept` Links, preserves each Link's `ERL...` identity, and writes only the two
ontology-approved mapping directions:

```bash
bash scripts/project-industry-chains.sh plan
bash scripts/project-industry-chains.sh run --replace
bash scripts/project-industry-chains.sh verify
```

Graph relationship `created_at` is generated when Reason first creates the relationship and is
preserved by deterministic UUID on later upserts. It is not the business-valid time of the source
fact. `primary_country_id` remains an IndustryChain property and does not create a Country link;
ChainNode membership is owned by the later ChainNode projection.

ChainNode initialization is a replayable one-time operation. It reads an explicit read-only,
repeatable snapshot directly from the local Tidewise Data PostgreSQL container because no suitable
complete Data API exists yet. It never reads the retired `chain_node_relations` table. Membership
stores only stage and position; the three typed node-to-node relations store only their canonical
edge ID and IndustryChain scope:

```bash
bash scripts/initialize-chainnode-graph.sh plan
bash scripts/initialize-chainnode-graph.sh run --replace
bash scripts/initialize-chainnode-graph.sh verify
```

The geopolitical demo catalog is a graph-only evaluation fixture. It writes reviewed
`GeopoliticRivalry` nodes with deterministic UUIDs, embeddings and no relationships. It never reads
or writes Tidewise Data, never sets `data_object_id`, and never deletes graph data:

```bash
bash scripts/initialize-geopolitic-demo.sh plan
bash scripts/initialize-geopolitic-demo.sh run
bash scripts/initialize-geopolitic-demo.sh verify
```

The macroeconomic demo catalog writes 78 reusable policy-action nodes across ten controlled
categories. It resolves only the existing canonical Country nodes for China, the United States,
Japan, South Korea and the United Kingdom, then writes the curated `IMPLEMENTS` applicability
relations. These relations do not claim that a policy is currently active. The initializer never
reads or writes Tidewise Data, never sets `data_object_id`, and never deletes graph data:

```bash
bash scripts/initialize-macroeconomic-demo.sh plan
bash scripts/initialize-macroeconomic-demo.sh run
bash scripts/initialize-macroeconomic-demo.sh verify
```

The Reason-owned `variable-catalog/v1` packages 56 fundamental Variables in nine causal groups.
It writes deterministic, embedded `Variable` nodes only. `allowed_anchor_types` remains applicability
metadata; the initializer does not create Variable-to-anchor or any other relationship, does not
call the LLM, and does not delete graph data:

```bash
bash scripts/initialize-variable-catalog.sh plan
bash scripts/initialize-variable-catalog.sh run
bash scripts/initialize-variable-catalog.sh verify
```

## Event Candidate Ingestion

Agent OS sends Event Candidates plus their authoritative Evidence IDs to the standalone Reason API:

```text
POST /api/reason/v1/event-candidates
GET  /api/reason/v1/event-candidates/{submission_id}
```

Local operators may use the CLI entry with the same JSON contract and Pipeline:

```bash
python -m ingestion.episcode.event.cli submit candidate.json --wait
python -m ingestion.episcode.event.cli status evt-submission-...
```

Reason resolves Event identity, publishes a genuinely new Event and its Evidence links through
Data Service, then projects only the returned formal Event into Graphiti. Configure
`REASON_API_SERVICE_TOKEN` in the private mode-`0600` runtime environment, then use only the
service-scoped commands:

```bash
bash infra/graphiti/start-api.sh
bash infra/graphiti/verify-api.sh
bash infra/graphiti/stop-api.sh
```

The API binds to the fixed address <http://127.0.0.1:8890>. Its Pipeline state is stored in the
dedicated `tidewise-reason_graphiti-api-state` volume; stopping the service does not delete that
volume.

Formal Events use Graphiti's native `add_episode()` pipeline, including entity extraction and
resolution, contextual Entity creation, explicit Fact extraction, Fact deduplication and temporal
invalidation. An internal Pipeline Stage preserves deterministic Event Episode identity and marks
the completed Episode with `episode_kind=EVENT` and its Data Event ID. It is not a separate
publication interface. Native Graphiti processing does not create
Tidewise Variables, Signals or Storylines; those remain separate reasoning stages.

## Deployment boundary

Reason currently has no UAT publication workflow or UAT CI gate. The retired OpenSPG local and UAT
runtime definitions are not part of this repository's executable surface.
