"""Environment composition for the standalone ingestion API runtime."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from fastapi import FastAPI
from pydantic import AnyHttpUrl, Field, SecretStr, field_validator

from analysis.event.adapters import GraphitiEventAnalysisLLM
from analysis.event.graphiti import (
    GraphitiCandidateRetriever,
    GraphitiSignalFactProjector,
)
from analysis.event.module import EventAnalysisModule
from analysis.event.pipeline import EventAnalysisPipeline
from analysis.event.review import ControlledSignalReviewer
from analysis.event.store import EventAnalysisStore
from analysis.event.trigger import AnalysisSchedulingEventProjector
from ingestion.app import create_app
from ingestion.episcode.event.adapters import (
    CompositeEventHistory,
    DataEventClient,
    GraphitiLLMComparator,
)
from ingestion.episcode.event.graphiti import GraphitiEventProjector
from ingestion.episcode.event.resolver import EventResolver
from projection.runtime import GraphitiProviderConfig, create_graphiti


class IngestionRuntimeConfig(GraphitiProviderConfig):
    service_token: SecretStr = Field(alias="REASON_API_SERVICE_TOKEN")
    state_path: Path = Field(alias="REASON_STATE_PATH")
    tidewise_data_base_url: AnyHttpUrl = Field(alias="TIDEWISE_DATA_BASE_URL")
    tidewise_data_service_token: SecretStr = Field(alias="TIDEWISE_DATA_SERVICE_TOKEN")
    worker_poll_interval_seconds: float = Field(
        default=1.0,
        alias="REASON_WORKER_POLL_INTERVAL_SECONDS",
        gt=0,
    )
    worker_batch_size: int = Field(default=5, alias="REASON_WORKER_BATCH_SIZE", ge=1, le=50)

    @field_validator("service_token", "tidewise_data_service_token")
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
    payload: dict[str, str] = {}
    for field in IngestionRuntimeConfig.model_fields.values():
        alias = field.alias
        if alias is not None and alias in values:
            payload[alias] = values[alias]
    return IngestionRuntimeConfig.model_validate(payload)


def create_runtime_app(config: IngestionRuntimeConfig) -> FastAPI:
    graphiti = create_graphiti(config)
    data = DataEventClient(
        str(config.tidewise_data_base_url),
        config.tidewise_data_service_token.get_secret_value(),
    )
    analysis_llm = GraphitiEventAnalysisLLM(graphiti)
    analysis_pipeline = EventAnalysisPipeline(
        analysis_llm,
        GraphitiCandidateRetriever(graphiti),
        analysis_llm,
        ControlledSignalReviewer(),
        GraphitiSignalFactProjector(graphiti),
    )
    analysis_module = EventAnalysisModule(
        EventAnalysisStore(config.state_path), analysis_pipeline
    )
    projector = AnalysisSchedulingEventProjector(
        GraphitiEventProjector(graphiti), analysis_module
    )
    resolver = EventResolver(
        CompositeEventHistory(graphiti, data),
        GraphitiLLMComparator(graphiti),
        data,
        projector,
    )
    return create_app(
        state_path=config.state_path,
        service_token=config.service_token.get_secret_value(),
        event_resolver=resolver,
        event_analysis_module=analysis_module,
        dependency_readiness=(data.ready, projector.ready),
        shutdown_callbacks=(projector.close,),
        worker_poll_interval_seconds=config.worker_poll_interval_seconds,
        worker_batch_size=config.worker_batch_size,
    )
