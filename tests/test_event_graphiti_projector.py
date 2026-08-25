from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from graphiti_core.nodes import EntityNode

from ingestion.episcode.event.adapters import ControlledEventProjector
from ingestion.episcode.event.contracts import EventCandidateRequest, HistoricalEvent
from tests.test_event_candidate_api import EVENT_ID, candidate_payload


class Driver:
    def __init__(self, existing: list[dict] | None = None) -> None:
        self.writes: list[dict] = []
        self.existing = existing or []
        self.queries: list[str] = []

    async def execute_query(self, query: str, **kwargs):
        self.queries.append(query)
        if "controlled_episode_resolve" in query:
            return [
                {
                    "candidate_uuid": item["candidate_uuid"],
                    "entity_uuid": "concept-ai",
                    "entity_name": "人工智能",
                    "data_object_id": "CON11111111-1111-4111-8111-111111111111",
                }
                for item in kwargs["candidates"]
                if item["entity_type"] == "Concept" and item["name"] == "AI"
            ], None, None
        if "MATCH (episode:Episodic" in query:
            return self.existing, None, None
        if "MERGE (episode:Episodic" in query:
            self.writes.append(kwargs)
            self.existing = [
                {
                    "uuid": kwargs["episode_uuid"],
                    "content": kwargs["content"],
                    "complete": True,
                    "episode_kind": "EVENT",
                    "domain_object_id": kwargs["name"],
                }
            ]
            return [
                {
                    "uuid": kwargs["episode_uuid"],
                    "linked": len(kwargs["mentions"]),
                }
            ], None, None
        raise AssertionError(f"unexpected query: {query}")


class EventGraphitiProjectorTest(unittest.IsolatedAsyncioTestCase):
    async def test_projects_only_the_formal_data_event_as_event_episode(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        historical = HistoricalEvent(id=EVENT_ID, event=request.event)
        driver = Driver()
        graphiti = SimpleNamespace(driver=driver, clients=object())

        with patch(
            "ingestion.episcode.event.adapters.extract_nodes",
            new=AsyncMock(return_value=([], [])),
        ):
            await ControlledEventProjector(graphiti).project(historical)

        self.assertEqual(len(driver.writes), 1)
        write = driver.writes[0]
        self.assertEqual(write["name"], EVENT_ID)
        self.assertEqual(write["target_uuids"], [])
        self.assertIn('\"status\":\"ACTIVE\"', write["content"])
        self.assertNotIn("EVD", write["content"])
        self.assertTrue(all("EntityEdge" not in query for query in driver.queries))

    async def test_links_only_a_preexisting_canonical_entity(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        historical = HistoricalEvent(id=EVENT_ID, event=request.event)
        driver = Driver()
        graphiti = SimpleNamespace(driver=driver, clients=object())
        extracted = EntityNode(
            name="AI",
            group_id="neo4j",
            labels=["Concept"],
            summary="",
        )

        with patch(
            "ingestion.episcode.event.adapters.extract_nodes",
            new=AsyncMock(return_value=([extracted], [])),
        ):
            await ControlledEventProjector(graphiti).project(historical)

        self.assertEqual(driver.writes[0]["target_uuids"], ["concept-ai"])
        self.assertEqual(driver.writes[0]["mentions"][0]["entity_type"], "Concept")

    async def test_replay_with_same_content_is_idempotent(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        historical = HistoricalEvent(id=EVENT_ID, event=request.event)
        driver = Driver()
        graphiti = SimpleNamespace(driver=driver, clients=object())

        with patch(
            "ingestion.episcode.event.adapters.extract_nodes",
            new=AsyncMock(return_value=([], [])),
        ):
            projector = ControlledEventProjector(graphiti)
            await projector.project(historical)
            await projector.project(historical)

        self.assertEqual(len(driver.writes), 1)

    async def test_existing_same_identity_with_conflicting_content_fails_closed(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        historical = HistoricalEvent(id=EVENT_ID, event=request.event)
        driver = Driver(
            existing=[
                {
                    "uuid": "episode-1",
                    "content": "{}",
                    "complete": True,
                    "episode_kind": "EVENT",
                    "domain_object_id": EVENT_ID,
                }
            ]
        )
        graphiti = SimpleNamespace(driver=driver, clients=object())

        with self.assertRaisesRegex(RuntimeError, "conflicts"):
            await ControlledEventProjector(graphiti).project(historical)

        self.assertEqual(driver.writes, [])


if __name__ == "__main__":
    unittest.main()
