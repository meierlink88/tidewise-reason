# ADR 0009: Initialize unlinked fundamental Variables

- Status: Accepted
- Date: 2026-08-26

## Context

Investment reasoning needs a controlled vocabulary for changes in demand, supply, capacity, price,
profitability, technology, competition, macro policy, geopolitics and company financials. These
Variables must be available before the Event-analysis pipeline can create Signal Facts.

Pre-linking every Variable to every IndustryChain, ChainNode, GeopoliticRivalry, MacroEconomic or
Company would create a large Cartesian graph and falsely imply that every Variable currently
applies to every anchor. Keeping an undifferentiated catalog would instead force the LLM to compare
every Event with every Variable and would mix fundamental observations with investment conclusions.

## Decision

- `Variable` gains a required `variable_role` that distinguishes `FUNDAMENTAL` from the later
  `INVESTMENT_ASSESSMENT` role.
- `Variable` gains one required primary `variable_group` used to reduce candidate retrieval by
  causal channel. Investment-assessment role and group must be declared together.
- `allowed_anchor_types` remains type-level applicability metadata. It does not create graph edges.
- The Reason-owned `variable-catalog/v1` contains 56 reviewed fundamental Variables in nine groups:
  demand, supply/capacity, price/profitability, capital cycle, technology, competition/security,
  macro policy, geopolitics and company financials.
- The initializer writes only deterministic `Variable` nodes with embeddings. It writes no edges,
  calls no LLM, performs no Data Service write and deletes no graph data.
- A concrete Variable-to-anchor association is created only later as an Event-supported temporal
  Signal Fact containing direction, intensity, horizon, validity and confidence.
- Investment-assessment Variables are intentionally excluded from `variable-catalog/v1`; they will
  be introduced with the investment-reasoning pipeline and its derivation rules.

## Consequences

- The ontology catalog advances to `reasoning-ontology/v4`.
- Event analysis can shortlist Variables by Event class, `variable_group` and
  `allowed_anchor_types` without traversing static Variable-to-anchor relations.
- An isolated Variable node is expected before Signal extraction and is not missing graph data.
- Future Signal Facts can reuse one Variable identity across many anchors, periods and directions
  without copying the Variable node.
