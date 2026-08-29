# ADR 0011: Use one Event Candidate Pipeline for all entries

- Status: Accepted
- Date: 2026-08-28

## Context

The Event Candidate API correctly resolved Event identity before Data publication, but the public
`GraphitiEventProjector.project(HistoricalEvent)` interface allowed evaluations or callers to bypass
that decision and write a caller-constructed Event directly. A simulation used this alternate path,
so semantically duplicate Events with different IDs became separate Episodes and produced repeated
MENTIONS and Event Facts.

The project also used both `Workflow` and `Pipeline` for complete business processes, creating an
unnecessary second vocabulary.

## Decision

- `EventCandidatePipeline` is the only business interface for Event Candidate acceptance, identity
  resolution, Data publication, Graphiti Episode creation and Event Analysis scheduling.
- HTTP and CLI are entry adapters to the same Pipeline and the same durable Store.
- `Graphiti.add_episode()` is executed only by an internal Event Episode Stage after Data publication
  is durably checkpointed. The Stage is not exported as a publication interface.
- Remove the public Event projector, the projection/scheduling decorator and evaluations that create
  `HistoricalEvent` instances and write them directly.
- Use `Pipeline` for complete business processes and `Stage` for their internal steps. Do not add a
  parallel `Workflow` abstraction.

## Consequences

Semantic duplicates terminate as `SAME_EVENT` before Data or Graphiti writes regardless of whether
the Candidate arrived through API or CLI. Projection and analysis retries remain resumable from the
same Pipeline state after Data publication. Tests target the Pipeline interface; internal Episode
Stage tests cover only provider integration behavior.
