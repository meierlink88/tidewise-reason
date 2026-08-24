"""Reason-owned controlled alternative to Graphiti ``add_episode`` for Evidence."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5

from graphiti_core import Graphiti
from graphiti_core.nodes import EntityNode, EpisodicNode
from graphiti_core.utils.bulk_utils import RawEpisode
from graphiti_core.utils.maintenance.node_operations import extract_nodes

from ingestion.episcode.evidence.graphiti.resolver import (
    CanonicalEntityResolver,
    SemanticResolver,
    resolve_with_graphiti_vectors,
)
from ontology import ENTITY_TYPES
from projection.runtime import GRAPHITI_GROUP_ID


EVIDENCE_EPISODE_KIND = "EVIDENCE"

EXTRACTION_INSTRUCTIONS = """
The JSON payload is one published, atomic investment-research Evidence record.
Extract only explicitly mentioned candidates that fit the registered ontology descriptions.
Region means a reviewed global or cross-country analysis region, never a province, state, city,
county or other national subdivision. Organization means a reviewed international alliance or
multilateral organization, never a company, listed issuer, media business, domestic enterprise or
ordinary government department. Never invent identifiers, entities, relationships, events,
variables, signals, causal effects, forecasts or Storylines. When no registered type fits, do not
extract the mention.
""".strip()

FIND_EXISTING_EPISODE = """
/* controlled_episode_existing */
MATCH (episode:Episodic {name: $name, group_id: $group_id})
RETURN episode.uuid AS uuid, episode.content AS content,
       episode.created_at AS created_at,
       coalesce(episode.tidewise_ingestion_complete, false) AS complete,
       episode.episode_kind AS episode_kind,
       episode.domain_object_id AS domain_object_id
ORDER BY episode.created_at ASC
LIMIT 2
""".strip()

WRITE_CONTROLLED_EPISODE = """
/* controlled_episode_write */
OPTIONAL MATCH (target:Entity {group_id: $group_id})
WHERE target.uuid IN $target_uuids
  AND target.data_object_id IS NOT NULL
  AND any(mention IN $mentions
          WHERE mention.entity_uuid = target.uuid
            AND mention.entity_type IN labels(target))
WITH collect(target) AS targets
WHERE size(targets) = size($target_uuids)
MERGE (episode:Episodic {uuid: $episode_uuid, group_id: $group_id})
SET episode.name = $name,
    episode.source = $source,
    episode.source_description = $source_description,
    episode.content = $content,
    episode.valid_at = $valid_at,
    episode.created_at = $created_at,
    episode.entity_edges = [],
    episode.episode_kind = $episode_kind,
    episode.domain_object_id = $domain_object_id
WITH episode, targets
OPTIONAL MATCH (episode)-[old:MENTIONS]->()
DELETE old
WITH DISTINCT episode, targets
FOREACH (mention IN $mentions |
  FOREACH (target IN [entity IN targets WHERE entity.uuid = mention.entity_uuid] |
    MERGE (episode)-[edge:MENTIONS {uuid: mention.edge_uuid}]->(target)
    SET edge.group_id = $group_id,
        edge.created_at = $created_at
  )
)
SET episode.tidewise_ingestion_complete = true
RETURN episode.uuid AS uuid, size($mentions) AS linked
""".strip()

EntityExtractor = Callable[[Graphiti, EpisodicNode], Awaitable[list[EntityNode]]]


def _as_utc_datetime(value: object) -> datetime:
    native: object
    if isinstance(value, datetime):
        native = value
    else:
        to_native = getattr(value, "to_native", None)
        native = to_native() if callable(to_native) else None
    if not isinstance(native, datetime) or native.tzinfo is None:
        raise RuntimeError("Graphiti Episode created_at is not an explicit datetime")
    return native.astimezone(UTC)


async def _extract_entities(graphiti: Graphiti, episode: EpisodicNode) -> list[EntityNode]:
    nodes, _ = await extract_nodes(
        graphiti.clients,
        episode,
        [],
        ENTITY_TYPES,
        ["Entity"],
        EXTRACTION_INSTRUCTIONS,
    )
    return nodes


def _mention_uuid(episode_uuid: str, entity_uuid: str) -> str:
    return str(
        uuid5(
            NAMESPACE_URL,
            f"urn:tidewise:evidence-mention:{episode_uuid}:{entity_uuid}",
        )
    )


class AuthoritativeEpisodeWriter:
    """Persist one Evidence Episode without allowing extraction to create Entities."""

    def __init__(
        self,
        graphiti: Graphiti,
        *,
        extract_entities: EntityExtractor = _extract_entities,
        resolve_semantically: SemanticResolver = resolve_with_graphiti_vectors,
    ):
        self._graphiti = graphiti
        self._extract_entities = extract_entities
        self._resolver = CanonicalEntityResolver(
            graphiti,
            resolve_semantically=resolve_semantically,
        )

    async def _find_existing(
        self, name: str
    ) -> tuple[str, str, datetime, bool, str | None, str | None] | None:
        records, _, _ = await self._graphiti.driver.execute_query(
            FIND_EXISTING_EPISODE,
            name=name,
            group_id=GRAPHITI_GROUP_ID,
            routing_="r",
        )
        if len(records) > 1:
            raise RuntimeError("multiple Graphiti Episodes share one Evidence identity")
        if not records:
            return None
        record = records[0]
        return (
            str(record["uuid"]),
            str(record["content"]),
            _as_utc_datetime(record["created_at"]),
            bool(record["complete"]),
            str(record["episode_kind"]) if record.get("episode_kind") is not None else None,
            (
                str(record["domain_object_id"])
                if record.get("domain_object_id") is not None
                else None
            ),
        )

    async def write(self, episode: RawEpisode) -> str:
        existing = await self._find_existing(episode.name)
        if existing is not None:
            (
                episode_uuid,
                content,
                created_at,
                complete,
                episode_kind,
                domain_object_id,
            ) = existing
            if content != episode.content:
                raise RuntimeError("Graphiti Episode identity has conflicting content")
            if (
                complete
                and episode_kind == EVIDENCE_EPISODE_KIND
                and domain_object_id == episode.name
            ):
                return episode_uuid
        else:
            episode_uuid = episode.uuid or str(uuid4())
            created_at = datetime.now(UTC)

        graph_episode = EpisodicNode(
            uuid=episode_uuid,
            name=episode.name,
            group_id=GRAPHITI_GROUP_ID,
            labels=[],
            source=episode.source,
            source_description=episode.source_description,
            content=episode.content,
            created_at=created_at,
            valid_at=episode.reference_time,
        )
        candidates = await self._extract_entities(self._graphiti, graph_episode)
        mentions = await self._resolver.resolve(candidates, graph_episode)
        payload = [
            {
                "entity_uuid": mention.entity_uuid,
                "entity_type": mention.entity_type,
                "edge_uuid": _mention_uuid(episode_uuid, mention.entity_uuid),
            }
            for mention in mentions
        ]
        records, _, _ = await self._graphiti.driver.execute_query(
            WRITE_CONTROLLED_EPISODE,
            episode_uuid=episode_uuid,
            group_id=GRAPHITI_GROUP_ID,
            name=episode.name,
            source=episode.source.value,
            source_description=episode.source_description,
            content=episode.content,
            valid_at=episode.reference_time,
            created_at=created_at,
            mentions=payload,
            target_uuids=[mention.entity_uuid for mention in mentions],
            episode_kind=EVIDENCE_EPISODE_KIND,
            domain_object_id=episode.name,
        )
        if len(records) != 1 or int(records[0]["linked"]) != len(payload):
            raise RuntimeError("canonical Evidence mentions changed during Episode write")
        return str(records[0]["uuid"])

    async def close(self) -> None:
        await self._graphiti.close()

    async def ready(self) -> bool:
        records, _, _ = await self._graphiti.driver.execute_query(
            "RETURN 1 AS ready",
            routing_="r",
        )
        return bool(records and records[0]["ready"] == 1)
