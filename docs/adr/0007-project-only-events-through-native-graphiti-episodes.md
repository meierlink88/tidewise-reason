# ADR 0007: Project only Events through native Graphiti Episodes

- Status: Accepted
- Date: 2026-08-26
- Supersedes: [ADR 0002](0002-ingest-published-evidence-as-graphiti-episodes.md) and the controlled
  Event projection restriction in [ADR 0005](0005-resolve-event-candidates-before-graphiti-projection.md)

## Context

Evidence is immutable provenance used upstream to curate and publish an Event. It does not enter
Event Analysis or Investment Reasoning as a direct inference input. Projecting the complete
Evidence into Graphiti duplicates authoritative source content and requires a separate API, durable
queue and controlled writer that do not contribute to the target Storyline-bounded reasoning flow.

The controlled Event writer also discarded every unmatched extracted entity and disabled Graphiti
Fact extraction. That prevents a formal Event from retaining event-specific contextual entities and
explicit relationships needed to connect dynamic occurrences with later Storyline reasoning.

## Decision

- Retire `POST/GET /api/reason/v1/evidence-episodes`, its SQLite delivery workflow, worker, converter
  and controlled Graphiti writer. New Evidence is not projected into Graphiti.
- Preserve existing Data Evidence, Evidence links, SQLite volume contents and historical Graphiti
  nodes. This decision does not authorize deleting or migrating existing data.
- Continue to accept Event Candidates and resolve Event identity before any graph write. Only a
  formal Event returned by Data Service enters Graphiti.
- Project that Event through Graphiti 0.29.3's public `add_episode()` method with the Reason-owned
  ontology models. Use the native entity extraction and resolution, contextual Entity creation,
  explicit Fact extraction, Fact deduplication, temporal invalidation and persistence flow.
- Keep only a thin Reason adapter around `add_episode()`: deterministic UUID from the formal Event
  ID, content conflict detection, idempotent completed-replay handling, and post-success
  `episode_kind=EVENT` / `domain_object_id` metadata.
- An LLM-created contextual Entity has no authoritative `data_object_id` and does not become
  Tidewise master data. The Event extraction instruction forbids invented IDs and forbids promoting
  forecasts, investment impacts, Variables, Signals or Storylines into Event facts.
- Variable, Signal, Storyline routing and investment conclusions remain later Reasoning stages;
  native Graphiti Fact extraction does not replace them.

## Consequences

- Agent OS must stop calling the retired Evidence Episode resource. Evidence IDs continue to cross
  the Event Candidate contract so Data can create authoritative Event-to-Evidence links.
- The Reason API runs only the Event Candidate worker. Graphiti readiness and shutdown remain owned
  by the Event projector adapter.
- New formal Events can create contextual Entity nodes and Graphiti EntityEdges. Only Data-owned
  projection creates canonical entities with authoritative IDs.
- Existing controlled Event Episodes are not automatically reprocessed. Any historical Event or
  Evidence graph cleanup/rebuild requires a separate reviewed operation and explicit authorization.
- Event projection retries remain safe after completion. A partial native Graphiti failure is retried
  under the existing Event Candidate workflow and is visible as Graph projection failure.
