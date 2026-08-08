from __future__ import annotations

import json


def test_context_graph_can_round_trip_through_json(tmp_path):
    """The pinned Intel macOS environment must support Semantica ContextGraph."""
    from semantica.context import ContextGraph

    graph = ContextGraph(
        extract_entities=False,
        extract_relationships=False,
        advanced_analytics=False,
    )
    graph.add_node(
        node_id="event:compatibility-check",
        node_type="Event",
        content="Semantica ContextGraph compatibility check",
    )

    graph_path = tmp_path / "context-graph.json"
    graph.save_to_file(str(graph_path))

    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    assert payload["nodes"][0]["id"] == "event:compatibility-check"

    restored = ContextGraph(
        extract_entities=False,
        extract_relationships=False,
        advanced_analytics=False,
    )
    restored.load_from_file(str(graph_path))

    assert restored.has_node("event:compatibility-check")
