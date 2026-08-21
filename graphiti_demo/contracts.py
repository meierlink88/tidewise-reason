from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, field_validator

from runtime import EvidenceRecord


class GraphFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_uuid: str
    source: str
    source_labels: list[str]
    relation_uuid: str
    relation: str
    fact: str
    target_uuid: str
    target: str
    target_labels: list[str]
    valid_at: datetime | None
    invalid_at: datetime | None
    episodes: list[str]

    @field_validator("valid_at", "invalid_at", mode="before")
    @classmethod
    def convert_provider_datetime(cls, value):
        return value.to_native() if hasattr(value, "to_native") else value


class SearchFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    uuid: str
    name: str
    fact: str
    valid_at: datetime | None
    invalid_at: datetime | None
    episodes: list[str]


class ProvenanceLink(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str
    event_uuid: str
    event_name: str
    signal_uuid: str
    signal_name: str


class GraphState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fingerprint: str
    counts: dict[str, int]
    episode_uuids: list[str]
    chain_nodes: list[str]
    provider_contract_ready: bool
    online_index_count: int
    graph_facts: list[GraphFact]
    provenance_links: list[ProvenanceLink]


class RetrievalSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    graph_state: GraphState
    hybrid_search_facts: list[SearchFact]


class SeedSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    topology_episode_uuid: str
    evidence_episode_uuids: list[str]
    counts: dict[str, int]
    graph_fingerprint: str


class EvidenceSource(Protocol):
    async def load(
        self,
        evidence_ids: list[str],
        *,
        published_from: datetime,
        published_to: datetime,
    ) -> list[EvidenceRecord]: ...


class GraphMemory(Protocol):
    async def rebuild(
        self,
        evidence_records: list[EvidenceRecord],
        *,
        reset_all: bool,
    ) -> SeedSummary: ...

    async def retrieve(self, queries: list[str]) -> RetrievalSnapshot: ...

    async def state(self) -> GraphState: ...

    async def inspect_labels(self) -> list[dict]: ...


class AnalysisModel(Protocol):
    async def generate_json(self, *, system: str, context: dict) -> str: ...
