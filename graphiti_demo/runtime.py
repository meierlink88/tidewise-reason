from __future__ import annotations

import asyncio
import os
import re
import stat
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

import httpx
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = REPO_ROOT / ".runtime" / "graphiti.env"
ENV_KEY = re.compile(r"^[A-Z][A-Z0-9_]*$")


class ErrorCode(StrEnum):
    CONFIG_INVALID = "CONFIG_INVALID"
    EVIDENCE_API_FAILED = "EVIDENCE_API_FAILED"
    EVIDENCE_INVALID = "EVIDENCE_INVALID"
    EVIDENCE_UNUSABLE = "EVIDENCE_UNUSABLE"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    PROVIDER_FAILED = "PROVIDER_FAILED"
    GRAPH_STATE_INVALID = "GRAPH_STATE_INVALID"
    ANALYSIS_INVALID = "ANALYSIS_INVALID"


class DemoError(RuntimeError):
    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code

    def __str__(self) -> str:
        return f"{self.code}: {super().__str__()}"


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    neo4j_user: str = Field(alias="NEO4J_USER", min_length=1)
    neo4j_password: SecretStr = Field(alias="NEO4J_PASSWORD")
    neo4j_bolt_port: int = Field(alias="NEO4J_BOLT_PORT", ge=1, le=65535)
    neo4j_http_port: int = Field(alias="NEO4J_HTTP_PORT", ge=1, le=65535)
    graphiti_llm_api_key: SecretStr = Field(alias="GRAPHITI_LLM_API_KEY")
    graphiti_llm_base_url: AnyHttpUrl = Field(alias="GRAPHITI_LLM_BASE_URL")
    graphiti_llm_model: str = Field(alias="GRAPHITI_LLM_MODEL", min_length=1)
    graphiti_embedding_api_key: SecretStr = Field(alias="GRAPHITI_EMBEDDING_API_KEY")
    graphiti_embedding_base_url: AnyHttpUrl = Field(alias="GRAPHITI_EMBEDDING_BASE_URL")
    graphiti_embedding_model: str = Field(alias="GRAPHITI_EMBEDDING_MODEL", min_length=1)
    graphiti_embedding_dim: int = Field(alias="GRAPHITI_EMBEDDING_DIM", ge=1, le=65536)
    tidewise_data_base_url: AnyHttpUrl = Field(alias="TIDEWISE_DATA_BASE_URL")
    tidewise_data_service_token: SecretStr = Field(alias="TIDEWISE_DATA_SERVICE_TOKEN")

    @field_validator(
        "neo4j_password",
        "graphiti_llm_api_key",
        "graphiti_embedding_api_key",
        "tidewise_data_service_token",
    )
    @classmethod
    def secret_must_not_be_blank(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("secret must not be blank")
        return value

    @property
    def neo4j_uri(self) -> str:
        return f"bolt://127.0.0.1:{self.neo4j_bolt_port}"


class EvidenceSemantic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    who: str | None
    what: str = Field(min_length=1)
    when: str | None
    where: str | None
    why: str | None
    how: str | None


class AdminEvidenceDTO(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(
        pattern=r"^EVD[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    )
    summary: str = Field(min_length=1, max_length=200)
    semantic: EvidenceSemantic
    source_name: str = Field(min_length=1, max_length=100)
    source_level: Literal["L1_OFFICIAL", "L2_WIRE", "L3_MEDIA", "L4_SOCIAL"]
    source_url: AnyHttpUrl
    published_at: datetime | None

    @field_validator("published_at")
    @classmethod
    def published_at_must_be_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("published_at must be an explicit UTC timestamp")
        return value.astimezone(UTC)


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str
    summary: str
    semantic: EvidenceSemantic
    source_name: str
    source_level: Literal["L1_OFFICIAL", "L2_WIRE", "L3_MEDIA", "L4_SOCIAL"]
    source_url: AnyHttpUrl
    published_at: datetime


class EvidencePage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: list[AdminEvidenceDTO]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class EvidenceEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1, max_length=128)
    result: EvidencePage


def _parse_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise DemoError(ErrorCode.CONFIG_INVALID, f"missing runtime environment: {path}")
    if os.name == "posix" and stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise DemoError(ErrorCode.CONFIG_INVALID, "runtime environment must have mode 0600")
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise DemoError(
                ErrorCode.CONFIG_INVALID,
                f"invalid environment entry at line {line_number}",
            )
        key, value = line.split("=", 1)
        if not ENV_KEY.fullmatch(key) or key in values:
            raise DemoError(
                ErrorCode.CONFIG_INVALID,
                f"invalid or duplicate environment key at line {line_number}",
            )
        values[key] = value
    return values


def load_config(path: Path | None = None) -> RuntimeConfig:
    selected = path or DEFAULT_ENV_FILE
    try:
        return RuntimeConfig.model_validate(_parse_env(selected))
    except ValidationError as exc:
        fields = sorted({str(item["loc"][0]) for item in exc.errors()})
        raise DemoError(
            ErrorCode.CONFIG_INVALID,
            f"invalid runtime fields: {', '.join(fields)}",
        ) from None


class EvidenceClient:
    def __init__(
        self,
        config: RuntimeConfig,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = str(config.tidewise_data_base_url).rstrip("/")
        self._token = config.tidewise_data_service_token.get_secret_value()
        self._transport = transport

    async def load(
        self,
        evidence_ids: list[str],
        *,
        published_from: datetime,
        published_to: datetime,
    ) -> list[EvidenceRecord]:
        wanted = set(evidence_ids)
        records: dict[str, EvidenceRecord] = {}
        page = 1
        headers = {"Authorization": f"Bearer {self._token}"}
        async with httpx.AsyncClient(
            timeout=1.4,
            headers=headers,
            transport=self._transport,
        ) as client:
            while True:
                try:
                    response = await self._get_page(
                        client,
                        page=page,
                        published_from=published_from,
                        published_to=published_to,
                    )
                    response.raise_for_status()
                    envelope = EvidenceEnvelope.model_validate(response.json())
                except ValidationError:
                    raise DemoError(
                        ErrorCode.EVIDENCE_INVALID,
                        "Data Evidence API response violates data.v1.listAdminEvidence",
                    ) from None
                except (httpx.HTTPError, ValueError) as exc:
                    detail = exc.__class__.__name__
                    if isinstance(exc, httpx.HTTPStatusError):
                        detail = f"HTTP {exc.response.status_code}"
                    raise DemoError(
                        ErrorCode.EVIDENCE_API_FAILED,
                        f"Data Evidence API request failed ({detail})",
                    ) from None
                for item in envelope.result.items:
                    if item.id not in wanted:
                        continue
                    if item.published_at is None:
                        raise DemoError(
                            ErrorCode.EVIDENCE_UNUSABLE,
                            f"Evidence {item.id} has no published_at for temporal analysis",
                        ) from None
                    record = EvidenceRecord(
                        evidence_id=item.id,
                        summary=item.summary,
                        semantic=item.semantic,
                        source_name=item.source_name,
                        source_level=item.source_level,
                        source_url=item.source_url,
                        published_at=item.published_at,
                    )
                    records[record.evidence_id] = record
                if wanted.issubset(records) or page * envelope.result.page_size >= envelope.result.total:
                    break
                page += 1
        missing = sorted(wanted - records.keys())
        if missing:
            raise DemoError(
                ErrorCode.EVIDENCE_MISSING,
                f"missing Tidewise Evidence IDs: {', '.join(missing)}",
            )
        return [records[evidence_id] for evidence_id in evidence_ids]

    async def _get_page(
        self,
        client: httpx.AsyncClient,
        *,
        page: int,
        published_from: datetime,
        published_to: datetime,
    ) -> httpx.Response:
        params = {
            "page": page,
            "page_size": 100,
            "published_from": _utc_rfc3339(published_from),
            "published_to": _utc_rfc3339(published_to),
        }
        for attempt in range(2):
            try:
                response = await client.get(
                    f"{self._base_url}/api/data/v1/evidences",
                    params=params,
                )
            except httpx.TransportError:
                if attempt == 0:
                    await asyncio.sleep(0.05)
                    continue
                raise
            if attempt == 0 and (response.status_code == 429 or response.status_code >= 500):
                await asyncio.sleep(0.05)
                continue
            return response
        raise AssertionError("unreachable retry state")


def _utc_rfc3339(value: datetime) -> str:
    if value.tzinfo is None:
        raise DemoError(ErrorCode.CONFIG_INVALID, "time boundary must include a timezone")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
