# Semantic Runtime Context

**Semantic Model**:
The versioned LinkML definition of Tidewise domain concepts, properties, links, and constraints.
It is the semantic authoring authority.

**Semantic Runtime**:
The runtime that publishes and validates Semantic Model projections, retrieves bounded semantic
context, executes approved reasoning, and exposes those capabilities through a versioned interface.

**Projection**:
A rebuildable OWL, SHACL, concept-card, RDF, Neo4j, or Qdrant representation generated from the
Semantic Model or accepted domain facts. A Projection is never an authority by itself.
