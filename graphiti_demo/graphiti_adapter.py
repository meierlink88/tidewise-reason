from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from graphiti_core.nodes import EpisodeType, EpisodicNode

from contracts import (
    GraphFact,
    GraphState,
    ProvenanceLink,
    RetrievalSnapshot,
    SearchFact,
    SeedSummary,
)
from demo_data import (
    AS_OF,
    CHAIN,
    DEMO_GROUP_ID,
    EVIDENCE_EPISODE_UUIDS,
    EVIDENCE_IDS,
    TOPOLOGY_EPISODE_UUID,
)
from models import EDGE_TYPE_MAP, EDGE_TYPES, ENTITY_TYPES
from providers import create_graphiti
from runtime import EvidenceRecord, RuntimeConfig


def extraction_instructions() -> str:
    nodes = ", ".join(node["name"] for node in CHAIN["nodes"])
    return f"""
Use only the declared custom entity and edge types. Keep the exact stable names supplied in JSON.
For an evidence episode, create the Evidence entity with its evidence_id as its name, one concise
ResearchEvent, and one or more VariableSignal entities only when the evidence supports a directional
change. Encode the affected variable, POSITIVE/NEGATIVE/NEUTRAL direction, estimated horizon and
evidence_id in each VariableSignal name because custom properties are intentionally disabled for
this compatibility PoC. Each signal must apply to one of these exact chain nodes: {nodes}. Include
the mechanism, horizon basis and confidence in relation facts. Do not turn an analytical opinion
into an immutable Evidence property. Never invent a source.
""".strip()


class GraphitiEvaluationAdapter:
    """Contain Graphiti/Neo4j operations behind demo-domain return contracts."""

    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config

    async def rebuild(self, evidence_records: list[EvidenceRecord], *, reset_all: bool) -> SeedSummary:
        graphiti = create_graphiti(self._config)
        try:
            await graphiti.driver.health_check()
            if reset_all:
                await graphiti.driver.execute_query("MATCH (n) DETACH DELETE n")
            else:
                await graphiti.driver.execute_query(
                    "MATCH (n {group_id: $group_id}) DETACH DELETE n",
                    group_id=DEMO_GROUP_ID,
                )
            await graphiti.build_indices_and_constraints()

            topology = await self._add_fixed_episode(
                graphiti,
                uuid=TOPOLOGY_EPISODE_UUID,
                name="AI液冷产业链拓扑",
                body=json.dumps(CHAIN, ensure_ascii=False),
                source_description="Tidewise reasoning demo topology",
                reference_time=AS_OF,
                previous_episode_uuid=None,
                instructions=(
                    "Extract the exact IndustryChain, all exact ChainNode names, membership edges "
                    "and the four declared topology relations. " + extraction_instructions()
                ),
            )
            previous_uuid = topology
            episodes: list[str] = []
            for record in evidence_records:
                body = json.dumps(
                    {
                        "evidence_id": record.evidence_id,
                        "summary": record.summary,
                        "semantic": record.semantic.model_dump(mode="json"),
                        "source_name": record.source_name,
                        "source_level": record.source_level,
                        "source_url": str(record.source_url),
                        "published_at": record.published_at.isoformat(),
                        "analysis_anchor": CHAIN["name"],
                        "analysis_as_of": AS_OF.isoformat(),
                        "analysis_horizon": "未来12个月",
                    },
                    ensure_ascii=False,
                )
                episode_uuid = await self._add_fixed_episode(
                    graphiti,
                    uuid=EVIDENCE_EPISODE_UUIDS[record.evidence_id],
                    name=f"Evidence {record.evidence_id}",
                    body=body,
                    source_description=f"Tidewise Atomic Evidence {record.evidence_id}",
                    reference_time=record.published_at.astimezone(UTC),
                    previous_episode_uuid=previous_uuid,
                    instructions=extraction_instructions(),
                )
                episodes.append(episode_uuid)
                previous_uuid = episode_uuid
            state = await self._state(graphiti)
            return SeedSummary(
                topology_episode_uuid=topology,
                evidence_episode_uuids=episodes,
                counts=state.counts,
                graph_fingerprint=state.fingerprint,
            )
        finally:
            await graphiti.close()

    async def retrieve(self, queries: list[str]) -> RetrievalSnapshot:
        graphiti = create_graphiti(self._config)
        try:
            await graphiti.driver.health_check()
            facts: dict[str, SearchFact] = {}
            for query in queries:
                for edge in await graphiti.search(
                    query,
                    group_ids=[DEMO_GROUP_ID],
                    num_results=30,
                ):
                    facts[edge.uuid] = SearchFact(
                        uuid=edge.uuid,
                        name=edge.name,
                        fact=edge.fact,
                        valid_at=edge.valid_at,
                        invalid_at=edge.invalid_at,
                        episodes=edge.episodes,
                    )
            state = await self._state(graphiti)
            return RetrievalSnapshot(
                graph_state=state,
                hybrid_search_facts=sorted(facts.values(), key=lambda item: item.uuid),
            )
        finally:
            await graphiti.close()

    async def state(self) -> GraphState:
        graphiti = create_graphiti(self._config)
        try:
            await graphiti.driver.health_check()
            return await self._state(graphiti)
        finally:
            await graphiti.close()

    async def inspect_labels(self) -> list[dict[str, Any]]:
        graphiti = create_graphiti(self._config)
        try:
            await graphiti.driver.health_check()
            result = await graphiti.driver.execute_query(
                """
                MATCH (n {group_id: $group_id})
                RETURN labels(n) AS labels, count(*) AS count
                ORDER BY labels
                """,
                group_id=DEMO_GROUP_ID,
            )
            return [record.data() for record in result.records]
        finally:
            await graphiti.close()

    async def _add_fixed_episode(
        self,
        graphiti,
        *,
        uuid: str,
        name: str,
        body: str,
        source_description: str,
        reference_time: datetime,
        previous_episode_uuid: str | None,
        instructions: str,
    ) -> str:
        # Graphiti 0.29 accepts `uuid` only for an existing Episode. Registering the deterministic
        # node first is the provider-supported path; add_episode then performs extraction/resolution.
        await EpisodicNode(
            uuid=uuid,
            name=name,
            group_id=DEMO_GROUP_ID,
            labels=[],
            created_at=AS_OF,
            source=EpisodeType.json,
            source_description=source_description,
            content=body,
            valid_at=reference_time,
        ).save(graphiti.driver)
        result = await graphiti.add_episode(
            name=name,
            episode_body=body,
            source_description=source_description,
            reference_time=reference_time,
            source=EpisodeType.json,
            group_id=DEMO_GROUP_ID,
            uuid=uuid,
            entity_types=ENTITY_TYPES,
            edge_types=EDGE_TYPES,
            edge_type_map=EDGE_TYPE_MAP,
            custom_extraction_instructions=instructions,
            previous_episode_uuids=[previous_episode_uuid] if previous_episode_uuid else None,
        )
        return result.episode.uuid

    async def _state(self, graphiti) -> GraphState:
        graph_rows = await graphiti.driver.execute_query(
            """
            MATCH (a:Entity {group_id: $group_id})-[r:RELATES_TO]->
                  (b:Entity {group_id: $group_id})
            RETURN a.uuid AS source_uuid, a.name AS source, labels(a) AS source_labels,
                   r.uuid AS relation_uuid, r.name AS relation, r.fact AS fact,
                   b.uuid AS target_uuid, b.name AS target, labels(b) AS target_labels,
                   r.valid_at AS valid_at, r.invalid_at AS invalid_at,
                   r.episodes AS episodes
            ORDER BY source_uuid, relation_uuid, target_uuid
            """,
            group_id=DEMO_GROUP_ID,
        )
        graph_facts = [GraphFact.model_validate(record.data()) for record in graph_rows.records]
        count_rows = await graphiti.driver.execute_query(
            """
            MATCH (n {group_id: $group_id})
            RETURN count(n) AS nodes,
                   count(CASE WHEN n:ChainNode THEN 1 END) AS chain_nodes,
                   count(CASE WHEN n:Evidence THEN 1 END) AS evidence,
                   count(CASE WHEN n:ResearchEvent THEN 1 END) AS events,
                   count(CASE WHEN n:VariableSignal THEN 1 END) AS signals,
                   count(CASE WHEN n:Episodic THEN 1 END) AS episodes
            """,
            group_id=DEMO_GROUP_ID,
        )
        episode_rows = await graphiti.driver.execute_query(
            """
            MATCH (n:Episodic {group_id: $group_id})
            RETURN n.uuid AS uuid, n.content AS content, n.valid_at AS valid_at
            ORDER BY uuid
            """,
            group_id=DEMO_GROUP_ID,
        )
        episode_snapshots = [record.data() for record in episode_rows.records]
        chain_rows = await graphiti.driver.execute_query(
            "MATCH (n:ChainNode {group_id: $group_id}) RETURN n.name AS name ORDER BY name",
            group_id=DEMO_GROUP_ID,
        )
        index_rows = await graphiti.driver.execute_query(
            "SHOW INDEXES YIELD name, state RETURN name, state"
        )
        provenance_rows = await graphiti.driver.execute_query(
            """
            MATCH (e:Evidence {group_id: $group_id})-[s]->(event:ResearchEvent)
                  -[p]->(signal:VariableSignal)
            WHERE toLower(s.name) = 'supports' AND toLower(p.name) = 'producessignal'
            RETURN e.name AS evidence_id, event.uuid AS event_uuid, event.name AS event_name,
                   signal.uuid AS signal_uuid, signal.name AS signal_name
            ORDER BY evidence_id, event_uuid, signal_uuid
            """,
            group_id=DEMO_GROUP_ID,
        )
        provenance = [ProvenanceLink.model_validate(record.data()) for record in provenance_rows.records]
        fingerprint_input = {
            "episodes": episode_snapshots,
            "facts": [fact.model_dump(mode="json") for fact in graph_facts],
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                fingerprint_input,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        ).hexdigest()
        online_indexes = {
            record["name"] for record in index_rows.records if record["state"] == "ONLINE"
        }
        required_indexes = {
            "entity_uuid",
            "episode_uuid",
            "node_name_and_summary",
            "edge_name_and_fact",
            "episode_content",
        }
        return GraphState(
            fingerprint=fingerprint,
            counts=count_rows.records[0].data(),
            episode_uuids=[item["uuid"] for item in episode_snapshots],
            chain_nodes=[record["name"] for record in chain_rows.records],
            provider_contract_ready=required_indexes.issubset(online_indexes),
            online_index_count=len(online_indexes),
            graph_facts=graph_facts,
            provenance_links=provenance,
        )
