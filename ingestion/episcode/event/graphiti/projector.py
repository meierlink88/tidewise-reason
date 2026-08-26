"""Native Graphiti Episode projection for formal Tidewise Events."""

from __future__ import annotations

import json
from uuid import NAMESPACE_URL, uuid5

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

from ingestion.episcode.event.contracts import HistoricalEvent
from ontology import ENTITY_TYPES
from projection.runtime import GRAPHITI_GROUP_ID


EVENT_EPISODE_KIND = "EVENT"

EXTRACTION_INSTRUCTIONS = """
The JSON is one canonical investment Event published by Tidewise Data. Extract entities and factual
relationships explicitly supported by this Event. Reuse existing entities when they resolve to the
same real-world identity; otherwise Graphiti may create a contextual Entity. Never invent a
data_object_id or promote a contextual Entity to an authoritative Tidewise identity. Region means a
reviewed global or cross-country region, not a province or city. Organization means an international
alliance or multilateral organization, not a company, issuer, media company or government department.
Do not turn forecasts, investment impacts, Variables, Signals, Storylines or inferred causal effects
into Event facts.
""".strip()

FIND_EVENT = """
MATCH (episode:Episodic {name: $name, group_id: $group_id})
RETURN episode.uuid AS uuid, episode.content AS content,
       coalesce(episode.tidewise_ingestion_complete, false) AS complete,
       episode.episode_kind AS episode_kind, episode.domain_object_id AS domain_object_id
LIMIT 2
""".strip()

MARK_EVENT = """
/* graphiti_native_event_metadata */
MATCH (episode:Episodic {uuid: $episode_uuid, group_id: $group_id})
WHERE episode.name = $name AND episode.content = $content
SET episode.episode_kind = 'EVENT',
    episode.domain_object_id = $name,
    episode.tidewise_ingestion_complete = true
RETURN episode.uuid AS uuid
""".strip()


class GraphitiEventProjector:
    """Project a Data-published Event through Graphiti's native Episode pipeline."""

    def __init__(self, graphiti: Graphiti):
        self._graphiti = graphiti

    async def project(self, historical: HistoricalEvent) -> None:
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
        records, _, _ = await self._graphiti.driver.execute_query(
            FIND_EVENT,
            name=historical.id,
            group_id=GRAPHITI_GROUP_ID,
            routing_="r",
        )
        if len(records) > 1:
            raise RuntimeError("multiple Graphiti Episodes share one Event identity")
        if records:
            row = records[0]
            if row["content"] != content:
                raise RuntimeError("Graphiti Event Episode conflicts with Data Event")
            if (
                row["complete"]
                and row["episode_kind"] == EVENT_EPISODE_KIND
                and row["domain_object_id"] == historical.id
            ):
                return

        episode_uuid = str(
            uuid5(NAMESPACE_URL, f"urn:tidewise:event-episode:{historical.id}")
        )
        valid_at = (
            historical.event.occurred_at
            or historical.event.announced_at
            or historical.event.semantic.effective_at
        )
        assert valid_at is not None
        result = await self._graphiti.add_episode(
            name=historical.id,
            episode_body=content,
            source_description="Published canonical Event from Data Service",
            reference_time=valid_at,
            source=EpisodeType.json,
            group_id=GRAPHITI_GROUP_ID,
            uuid=episode_uuid,
            update_communities=False,
            entity_types=ENTITY_TYPES,
            custom_extraction_instructions=EXTRACTION_INSTRUCTIONS,
        )
        if result.episode.uuid != episode_uuid:
            raise RuntimeError("Graphiti returned an unexpected Event Episode identity")

        written, _, _ = await self._graphiti.driver.execute_query(
            MARK_EVENT,
            episode_uuid=episode_uuid,
            group_id=GRAPHITI_GROUP_ID,
            name=historical.id,
            content=content,
        )
        if len(written) != 1 or str(written[0]["uuid"]) != episode_uuid:
            raise RuntimeError("Graphiti Event Episode metadata was not persisted")

    async def ready(self) -> bool:
        records, _, _ = await self._graphiti.driver.execute_query(
            "RETURN 1 AS ready",
            routing_="r",
        )
        return bool(records and records[0]["ready"] == 1)

    async def close(self) -> None:
        await self._graphiti.close()
