# Reasoning Evaluation Context

This context defines how Tidewise investment-research semantics are projected into the active
Graphiti-backed Reasoning Server and identifies any authoritative domain facts or relations that
the owning system must add before the reasoning flow can be complete. OpenSPG runtime support is
retired; its remaining design and Schema files are historical, non-executable research records.
Graphiti never becomes the authoritative fact owner.

## Language

**TBox Projection**:
A read-only, version-pinned OpenSPG Schema representation of authoritative Tidewise entity types,
variable definitions, relation signatures and rule identities.
_Avoid_: TBox migration, ontology replacement, continuous synchronization

**SPG Schema**:
The OpenSPG type system that constrains future entities, events, properties and relations; it is not
instance data.
_Avoid_: Knowledge graph data, facts, ABox

**EntityType Review Fragment**:
A standalone, parseable Schema file used to review one Tidewise EntityType before merging it into
the complete OpenSPG project Schema.
_Avoid_: Complete import Schema, incremental Schema patch

**Alliance Organization**:
A persistent intergovernmental or cross-entity organization formed by independent formal members
under a charter, treaty or institutional rules, with stable identity, membership, governance and
ongoing functions.
_Avoid_: Initiative, agreement, trade arrangement, summit, ad hoc forum, temporary partnership

**Industry**:
A stable category of economic activity organized by the products or services it supplies, with an
optional direct parent Industry in the canonical Tidewise hierarchy.
_Avoid_: Market Sector, Research Concept, Industry Chain, Company, Product

**Industry Chain**:
A bounded, directed research subgraph organized around a target output and end use, formed by
Industry Chain Nodes connected through input, component or dependency relations.
_Avoid_: Industry, Company, Product, Industry Chain Node, temporary event-transmission path

**Industry Chain Node**:
A reusable business or technical stage that may participate in multiple Industry Chains. Its
upstream, midstream or downstream position belongs to a specific Industry Chain membership and is
not a global node property.
_Avoid_: Company, Security, complete Industry Chain, temporary event action

**Concept**:
A cross-industry technology, policy, application, demand, business-model, ecosystem, event-narrative
or market-theme fact with a stable identity and reviewed boundary.
_Avoid_: Industry classification, Industry Chain, Industry Chain Node, temporary event tag

**Company**:
An independently operating business entity belonging to one or more Industries, Industry Chain
Nodes, Market Concepts and Trading Markets, and with one Country of registration or primary legal
domicile.
_Avoid_: Security, Brand, Product, Industry Chain Node, government body, temporary project

**Trading Market**:
A formal market or exchange with a stable trading scope, operating rules or venue identity, under
the legal jurisdiction or primary operation of a Country.
_Avoid_: Market Index, Market Sector, Security, Financial Instrument, market sentiment

**ABox**:
Entity, event, signal and relation instances that conform to the SPG Schema.
_Avoid_: Schema, type catalog, TBox

**Controlled Variable**:
A globally reusable, versioned change dimension that a Signal may apply to one permitted Analysis
Anchor type. Its stable identity, definition, measurement basis, optional unit, applicability and
maintenance owner belong to the Variable catalog. Direction, impact period, confidence and the
concrete Anchor belong to a Signal and never create Anchor-specific Variable copies.
_Avoid_: Signal direction, current value, permanent Anchor attribute, per-Anchor Variable duplicate

**GeopoliticRivalry**:
A stable Tidewise Data narrative blueprint for one geopolitical rivalry or military war. Reviewed
actor and influenced-region texts describe its scope but do not establish authoritative Country,
Region or Organization relationships.
_Avoid_: Event category, Storyline, inferred Actor relation, GeopoliticalRivalry alias type

**MacroEconomic**:
A stable Tidewise Data narrative blueprint for one monetary, fiscal, trade-policy, regulatory or
data-economic subject. It has no implied Country, Region, Institution or Storyline relationship.
_Avoid_: Event category, one economic data release, MacroEconomics alias type, inferred ownership

**Signal**:
A time-scoped, Event-linked statement that a controlled Variable changes or holds on one Analysis
Anchor. A direct Signal interprets one curated Event; a derived Signal records an explicitly
grounded analytical consequence. It remains transitively auditable to the Event's Evidence but does
not use Evidence as a downstream reasoning input. A Signal is not a static attribute or an
investment conclusion.
_Avoid_: Variable definition, Company property, permanent trend label, buy/sell conclusion

**Signal Transmission Link**:
A reasoning Link from one Signal to another that records the business mechanism, time lag,
conditions, invalidation criteria and the authoritative topology Link used to ground one
cross-entity step. Its existence records a reviewed analytical path, not an automatic graph rule.
_Avoid_: Direct Impact Assertion, synthetic industry-chain edge, fixed-hop propagation rule

**Evidence**:
An immutable, source-addressable input used by the upstream Event curation work to establish,
split, normalize, support or challenge an Event. Evidence is retained for provenance and audit but
does not enter Event Analysis or Investment Reasoning as a direct inference input and is not
projected into Graphiti.
_Avoid_: Event, Signal, downstream AgentContext input, LLM conclusion, unsupported market opinion

**Event**:
A time-scoped factual occurrence, plan or evaluation scenario produced by upstream Evidence
curation and accepted as the factual starting point of downstream reasoning. Live and isolated
evaluation Events use the same domain language; their source, public-knowledge and ingestion times
remain distinct and auditable through upstream Evidence links. A Data-published Event enters
Graphiti through its native Episode pipeline, which may create contextual Entities and explicit
Facts without making them authoritative Tidewise master data.
_Avoid_: Research Event, Scenario Event, Signal, forecast, investment conclusion

**Event Candidate Submission**:
Agent OS 已从 Evidence 提炼的一次现实动作候选及其 Evidence IDs，由 Reasoning
持久化为可重放工作流输入。它不是 Event 领域对象，不进入 Graphiti；只有判定为新事件并由
Data 发布后的正式 Event 才投影。
_Avoid_: Agent 提交 Event ID、Candidate 图节点、用请求指纹做语义去重

**Analysis Anchor**:
The stable Entity whose connected facts and relations define the bounded scope of one analysis.
_Avoid_: Storyline, user prompt, temporary result, unbounded graph traversal

**Event Anchor Link**:
A reviewed reasoning Link that grounds one curated Event's direct 5W1H meaning to a stable Analysis
Anchor or a scope/mechanism Entity required by downstream reasoning. It does not represent every
mentioned Entity or an indirectly inferred affected node.
_Avoid_: Mention edge, all Event entities, derived impact Link, Storyline route

**Storyline**:
A versioned, falsifiable investment-research thesis around one Analysis Anchor, research question
and scope. It preserves the prior thesis baseline, supporting and contradicting Events and Signals,
competing explanations, horizon views, invalidation conditions and review triggers across runs.
_Avoid_: Event category, evidence folder, one Agent answer, permanent positive narrative

**Analysis Result**:
A reproducible, time-stamped interpretation produced from a declared question, retrieved graph
context, Events, Signals and the applicable Storyline baseline. It contains a concise conclusion,
an auditable reasoning tree, horizon-specific opportunity/risk assessments and their conditions;
it is not silently promoted to a new fact. Event-to-Evidence provenance remains available for audit
outside the downstream reasoning input.
_Avoid_: Evidence, Event, Storyline, permanent entity attribute, raw hidden chain of thought

**Ontology Catalog**:
The versioned, Reason-owned extraction contract derived from authoritative Data entity and relation
contracts. It constrains Graphiti extraction and supplies task-specific Schema subsets without
becoming the owner of the projected facts.
_Avoid_: All graph instances, generated Cypher, unversioned prompt text

**Analysis Context**:
The reproducible task input assembled from one question, anchor, as-of time, horizon, selected
Ontology fragment, temporally eligible Events and Signals, graph relations, Storyline baseline and
explicit validation issues. It may carry Event provenance identifiers for audit but not Evidence
content as a reasoning input.
_Avoid_: Final conclusion, unbounded graph dump, provider-specific search response
