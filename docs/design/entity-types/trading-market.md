# TradingMarket EntityType Review

> Status: reviewed and published to the local OpenSPG evaluation project through a targeted Schema
> API update.

## Boundary

`TradingMarket` is a formal market or exchange with a stable trading scope, operating rules or
venue identity. Individual securities, indices, financial instruments, market sectors and general
market sentiment are excluded.

## Domain properties

| OpenSPG field | Domain meaning |
| --- | --- |
| built-in `id` | Stable identity of the Trading Market. |
| built-in `name` | Canonical Trading Market name. |
| built-in `description` | Concise description used to understand and retrieve the Trading Market. |
| `aliases` | Other names that identify the same Trading Market. |
| `marketType` | Business type based on traded assets or organization form. |
| `currencyCode` | Main currency used for quotation, trading or settlement. |
| `timezone` | Canonical timezone used for the published trading schedule. |

## Relations

`TradingMarket --belongsToCountry--> Country` identifies the country whose legal jurisdiction or
primary operating scope governs the Trading Market. It does not imply that every listed issuer or
traded asset belongs to that country.

## Non-goals

- No Market Index or Market Sector projection.
- No securities, instruments or ABox instances.
- No database join keys, persistence status or timestamps.
