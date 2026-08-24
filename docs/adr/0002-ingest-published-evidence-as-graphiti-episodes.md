# ADR 0002: Ingest published Evidence as Graphiti Episodes

- Status: Accepted
- Date: 2026-08-24
- Issue: [#14](https://github.com/meierlink88/tidewise-reason/issues/14)

## Context

Agent OS already holds the complete Atomic Evidence immediately after Data Service publishes it and
assigns the formal Evidence ID. Re-reading the same record before Graphiti processing adds latency
and another failure path, while calling Graphiti directly would expose provider DTOs, ontology
selection, retries and graph lifecycle to Agent OS.

Graphiti 0.29.3 also treats an explicit `group_id` as the Neo4j database selection. Neo4j Community
provides the `neo4j` database but not arbitrary application-named databases, so the former
`tidewise-investment-research` group value prevents Episode extraction from sharing the same scope
as canonical facts.

## Decision

Reason exposes `POST /api/reason/v1/evidence-episodes` for Agent OS to push batches of complete,
already-published Evidence. The request contains only `evidences`. Reason validates and durably
records each payload before returning `202`, then a sequential internal worker converts it to a
Graphiti JSON Episode. Processing state is queried by formal Evidence ID.

The implementation lives under `ingestion/episcode/evidence/`. It uses a strict external Evidence
DTO, a lossless canonical JSON conversion, a Reason-owned SQLite delivery store, bounded retries,
lease recovery and a constrained Graphiti writer. The public boundary never accepts Graphiti types,
ontology definitions or provider configuration.

The Graphiti database/group value is fixed to `neo4j` for both canonical projection and Episode
ingestion. Existing nodes and relationships are migrated in place by changing only their
`group_id`; no graph node, relationship or volume is deleted. The business namespace remains a
Reason application concern rather than a Neo4j Community database name.

The API runs as the separate `api` service in the `tidewise-reasoning` Compose project, with the
fixed container name `reason-graphiti-api`, a loopback port, private bearer token and dedicated
SQLite volume. It does not modify the legacy OpenSPG `reason-server`.

## Consequences

- Data Service remains the Evidence persistence authority; direct delivery occurs only after
  successful publication.
- Same Evidence ID and payload is idempotent; reuse of an ID with different content fails closed.
- Provider failures do not block the publishing HTTP call and can recover after process restarts.
- Evidence extraction can resolve canonical facts because both use the real `neo4j` graph scope.
- A single API replica owns the SQLite worker state. A distributed queue is deferred until a
  multi-replica runtime is required.

This ADR supersedes ADR 0001 only where ADR 0001 says all Atomic Evidence must be pulled through a
Data Service GET. ADR 0001 remains authoritative for the original local evaluation and provider
selection decisions.
