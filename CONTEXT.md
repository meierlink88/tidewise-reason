# Semantic Runtime Context

**Semantic Model**:
The versioned LinkML definition of Tidewise domain concepts, properties, links, and constraints.
It is the authoring authority for this proof of concept.
_Avoid_: database schema, prompt text, vector payload

**Concept Card**:
A task-readable projection of one Semantic Model concept, carrying its stable semantic identity,
definition, properties, boundaries, and references. It is generated from the Semantic Model.
_Avoid_: hand-maintained prompt fragment, executable action, business fact

**Semantic Runtime**:
The infrastructure that loads a published Semantic Model projection, validates semantic facts,
stores/query them, and returns bounded semantic context to an Agent Workflow.
_Avoid_: business system of record, LLM orchestration, unrestricted database access

**Semantic Fact**:
A typed assertion about a domain object, linked to a Semantic Model release and provenance. A
Semantic Fact is authoritative only after acceptance by its owning domain service.
_Avoid_: model suggestion, vector search hit, unreviewed extraction

**Event Candidate**:
A structured proposal produced from source text using the active Event Concept Card. It is not a
formal Tidewise Event until validated and accepted by the Data Domain Service.
_Avoid_: formal Event, free-form summary, automatically trusted model output

