# ADR 0004: Initialize ChainNode topology from a read-only Data snapshot

- Status: Accepted
- Date: 2026-08-24
- Issue: [#19](https://github.com/meierlink88/tidewise-reason/issues/19)

## Context

Tidewise Data owns canonical ChainNode records, their IndustryChain memberships and direct typed
topology. The retired `chain_node_relations` table is not authoritative. The Data Service does not
currently expose a practical complete snapshot contract for this one-time initialization, and the
retired `research-graph:search` endpoint must not be reused.

Graphiti already contains the canonical IndustryChain targets. Reason needs one deterministic,
replayable initialization without creating a permanent runtime dependency on the Data database or
copying Data-only review, evidence and provenance fields into the reasoning graph.

## Decision

The initializer reads exactly `chain_node`, `industry_chain_node_memberships` and
`industry_chain_graph_edges` from the existing local Tidewise Data PostgreSQL container. It runs
one `REPEATABLE READ`, `READ ONLY` transaction and emits a complete JSON Lines snapshot. It uses
the container's existing PostgreSQL environment and stores no database credential in this
repository.

Only approved ChainNodes, approved/active memberships and approved/active direct graph edges are
included. The initializer validates the entire snapshot and all references before opening a graph
write. It then uses the authoritative Graphiti bulk writer with deterministic identities and a
scoped replacement limited to `ChainNode` plus these four relationship names:

- `ChainNodeBelongsToIndustryChain`
- `ChainNodeInputTo`
- `ChainNodeIsComponentOf`
- `ChainNodeDependsOn`

Memberships project only `contextual_stage` and `position`. Directed topology projects only the
canonical `IGE...` edge ID and the owning `ICH...` IndustryChain ID. Relationship `created_at` is
the first Graphiti creation time and is preserved on deterministic upsert.

## Consequences

- This is an explicitly authorized initialization exception, not a general runtime Data PG client.
- `chain_node_relations` and `research-graph:search` are never read.
- Data PG remains read-only and Graphiti is the only mutated system.
- The initializer fails closed if a topology endpoint is not a member of the same IndustryChain or
  if a canonical IndustryChain target is missing or wrongly typed in Graphiti.
- Re-running with `--replace` removes stale facts only from the initializer's owned projection
  scope and preserves unrelated graph entities, episodes and relationships.
