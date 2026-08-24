"""FastAPI composition root for the Tidewise Reasoning API."""

from __future__ import annotations

import asyncio
import inspect
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status

from ingestion.http import RequestBodyLimitMiddleware
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
) -> FastAPI:
    if not service_token.strip():
        raise ValueError("service token must not be blank")
    if start_worker and writer is None:
        raise ValueError("writer is required when the worker is enabled")
    store = EvidenceEpisodeDeliveryStore(state_path)
    module = EvidenceEpisodeModule(store, writer=writer)

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
        try:
            yield
        finally:
            if worker_task is not None:
                stop_event.set()
                await worker_task
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
    app.include_router(create_router(module, service_token=service_token))

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
    return app
