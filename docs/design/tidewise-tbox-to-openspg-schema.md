# Tidewise TBox to OpenSPG Schema

> Status: manual-import candidate. The file has not been submitted to OpenSPG.

## Outcome

Represent the 16 active entity types from the authoritative Tidewise PostgreSQL TBox as an
OpenSPG 0.8 declarative Schema while retaining the OpenSPG/KAG foundation types already present in
the `Tidewise` project.

## Scope

- Source snapshot: `event-semantics.phase-one@1`.
- Source table: `public.entity_type_definitions`, active rows only.
- Target file: `schemas/Tidewise.schema`.
- The existing `Person` foundation type is enriched from `person@1`; the other 15 domain types are
  added as distinct EntityTypes.
- PostgreSQL ABox facts, variable signals, event types, relations and executable rules are not part
  of this file.
- The file is prepared for manual review and import; this repository does not submit it
  automatically.

## Mapping

| PostgreSQL `type_key` | OpenSPG type |
| --- | --- |
| `alliance_org` | `AllianceOrganization` |
| `chain_node` | `IndustryChainNode` |
| `commodity` | `Commodity` |
| `company` | `Company` |
| `concept` | `MarketConcept` |
| `economy` | `Economy` |
| `index` | `MarketIndex` |
| `industry` | `Industry` |
| `industry_chain` | `IndustryChain` |
| `instrument` | `FinancialInstrument` |
| `market` | `TradingMarket` |
| `person` | `Person` |
| `policy_body` | `PolicyBody` |
| `product` | `Product` |
| `sector` | `MarketSector` |
| `security` | `Security` |

## Modeling decisions

- `namespace Tidewise` is the first line because OpenSPG requires the project prefix first.
- Parent-child inheritance is not introduced: the PostgreSQL TBox does not currently declare an
  authoritative type hierarchy.
- TBox governance fields are not modeled as instance properties. Repeating `type_key`, version,
  inclusion criteria or extraction permissions on every ABox entity would change their meaning.
- Business definitions and inclusion/exclusion criteria are consolidated into each OpenSPG type's
  `desc`, where they can guide later schema-constrained extraction.
- `MarketConcept` remains an EntityType. Converting it to OpenSPG ConceptType would introduce
  concept hierarchy semantics that the source TBox does not yet define.

## Manual import gate

1. Review the diff in OpenSPG before confirming the Schema update.
2. Confirm the 11 KAG foundation types are retained.
3. Confirm the resulting project exposes 16 Tidewise TBox entity types, counting the enriched
   `Person` type.
4. Do not start an ABox build until the Schema diff is accepted.

## Rollback

Restore the pre-projection Schema from `.runtime/Tidewise/schema/Tidewise.schema`. No PostgreSQL
state is modified by either import or rollback.
