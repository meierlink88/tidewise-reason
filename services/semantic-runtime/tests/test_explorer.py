from __future__ import annotations

import json

from tidewise_semantic_runtime.explorer import ensure_context_graph


def test_explorer_initializes_an_empty_generated_context_graph(tmp_path) -> None:
    graph_path = tmp_path / "context-graph.json"

    ensure_context_graph(graph_path)

    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    assert payload["nodes"] == []
    assert payload["edges"] == []


def test_explorer_preserves_an_existing_context_graph(tmp_path) -> None:
    graph_path = tmp_path / "context-graph.json"
    graph_path.write_text('{"sentinel": true}', encoding="utf-8")

    ensure_context_graph(graph_path)

    assert graph_path.read_text(encoding="utf-8") == '{"sentinel": true}'
