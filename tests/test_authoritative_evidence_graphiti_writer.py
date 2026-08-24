from __future__ import annotations

import asyncio
import unittest
from datetime import UTC, datetime

from graphiti_core.nodes import EntityNode
from neo4j.time import DateTime as Neo4jDateTime

from ingestion.episcode.evidence.converter import to_raw_episode
from ingestion.episcode.evidence.graphiti.writer import AuthoritativeEpisodeWriter
from tests.test_evidence_episode_converter import evidence


class FakeDriver:
    def __init__(
        self,
        *,
        canonical_entities: dict[str, dict[str, object]] | None = None,
        existing_records: list[dict[str, object]] | None = None,
    ) -> None:
        default_entities = {
            "concept-ai": {
                "uuid": "concept-ai",
                "name": "人工智能",
                "labels": ["Entity", "Concept"],
                "data_object_id": "CONd34afc45-2eaa-5aa4-b23e-cbb0b2aaaf10",
                "code": None,
                "aliases": ["AI"],
            }
        }
        self.canonical_entities = (
            default_entities if canonical_entities is None else canonical_entities
        )
        self.existing_records = existing_records or []
        self.episodes: dict[str, dict[str, object]] = {}
        self.mentions: dict[str, set[str]] = {}

    async def execute_query(self, query: str, **kwargs):
        if "controlled_episode_existing" in query:
            return self.existing_records, None, None
        if "controlled_episode_resolve" in query:
            records: list[dict[str, object]] = []
            for candidate in kwargs["candidates"]:
                for entity in self.canonical_entities.values():
                    if candidate["entity_type"] not in entity["labels"]:
                        continue
                    identities = {entity["name"], entity["code"], *entity["aliases"]}
                    if candidate["name"] in identities:
                        records.append(
                            {
                                "candidate_uuid": candidate["candidate_uuid"],
                                "entity_uuid": entity["uuid"],
                                "entity_name": entity["name"],
                                "data_object_id": entity["data_object_id"],
                            }
                        )
            return records, None, None
        if "controlled_episode_verify_semantic" in query:
            records = []
            for match in kwargs["matches"]:
                entity = self.canonical_entities.get(match["entity_uuid"])
                if entity is None or entity["data_object_id"] is None:
                    continue
                if match["entity_type"] not in entity["labels"]:
                    continue
                records.append(
                    {
                        "candidate_uuid": match["candidate_uuid"],
                        "entity_uuid": entity["uuid"],
                        "entity_name": entity["name"],
                        "data_object_id": entity["data_object_id"],
                    }
                )
            return records, None, None
        if "controlled_episode_write" in query:
            episode_uuid = kwargs["episode_uuid"]
            self.episodes[episode_uuid] = {
                "name": kwargs["name"],
                "content": kwargs["content"],
                "complete": True,
                "episode_kind": kwargs["episode_kind"],
                "domain_object_id": kwargs["domain_object_id"],
            }
            self.mentions[episode_uuid] = {
                mention["entity_uuid"] for mention in kwargs["mentions"]
            }
            return [{"uuid": episode_uuid, "linked": len(kwargs["mentions"])}], None, None
        raise AssertionError(f"unexpected query: {query}")


class FakeGraphiti:
    def __init__(self, driver: FakeDriver | None = None) -> None:
        self.driver = driver or FakeDriver()


def candidate(name: str, entity_type: str) -> EntityNode:
    return EntityNode(
        name=name,
        group_id="neo4j",
        labels=[entity_type],
        summary="",
    )


async def no_semantic_matches(
    _: object, __: object, ___: list[EntityNode]
) -> dict[str, str]:
    return {}


class AuthoritativeEpisodeWriterTest(unittest.TestCase):
    def test_only_preprojected_authoritative_entities_receive_mentions(self) -> None:
        graphiti = FakeGraphiti()
        extracted = [
            candidate("人工智能", "Concept"),
            candidate("四川", "Region"),
            candidate("东方财富", "Organization"),
            candidate("豪美新材", "Organization"),
        ]

        async def extract(_: object, __: object) -> list[EntityNode]:
            return extracted

        writer = AuthoritativeEpisodeWriter(  # type: ignore[arg-type]
            graphiti,
            extract_entities=extract,
            resolve_semantically=no_semantic_matches,
        )

        episode_uuid = asyncio.run(writer.write(to_raw_episode(evidence())))

        self.assertEqual(set(graphiti.driver.canonical_entities), {"concept-ai"})
        self.assertEqual(graphiti.driver.mentions[episode_uuid], {"concept-ai"})
        self.assertEqual(
            graphiti.driver.episodes[episode_uuid]["episode_kind"],
            "EVIDENCE",
        )
        self.assertEqual(
            graphiti.driver.episodes[episode_uuid]["domain_object_id"],
            evidence().id,
        )

    def test_episode_succeeds_when_no_candidate_is_authoritative(self) -> None:
        graphiti = FakeGraphiti(FakeDriver(canonical_entities={}))

        async def extract(_: object, __: object) -> list[EntityNode]:
            return [candidate("四川", "Region")]

        writer = AuthoritativeEpisodeWriter(  # type: ignore[arg-type]
            graphiti,
            extract_entities=extract,
            resolve_semantically=no_semantic_matches,
        )

        episode_uuid = asyncio.run(writer.write(to_raw_episode(evidence())))

        self.assertIn(episode_uuid, graphiti.driver.episodes)
        self.assertEqual(graphiti.driver.mentions[episode_uuid], set())

    def test_curated_alias_resolves_to_the_existing_canonical_entity(self) -> None:
        graphiti = FakeGraphiti()

        async def extract(_: object, __: object) -> list[EntityNode]:
            return [candidate("AI", "Concept")]

        writer = AuthoritativeEpisodeWriter(  # type: ignore[arg-type]
            graphiti,
            extract_entities=extract,
        )

        episode_uuid = asyncio.run(writer.write(to_raw_episode(evidence())))

        self.assertEqual(graphiti.driver.mentions[episode_uuid], {"concept-ai"})

    def test_semantic_retrieval_can_only_select_an_existing_canonical_entity(self) -> None:
        graphiti = FakeGraphiti()
        extracted = candidate("智能产业技术", "Concept")

        async def extract(_: object, __: object) -> list[EntityNode]:
            return [extracted]

        async def resolve_semantically(
            _: object, __: object, ___: list[EntityNode]
        ) -> dict[str, str]:
            return {extracted.uuid: "concept-ai"}

        writer = AuthoritativeEpisodeWriter(  # type: ignore[arg-type]
            graphiti,
            extract_entities=extract,
            resolve_semantically=resolve_semantically,
        )

        episode_uuid = asyncio.run(writer.write(to_raw_episode(evidence())))

        self.assertEqual(graphiti.driver.mentions[episode_uuid], {"concept-ai"})

    def test_semantic_retrieval_rejects_a_non_authoritative_existing_node(self) -> None:
        graphiti = FakeGraphiti(
            FakeDriver(
                canonical_entities={
                    "synthetic-region": {
                        "uuid": "synthetic-region",
                        "name": "四川",
                        "labels": ["Entity", "Region"],
                        "data_object_id": None,
                        "code": None,
                        "aliases": [],
                    }
                }
            )
        )
        extracted = candidate("川蜀地区", "Region")

        async def extract(_: object, __: object) -> list[EntityNode]:
            return [extracted]

        async def resolve_semantically(
            _: object, __: object, ___: list[EntityNode]
        ) -> dict[str, str]:
            return {extracted.uuid: "synthetic-region"}

        writer = AuthoritativeEpisodeWriter(  # type: ignore[arg-type]
            graphiti,
            extract_entities=extract,
            resolve_semantically=resolve_semantically,
        )

        episode_uuid = asyncio.run(writer.write(to_raw_episode(evidence())))

        self.assertEqual(graphiti.driver.mentions[episode_uuid], set())

    def test_completed_identical_episode_is_reused_without_extraction(self) -> None:
        episode = to_raw_episode(evidence())
        graphiti = FakeGraphiti(
            FakeDriver(
                existing_records=[
                    {
                        "uuid": "existing-episode",
                        "content": episode.content,
                        "created_at": Neo4jDateTime.from_native(
                            datetime(2026, 8, 25, tzinfo=UTC)
                        ),
                        "complete": True,
                        "episode_kind": "EVIDENCE",
                        "domain_object_id": episode.name,
                    }
                ]
            )
        )

        async def fail_extract(_: object, __: object) -> list[EntityNode]:
            raise AssertionError("completed Episode must not be extracted again")

        writer = AuthoritativeEpisodeWriter(  # type: ignore[arg-type]
            graphiti,
            extract_entities=fail_extract,
        )

        self.assertEqual(asyncio.run(writer.write(episode)), "existing-episode")

    def test_incomplete_identical_episode_is_repaired_with_the_same_uuid(self) -> None:
        episode = to_raw_episode(evidence())
        graphiti = FakeGraphiti(
            FakeDriver(
                existing_records=[
                    {
                        "uuid": "incomplete-episode",
                        "content": episode.content,
                        "created_at": Neo4jDateTime.from_native(
                            datetime(2026, 8, 25, tzinfo=UTC)
                        ),
                        "complete": False,
                    }
                ]
            )
        )

        async def extract(_: object, __: object) -> list[EntityNode]:
            return [candidate("人工智能", "Concept")]

        writer = AuthoritativeEpisodeWriter(  # type: ignore[arg-type]
            graphiti,
            extract_entities=extract,
        )

        episode_uuid = asyncio.run(writer.write(episode))

        self.assertEqual(episode_uuid, "incomplete-episode")
        self.assertEqual(graphiti.driver.mentions[episode_uuid], {"concept-ai"})

    def test_existing_episode_with_conflicting_content_fails_closed(self) -> None:
        graphiti = FakeGraphiti(
            FakeDriver(
                existing_records=[
                    {
                        "uuid": "existing-episode",
                        "content": '{"different":true}',
                        "created_at": datetime(2026, 8, 25, tzinfo=UTC),
                        "complete": False,
                    }
                ]
            )
        )
        writer = AuthoritativeEpisodeWriter(graphiti)  # type: ignore[arg-type]

        with self.assertRaises(RuntimeError):
            asyncio.run(writer.write(to_raw_episode(evidence())))

    def test_ambiguous_authoritative_identity_fails_closed(self) -> None:
        graphiti = FakeGraphiti(
            FakeDriver(
                canonical_entities={
                    "concept-ai-1": {
                        "uuid": "concept-ai-1",
                        "name": "人工智能",
                        "labels": ["Entity", "Concept"],
                        "data_object_id": "CON11111111-1111-4111-8111-111111111111",
                        "code": None,
                        "aliases": [],
                    },
                    "concept-ai-2": {
                        "uuid": "concept-ai-2",
                        "name": "人工智能",
                        "labels": ["Entity", "Concept"],
                        "data_object_id": "CON22222222-2222-4222-8222-222222222222",
                        "code": None,
                        "aliases": [],
                    },
                }
            )
        )

        async def extract(_: object, __: object) -> list[EntityNode]:
            return [candidate("人工智能", "Concept")]

        writer = AuthoritativeEpisodeWriter(  # type: ignore[arg-type]
            graphiti,
            extract_entities=extract,
        )

        with self.assertRaises(RuntimeError):
            asyncio.run(writer.write(to_raw_episode(evidence())))


if __name__ == "__main__":
    unittest.main()
