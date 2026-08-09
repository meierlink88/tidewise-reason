# Tidewise TBox to OpenSPG Schema

> Status: unapproved draft. The combined projection was rolled back and must be reviewed one type
> at a time before any future submission.

## Outcome

Propose a projection of the current authoritative Tidewise PostgreSQL TBox into the existing
OpenSPG project `Tidewise` (project ID `1`) as Schema only. The proposal is not currently applied.

## Ownership and boundaries

- Tidewise Data Service and PostgreSQL remain the only owners of the source TBox and domain facts.
- OpenSPG owns only this local evaluation projection.
- This is a one-time, read-only source snapshot, not a production database integration or sync job.
- PostgreSQL ABox tables such as `entity_nodes` and `entity_edges` are explicitly out of scope.
- The source snapshot is `event-semantics.phase-one@1`: 16 active Entity Type Definitions, 12 active
  Variable Definitions and 4 approved Direct Transmission Rules.

## Mapping

| Tidewise TBox | OpenSPG Schema | Notes |
| --- | --- | --- |
| Entity Type Definition | `ResearchEntity` subtype | Stable key/version and definition are retained in the mapping and type description. |
| Variable Definition | `VariableSignal` EventType subtype | Keeps changes time-scoped instead of turning them into static entity attributes. |
| Applicable Entity Types | Event subtype description | OpenSPG 0.8 MarkLang cannot enforce a union-typed Event subject without a synthetic type hierarchy. |
| `produces` rule signature | Typed OpenSPG relation | Defines Company→Product, IndustryChainNode→Product and IndustryChainNode→IndustryChainNode. |
| Direct Transmission Rule | `DirectImpactAssertion` controlled fields | Rule keys are allowed identities; executable KGDSL is deferred until temporal fact semantics are designed. |

## Type-name mapping

| PostgreSQL `type_key` | OpenSPG type |
| --- | --- |
| `alliance_org` | `AllianceOrganization` |
| `chain_node` | `IndustryChainNode` |
| `commodity` | `Commodity` |
| `company` | `Company` |
| `concept` | `ResearchConcept` |
| `economy` | `Economy` |
| `index` | `MarketIndex` |
| `industry` | `Industry` |
| `industry_chain` | `IndustryChain` |
| `instrument` | `FinancialInstrument` |
| `market` | `TradingMarket` |
| `person` | `NaturalPerson` |
| `policy_body` | `PolicyBody` |
| `product` | `Product` |
| `sector` | `MarketSector` |
| `security` | `Security` |

## Variable-signal mapping

| PostgreSQL `variable_key` | OpenSPG EventType | Applicable OpenSPG entity types |
| --- | --- | --- |
| `gross_margin` | `GrossMarginSignal` | `Company` |
| `market_demand` | `MarketDemandSignal` | `IndustryChainNode`, `Commodity`, `Industry`, `IndustryChain`, `Product` |
| `market_price` | `MarketPriceSignal` | `Commodity`, `Product` |
| `market_supply` | `MarketSupplySignal` | `IndustryChainNode`, `Commodity`, `Industry`, `IndustryChain`, `Product` |
| `net_profit` | `NetProfitSignal` | `Company` |
| `order_quantity` | `OrderQuantitySignal` | `Company`, `Product` |
| `order_value` | `OrderValueSignal` | `Company`, `Product` |
| `policy_support_intensity` | `PolicySupportIntensitySignal` | `IndustryChainNode`, `Commodity`, `Company`, `ResearchConcept`, `Industry`, `IndustryChain`, `Product`, `MarketSector` |
| `production_volume` | `ProductionVolumeSignal` | `IndustryChainNode`, `Commodity`, `Company`, `Industry`, `Product` |
| `regulatory_restriction_intensity` | `RegulatoryRestrictionIntensitySignal` | `IndustryChainNode`, `Commodity`, `Company`, `ResearchConcept`, `Industry`, `IndustryChain`, `Product`, `MarketSector`, `Security` |
| `revenue` | `RevenueSignal` | `Company` |
| `sales_volume` | `SalesVolumeSignal` | `Company`, `Industry`, `Product` |

## Failure and rollback

- Schema submission is idempotent: re-submitting the same MarkLang produces no diff.
- A parse or server validation error stops before ABox creation because this task has no data-import
  step.
- Rollback is performed by committing the previous project Schema; no PostgreSQL state is modified.

## Acceptance

1. MarkLang parses locally without a server mutation.
2. OpenSPG project `1` exposes all 16 mapped domain entity types and all 12 variable-signal types.
3. The three `produces` relation signatures and `DirectImpactAssertion` controlled fields exist.
4. Neo4j contains no instances carrying the `Tidewise` domain labels after Schema submission.
