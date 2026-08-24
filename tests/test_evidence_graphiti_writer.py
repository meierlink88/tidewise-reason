from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace

from ingestion.episcode.evidence.converter import to_raw_episode
from ingestion.episcode.evidence.graphiti_writer import (
    GRAPHITI_GROUP_ID,
    GraphitiEvidenceEpisodeWriter,
)
from ontology import EDGE_TYPE_MAP, EDGE_TYPES, ENTITY_TYPES
from tests.test_evidence_episode_converter import EVIDENCE_ID, evidence


class FakeDriver:
    def __init__(self, records: list[dict[str, str]] | None = None):
        self.records = records or []
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def execute_query(self, query: str, **kwargs):
        self.calls.append((query, kwargs))
        return self.records, None, None


class FakeGraphiti:
    def __init__(self, records: list[dict[str, str]] | None = None):
        self.driver = FakeDriver(records)
        self.calls: list[dict[str, object]] = []

    async def add_episode(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(episode=SimpleNamespace(uuid="graphiti-episode-uuid"))


class GraphitiEvidenceEpisodeWriterTest(unittest.TestCase):
    def test_new_evidence_uses_the_registered_ontology(self) -> None:
        graphiti = FakeGraphiti()
        writer = GraphitiEvidenceEpisodeWriter(graphiti)  # type: ignore[arg-type]
        episode = to_raw_episode(evidence())

        episode_uuid = asyncio.run(writer.write(episode))

        self.assertEqual(episode_uuid, "graphiti-episode-uuid")
        self.assertEqual(len(graphiti.calls), 1)
        call = graphiti.calls[0]
        self.assertEqual(call["name"], EVIDENCE_ID)
        self.assertEqual(call["episode_body"], episode.content)
        self.assertEqual(call["group_id"], GRAPHITI_GROUP_ID)
        self.assertIs(call["entity_types"], ENTITY_TYPES)
        self.assertIs(call["edge_types"], EDGE_TYPES)
        self.assertIs(call["edge_type_map"], EDGE_TYPE_MAP)
        self.assertTrue(call["custom_extraction_instructions"])

    def test_existing_identical_episode_is_reused_after_worker_retry(self) -> None:
        episode = to_raw_episode(evidence())
        graphiti = FakeGraphiti(
            [{"uuid": "existing-uuid", "content": episode.content}]
        )
        writer = GraphitiEvidenceEpisodeWriter(graphiti)  # type: ignore[arg-type]

        episode_uuid = asyncio.run(writer.write(episode))

        self.assertEqual(episode_uuid, "existing-uuid")
        self.assertEqual(graphiti.calls, [])

    def test_existing_episode_with_different_content_fails_closed(self) -> None:
        graphiti = FakeGraphiti(
            [{"uuid": "existing-uuid", "content": '{"different":true}'}]
        )
        writer = GraphitiEvidenceEpisodeWriter(graphiti)  # type: ignore[arg-type]

        with self.assertRaises(RuntimeError):
            asyncio.run(writer.write(to_raw_episode(evidence())))


if __name__ == "__main__":
    unittest.main()
