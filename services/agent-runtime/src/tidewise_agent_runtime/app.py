"""Agno-based Tidewise Agent Runtime process."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

import uvicorn
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from tidewise_agent_runtime.semantic_client import SemanticRuntimeClient


class SemanticHealthClient(Protocol):
    def health(self) -> dict[str, object]: ...


def create_app(
    db_path: Path,
    semantic_client: SemanticHealthClient,
) -> FastAPI:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    base_app = FastAPI(title="Tidewise Agent Runtime")

    @base_app.get("/ready")
    def ready() -> JSONResponse:
        try:
            semantic_health = semantic_client.health()
        except Exception as exc:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unavailable",
                    "service": "agent-runtime",
                    "reason": str(exc)[:240],
                },
            )

        return JSONResponse(
            content={
                "status": "ok",
                "service": "agent-runtime",
                "semantic_runtime": semantic_health,
            }
        )

    agent_os = AgentOS(
        id="tidewise-agent-os",
        name="Tidewise Agent OS",
        description="Tidewise Agent Runtime",
        db=SqliteDb(id="tidewise-agent-runtime", db_file=str(db_path)),
        base_app=base_app,
        auto_provision_dbs=True,
        telemetry=False,
    )
    return agent_os.get_app()


def create_default_app() -> FastAPI:
    return create_app(
        db_path=Path(os.environ.get("AGENT_RUNTIME_DB_PATH", "/data/agent-runtime.db")),
        semantic_client=SemanticRuntimeClient(
            os.environ.get("SEMANTIC_RUNTIME_URL", "http://127.0.0.1:8100")
        ),
    )


def main() -> None:
    uvicorn.run(
        "tidewise_agent_runtime.app:create_default_app",
        factory=True,
        host="0.0.0.0",
        port=8200,
    )
