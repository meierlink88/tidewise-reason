"""Typed consumer of the Semantic Runtime v1 health contract."""

from __future__ import annotations

from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict


class ProjectionStoreHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    neo4j: Literal["ok"]
    qdrant: Literal["ok"]


class SemanticRuntimeHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: Literal["semantic-runtime"]
    version: str
    semantica_version: str
    dependencies: ProjectionStoreHealth


class SemanticRuntimeClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def health(self) -> dict[str, object]:
        response = httpx.get(
            f"{self._base_url}/health",
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        health = SemanticRuntimeHealth.model_validate(response.json())
        return health.model_dump()
