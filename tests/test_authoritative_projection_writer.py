from __future__ import annotations

import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from graphiti_core.edges import EntityEdge

from projection.authoritative_writer import _save_edges_with_creation_time
from projection.runtime import ProjectionError


class AuthoritativeProjectionWriterTest(unittest.IsolatedAsyncioTestCase):
    async def test_missing_relationship_embedding_fails_before_graph_write(self) -> None:
        edge = EntityEdge(
            uuid="11111111-1111-4111-8111-111111111111",
            group_id="neo4j",
            source_node_uuid="22222222-2222-4222-8222-222222222222",
            target_node_uuid="33333333-3333-4333-8333-333333333333",
            created_at=datetime(2026, 8, 24, tzinfo=UTC),
            name="TestRelation",
            fact="test fact",
        )
        driver = SimpleNamespace(execute_query=AsyncMock())

        with self.assertRaisesRegex(ProjectionError, "embedding is missing"):
            await _save_edges_with_creation_time(SimpleNamespace(driver=driver), [edge])

        driver.execute_query.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
