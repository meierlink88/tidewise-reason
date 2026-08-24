"""Environment composition for the standalone ingestion API runtime."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from fastapi import FastAPI
from pydantic import Field, SecretStr, field_validator

from ingestion.app import create_app
from ingestion.episcode.evidence.graphiti_writer import GraphitiEvidenceEpisodeWriter
from projection.runtime import GraphitiProviderConfig, create_graphiti


class IngestionRuntimeConfig(GraphitiProviderConfig):
    service_token: SecretStr = Field(alias="REASON_API_SERVICE_TOKEN")
    state_path: Path = Field(alias="REASON_STATE_PATH")
    worker_poll_interval_seconds: float = Field(
        default=1.0,
        alias="REASON_WORKER_POLL_INTERVAL_SECONDS",
        gt=0,
    )
    worker_batch_size: int = Field(default=5, alias="REASON_WORKER_BATCH_SIZE", ge=1, le=50)

    @field_validator("service_token")
    @classmethod
    def service_token_must_not_be_blank(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("service token must not be blank")
        return value


def load_ingestion_config(
    environment: Mapping[str, str] | None = None,
) -> IngestionRuntimeConfig:
    """Read only declared keys so unrelated process environment cannot enter the contract."""

    values = environment or os.environ
    payload = {
        field.alias: values[field.alias]
        for field in IngestionRuntimeConfig.model_fields.values()
        if field.alias in values
    }
    return IngestionRuntimeConfig.model_validate(payload)


def create_runtime_app(config: IngestionRuntimeConfig) -> FastAPI:
    graphiti = create_graphiti(config)
    return create_app(
        state_path=config.state_path,
        service_token=config.service_token.get_secret_value(),
        writer=GraphitiEvidenceEpisodeWriter(graphiti),
        worker_poll_interval_seconds=config.worker_poll_interval_seconds,
        worker_batch_size=config.worker_batch_size,
    )
