# ADR 0008: Model reusable macroeconomic policy actions

- Status: Accepted
- Date: 2026-08-26

## Context

The initial `MacroEconomic` ontology described broad country-specific narrative blueprints such as
"United States monetary policy". That shape mixes three separate meanings: a stable policy action,
the policy category, and the country whose institutions can use the action. It also encourages one
"rate hike" node per country and makes Event classification harder to distinguish from entity
resolution.

The investment-reasoning design needs reusable policy anchors such as rate hikes, reserve-ratio
cuts, fiscal stimulus and industrial subsidies. A concrete announcement or implementation remains
a time-scoped Event and Graphiti Fact.

## Decision

- `MacroEconomic` represents one reusable policy action and uses a stable `policy_key`.
- `MacroEconomic.category` is a property, not a graph node. Its closed enum contains ten policy
  lines: monetary, fiscal, industrial policy, growth/cycle, inflation/prices, employment/labor,
  financial stability, external sector, debt/leverage and real estate/land.
- Country names are not part of the policy node identity.
- `CountryImplementsMacroEconomic` is the ontology relation for institutional applicability. The
  graph fact name is `IMPLEMENTS`; it means that the country's policy system can use the action and
  does not mean that it is currently doing so.
- Current execution, direction, timing and market impact are expressed later by Event-derived Facts
  and Signals, not by mutating the static applicability relation.
- The graph-only evaluation catalog contains 78 reviewed policy actions. It links only existing
  canonical Country nodes for China, the United States, Japan, South Korea and the United Kingdom,
  using a curated applicability list rather than a Cartesian product.
- The catalog initializer is deterministic, idempotent, does not call the LLM, does not write
  Tidewise Data, does not assign `data_object_id`, and does not delete graph data.

## Consequences

- The ontology catalog advances to `reasoning-ontology/v3`; `macro_type` is replaced by `category`
  and the former five-value `MacroEconomicType` enum is retired.
- Event extraction may resolve an Event to a reusable policy action, while Event classification and
  Signal derivation remain separate reasoning stages.
- A future Data-owned MacroEconomic catalog can replace the graph-only fixture through a reviewed
  migration without changing the reusable-policy identity model.
