"""Semantica Explorer process over a generated local ContextGraph projection."""

from __future__ import annotations

import os
from pathlib import Path

from semantica.context import ContextGraph
from semantica.explorer import main as semantica_explorer_main


def ensure_context_graph(graph_path: Path) -> None:
    if graph_path.exists():
        return

    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph = ContextGraph(
        extract_entities=False,
        extract_relationships=False,
        advanced_analytics=False,
    )
    graph.save_to_file(str(graph_path))


def main() -> None:
    graph_path = Path(os.environ.get("SEMANTICA_EXPLORER_GRAPH", "/data/context-graph.json"))
    ensure_context_graph(graph_path)
    semantica_explorer_main(
        [
            "--graph",
            str(graph_path),
            "--host",
            "0.0.0.0",
            "--port",
            os.environ.get("SEMANTICA_EXPLORER_PORT", "8000"),
            "--no-browser",
        ]
    )
