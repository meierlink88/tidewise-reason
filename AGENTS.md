# AGENTS.md

This repository is an isolated proof of concept for the Tidewise Semantic Runtime.

- Keep LinkML under `semantic-model/` as the authoritative semantic authoring source.
- Treat OWL, SHACL, concept cards, RDF data, graph records, and vectors as generated projections.
- Never make an LLM, vector match, or graph projection the authority for Tidewise business facts.
- Add one behavior at a time through a public CLI or API seam and test it before implementation.
- Do not commit provider credentials, source documents, prompts containing sensitive data, or `.env`.
- Pin dependency versions and record any Semantica workaround with its removal condition.

