"""FastAPI composition root for the Tidewise Reasoning API."""

from __future__ import annotations

import asyncio
import inspect
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status

from ingestion.http import RequestBodyLimitMiddleware
from ingestion.episcode.event.api import create_router as create_event_router
from ingestion.episcode.event.module import EventCandidateModule
from ingestion.episcode.event.store import EventCandidateStore
from ingestion.episcode.event.worker import run_worker as run_event_worker
from ingestion.episcode.evidence.api import create_router
from ingestion.episcode.evidence.delivery_store import EvidenceEpisodeDeliveryStore
from ingestion.episcode.evidence.module import EpisodeWriter, EvidenceEpisodeModule
from ingestion.episcode.evidence.worker import run_worker


EVIDENCE_REQUEST_BODY_LIMIT = 2 * 1024 * 1024


def create_app(
    *,
    state_path: Path,
    service_token: str,
    start_worker: bool = True,
    writer: EpisodeWriter | None = None,
    worker_poll_interval_seconds: float = 1.0,
    worker_batch_size: int = 5,
    event_resolver: object | None = None,
) -> FastAPI:
    if not service_token.strip():
        raise ValueError("service token must not be blank")
    if start_worker and writer is None:
        raise ValueError("writer is required when the worker is enabled")
    store = EvidenceEpisodeDeliveryStore(state_path)
    module = EvidenceEpisodeModule(store, writer=writer)
    event_module = EventCandidateModule(EventCandidateStore(state_path), event_resolver)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        stop_event = asyncio.Event()
        worker_task = (
            asyncio.create_task(
                run_worker(
                    module,
                    stop_event=stop_event,
                    poll_interval_seconds=worker_poll_interval_seconds,
                    batch_size=worker_batch_size,
                ),
                name="evidence-episode-worker",
            )
            if start_worker
            else None
        )
        event_worker_task = (
            asyncio.create_task(
                run_event_worker(
                    event_module,
                    stop_event=stop_event,
                    poll_interval_seconds=worker_poll_interval_seconds,
                    batch_size=worker_batch_size,
                ),
                name="event-candidate-worker",
            )
            if start_worker and event_resolver is not None
            else None
        )
        try:
            yield
        finally:
            if worker_task is not None:
                stop_event.set()
                await worker_task
            if event_worker_task is not None:
                stop_event.set()
                await event_worker_task
            close = getattr(writer, "close", None)
            if close is not None:
                close_result = close()
                if inspect.isawaitable(close_result):
                    await close_result

    app = FastAPI(title="Tidewise Reasoning API", version="1", lifespan=lifespan)
    app.add_middleware(
        RequestBodyLimitMiddleware,
        max_bytes=EVIDENCE_REQUEST_BODY_LIMIT,
        path_prefix="/api/reason/v1/evidence-episodes",
    )
    app.add_middleware(
        RequestBodyLimitMiddleware,
        max_bytes=EVIDENCE_REQUEST_BODY_LIMIT,
        path_prefix="/api/reason/v1/event-candidates",
    )
    app.include_router(create_router(module, service_token=service_token))
    app.include_router(create_event_router(event_module, service_token=service_token))

    @app.get("/healthz", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", include_in_schema=False)
    async def readiness() -> dict[str, str]:
        ready = getattr(writer, "ready", None)
        if ready is not None and not await ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="not ready",
            )
        return {"status": "ready"}

    app.state.evidence_episode_module = module
    app.state.event_candidate_module = event_module
    return app
