"""Graphiti adapter for one canonical Evidence Episode write."""

from __future__ import annotations

from graphiti_core import Graphiti
from graphiti_core.utils.bulk_utils import RawEpisode

from ontology import EDGE_TYPE_MAP, EDGE_TYPES, ENTITY_TYPES
from projection.runtime import GRAPHITI_GROUP_ID


EXTRACTION_INSTRUCTIONS = """
The JSON payload is one published, atomic investment-research Evidence record.
Extract only entities and direct factual relationships explicitly supported by the payload.
Use the registered ontology types and prefer matching existing canonical entities by their
standard name, aliases, code, and data_object_id. Never invent data_object_id, codes, entities,
relationships, events, variables, signals, causal effects, forecasts, or Storylines. Preserve the
distinction between what the Evidence states and any background knowledge.
""".strip()


class GraphitiEvidenceEpisodeWriter:
    """Write Evidence through Graphiti while closing the crash-retry idempotency gap."""

    def __init__(self, graphiti: Graphiti):
        self._graphiti = graphiti

    async def _find_existing(self, name: str) -> tuple[str, str] | None:
        records, _, _ = await self._graphiti.driver.execute_query(
            """
            MATCH (episode:Episodic {name: $name, group_id: $group_id})
            RETURN episode.uuid AS uuid, episode.content AS content
            ORDER BY episode.created_at ASC
            LIMIT 2
            """,
            name=name,
            group_id=GRAPHITI_GROUP_ID,
            routing_="r",
        )
        if len(records) > 1:
            raise RuntimeError("multiple Graphiti Episodes share one Evidence identity")
        if not records:
            return None
        record = records[0]
        return str(record["uuid"]), str(record["content"])

    async def write(self, episode: RawEpisode) -> str:
        existing = await self._find_existing(episode.name)
        if existing is not None:
            episode_uuid, content = existing
            if content != episode.content:
                raise RuntimeError("Graphiti Episode identity has conflicting content")
            return episode_uuid

        result = await self._graphiti.add_episode(
            name=episode.name,
            episode_body=episode.content,
            source_description=episode.source_description,
            reference_time=episode.reference_time,
            source=episode.source,
            group_id=GRAPHITI_GROUP_ID,
            entity_types=ENTITY_TYPES,
            edge_types=EDGE_TYPES,
            edge_type_map=EDGE_TYPE_MAP,
            custom_extraction_instructions=EXTRACTION_INSTRUCTIONS,
        )
        return result.episode.uuid

    async def close(self) -> None:
        await self._graphiti.close()

    async def ready(self) -> bool:
        records, _, _ = await self._graphiti.driver.execute_query(
            "RETURN 1 AS ready",
            routing_="r",
        )
        return bool(records and records[0]["ready"] == 1)
