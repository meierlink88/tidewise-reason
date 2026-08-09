from __future__ import annotations

from fastapi.testclient import TestClient

from tidewise_semantic_runtime.app import create_app


class HealthyProjectionStores:
    def connect(self) -> None:
        pass

    def health(self) -> dict[str, str]:
        return {"neo4j": "ok", "qdrant": "ok"}

    def close(self) -> None:
        pass


class UnavailableProjectionStores(HealthyProjectionStores):
    def health(self) -> dict[str, str]:
        raise RuntimeError("projection stores unavailable")


def test_health_reports_semantica_and_required_projection_stores() -> None:
    with TestClient(create_app(storage=HealthyProjectionStores())) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "semantic-runtime",
        "version": "0.1.0",
        "semantica_version": "0.6.0",
        "dependencies": {"neo4j": "ok", "qdrant": "ok"},
    }


def test_health_fails_closed_when_a_projection_store_is_unavailable() -> None:
    with TestClient(create_app(storage=UnavailableProjectionStores())) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "service": "semantic-runtime",
        "reason": "projection stores unavailable",
    }
