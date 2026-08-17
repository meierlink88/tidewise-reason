# Company EntityType Review

> Status: reviewed and published to the local OpenSPG evaluation project through a targeted Schema
> API update.

## Boundary

`Company` is an independently operating enterprise, group or legal business entity. A Security,
brand, Product, government body, alliance organization or temporary project is not a Company.

## Domain properties

| OpenSPG field | Domain meaning |
| --- | --- |
| built-in `id` | Stable identity of the Company. |
| built-in `name` | Canonical Company name. |
| built-in `description` | Concise description used to understand and retrieve the Company. |
| `aliases` | Other names that identify the same Company. |
| `area` | Registration, headquarters or principal operating region below or across country level. |
| `controllerName` | Name of the ultimate or materially influential controlling party. |
| `controllerType` | Business type of that controlling party. |

`industryName` is excluded because Industry identity is represented by a relation rather than
duplicated text.

## Relations

`Company --belongsToIndustry--> Industry` identifies an Industry in which the Company principally
operates. One Company may belong to multiple Industries.

`Company --belongsToCountry--> Country` identifies its country of registration or primary legal
domicile.

`Company --belongsToIndustryChainNode--> IndustryChainNode` identifies a value-chain stage to which
the Company's business belongs. One Company may belong to multiple nodes.

`Company --belongsToMarketConcept--> MarketConcept` identifies a stock-market concept theme that
includes the Company. One Company may belong to multiple Market Concepts.

`Company --belongsToTradingMarket--> TradingMarket` identifies a principal listing market or market
assignment. One Company may belong to multiple Trading Markets.

## Non-goals

- No securities, products or ABox instances.
- No duplicated Industry-name property.
- No database join keys, persistence status or timestamps.
