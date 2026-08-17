# MarketConcept EntityType Review

> Status: reviewed and published to the local OpenSPG evaluation project through a targeted Schema
> API update.

## Boundary

`MarketConcept` is a governed stock-market theme commonly supplied by market-data providers such as
Tonghuashun or Eastmoney. It groups objects that share an investment narrative, technology direction
or business logic. An Industry, Industry Chain, Industry Chain Node, individual Security or temporary
event tag is not itself a Market Concept.

## Domain properties

| OpenSPG field | Domain meaning |
| --- | --- |
| built-in `id` | Stable identity of the Market Concept. |
| built-in `name` | Canonical Market Concept name. |
| built-in `description` | Concise description used to understand and retrieve the concept. |
| `aliases` | Other provider names or common names that identify the same concept. |
| `definition` | Business meaning and coverage of the stock-market concept. |

Provider identifiers, source names, review state and timestamps belong to ingestion governance and
are not projected as Market Concept properties.

## Incoming relations

Both `IndustryChain` and `IndustryChainNode` may point to one or more Market Concepts through
`belongsToMarketConcept`. Inverse relations are not duplicated on this type.

## Non-goals

- No generic research-concept taxonomy.
- No concept type, boundary note or provider fields.
- No ABox instances.
