# Semantica Ontology–Fact Mapping

Checked on 2026-08-09 against Semantica 0.6.0 and current official documentation.

## Conclusion

Facts must use, or be explicitly mapped to, the ontology's canonical class,
property, and entity identifiers if the ontology is expected to govern query,
validation, or reasoning. Semantica provides mapping-related components, but it
does not automatically pass imported ontologies through extraction, rewrite
facts, validate before storage, or repair violations.

If extraction emits canonical terms and IDs from the beginning, there is no
separate post-extraction mapping step; the facts are born aligned.

## Available mechanisms

1. **Ontology-to-ontology alignment**: `OntologyEngine.create_alignment()` stores
   explicit OWL/SKOS alignment triples in a configured `TripletStore`.
   `get_alignments()` and `list_alignments()` retrieve
   `owl:equivalentClass`, `owl:equivalentProperty`, `owl:sameAs`, and SKOS match
   predicates. `ReuseManager.suggest_alignments()` only suggests exact-label
   class/property matches; suggestions are not automatically committed.
2. **Entity identity alignment**: `EntityNormalizer` accepts a caller-provided
   `alias_map`; `EntityLinker` can assign URIs and propose `same_as` or
   `related_to` links using text similarity and an attached graph. These tools
   do not derive canonical A-share identities from an ontology.
3. **Stable names and IRIs**: `NamespaceManager` generates class/property IRIs
   and manages prefixes. It does not rewrite source facts by itself.
4. **Constraint checking**: `SHACLGenerator` and `OntologyValidator` validate a
   graph against shapes and return a report. The caller decides whether to
   reject, quarantine, repair, or accept a violation.
5. **Deduplication**: entity resolution can merge duplicate factual entities,
   but it is distinct from mapping their classes and predicates to an ontology.

## Missing automatic bridge

`AgentContext`, semantic extractors, and `GraphBuilder` do not accept an imported
ontology as an automatic canonicalisation contract. The caller must explicitly
constrain extraction, map source types/predicates and entity aliases, call SHACL
validation, and publish only accepted facts. Stored alignment triples also do
not automatically relabel Neo4j records or Qdrant metadata.

For Tidewise, LinkML remains the semantic authoring authority. A source mapping
registry should map incoming labels and identifiers to LinkML canonical terms;
generated OWL/SHACL and Semantica alignment records are projections and
governance aids.

## Primary sources

- https://docs.getsemantica.ai/guides/ontology/
- https://docs.getsemantica.ai/reference/ontology/
- https://docs.getsemantica.ai/guides/shacl-validation/
- https://docs.getsemantica.ai/reference/normalize/
- https://docs.getsemantica.ai/reference/context/
- https://github.com/semantica-agi/semantica/blob/main/semantica/ontology/engine.py
- https://github.com/semantica-agi/semantica/blob/main/semantica/ontology/reuse_manager.py
- https://github.com/semantica-agi/semantica/blob/main/semantica/context/entity_linker.py
