"""FastAPI composition root for the Tidewise Reasoning API."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status

from analysis.event.module import EventAnalysisModule
from analysis.event.worker import run_worker as run_event_analysis_worker
from ingestion.episcode.event.api import create_router as create_event_router
from ingestion.episcode.event.module import EventCandidateModule
from ingestion.episcode.event.store import EventCandidateStore
from ingestion.episcode.event.worker import run_worker as run_event_worker
from ingestion.http import RequestBodyLimitMiddleware

REQUEST_BODY_LIMIT = 2 * 1024 * 1024


def create_app(
    *,
    state_path: Path,
    service_token: str,
    start_worker: bool = True,
    worker_poll_interval_seconds: float = 1.0,
    worker_batch_size: int = 5,
    event_resolver: object | None = None,
    event_analysis_module: EventAnalysisModule | None = None,
    dependency_readiness: Sequence[Callable[[], Awaitable[bool]]] = (),
    shutdown_callbacks: Sequence[Callable[[], Awaitable[None]]] = (),
) -> FastAPI:
    if not service_token.strip():
        raise ValueError("service token must not be blank")
    event_module = EventCandidateModule(EventCandidateStore(state_path), event_resolver)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        stop_event = asyncio.Event()
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
        event_analysis_worker_task = (
            asyncio.create_task(
                run_event_analysis_worker(
                    event_analysis_module,
                    stop_event=stop_event,
                    poll_interval_seconds=worker_poll_interval_seconds,
                    batch_size=worker_batch_size,
                ),
                name="event-analysis-worker",
            )
            if start_worker and event_analysis_module is not None
            else None
        )
        try:
            yield
        finally:
            if event_worker_task is not None:
                stop_event.set()
                await event_worker_task
            if event_analysis_worker_task is not None:
                stop_event.set()
                await event_analysis_worker_task
            for callback in shutdown_callbacks:
                await callback()

    app = FastAPI(title="Tidewise Reasoning API", version="1", lifespan=lifespan)
    app.add_middleware(
        RequestBodyLimitMiddleware,
        max_bytes=REQUEST_BODY_LIMIT,
        path_prefix="/api/reason/v1/event-candidates",
    )
    app.include_router(create_event_router(event_module, service_token=service_token))

    @app.get("/healthz", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", include_in_schema=False)
    async def readiness() -> dict[str, str]:
        for check in dependency_readiness:
            try:
                dependency_ready = await check()
            except Exception:
                dependency_ready = False
            if not dependency_ready:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="not ready",
                )
        return {"status": "ready"}

    app.state.event_candidate_module = event_module
    app.state.event_analysis_module = event_analysis_module
    return app
