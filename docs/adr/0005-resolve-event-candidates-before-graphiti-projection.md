# ADR 0005: Resolve Event Candidates before Graphiti projection

- Status: Accepted
- Date: 2026-08-25
- Issue: #21

## Context

Agent OS can extract a proposed Event from Atomic Evidence, but Event identity depends on whether it
describes the same actor, real-world action, direct object, stage, and occurrence time as an already
published Event. Graphiti Episode similarity alone cannot make that business decision, and Graphiti
must not become the Event or Evidence Link authority.

## Decision

- Reason exposes an asynchronous `POST /api/reason/v1/event-candidates` resource and stores each
  accepted submission in durable SQLite workflow state.
- Exact request replays return the original submission. Historical candidate recall combines
  Graphiti Episode full text with Data Event reads; deterministic identity gates precede a constrained
  LLM comparison.
- `SAME_EVENT` is a terminal no-op: return the matched Event ID, do not publish to Data, do not add an
  Evidence Link, and do not write Graphiti.
- New or related-but-distinct occurrences are published to Data first. Only the returned formal Event
  is projected as an `EVENT` Episode, using a deterministic Episode identity. ADR 0007 supersedes
  the original canonical-only projection restriction with Graphiti's native Episode pipeline.
- Candidate submissions are workflow records, not graph objects. Graphiti extracts only explicit
  Event facts after Data publication; Candidate content never enters the graph directly.

## Consequences

Data remains the sole Event and Evidence Link authority, while Graphiti can be rebuilt from formal
Events. A Data success followed by Graphiti failure is retried from Reason state and never rolled back.
Ambiguous or revision-like cases stop for review instead of silently mutating historical facts.
