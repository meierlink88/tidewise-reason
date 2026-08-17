# OpenSPG Evaluation Context

This context evaluates how Tidewise investment-research semantics can be projected into OpenSPG
without changing the authoritative Tidewise domain model.

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
A stable business structure within one Industry, formed by Industry Chain Nodes connected in a
directed upstream-to-downstream sequence; it may belong to one or more Market Concepts.
_Avoid_: Industry, Company, Product, Industry Chain Node, temporary event-transmission path

**Industry Chain Node**:
A stable business stage within an Industry Chain that may directly point to one or more downstream
Industry Chain Nodes, has one canonical upstream, midstream or downstream position, and may belong
to one or more Market Concepts.
_Avoid_: Company, Security, complete Industry Chain, temporary event action

**Market Concept**:
A stock-market theme that groups Industry Chains and Industry Chain Nodes sharing an investment
narrative or business logic.
_Avoid_: Industry, Industry Chain, Industry Chain Node, Security, temporary event tag

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

**Variable Signal**:
A time-scoped event-native statement that a controlled variable changes or holds on a research
entity; it is not a static attribute of that entity.
_Avoid_: Company property, metric definition, investment conclusion

**Direct Impact Assertion**:
A one-hop analytical assertion from a source Variable Signal to a target entity's controlled
variable, with explicit mechanism and optional approved rule identity.
_Avoid_: Event fact, graph relation, security-price conclusion
