# IndustryChainNode EntityType Review

> Status: reviewed and published to the local OpenSPG evaluation project through targeted Schema
> API updates.

## Boundary

`IndustryChainNode` is a stable business stage within an Industry Chain. It can represent an input,
manufacturing step, process, component, equipment category, service or other economic stage. A
company, security, complete Industry Chain or temporary event action is not an Industry Chain Node.

## Domain properties

| OpenSPG field | Domain meaning |
| --- | --- |
| built-in `id` | Stable identity of the Industry Chain Node. |
| built-in `name` | Canonical Industry Chain Node name. |
| built-in `description` | Concise description used to understand and retrieve the node. |
| `aliases` | Other names that identify the same node. |
| `definition` | Business definition of the product, technology, process, equipment, service or stage. |
| `boundaryNote` | Inclusion, exclusion and adjacent-node boundary. |
| `chainPosition` | Canonical position: `upstream`, `midstream` or `downstream`. |

## Relations

`IndustryChainNode --downstreamNode--> IndustryChainNode` identifies a node that directly follows
the source node in the chain's business flow. One node may point to multiple downstream nodes.

`IndustryChainNode --belongsToIndustryChain--> IndustryChain` identifies the chain that contains the
node. The inverse `IndustryChain --containsNode--> IndustryChainNode` relation is intentionally not
duplicated.

`IndustryChainNode --belongsToMarketConcept--> MarketConcept` identifies a stock-market concept
theme that includes the node. One node may belong to multiple Market Concepts.

## Non-goals

- No category, component, input or dependency relation variants.
- No ABox instances.
- No database join keys, persistence status or timestamps.
