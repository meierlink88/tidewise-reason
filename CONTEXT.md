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
