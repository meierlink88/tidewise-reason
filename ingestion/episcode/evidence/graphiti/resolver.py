"""Resolve extracted Evidence mentions only to Data-owned canonical graph nodes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from graphiti_core import Graphiti
from graphiti_core.nodes import EntityNode, EpisodicNode
from graphiti_core.utils.maintenance.node_operations import resolve_extracted_nodes

from ontology import ENTITY_TYPES
from projection.runtime import GRAPHITI_GROUP_ID


RESOLVE_CANONICAL_ENTITIES = """
/* controlled_episode_resolve */
UNWIND $candidates AS candidate
MATCH (entity:Entity {group_id: $group_id})
WHERE entity.data_object_id IS NOT NULL
  AND candidate.entity_type IN labels(entity)
  AND (
    entity.name = candidate.name
    OR entity.code = candidate.name
    OR candidate.name IN coalesce(entity.aliases, [])
  )
RETURN candidate.candidate_uuid AS candidate_uuid,
       entity.uuid AS entity_uuid,
       entity.name AS entity_name,
       entity.data_object_id AS data_object_id
ORDER BY candidate_uuid, entity_uuid
""".strip()

VERIFY_SEMANTIC_ENTITIES = """
/* controlled_episode_verify_semantic */
UNWIND $matches AS match
MATCH (entity:Entity {uuid: match.entity_uuid, group_id: $group_id})
WHERE entity.data_object_id IS NOT NULL
  AND match.entity_type IN labels(entity)
RETURN match.candidate_uuid AS candidate_uuid,
       entity.uuid AS entity_uuid,
       entity.name AS entity_name,
       entity.data_object_id AS data_object_id
ORDER BY candidate_uuid, entity_uuid
""".strip()


@dataclass(frozen=True)
class CanonicalMention:
    """One extracted mention resolved to an existing authoritative Entity."""

    candidate_uuid: str
    entity_uuid: str
    entity_name: str
    data_object_id: str
    entity_type: str


SemanticResolver = Callable[
    [Graphiti, EpisodicNode, list[EntityNode]], Awaitable[dict[str, str]]
]


async def resolve_with_graphiti_vectors(
    graphiti: Graphiti,
    episode: EpisodicNode,
    candidates: list[EntityNode],
) -> dict[str, str]:
    """Use Graphiti vector retrieval and LLM dedup without persisting unresolved nodes."""

    if not candidates:
        return {}
    _, uuid_map, _ = await resolve_extracted_nodes(
        graphiti.clients,
        candidates,
        episode,
        [],
        ENTITY_TYPES,
    )
    return {
        candidate.uuid: resolved_uuid
        for candidate in candidates
        if (resolved_uuid := uuid_map.get(candidate.uuid)) is not None
        and resolved_uuid != candidate.uuid
    }


def _candidate_type(node: EntityNode) -> str | None:
    types = ENTITY_TYPES.keys() & node.labels
    if not types:
        return None
    if len(types) > 1:
        raise RuntimeError(f"extracted entity has ambiguous ontology types: {node.name}")
    return next(iter(types))


class CanonicalEntityResolver:
    """Fail closed unless an extracted candidate matches one canonical graph identity."""

    def __init__(
        self,
        graphiti: Graphiti,
        *,
        resolve_semantically: SemanticResolver = resolve_with_graphiti_vectors,
    ):
        self._graphiti = graphiti
        self._driver = graphiti.driver
        self._resolve_semantically = resolve_semantically

    def _mentions_from_records(
        self,
        records: list[Any],
        candidate_types: dict[str, str],
    ) -> list[CanonicalMention]:
        matches_by_candidate: dict[str, list[CanonicalMention]] = {}
        for record in records:
            candidate_uuid = str(record["candidate_uuid"])
            if candidate_uuid not in candidate_types:
                raise RuntimeError("canonical resolver returned an unknown candidate")
            match = CanonicalMention(
                candidate_uuid=candidate_uuid,
                entity_uuid=str(record["entity_uuid"]),
                entity_name=str(record["entity_name"]),
                data_object_id=str(record["data_object_id"]),
                entity_type=candidate_types[candidate_uuid],
            )
            matches_by_candidate.setdefault(candidate_uuid, []).append(match)
        mentions: list[CanonicalMention] = []
        for candidate_uuid, matches in matches_by_candidate.items():
            if len(matches) > 1:
                raise RuntimeError(
                    f"canonical entity resolution is ambiguous for candidate {candidate_uuid}"
                )
            mentions.append(matches[0])
        return mentions

    def _deduplicate_entities(
        self, mentions: list[CanonicalMention]
    ) -> list[CanonicalMention]:
        resolved_by_entity: dict[str, CanonicalMention] = {}
        for match in mentions:
            previous = resolved_by_entity.get(match.entity_uuid)
            if previous is not None and previous.entity_type != match.entity_type:
                raise RuntimeError(
                    f"canonical entity resolved through conflicting types: {match.entity_uuid}"
                )
            resolved_by_entity[match.entity_uuid] = match
        return list(resolved_by_entity.values())

    async def resolve(
        self,
        candidates: list[EntityNode],
        episode: EpisodicNode,
    ) -> list[CanonicalMention]:
        candidate_types: dict[str, str] = {}
        payload: list[dict[str, str]] = []
        for candidate in candidates:
            entity_type = _candidate_type(candidate)
            name = candidate.name.strip()
            if entity_type is None or not name:
                continue
            candidate_types[candidate.uuid] = entity_type
            payload.append(
                {
                    "candidate_uuid": candidate.uuid,
                    "name": name,
                    "entity_type": entity_type,
                }
            )
        if not payload:
            return []

        records, _, _ = await self._driver.execute_query(
            RESOLVE_CANONICAL_ENTITIES,
            candidates=payload,
            group_id=GRAPHITI_GROUP_ID,
            routing_="r",
        )
        exact_mentions = self._mentions_from_records(records, candidate_types)
        exact_candidate_uuids = {mention.candidate_uuid for mention in exact_mentions}
        unresolved = [
            candidate
            for candidate in candidates
            if candidate.uuid in candidate_types
            and candidate.uuid not in exact_candidate_uuids
        ]
        semantic_uuid_map = await self._resolve_semantically(
            self._graphiti,
            episode,
            unresolved,
        )
        unresolved_uuids = {candidate.uuid for candidate in unresolved}
        unexpected_candidates = semantic_uuid_map.keys() - unresolved_uuids
        if unexpected_candidates:
            raise RuntimeError("semantic resolver returned a candidate outside its input")
        semantic_payload = [
            {
                "candidate_uuid": candidate_uuid,
                "entity_uuid": entity_uuid,
                "entity_type": candidate_types[candidate_uuid],
            }
            for candidate_uuid, entity_uuid in semantic_uuid_map.items()
            if candidate_uuid in candidate_types and entity_uuid != candidate_uuid
        ]
        semantic_mentions: list[CanonicalMention] = []
        if semantic_payload:
            semantic_records, _, _ = await self._driver.execute_query(
                VERIFY_SEMANTIC_ENTITIES,
                matches=semantic_payload,
                group_id=GRAPHITI_GROUP_ID,
                routing_="r",
            )
            semantic_mentions = self._mentions_from_records(
                semantic_records,
                candidate_types,
            )
        return self._deduplicate_entities(exact_mentions + semantic_mentions)
