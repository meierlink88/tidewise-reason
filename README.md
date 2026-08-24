# Tidewise Reason: OpenSPG + KAG

Local OpenSPG and KAG evaluation environment. The official OpenSPG Server `latest` image is the
sole runtime release. Reason Server joins the shared `tidewise-app` project and consumes MySQL,
Neo4j and MinIO from `tidewise-infra`.

## Start

```bash
./scripts/start.sh
```

Open <http://127.0.0.1:8887> and sign in with the official local demo account:

- Username: `openspg`
- Password: `openspg@kag`

`start.sh` pulls the official image before recreating only the `server` service. The bundled KAG
developer commands are available inside the container:

```bash
docker compose exec -e KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 server kag --help
docker compose exec -e KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 server knext --help
```

This repository does not build OpenSPG or KAG from source and does not inject a replacement JAR or
wheel into the official image.

The official image currently ships a `kag_thinker_pipeline` file that omits the
`rewrite_prompt` required by its bundled planner. Its `kag_clarification` prompt also leaves
Action numbering implicit even though the bundled parser accepts only `ActionN:` labels; generic
models can therefore produce valid-looking plans that fail with `sub query not equal logic form
num`. Compose mounts the narrowly corrected
[`runtime-overrides/kag/pipelineconf/kag_thinker.yaml`](runtime-overrides/kag/pipelineconf/kag_thinker.yaml)
over that single file as read-only. The override supplies the missing rewrite prompt and reuses
the bundled `default_logic_form_plan` prompt, whose examples explicitly emit `StepN:`/`ActionN:`.
Because the configured DeepSeek model does not emit the KAG-Thinker-specific `<search>` protocol,
the pipeline keeps `KAGModelPlanner` for multi-step planning but uses the bundled standard KAG
hybrid retrieval executor for each planned retrieval step. Its optional per-step LLM summary is
disabled; the pipeline's final generator remains responsible for synthesizing the answer.
The image, executable JAR and KAG wheel remain unchanged.

## Tidewise Schema

The OpenSPG project `Tidewise` currently uses its pre-projection default Schema. The manual-review
import candidate in [`schemas/Tidewise.schema`](schemas/Tidewise.schema) preserves those KAG
foundation types and represents all 16 active PostgreSQL TBox entity types. It has not been
submitted to OpenSPG, and no PostgreSQL ABox facts have been imported.

## Services

This repository starts only the `reason-server` OpenSPG/KAG Web container. The remaining endpoints
belong to the independently operated shared infrastructure stack.

| Service | Local address |
| --- | --- |
| OpenSPG/KAG Web | <http://127.0.0.1:8887> |
| Neo4j Browser | <http://127.0.0.1:7474> |
| MinIO Console | <http://127.0.0.1:9001> |
| MySQL | `127.0.0.1:3306` |

## Stop

```bash
./scripts/stop.sh
```

The stop script removes only Reason Server. It never stops shared infrastructure or removes its
persistent volumes. Do not run unscoped `docker compose down` or `--remove-orphans` in this
repository.

The base UI can run without a model provider. Building a knowledge base and using KAG inference
requires configuring a generation model and an embedding model in the product UI.

See [the local deployment design](docs/design/local-openspg-kag.md) and
[the official runtime policy](docs/design/official-openspg-kag-runtime.md) for boundaries,
extension seams and recovery.

## Graphiti Ontology

The formal Graphiti extraction types live in [`ontology/`](ontology/). The first
`evidence-curation/v1` catalog mirrors the selected Tidewise Data entity and stable-link contracts;
it contains no authoritative facts and models Evidence as an Episode rather than an Entity.

```bash
bash scripts/test-ontology.sh
bash scripts/verify-graphiti-contract.sh
```

Authoritative fact imports are explicit projections, not Evidence Episodes. The first projection
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

## Evidence Episode Ingestion

Agent OS can push complete, already-published Atomic Evidence to the standalone Reason ingestion
API. The feature-local implementation is under [`ingestion/episcode/evidence/`](ingestion/episcode/evidence/):

```text
POST /api/reason/v1/evidence-episodes
GET  /api/reason/v1/evidence-episodes/{evidence_id}
```

The POST body contains only `evidences` and accepts 1–50 complete Evidence records. Acceptance is
asynchronous and idempotent by formal Evidence ID. Configure `REASON_API_SERVICE_TOKEN` in the
private mode-`0600` runtime environment, then use only the service-scoped commands:

```bash
bash infra/graphiti/start-api.sh
bash infra/graphiti/verify-api.sh
bash infra/graphiti/stop-api.sh
```

The API binds to <http://127.0.0.1:8890> by default. Its delivery state is stored in the dedicated
`tidewise-reason_graphiti-api-state` volume; stopping the service does not delete that volume.

## UAT

UAT deploys only the official OpenSPG Server/KAG runtime and Tidewise Reasoning-owned content. It
consumes MySQL, Neo4j and MinIO managed independently by `tidewise-ai`, and never changes their
lifecycle. See [the Reason UAT deployment contract](infra/uat/README.md).
