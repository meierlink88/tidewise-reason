"""Reliable handoff from native Event projection to Event Analysis."""

from __future__ import annotations

from datetime import UTC, datetime

from analysis.event.contracts import EventAnalysisInput
from ingestion.episcode.event.contracts import HistoricalEvent
from ingestion.episcode.event.resolver import AnalysisSchedulingUnavailable


class AnalysisSchedulingEventProjector:
    """Decorate native projection with one idempotent durable analysis enqueue."""

    def __init__(self, native_projector, analysis_module) -> None:
        self._native_projector = native_projector
        self._analysis_module = analysis_module

    async def project(self, event: HistoricalEvent) -> str:
        episode_uuid = await self._native_projector.project(event)
        try:
            self._analysis_module.enqueue(
                EventAnalysisInput(
                    event=event,
                    episode_uuid=episode_uuid,
                    reference_time=datetime.now(UTC),
                )
            )
        except Exception as exc:
            raise AnalysisSchedulingUnavailable(
                "native Event projection succeeded but analysis enqueue failed"
            ) from exc
        return episode_uuid

    async def ready(self) -> bool:
        return await self._native_projector.ready()

    async def close(self) -> None:
        await self._native_projector.close()
