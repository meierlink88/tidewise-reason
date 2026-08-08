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
`transformers==4.57.6`, `numpy==1.26.4`, `numba==0.61.2`, and `llvmlite==0.44.0`. Newer PyTorch
releases do not publish compatible x86_64 macOS wheels, PyTorch 2.2.2 uses the NumPy 1 ABI, and
Transformers 5 requires PyTorch 2.4 or newer. Because Semantica 0.6.0 declares `numpy>=2.0.2`, uv
uses an explicit NumPy override documented in `pyproject.toml`. Remove the override only after a
Semantica and PyTorch release pair is verified on Intel macOS, or after Intel macOS ceases to be a
supported development target.

The Semantica 0.6.0 PyPI distribution does not contain the Oxigraph module present in the current
source repository, so this slice does not claim embedded RDF persistence.

## Local setup

```bash
uv sync
PYSTOW_HOME=.cache/pystow uv run python -c "import semantica; print(semantica.__version__)"
PYSTOW_HOME=.cache/pystow .venv/bin/python scripts/smoke_semantic_model.py
uv run pytest tests/test_semantica_compatibility.py -q
```

`PYSTOW_HOME` is project-local so LinkML tooling remains hermetic in sandboxed and CI runs.
