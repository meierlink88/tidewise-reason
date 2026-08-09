from __future__ import annotations

from fastapi.testclient import TestClient

from tidewise_agent_runtime.app import create_app


SEMANTIC_HEALTH = {
    "status": "ok",
    "service": "semantic-runtime",
    "version": "0.1.0",
    "semantica_version": "0.6.0",
    "dependencies": {"neo4j": "ok", "qdrant": "ok"},
}


class HealthySemanticRuntime:
    def health(self) -> dict[str, object]:
        return SEMANTIC_HEALTH


class UnavailableSemanticRuntime:
    def health(self) -> dict[str, object]:
        raise RuntimeError("semantic runtime unavailable")


def test_agent_runtime_exposes_agno_health_and_semantic_readiness(tmp_path) -> None:
    app = create_app(
        db_path=tmp_path / "agent-runtime.db",
        semantic_client=HealthySemanticRuntime(),
    )

    with TestClient(app) as client:
        health_response = client.get("/health")
        ready_response = client.get("/ready")

    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
    assert ready_response.status_code == 200
    assert ready_response.json() == {
        "status": "ok",
        "service": "agent-runtime",
        "semantic_runtime": SEMANTIC_HEALTH,
    }


def test_agent_runtime_readiness_fails_closed_when_semantic_runtime_is_unavailable(
    tmp_path,
) -> None:
    app = create_app(
        db_path=tmp_path / "agent-runtime.db",
        semantic_client=UnavailableSemanticRuntime(),
    )

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "service": "agent-runtime",
        "reason": "semantic runtime unavailable",
    }
