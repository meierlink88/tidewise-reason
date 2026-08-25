# ADR 0001: Use Graphiti for the local temporal-memory evaluation

- Status: Accepted for local evaluation
- Date: 2026-08-21
- Issue: [#12](https://github.com/meierlink88/tidewise-reason/issues/12)
- Runtime-retention decision superseded by [ADR 0006](0006-retire-openspg-runtime-and-fix-reason-port.md)

## Context

The OpenSPG + KAG evaluation showed strong centralized TBox capabilities, but the target investment
workflow still requires a domain pipeline for anchor selection, temporal filtering, conflict
handling and LLM reasoning. We need to compare a lighter temporal graph-memory provider under the
same Evidence/Event/Signal scenario without changing Tidewise AI's authoritative domain model.

The local Neo4j provider is no longer consumed by a Tidewise AI application. The user authorized
deleting the legacy local OpenSPG Neo4j volumes. UAT remains unchanged.

## Decision

Use `graphiti-core==0.29.3` with a reasoning-owned, digest-pinned Neo4j Community 5.26.28 container
for the active local evaluation. Keep the provider and Graphiti runtime outside the shared
`tidewise-app` lifecycle.

The reasoning repository owns a versioned Pydantic Ontology Catalog and a provider-neutral Analysis
Context contract. Atomic Evidence crosses the repository boundary only through Tidewise Data
Service's authenticated versioned API. Model and Data Service credentials remain in an ignored,
mode-`0600` runtime environment file.

Graphiti remains a temporal memory, extraction and retrieval provider. It does not own the final
investment conclusion or silently promote Analysis Results into Evidence.

## Cross-service contract

- Caller identity: the ignored runtime credential is presented as a Bearer principal with
  `data.admin.read`; Data Service remains the authorization and audit owner and returns its
  `request_id` envelope field.
- Operation: `GET /api/data/v1/evidences`, contract anchor `data.v1.listAdminEvidence`. The consumer
  freezes the canonical Evidence ID, nullable `published_at`, UTC timestamps, SourceLevel values,
  pagination and error/status behavior while tolerating additive item fields.
- Budget and retry: two safe GET attempts, each capped at 1.4 seconds with a 50 ms interval, remain
  below the provider's 3-second total budget. Only transport errors, HTTP 429 and 5xx are retried;
  4xx and contract errors fail immediately.
- Result semantics: all three requested Evidence records must be present and temporally usable;
  there is no partial-success mode. A provider-valid record with null `published_at` is classified
  as unsuitable for this temporal demo, not as an invalid provider response.
- Compatibility: additive Data fields are accepted, but missing/invalid frozen fields fail closed.
  Mixed versions do not degrade to direct database reads.
- Mutation and rollback: the Data call is read-only and completes before graph mutation. A failed
  Graphiti rebuild may leave an unverified partial local graph; the explicit recovery path is the
  idempotent next `seed`, which clears only the dedicated group, or `seed --reset` for the dedicated
  evaluation database. Runtime verification rejects partial state.

## Dependency decision

All direct dependencies are owned by this reasoning evaluation and resolved with hashes under exact
Python 3.12.11. Security updates require regenerating and reviewing the lock; no package executes in
Tidewise AI application services.

| Dependency | Purpose | Alternatives considered | License | Security/operational impact |
| --- | --- | --- | --- | --- |
| `graphiti-core` | temporal graph extraction/retrieval | retain OpenSPG; Semantica; custom temporal projection | Apache-2.0 | invokes LLM/embedder and reads/writes Neo4j |
| `neo4j` | authenticated Bolt driver | raw Bolt; py2neo; FalkorDB client | Apache-2.0 | database network and query surface |
| `openai` | OpenAI-compatible DeepSeek calls | provider-specific SDK; raw HTTP client | Apache-2.0 | sends bounded analysis/extraction context externally |
| `httpx` | authenticated Data Service client | standard-library HTTP; `aiohttp` | BSD-3-Clause | carries the scoped Bearer credential on loopback |
| `pydantic` | DTO, config and analysis contracts | dataclasses plus JSON Schema; `msgspec` | MIT | validation-only; no network or persistence owner |

## Consequences

- Local Episode identities and verification are deterministic and stale artifacts are rejected.
- Analysis run identity binds the current Episode contents, extracted graph facts and entity/edge
  identities; retrieval invalidates the old result before a new LLM attempt.
- The same Ontology fragment constrains extraction and is visible during LLM reasoning.
- DeepSeek JSON-object compatibility requires a narrow response-envelope adapter.
- Reliable whole-chain traversal will require a bounded Analysis Context tool/service above
  Graphiti; semantic MCP search alone is insufficient.
- Graphiti can later be replaced without changing the Analysis Context contract.

## Alternatives considered

- Keep OpenSPG + KAG active locally: originally retained as a reversible evaluation, then retired
  by ADR 0006 after the project was taken out of service.
- Use Graphiti MCP as the entire reasoning engine: rejected because it exposes memory/search tools,
  not deterministic multi-hop domain traversal.
- Let the Agent query Neo4j freely: rejected because it bypasses Graphiti temporal/provenance
  semantics and weakens the service boundary.
