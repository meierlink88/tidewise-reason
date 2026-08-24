# ADR 0003: Project IndustryChain mappings with graph creation time

- Status: Accepted
- Date: 2026-08-24
- Issue: [#17](https://github.com/meierlink88/tidewise-reason/issues/17)

## Context

Tidewise Data owns 708 canonical IndustryChain records and typed `mapped_to_industry` and
`mapped_to_concept` Links. The IndustryChain list exposes source-record timestamps, while the
Research Graph mapping contract exposes stable Link IDs and status but no Link timestamp.

Graphiti requires `created_at` on an Entity relationship. For a deterministic projection this
timestamp describes when the relationship first became a graph fact; copying the IndustryChain
timestamp would falsely describe a Data record time as a graph write time. Refreshing it on every
upsert would also erase the graph's ingestion history.

## Decision

Reason projects canonical IndustryChain nodes after their mapped Industry and Concept targets have
already been projected. Every mapping keeps the Data Link's `ERL...` ID in `data_object_id` and uses
a deterministic Graphiti UUID derived from relation type and endpoints.

The authoritative writer generates an explicit UTC `created_at` for each new relationship write
batch. Its Neo4j upsert keeps the existing value when the deterministic UUID already exists, while
replacing all other relationship properties and the vector. Deleting and later recreating a
relationship creates a new timestamp. Source business-effective time, if later exposed, belongs in
Graphiti `valid_at` rather than `created_at`.

The IndustryChain projection writes only `IndustryChainMappedToIndustry` and
`IndustryChainMappedToConcept`. `primary_country_id` remains a node property. Country and ChainNode
relationships are not created; ChainNode membership remains owned by the later ChainNode
projection.

## Consequences

- Data Service does not need to fabricate or expose a mapping creation timestamp for this import.
- Re-running an unchanged projection preserves the first graph creation time.
- A complete preflight rejects missing Industry mappings, duplicate endpoint mappings, incorrect
  target types, inactive mappings and targets that are not canonical deterministic graph nodes.
- The projection can safely replace only its owned IndustryChain nodes and two mapping types while
  preserving Country, Region, Industry, Concept and Episode facts.
- Historical relationships created by older projectors are not timestamp-migrated because their
  original graph creation instants are no longer observable.
