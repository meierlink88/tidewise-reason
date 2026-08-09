# Open-source alternatives to Semantica

Checked on 2026-08-09 against official project documentation, repositories,
licenses, and current public release information.

## Conclusion

No single open-source project is clearly more mature than Semantica across
ingestion, extraction, ontology, graph/vector retrieval, deterministic rules,
temporal facts, provenance, and agent integration. Several projects are much
more mature in narrower layers.

- **Closest integrated alternative:** OpenSPG + KAG.
- **Most mature standards-based semantic core:** Apache Jena/Fuseki; Eclipse
  RDF4J is a close alternative, especially for transactional SHACL validation.
- **Strongest schema-enforced database:** TypeDB.
- **Strongest versioned structured-fact store:** TerminusDB.
- **Agent-memory alternatives, not formal semantic-engine replacements:**
  Graphiti and Cognee.

## Shortlist

### OpenSPG + KAG

OpenSPG exposes schema-based domain modeling, a builder operator framework with
entity linking, concept standardization and entity normalization, and KGDSL rule
reasoning. KAG adds schema-constrained extraction, graph/chunk mutual indexing,
semantic alignment, and logical-form-guided hybrid retrieval/reasoning. This is
the closest match to Tidewise's desired event-to-fact-to-signal-to-agent path and
has Chinese documentation/ecosystem. It is Apache-2.0.

It is also a substantially heavier stack than Semantica: OpenSPG engine and
dependent services are deployed through Docker Compose, while KAG provides a
Python toolkit on top. Its latest advertised KAG release is 0.8.0 (2025-06-27),
so current maintenance, upgrade safety, operational footprint, and API fit must
be verified in a local spike. It still does not provide an A-share ontology,
event taxonomy, signal model, or investment rules.

### Apache Jena / Fuseki

Jena is the mature Apache-2.0 semantic-web foundation: RDF/OWL, SPARQL 1.1,
TDB2, Fuseki HTTP service, SHACL Core/SPARQL constraints, RDFS/OWL reasoners,
and custom rule inference. It directly consumes ontology and instance facts in
one standards-based model, eliminating much of Semantica's disconnected
ontology/fact behavior.

It does not provide Chinese financial extraction, agent memory, production
GraphRAG, or a vector database. Tidewise would compose LinkML-generated
RDF/SHACL with Jena/Fuseki and Qdrant, and implement mapping, event orchestration,
and agent-facing contracts itself.

### Eclipse RDF4J

RDF4J is another mature RDF/SPARQL foundation. Its SHACL engine can validate
transaction changes at commit, which is stronger for fact-quality gates than a
separate report-only validation step. It supports RDFS reasoning and server/UI
components but is not an extraction/vector/agent platform.

### TypeDB

TypeDB CE is MPL-2.0 and enforces a strongly typed entity/relation/attribute
schema at write/commit time. Invalid relationships cannot be stored, which fits
semantic integrity well. TypeDB 3 uses functions instead of TypeDB 2 rules for
reasoning. It is not OWL/RDF/SHACL-native and does not provide vector retrieval,
document extraction, or agent context, so integration would be custom and the
current Neo4j/LinkML model would need translation.

### TerminusDB

TerminusDB 12 is Apache-2.0 and combines schema-enforced JSON/JSON-LD documents,
RDF triples, ACID transactions, immutable history, branch/diff/merge, WOQL
Datalog, and temporal interval reasoning. It is attractive for versioned facts
and event corrections. It lacks the integrated extraction/vector/GraphRAG and
agent context expected from the full Tidewise engine.

### Graphiti and Cognee

Graphiti is strong for temporal agent context graphs, episodes/provenance, and
LLM-driven graph construction, but its prescribed ontology is Pydantic-based and
it has no comparable deterministic domain-rule engine or formal OWL/SHACL
governance. Its own documentation says OSS users bring and operate surrounding
infrastructure.

Cognee offers an appealing add/cognify/search graph+vector memory workflow and
ontology grounding, but remains agent-memory/LLM-extraction-first. It is not a
more mature replacement for formal schema governance, approved rules, and
authoritative fact lifecycle.

## Recommended evaluation

Do not replace Semantica based on feature lists. Run the same bounded vertical
slice against three candidates:

1. Current Semantica 0.6.0 baseline.
2. OpenSPG + KAG as the closest integrated alternative.
3. Apache Jena/Fuseki + Qdrant as the standards-first control.

Use one real Chinese policy or corporate event and require: LinkML-to-runtime
schema projection, canonical company/security mapping, invalid-fact rejection,
graph+source-text retrieval, one deterministic rule, an evidence path, temporal
validity, and an Agent-consumable response. Compare correctness, hidden custom
code, latency, deployment weight, observability, and upgrade risk.

Until that spike, keep LinkML as Tidewise's semantic authoring authority and
keep every candidate behind the versioned Semantic Runtime contract.

## Primary sources

- https://github.com/OpenSPG/openspg
- https://github.com/OpenSPG/KAG
- https://jena.apache.org/documentation/index.html
- https://jena.apache.org/documentation/fuseki2/
- https://jena.apache.org/documentation/shacl/
- https://jena.apache.org/documentation/inference/
- https://rdf4j.org/documentation/programming/shacl/
- https://github.com/typedb/typedb
- https://typedb.com/docs/core-concepts/typeql/schema-data/
- https://typedb.com/docs/typeql-reference/functions/functions-vs-rules/
- https://github.com/terminusdb/terminusdb
- https://github.com/getzep/graphiti
- https://github.com/topoteretes/cognee
