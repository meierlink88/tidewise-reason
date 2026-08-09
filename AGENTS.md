# AGENTS.md

This repository is the Tidewise Agent OS proof of concept.

- Treat `services/semantic-runtime/` and `services/agent-runtime/` as separate runtime ownership
  contexts. They communicate through versioned contracts, never implementation imports.
- Keep LinkML under `services/semantic-runtime/semantic-model/` as the authoritative semantic
  authoring source.
- Treat OWL, SHACL, concept cards, RDF data, graph records, and vectors as generated projections.
- Never make an LLM, vector match, or graph projection the authority for Tidewise business facts.
- Agent Runtime owns LLM access, Agent/Workflow orchestration, prompts, run state, and calls to the
  Semantic Runtime interface.
- Semantic Runtime owns semantic model publication, validation, semantic retrieval, reasoning,
  provenance, and decision-support interfaces. It does not own Agent workflow state.
- Add one behavior at a time through a public CLI or API seam and test it before implementation.
- Do not commit provider credentials, source documents, prompts containing sensitive data, or
  `.env`.
- Pin dependency versions and record any Semantica workaround with its removal condition.
