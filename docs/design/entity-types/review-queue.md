# EntityType Draft Review Queue

> Status: generated drafts only. None of the types in this queue have been submitted to OpenSPG.

## Shared modeling rules

- Model domain objects and domain relations, not database tables.
- Keep stable business attributes such as aliases, classifications, definitions and codes.
- Exclude join keys, source discriminators, persistence status, review workflow fields and audit
  timestamps.
- Describe properties only in business language.
- Do not import or infer ABox facts during Schema review.
- Review and accept one EntityType before any targeted OpenSPG submission.

## Suggested review order

1. `Commodity`
2. `MarketConcept`
3. `PolicyBody`
4. `MarketSector`
5. `Industry`
6. `IndustryChainNode`
7. `IndustryChain`
8. `Company`
9. `Product`
10. `TradingMarket`
11. `MarketIndex`
12. `FinancialInstrument`
13. `Security`
14. `Person`

## Deferred relationship decisions

- `FinancialInstrument` underlying targets can be commodities, indices, securities or other entity
  types. Do not use a database UUID or an unconstrained `Thing` relation before a reviewed target
  model exists.
- `Person` organization membership can target companies, policy bodies or alliance organizations.
  A shared organization supertype has not been accepted, so this relation is deferred.
- Industry-chain membership is expressed as
  `IndustryChainNode --belongsToIndustryChain--> IndustryChain`; the inverse
  `IndustryChain --containsNode--> IndustryChainNode` relation is not duplicated. Direct business
  flow is expressed as `IndustryChainNode --downstreamNode--> IndustryChainNode`.
- `IndustryChain` and `IndustryChainNode` may each have multiple `belongsToMarketConcept` relations
  to provider-governed stock-market concepts.
- Company classification is expressed through `belongsToIndustry`, legal domicile through
  `belongsToCountry`, value-chain membership through `belongsToIndustryChainNode`, and stock-market
  theme membership through `belongsToMarketConcept`; `belongsToTradingMarket` identifies its main
  listing or market assignment. Product relations remain deferred until the Product endpoint is
  reviewed.
- Source `Economy` references are broader than the accepted `Country` type. Company, market and
  person relations targeting `Country` require country-level filtering before any ABox import.
- `MarketSector` has no current profile contract, so its first draft contains only identity,
  canonical name/description and aliases.
