"""Concrete Data, Graphiti, and LLM adapters hidden by Event resolution."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

import httpx
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodicNode
from graphiti_core.prompts.models import Message
from graphiti_core.search.search_filters import SearchFilters
from graphiti_core.utils.maintenance.node_operations import extract_nodes
from pydantic import BaseModel, ConfigDict

from ingestion.episcode.event.contracts import (
    AtomicityAssessment,
    EventCandidateDTO,
    HistoricalEvent,
    PairComparison,
)
from ingestion.episcode.event.resolver import EventHistoryUnavailable, PublicationRejected
from ingestion.episcode.evidence.graphiti.resolver import CanonicalEntityResolver, resolve_with_graphiti_vectors
from ontology import ENTITY_TYPES
from projection.runtime import GRAPHITI_GROUP_ID


EVENTS_PATH = "/api/data/v1/events"
EVENT_EPISODE_KIND = "EVENT"
MAX_DATA_HISTORY = 1_000
MAX_RESOLUTION_CANDIDATES = 30


class DataEventDTO(EventCandidateDTO):
    id: str
    status: Literal["ACTIVE", "DEPRECATED", "ARCHIVED"]

    def historical(self) -> HistoricalEvent:
        return HistoricalEvent(id=self.id, event=EventCandidateDTO.model_validate(self.model_dump(exclude={"id", "status"})))


class DataEventPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    items: list[DataEventDTO]
    total: int
    page: int
    page_size: int


class DataEventPageEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: str
    result: DataEventPage


class DataEventPublicationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event: DataEventDTO
    evidence_link_ids: list[str]
    receipt_id: str
    payload_hash: str
    replayed: bool


class DataEventPublicationEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: str
    result: DataEventPublicationResult


class DataEventClient:
    def __init__(self, base_url: str, service_token: str, *, timeout_seconds: float = 5,
                 transport: httpx.AsyncBaseTransport | None = None):
        self._url = f"{base_url.rstrip('/')}{EVENTS_PATH}"
        self._headers = {"Authorization": f"Bearer {service_token}"}
        self._timeout = timeout_seconds
        self._transport = transport

    async def ready(self) -> bool:
        """Validate connectivity and the authoritative Event page contract."""

        params = {"page": 1, "page_size": 1, "status": "ACTIVE"}
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                headers=self._headers,
                transport=self._transport,
            ) as client:
                response = await client.get(self._url, params=params)
                response.raise_for_status()
                DataEventPageEnvelope.model_validate(response.json())
        except Exception:
            return False
        return True

    async def list_candidates(self, candidate: EventCandidateDTO) -> list[HistoricalEvent]:
        anchor = candidate.occurred_at or candidate.announced_at or candidate.semantic.effective_at
        assert anchor is not None
        lower, upper = anchor - timedelta(days=30), anchor + timedelta(days=30)
        params = {"page": 1, "page_size": 100, "status": "ACTIVE"}
        result: list[HistoricalEvent] = []
        async with httpx.AsyncClient(
            timeout=self._timeout,
            headers=self._headers,
            transport=self._transport,
        ) as client:
            while True:
                response = await client.get(self._url, params=params)
                response.raise_for_status()
                page = DataEventPageEnvelope.model_validate(response.json()).result
                if page.total > MAX_DATA_HISTORY:
                    raise RuntimeError("Event history window exceeds the safe retrieval bound")
                result.extend(item.historical() for item in page.items)
                if page.page * page.page_size >= page.total:
                    break
                params["page"] = page.page + 1
        return [
            event
            for event in result
            if (
                event_anchor := event.event.occurred_at
                or event.event.announced_at
                or event.event.semantic.effective_at
            )
            and lower <= event_anchor <= upper
        ]

    async def publish(self, submission) -> HistoricalEvent:
        payload = {
            "publication_key": f"{submission.submission_id}:create",
            "event": submission.event.model_dump(mode="json"),
            "evidence_ids": sorted(submission.evidence_ids),
        }
        async with httpx.AsyncClient(timeout=self._timeout, headers=self._headers, transport=self._transport) as client:
            response = await client.post(self._url, json=payload)
        if 400 <= response.status_code < 500:
            raise PublicationRejected(
                f"Data rejected Event publication with HTTP {response.status_code}"
            )
        response.raise_for_status()
        envelope = DataEventPublicationEnvelope.model_validate(response.json())
        return envelope.result.event.historical()


ANCHOR_EVENTS = """
/* event_candidate_anchor_history */
UNWIND $mentions AS mention
MATCH (target:Entity {group_id: $group_id})
WHERE target.data_object_id IS NOT NULL
  AND (target.name = mention OR target.code = mention OR mention IN coalesce(target.aliases, []))
WITH collect(DISTINCT target.uuid) AS target_uuids
MATCH (episode:Episodic {group_id: $group_id, episode_kind: 'EVENT'})-[:MENTIONS]->(target:Entity)
WHERE target.uuid IN target_uuids
RETURN DISTINCT episode.name AS name, episode.content AS content
LIMIT $limit
""".strip()


def _historical_from_content(content: str) -> HistoricalEvent | None:
    try:
        return DataEventDTO.model_validate(json.loads(content)).historical()
    except (ValueError, TypeError):
        return None


def _identity_rank(candidate: EventCandidateDTO, historical: HistoricalEvent) -> tuple:
    event = historical.event
    actors = {value.casefold() for value in candidate.semantic.actors}
    objects = {value.casefold() for value in candidate.semantic.objects}
    actor_overlap = len(actors & {value.casefold() for value in event.semantic.actors})
    object_overlap = len(objects & {value.casefold() for value in event.semantic.objects})
    action_match = candidate.semantic.action.casefold() == event.semantic.action.casefold()
    stage_match = candidate.semantic.stage == event.semantic.stage
    anchor = candidate.occurred_at or candidate.announced_at or candidate.semantic.effective_at
    other = event.occurred_at or event.announced_at or event.semantic.effective_at
    distance = abs((anchor - other).total_seconds()) if anchor and other else float("inf")
    return (-int(stage_match), -actor_overlap, -object_overlap, -int(action_match), distance, historical.id)


class CompositeEventHistory:
    def __init__(self, graphiti: Graphiti, data: DataEventClient):
        self._graphiti, self._data = graphiti, data

    async def retrieve(self, candidate: EventCandidateDTO) -> list[HistoricalEvent]:
        query = " ".join([candidate.title, candidate.summary, *candidate.semantic.actors,
                          candidate.semantic.action, *candidate.semantic.objects])
        result: dict[str, HistoricalEvent] = {}
        try:
            episodes = await self._graphiti.driver.search_interface.episode_fulltext_search(
                self._graphiti.driver,
                query,
                SearchFilters(),
                [GRAPHITI_GROUP_ID],
                MAX_RESOLUTION_CANDIDATES,
            )
            for episode in episodes:
                if not episode.name.startswith("EVT"):
                    continue
                if event := _historical_from_content(episode.content):
                    result[event.id] = event
        except Exception:
            pass

        try:
            records, _, _ = await self._graphiti.driver.execute_query(
                ANCHOR_EVENTS,
                mentions=[
                    *candidate.semantic.actors,
                    *candidate.semantic.objects,
                    *candidate.semantic.jurisdictions,
                ],
                group_id=GRAPHITI_GROUP_ID,
                limit=MAX_RESOLUTION_CANDIDATES,
                routing_="r",
            )
            for record in records:
                if str(record["name"]).startswith("EVT") and (
                    event := _historical_from_content(str(record["content"]))
                ):
                    result[event.id] = event
        except Exception:
            pass

        try:
            for event in await self._data.list_candidates(candidate):
                result[event.id] = event
        except Exception as exc:
            raise EventHistoryUnavailable(
                "authoritative Data Event history retrieval failed"
            ) from exc
        return sorted(result.values(), key=lambda item: _identity_rank(candidate, item))[
            :MAX_RESOLUTION_CANDIDATES
        ]


class GraphitiLLMComparator:
    def __init__(self, graphiti: Graphiti):
        self._client = graphiti.clients.llm_client

    async def assess_atomicity(self, candidate: EventCandidateDTO) -> AtomicityAssessment:
        messages = [
            Message(
                role="system",
                content=(
                    "Assess whether one investment Event record describes exactly one independently timed "
                    "real-world action. A compound announcement plus implementation, or unrelated actions "
                    "joined together, is not atomic. Multiple objects are allowed only when they are direct "
                    "objects of the same action at the same stage and time. Return only the structured result."
                ),
            ),
            Message(
                role="user",
                content=json.dumps(candidate.model_dump(mode="json"), ensure_ascii=False, sort_keys=True),
            ),
        ]
        response = await self._client.generate_response(
            messages,
            response_model=AtomicityAssessment,
            group_id=GRAPHITI_GROUP_ID,
            prompt_name="tidewise_event_atomicity_v1",
        )
        return AtomicityAssessment.model_validate(response)

    async def compare(self, candidate: EventCandidateDTO, historical: HistoricalEvent) -> PairComparison:
        messages = [
            Message(role="system", content=(
                "Compare two investment-research Event records. SAME_EVENT only when actor, one real-world action, "
                "direct object, stage, and occurrence time identify the same occurrence. Announcement, effectiveness, "
                "implementation, update, suspension, and termination are distinct. Return only the structured result."
            )),
            Message(role="user", content=json.dumps({"candidate": candidate.model_dump(mode="json"),
                "historical": historical.model_dump(mode="json")}, ensure_ascii=False, sort_keys=True)),
        ]
        response = await self._client.generate_response(messages, response_model=PairComparison, group_id=GRAPHITI_GROUP_ID,
                                                          prompt_name="tidewise_event_identity_v1")
        return PairComparison.model_validate(response)


EXTRACTION_INSTRUCTIONS = """
The JSON is one Data-published investment Event. Extract only explicit candidates fitting registered
ontology descriptions. Only canonical entities already present in the graph may be linked later.
Region means a reviewed global or cross-country region, not a province or city. Organization means
an international alliance or multilateral organization, not a company, issuer, media company or
government department. Never invent entities, links, facts, variables, signals, forecasts, or Storylines.
""".strip()

FIND_EVENT = """
MATCH (episode:Episodic {name: $name, group_id: $group_id})
RETURN episode.uuid AS uuid, episode.content AS content,
       coalesce(episode.tidewise_ingestion_complete, false) AS complete,
       episode.episode_kind AS episode_kind, episode.domain_object_id AS domain_object_id
LIMIT 2
""".strip()

WRITE_EVENT = """
OPTIONAL MATCH (target:Entity {group_id: $group_id})
WHERE target.uuid IN $target_uuids AND target.data_object_id IS NOT NULL
  AND any(mention IN $mentions WHERE mention.entity_uuid = target.uuid AND mention.entity_type IN labels(target))
WITH collect(target) AS targets
WHERE size(targets) = size($target_uuids)
MERGE (episode:Episodic {uuid: $episode_uuid, group_id: $group_id})
SET episode.name=$name, episode.source='json', episode.source_description=$source_description,
    episode.content=$content, episode.valid_at=$valid_at, episode.created_at=$created_at,
    episode.entity_edges=[], episode.episode_kind='EVENT', episode.domain_object_id=$name
WITH episode, targets OPTIONAL MATCH (episode)-[old:MENTIONS]->() DELETE old
WITH DISTINCT episode, targets
FOREACH (mention IN $mentions | FOREACH (target IN [entity IN targets WHERE entity.uuid=mention.entity_uuid] |
  MERGE (episode)-[edge:MENTIONS {uuid: mention.edge_uuid}]->(target)
  SET edge.group_id=$group_id, edge.created_at=$created_at))
SET episode.tidewise_ingestion_complete=true
RETURN episode.uuid AS uuid, size($mentions) AS linked
""".strip()


class ControlledEventProjector:
    def __init__(self, graphiti: Graphiti):
        self._graphiti = graphiti
        self._resolver = CanonicalEntityResolver(graphiti, resolve_semantically=resolve_with_graphiti_vectors)

    async def project(self, historical: HistoricalEvent) -> None:
        content = json.dumps({"id": historical.id, **historical.event.model_dump(mode="json"), "status": "ACTIVE"},
                             ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        records, _, _ = await self._graphiti.driver.execute_query(FIND_EVENT, name=historical.id,
                                                                   group_id=GRAPHITI_GROUP_ID, routing_="r")
        if len(records) > 1:
            raise RuntimeError("multiple Graphiti Episodes share one Event identity")
        if records:
            row = records[0]
            if row["content"] != content:
                raise RuntimeError("Graphiti Event Episode conflicts with Data Event")
            if row["complete"] and row["episode_kind"] == EVENT_EPISODE_KIND and row["domain_object_id"] == historical.id:
                return
        episode_uuid = str(uuid5(NAMESPACE_URL, f"urn:tidewise:event-episode:{historical.id}"))
        created_at = datetime.now(UTC)
        valid_at = historical.event.occurred_at or historical.event.announced_at or historical.event.semantic.effective_at
        assert valid_at is not None
        episode = EpisodicNode(uuid=episode_uuid, name=historical.id, group_id=GRAPHITI_GROUP_ID, labels=[],
            source="json", source_description="Published canonical Event from Data Service", content=content,
            created_at=created_at, valid_at=valid_at)
        candidates, _ = await extract_nodes(self._graphiti.clients, episode, [], ENTITY_TYPES, ["Entity"], EXTRACTION_INSTRUCTIONS)
        mentions = await self._resolver.resolve(candidates, episode)
        payload = [{"entity_uuid": item.entity_uuid, "entity_type": item.entity_type,
                    "edge_uuid": str(uuid5(NAMESPACE_URL, f"urn:tidewise:event-mention:{episode_uuid}:{item.entity_uuid}"))}
                   for item in mentions]
        written, _, _ = await self._graphiti.driver.execute_query(WRITE_EVENT, episode_uuid=episode_uuid,
            group_id=GRAPHITI_GROUP_ID, name=historical.id, source_description=episode.source_description,
            content=content, valid_at=valid_at, created_at=created_at, mentions=payload,
            target_uuids=[item.entity_uuid for item in mentions])
        if len(written) != 1 or int(written[0]["linked"]) != len(payload):
            raise RuntimeError("canonical Event mentions changed during projection")
