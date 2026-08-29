from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EntityNode, EpisodicNode

from analysis.event.graphiti.signals import GraphitiSignalFactProjector
from ingestion.episcode.event.provenance import EVENT_SOURCE_DESCRIPTION
from tests.test_event_analysis_pipeline import (
    ANCHOR_UUID,
    EPISODE_UUID,
    VARIABLE_UUID,
    candidates,
    classification,
    event_input,
    proposal,
)


def node(uuid: str, name: str, label: str, **attributes) -> EntityNode:
    return EntityNode(
        uuid=uuid,
        name=name,
        labels=[label],
        group_id="neo4j",
        created_at=datetime(2026, 8, 20, tzinfo=UTC),
        summary=name,
        attributes=attributes,
    )


class SignalFactProjectorTest(unittest.IsolatedAsyncioTestCase):
    async def test_projects_graphiti_fact_between_existing_variable_and_anchor(self) -> None:
        variable_node = node(
            VARIABLE_UUID,
            "订单能见度",
            "Variable",
            variable_id="order_visibility",
            variable_role="FUNDAMENTAL",
            variable_catalog_source="tidewise-reason/fundamental-variable-catalog",
        )
        anchor_node = node(
            ANCHOR_UUID,
            "AI服务器",
            "ChainNode",
            data_object_id="CHN-existing",
        )
        input_ = event_input()
        episode = EpisodicNode(
            uuid=EPISODE_UUID,
            name="模拟AI服务器订单事件",
            group_id="neo4j",
            labels=[],
            created_at=datetime(2026, 8, 26, tzinfo=UTC),
            source="json",
            source_description=EVENT_SOURCE_DESCRIPTION,
            content=json.dumps(
                {
                    "id": input_.event.id,
                    **input_.event.event.model_dump(mode="json"),
                    "status": "ACTIVE",
                }
            ),
            valid_at=datetime(2026, 8, 26, tzinfo=UTC),
            entity_edges=[],
        )
        driver = SimpleNamespace(execute_query=AsyncMock())

        async def execute_query(query, **kwargs):
            if "signal_fact_existing_event_provenance" in query:
                return [{"uuid": EPISODE_UUID, "content": episode.content}], None, None
            if "signal_fact_link_event_episode" in query:
                self.assertEqual(kwargs["episode_uuid"], EPISODE_UUID)
                self.assertEqual(kwargs["event_id"], input_.event.id)
                return [
                    {
                        "uuid": EPISODE_UUID,
                        "episode_kind": "EVENT",
                        "domain_object_id": input_.event.id,
                        "entity_edges": [kwargs["fact_uuid"]],
                    }
                ], None, None
            raise AssertionError(query)

        driver.execute_query.side_effect = execute_query
        graphiti = SimpleNamespace(driver=driver, add_triplet=AsyncMock())

        async def add_triplet(source, edge, target):
            self.assertIs(source, variable_node)
            self.assertIs(target, anchor_node)
            self.assertIsInstance(edge, EntityEdge)
            return SimpleNamespace(edges=[edge], nodes=[source, target])

        graphiti.add_triplet.side_effect = add_triplet
        variable, anchor = candidates().variables[0], candidates().anchors[0]

        with (
            patch.object(
                EntityNode,
                "get_by_uuid",
                new=AsyncMock(side_effect=[variable_node, anchor_node]),
            ),
            patch.object(
                EpisodicNode, "get_by_uuid", new=AsyncMock(return_value=episode)
            ),
            patch.object(EntityEdge, "save", new=AsyncMock()) as save_edge,
            patch.object(EpisodicNode, "save", new=AsyncMock()) as save_episode,
        ):
            fact_uuid = await GraphitiSignalFactProjector(graphiti).project(
                event_input(), classification(), variable, anchor, proposal()
            )

        self.assertTrue(fact_uuid)
        written = graphiti.add_triplet.await_args.args[1]
        self.assertEqual(written.name, "SIGNAL_ON")
        self.assertEqual(written.fact, proposal().fact)
        self.assertEqual(written.source_node_uuid, VARIABLE_UUID)
        self.assertEqual(written.target_node_uuid, ANCHOR_UUID)
        self.assertEqual(written.episodes, [EPISODE_UUID])
        self.assertEqual(written.valid_at, proposal().valid_at)
        self.assertIsNone(written.invalid_at)
        self.assertEqual(written.reference_time, event_input().reference_time)
        self.assertEqual(written.attributes["direction"], "UP")
        self.assertEqual(written.attributes["expected_end_latest"], "2026-12-31T00:00:00Z")
        self.assertEqual(written.attributes["source_event_ids"], [event_input().event.id])
        self.assertNotIn("analysis_run_id", written.attributes)
        save_edge.assert_awaited_once()
        save_episode.assert_not_awaited()

    async def test_missing_existing_endpoint_fails_before_add_triplet(self) -> None:
        from graphiti_core.errors import NodeNotFoundError

        graphiti = SimpleNamespace(driver=object(), add_triplet=AsyncMock())
        variable, anchor = candidates().variables[0], candidates().anchors[0]
        with patch.object(
            EntityNode,
            "get_by_uuid",
            new=AsyncMock(side_effect=NodeNotFoundError("missing")),
        ), self.assertRaisesRegex(RuntimeError, "existing graph identity"):
            await GraphitiSignalFactProjector(graphiti).project(
                event_input(), classification(), variable, anchor, proposal()
            )
        graphiti.add_triplet.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
