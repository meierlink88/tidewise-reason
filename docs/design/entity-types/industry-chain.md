# IndustryChain EntityType Review

> Status: reviewed and published to the local OpenSPG evaluation project through targeted Schema
> API updates.

## Boundary

`IndustryChain` is a stable business structure within one Industry. Its nodes are connected in a
directed upstream-to-downstream sequence. A single Industry, company, product, node or temporary
event-transmission path is not an Industry Chain.

## Domain properties

| OpenSPG field | Domain meaning |
| --- | --- |
| built-in `id` | Stable identity of the Industry Chain. |
| built-in `name` | Canonical Industry Chain name. |
| built-in `description` | Concise description used to understand and retrieve the Industry Chain. |
| `aliases` | Other names that identify the same Industry Chain. |
| `scope` | Business activities, key stages and analytical boundary covered by the Industry Chain. |

## Relations

`IndustryChain --belongsToIndustry--> Industry` identifies the Industry that owns the chain in the
business classification. Node membership is owned by `IndustryChainNode` and will be expressed in
that type's review; the inverse `containsNode` relation is intentionally omitted.

`IndustryChain --belongsToMarketConcept--> MarketConcept` identifies a stock-market concept theme
that includes the chain. One Industry Chain may belong to multiple Market Concepts.

## Excluded properties

Target output, end use, geography, effective date, technology-route qualifier and observable
variables are not stable metadata required to identify an Industry Chain, so they are not projected
as properties.

## Non-goals

- No ABox instances.
- No node-membership relation on this type.
- No database join keys, persistence status or timestamps.
