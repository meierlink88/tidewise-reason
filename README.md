# Semantica Runtime

An isolated Tidewise proof of concept for publishing a LinkML semantic model into Semantica and
using it as the semantic infrastructure for an Agent Workflow.

## First vertical slice

The first concept is `Event`. The first Agent scenario turns one source-supported statement into a
strict `EventCandidate` using the active Event Concept Card.

Planned flow:

```text
LinkML Event model
  -> OWL + SHACL + Concept Card release
  -> Semantica ontology and validation runtime
  -> task-scoped semantic query
  -> model adapter
  -> validated EventCandidate
```

## Status

- Repository scaffolded.
- LinkML Event model authored.
- Semantica dependency pinned.
- Runtime behavior intentionally waits for confirmation of the public test seam.

The Intel macOS development environment pins `onnxruntime==1.20.1`, `torch==2.2.2`,
`numba==0.61.2`, and `llvmlite==0.44.0` because newer releases do not publish compatible x86_64
wheels. The Semantica 0.6.0 PyPI distribution does not contain the Oxigraph module present in the
current source repository, so this slice does not claim embedded RDF persistence. Remove the
platform pins after upstream package metadata and wheels are verified.

## Local setup

```bash
uv sync
PYSTOW_HOME=.cache/pystow uv run python -c "import semantica; print(semantica.__version__)"
PYSTOW_HOME=.cache/pystow .venv/bin/python scripts/smoke_semantic_model.py
```

`PYSTOW_HOME` is project-local so LinkML tooling remains hermetic in sandboxed and CI runs.
