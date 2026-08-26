# ADR 0010: Analyze formal Events into controlled Signal Facts

- Status: Accepted
- Date: 2026-08-26

## Context

The daily investment-reasoning flow needs reviewed, time-scoped changes on canonical IndustryChain
and ChainNode anchors rather than an unbounded dump of 48-hour Event narratives. A formal Event is
already projected through Graphiti's native `add_episode` flow, but its extracted Facts describe the
Event and do not by themselves encode a controlled Variable, impact direction or expected impact
window.

Graphiti 0.29.3 persists an `EpisodicNode` with replacement semantics (`SET n = {...}`). Custom
Episode properties can therefore disappear during a later native save and cannot be authoritative
workflow or identity fields.

## Decision

- Native Event projection durably identifies a formal Event by deterministic Episode UUID, the
  native `source_description`, and the Event ID inside native Episode `content`. Custom Episode
  metadata is never required for identity or Signal provenance. A newly created native shell uses
  a distinct pending `source_description`; the final native description is the durable completion
  marker and survives later `EpisodicNode.save()` replacement writes.
- An asynchronous Event Analysis workflow starts only after native Event projection succeeds. It
  classifies the Event, recalls a bounded set of existing anchors and fundamental Variables, asks the
  configured LLM for direct Signal candidates, independently reviews them and projects accepted
  results.
- Event classes are `GEOPOLITICAL`, `MACRO_ECONOMIC`, `INDUSTRY_CHAIN` and `CHAIN_NODE`. `COMPANY`
  remains accepted at the contract boundary but terminates with `COMPANY_ANALYSIS_OUT_OF_SCOPE`;
  this version creates no Company Signal and no Company-level conclusion.
- Event classification is workflow state, not a graph Entity. Durable classification, stages,
  retries and terminal results live in the Reason-owned SQLite workflow store.
- A Signal is represented by Graphiti's native `EntityEdge` Fact:
  `(Variable)-[:RELATES_TO {name: "SIGNAL_ON", ...}]->(AnalysisAnchor)`.
- Signal Fact endpoints are loaded by exact UUID and checked for a stable business identity before
  `add_triplet`. The pipeline never creates an endpoint. Contextual Event Entities may support
  Graphiti's Event Facts but are not eligible Signal anchors.
- Signal Fact native time fields carry `valid_at`, confirmed `invalid_at` and `reference_time`.
  Estimated impact onset/end, horizon, mechanism, assumptions, invalidation conditions and three
  confidence dimensions are validated Tidewise attributes. Expected end never becomes Graphiti
  `invalid_at` without a later contradicting or superseding fact.
- Signal eligibility is derived at query time from `valid_at`, `invalid_at` and `expired_at`; no
  frozen ACTIVE/INACTIVE attribute can prevent a future-effective Signal becoming active.
- Candidate selection uses short request-local keys that are mapped back to whitelisted UUIDs by the
  service. The LLM never supplies a graph identity directly. Classification and selection prompts use
  compact JSON contracts; Pydantic remains the strict server-side validation boundary.
- Native Event mentions and Fact endpoints, semantic search and bounded topology are recall channels
  only. A separate semantic critic must reject topology-only or cross-variable inference before the
  deterministic identity/time gate can mark a Signal reviewed.
- Signal onset and peak are explicit offsets from the Event's effective/occurrence time. Provenance,
  mechanism and temporal confidence are elicited independently rather than copied from one score.
- Event Analysis creates only direct or one-explicit-mechanism Signals. Cross-node propagation,
  investment-value assessment and final warming/cooling/diverging conclusions belong to the later
  investment-reasoning pipeline.

## Consequences

- Evidence remains outside Graphiti and downstream reasoning.
- Graphiti continues to create native Event Facts and contextual Entities, while formal Signal Facts
  are constrained to reviewed catalog identities.
- A 48-hour reasoning run can retrieve active Signal Facts by Event provenance and Graphiti valid
  time, then combine them with canonical IndustryChain topology.
- Missing anchors or unsupported Signals terminate explicitly instead of inventing graph nodes.
- Provider JSON failures are retryable workflow failures and do not partially publish unreviewed
  Signal endpoints.
- Expired in-progress workflow leases are reclaimable. Failure to enqueue later analysis is logged
  as a separate durable Event-workflow stage and retried without turning the already successful
  native Event projection into a projection failure. Permanent endpoint/provenance validation
  failures terminate immediately; provider and dependency failures remain retryable.
- Company analysis can be introduced later without changing the current graph Fact representation,
  but requires a separately reviewed Company anchor and reasoning scope.
