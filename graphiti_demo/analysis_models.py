from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NodeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conclusion: Literal["看好", "风险", "无明显影响"]
    evidence_ids: list[str] = Field(min_length=1)
    episode_uuids: list[str] = Field(min_length=1)
    research_event_uuids: list[str] = Field(min_length=1)
    variable_signal_uuids: list[str] = Field(min_length=1)
    transmission_path: str = Field(min_length=1)
    counter_evidence: str = Field(min_length=1)
    invalidation_conditions: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class AnalysisPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    as_of: datetime
    horizon: Literal["12 months"]
    nodes: dict[str, NodeAnalysis]
    summary: str = Field(min_length=1)

    @field_validator("nodes", mode="before")
    @classmethod
    def normalize_named_node_list(cls, value):
        if not isinstance(value, list):
            return value
        normalized = {}
        for item in value:
            if not isinstance(item, dict) or not isinstance(item.get("node"), str):
                raise ValueError("each list item must contain a node name")
            node = item["node"]
            if node in normalized:
                raise ValueError("node names must be unique")
            normalized[node] = {key: field for key, field in item.items() if key != "node"}
        return normalized

    @field_validator("as_of")
    @classmethod
    def as_of_must_be_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("as_of must be an explicit UTC timestamp")
        return value.astimezone(UTC)


class AnalysisArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    payload: AnalysisPayload
