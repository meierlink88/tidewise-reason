from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import NAMESPACE_URL, uuid5

from graphiti_core.nodes import EpisodeType, EpisodicNode

from ingestion.episcode.event.contracts import EventCandidateRequest, HistoricalEvent
from ingestion.episcode.event.graphiti.projector import (
    EVENT_ENTITY_TYPE_NAMES,
    EVENT_SOURCE_DESCRIPTION,
    EXTRACTION_INSTRUCTIONS,
    PENDING_EVENT_SOURCE_DESCRIPTION,
    GraphitiEventProjector,
    event_entity_types,
)
from tests.test_event_candidate_api import EVENT_ID, candidate_payload


class Driver:
    def __init__(self, existing: list[dict] | None = None) -> None:
        self.existing = existing or []
        self.metadata_writes: list[dict] = []
        self.identity_reads: list[dict] = []

    async def execute_query(self, query: str, **kwargs):
        if "graphiti_event_projection_identity" in query:
            self.identity_reads.append(kwargs)
            return self.existing, None, None
        if "graphiti_native_event_metadata" in query:
            self.metadata_writes.append(kwargs)
            self.existing = [
                {
                    "uuid": kwargs["episode_uuid"],
                    "content": kwargs["content"],
                    "complete": True,
                    "episode_kind": "EVENT",
                    "domain_object_id": kwargs["event_id"],
                    "source_description": EVENT_SOURCE_DESCRIPTION,
                    "name": kwargs["title"],
                }
            ]
            return [{"uuid": kwargs["episode_uuid"]}], None, None
        if query == "RETURN 1 AS ready":
            return [{"ready": 1}], None, None
        raise AssertionError(f"unexpected query: {query}")


def event() -> HistoricalEvent:
    request = EventCandidateRequest.model_validate(candidate_payload())
    return HistoricalEvent(id=EVENT_ID, event=request.event)


class EventGraphitiProjectorTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.episode_save = patch.object(
            EpisodicNode, "save", new=AsyncMock()
        ).start()
        self.addCleanup(patch.stopall)

    async def test_delegates_formal_event_to_native_add_episode(self) -> None:
        driver = Driver()
        graphiti = SimpleNamespace(driver=driver, add_episode=AsyncMock())
        graphiti.add_episode.return_value = SimpleNamespace(
            episode=SimpleNamespace(
                uuid=str(
                    uuid5(NAMESPACE_URL, f"urn:tidewise:event-episode:{EVENT_ID}")
                )
            )
        )

        await GraphitiEventProjector(graphiti).project(event())

        call = graphiti.add_episode.await_args.kwargs
        self.assertEqual(call["name"], event().event.title)
        self.assertEqual(call["source"], EpisodeType.json)
        self.assertEqual(call["group_id"], "neo4j")
        self.assertEqual(tuple(call["entity_types"]), EVENT_ENTITY_TYPE_NAMES)
        for curated_type in ("Variable", "GeopoliticRivalry", "MacroEconomic"):
            self.assertNotIn(curated_type, call["entity_types"])
        self.assertIsNot(event_entity_types(), event_entity_types())
        self.assertFalse(call["update_communities"])
        self.assertEqual(
            call["custom_extraction_instructions"], EXTRACTION_INSTRUCTIONS
        )
        self.assertNotIn("excluded_entity_types", call)
        self.assertNotIn("edge_types", call)
        self.assertNotIn("EVD", call["episode_body"])
        self.assertEqual(
            driver.identity_reads[0]["episode_uuid"],
            str(uuid5(NAMESPACE_URL, f"urn:tidewise:event-episode:{EVENT_ID}")),
        )
        self.assertNotIn("title", driver.identity_reads[0])
        self.episode_save.assert_awaited_once()

    async def test_marks_native_episode_as_formal_event(self) -> None:
        driver = Driver()
        graphiti = SimpleNamespace(driver=driver, add_episode=AsyncMock())
        projector = GraphitiEventProjector(graphiti)

        async def add_episode(**kwargs):
            return SimpleNamespace(episode=SimpleNamespace(uuid=kwargs["uuid"]))

        graphiti.add_episode.side_effect = add_episode
        await projector.project(event())

        self.assertEqual(len(driver.metadata_writes), 1)
        self.assertEqual(driver.metadata_writes[0]["event_id"], EVENT_ID)
        self.assertEqual(driver.metadata_writes[0]["title"], event().event.title)
        self.assertEqual(
            driver.metadata_writes[0]["source_description"], EVENT_SOURCE_DESCRIPTION
        )

    async def test_replay_with_same_content_is_idempotent(self) -> None:
        driver = Driver()
        graphiti = SimpleNamespace(driver=driver, add_episode=AsyncMock())
        projector = GraphitiEventProjector(graphiti)

        async def add_episode(**kwargs):
            return SimpleNamespace(episode=SimpleNamespace(uuid=kwargs["uuid"]))

        graphiti.add_episode.side_effect = add_episode
        await projector.project(event())
        driver.existing[0].pop("complete", None)
        driver.existing[0].pop("episode_kind", None)
        driver.existing[0].pop("domain_object_id", None)
        await projector.project(event())

        self.assertEqual(graphiti.add_episode.await_count, 1)
        self.assertEqual(len(driver.metadata_writes), 1)

    async def test_existing_same_identity_with_conflicting_content_fails_closed(self) -> None:
        driver = Driver(
            existing=[
                {
                    "uuid": str(
                        uuid5(NAMESPACE_URL, f"urn:tidewise:event-episode:{EVENT_ID}")
                    ),
                    "name": EVENT_ID,
                    "content": "{}",
                    "complete": True,
                    "episode_kind": "EVENT",
                    "domain_object_id": EVENT_ID,
                    "source_description": EVENT_SOURCE_DESCRIPTION,
                }
            ]
        )
        graphiti = SimpleNamespace(driver=driver, add_episode=AsyncMock())

        with self.assertRaisesRegex(RuntimeError, "conflicts"):
            await GraphitiEventProjector(graphiti).project(event())

        graphiti.add_episode.assert_not_awaited()

    async def test_pending_native_shell_is_resumed(self) -> None:
        historical = event()
        content = json.dumps(
            {
                "id": historical.id,
                **historical.event.model_dump(mode="json"),
                "status": "ACTIVE",
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        driver = Driver(
            existing=[
                {
                    "uuid": str(
                        uuid5(NAMESPACE_URL, f"urn:tidewise:event-episode:{EVENT_ID}")
                    ),
                    "name": historical.event.title,
                    "content": content,
                    "source_description": PENDING_EVENT_SOURCE_DESCRIPTION,
                }
            ]
        )
        graphiti = SimpleNamespace(driver=driver, add_episode=AsyncMock())
        graphiti.add_episode.return_value = SimpleNamespace(
            episode=SimpleNamespace(uuid=driver.existing[0]["uuid"])
        )

        await GraphitiEventProjector(graphiti).project(historical)

        graphiti.add_episode.assert_awaited_once()
        self.episode_save.assert_not_awaited()

    async def test_legacy_id_name_is_renamed_without_reextracting_episode(self) -> None:
        historical = event()
        content = json.dumps(
            {
                "id": historical.id,
                **historical.event.model_dump(mode="json"),
                "status": "ACTIVE",
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        driver = Driver(
            existing=[
                {
                    "uuid": str(
                        uuid5(NAMESPACE_URL, f"urn:tidewise:event-episode:{EVENT_ID}")
                    ),
                    "name": EVENT_ID,
                    "content": content,
                    "complete": True,
                    "episode_kind": "EVENT",
                    "domain_object_id": EVENT_ID,
                    "source_description": EVENT_SOURCE_DESCRIPTION,
                }
            ]
        )
        graphiti = SimpleNamespace(driver=driver, add_episode=AsyncMock())

        await GraphitiEventProjector(graphiti).project(historical)

        graphiti.add_episode.assert_not_awaited()
        self.assertEqual(driver.metadata_writes[0]["title"], historical.event.title)

    async def test_matching_domain_id_with_non_deterministic_uuid_fails_closed(self) -> None:
        historical = event()
        content = json.dumps(
            {
                "id": historical.id,
                **historical.event.model_dump(mode="json"),
                "status": "ACTIVE",
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        driver = Driver(
            existing=[
                {
                    "uuid": "legacy-random-uuid",
                    "name": historical.event.title,
                    "content": content,
                    "complete": True,
                    "episode_kind": "EVENT",
                    "domain_object_id": EVENT_ID,
                    "source_description": EVENT_SOURCE_DESCRIPTION,
                }
            ]
        )
        graphiti = SimpleNamespace(driver=driver, add_episode=AsyncMock())

        with self.assertRaisesRegex(RuntimeError, "non-deterministic identity"):
            await GraphitiEventProjector(graphiti).project(historical)

        graphiti.add_episode.assert_not_awaited()
        self.assertEqual(driver.metadata_writes, [])

    async def test_readiness_checks_graph_provider(self) -> None:
        graphiti = SimpleNamespace(driver=Driver())
        self.assertTrue(await GraphitiEventProjector(graphiti).ready())


if __name__ == "__main__":
    unittest.main()
