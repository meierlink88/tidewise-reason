"""Strict external contracts for complete Atomic Evidence delivery."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
    model_validator,
)


class EvidenceSemanticDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    who: str | None = Field(default=None, min_length=1)
    what: str = Field(min_length=1)
    when: str | None = Field(default=None, min_length=1)
    where: str | None = Field(default=None, min_length=1)
    why: str | None = Field(default=None, min_length=1)
    how: str | None = Field(default=None, min_length=1)


class EvidenceCategoryDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(
        min_length=1,
        max_length=39,
        pattern=r"^EVC[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )
    code: str = Field(min_length=1, max_length=50, pattern=r"^[A-Z][A-Z0-9_]*$")
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1)


class EvidenceDTO(BaseModel):
    """Complete Data-published Evidence accepted from Agent OS."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(
        max_length=39,
        pattern=r"^EVD[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )
    raw_evidence_id: str = Field(
        max_length=39,
        pattern=r"^RAW[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    )
    title: str | None = Field(default=None, max_length=500)
    summary: str = Field(min_length=1, max_length=200)
    semantic: EvidenceSemanticDTO
    categories: list[EvidenceCategoryDTO]
    source_id: str = Field(min_length=1, max_length=32)
    source_name: str = Field(min_length=1, max_length=100)
    source_level: Literal["L1_OFFICIAL", "L2_WIRE", "L3_MEDIA", "L4_SOCIAL"]
    source_url: AnyUrl = Field(max_length=2048)
    is_original: StrictBool
    quoted_source_name: str | None = Field(default=None, max_length=100)
    keywords: list[str]
    is_split: StrictBool
    published_at: datetime | None
    collected_at: datetime

    @field_validator("published_at", "collected_at", mode="before")
    @classmethod
    def timestamps_must_be_text_or_datetime(cls, value: object) -> object:
        if value is not None and not isinstance(value, (str, datetime)):
            raise ValueError("Evidence timestamps must be explicit RFC3339 values")
        return value

    @field_validator("published_at", "collected_at")
    @classmethod
    def timestamps_must_be_explicit_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None and (
            value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value)
        ):
            raise ValueError("Evidence timestamps must be explicit UTC")
        return value

    @model_validator(mode="after")
    def collections_must_match_data_contract(self) -> "EvidenceDTO":
        category_ids = [category.id for category in self.categories]
        if len(category_ids) != len(set(category_ids)):
            raise ValueError("Evidence categories must be unique")
        if self.is_original and self.quoted_source_name is not None:
            raise ValueError("original Evidence must not declare a quoted source")
        if not self.is_original and not (self.quoted_source_name or "").strip():
            raise ValueError("reposted Evidence requires a quoted source name")
        return self


class EvidenceEpisodeBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidences: list[EvidenceDTO] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def evidence_ids_must_be_unique(self) -> "EvidenceEpisodeBatchRequest":
        identifiers = [evidence.id for evidence in self.evidences]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Evidence IDs must be unique within one request")
        return self


class EvidenceEpisodeAcceptance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    accepted_ids: list[str]
    duplicate_ids: list[str]


class EvidenceEpisodeAcceptanceEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str
    result: EvidenceEpisodeAcceptance


class EvidenceEpisodeStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str
    status: Literal["ACCEPTED", "PROCESSING", "SUCCEEDED", "FAILED"]
    attempt_count: int = Field(ge=0)
    graphiti_episode_uuid: str | None
    last_error: str | None


class EvidenceEpisodeProcessingResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    succeeded_ids: list[str]
    retry_ids: list[str]
    failed_ids: list[str]
