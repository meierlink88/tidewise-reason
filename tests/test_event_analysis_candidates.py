from __future__ import annotations

import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from graphiti_core.nodes import EntityNode

from analysis.event.graphiti.candidates import GraphitiCandidateRetriever
from tests.test_event_analysis_pipeline import ANCHOR_UUID, classification, event_input


def graph_node(uuid: str, name: str, label: str, **attributes) -> EntityNode:
    return EntityNode(
        uuid=uuid,
        name=name,
        labels=[label],
        group_id="neo4j",
        created_at=datetime(2026, 8, 20, tzinfo=UTC),
        summary=name,
        attributes=attributes,
    )


class Driver:
    def __init__(self) -> None:
        self.calls = 0

    async def execute_query(self, query: str, **kwargs):
        if "event_analysis_mentioned_anchor_candidates" in query:
            return [
                {"uuid": ANCHOR_UUID},
                {"uuid": "contextual-node"},
            ], None, None
        if "event_analysis_fact_endpoint_candidates" in query:
            return [], None, None
        if "event_analysis_topology_anchor_candidates" in query:
            return [], None, None
        if "event_analysis_fundamental_variable_candidates" in query:
            return [
                {
                    "uuid": "variable-1",
                    "name": "订单能见度",
                    "variable_id": "order_visibility",
                    "variable_group": "DEMAND",
                    "allowed_anchor_types": ["ChainNode", "IndustryChain"],
                    "definition": "未来订单及交付需求的可观察程度。",
                }
            ], None, None
        raise AssertionError(query)


class CandidateRetrieverTest(unittest.IsolatedAsyncioTestCase):
    async def test_excludes_contextual_node_without_stable_business_identity(self) -> None:
        canonical = graph_node(
            ANCHOR_UUID,
            "AI服务器",
            "ChainNode",
            data_object_id="CND-existing",
        )
        contextual = graph_node("contextual-node", "某临时服务器称呼", "ChainNode")
        graphiti = SimpleNamespace(
            driver=Driver(),
            search_=AsyncMock(return_value=SimpleNamespace(nodes=[])),
        )
        with patch.object(
            EntityNode,
            "get_by_uuid",
            new=AsyncMock(side_effect=[canonical, contextual]),
        ):
            result = await GraphitiCandidateRetriever(graphiti).retrieve(
                event_input(), classification()
            )

        self.assertEqual([item.uuid for item in result.anchors], [ANCHOR_UUID])
        self.assertEqual([item.variable_id for item in result.variables], ["order_visibility"])


if __name__ == "__main__":
    unittest.main()
