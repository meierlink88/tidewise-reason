"""Semantic Runtime HTTP process."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import Protocol

import semantica
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from tidewise_semantic_runtime import __version__
from tidewise_semantic_runtime.config import SemanticRuntimeSettings
from tidewise_semantic_runtime.storage import SemanticaProjectionStores


class ProjectionStores(Protocol):
    def connect(self) -> None: ...

    def health(self) -> dict[str, str]: ...

    def close(self) -> None: ...


def create_app(storage: ProjectionStores | None = None) -> FastAPI:
    projection_stores = storage or SemanticaProjectionStores(
        SemanticRuntimeSettings.from_env()
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> Iterator[None]:
        projection_stores.connect()
        try:
            yield
        finally:
            projection_stores.close()

    app = FastAPI(
        title="Tidewise Semantic Runtime",
        version=__version__,
        lifespan=lifespan,
    )

    @app.get("/health")
    def health() -> JSONResponse:
        try:
            dependencies = projection_stores.health()
        except Exception as exc:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unavailable",
                    "service": "semantic-runtime",
                    "reason": str(exc)[:240],
                },
            )

        return JSONResponse(
            content={
                "status": "ok",
                "service": "semantic-runtime",
                "version": __version__,
                "semantica_version": semantica.__version__,
                "dependencies": dependencies,
            }
        )

    return app


def main() -> None:
    uvicorn.run(
        "tidewise_semantic_runtime.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8100,
    )
