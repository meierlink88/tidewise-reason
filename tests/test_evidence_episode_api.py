from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from graphiti_core.utils.bulk_utils import RawEpisode

from ingestion.app import create_app
from tests.test_evidence_episode_converter import EVIDENCE_ID, evidence


class APITestWriter:
    def __init__(self):
        self.closed = False

    async def write(self, episode: RawEpisode) -> str:
        return f"episode-{episode.name}"

    async def close(self) -> None:
        self.closed = True

    async def ready(self) -> bool:
        return True


class EvidenceEpisodeAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        state_path = Path(self.temporary_directory.name) / "reasoning-state.sqlite3"
        self.client = TestClient(
            create_app(
                state_path=state_path,
                service_token="test-reason-token",
                start_worker=False,
            )
        )
        self.headers = {"Authorization": "Bearer test-reason-token"}

    def tearDown(self) -> None:
        self.client.close()
        self.temporary_directory.cleanup()

    def test_agent_os_can_accept_evidence_and_query_its_state(self) -> None:
        response = self.client.post(
            "/api/reason/v1/evidence-episodes",
            headers=self.headers,
            json={"evidences": [evidence().model_dump(mode="json")]},
        )

        self.assertEqual(response.status_code, 202, response.text)
        body = response.json()
        self.assertEqual(body["result"]["accepted_ids"], [EVIDENCE_ID])
        self.assertEqual(body["result"]["duplicate_ids"], [])
        self.assertTrue(body["request_id"])

        status = self.client.get(
            f"/api/reason/v1/evidence-episodes/{EVIDENCE_ID}",
            headers=self.headers,
        )
        self.assertEqual(status.status_code, 200, status.text)
        self.assertEqual(
            status.json(),
            {
                "evidence_id": EVIDENCE_ID,
                "status": "ACCEPTED",
                "attempt_count": 0,
                "graphiti_episode_uuid": None,
                "last_error": None,
            },
        )

    def test_oversized_request_is_rejected_before_validation(self) -> None:
        response = self.client.post(
            "/api/reason/v1/evidence-episodes",
            headers={**self.headers, "Content-Type": "application/json"},
            content=b" " * (2 * 1024 * 1024 + 1),
        )

        self.assertEqual(response.status_code, 413, response.text)

    def test_boolean_coercion_and_invalid_source_provenance_are_rejected(self) -> None:
        coerced = evidence().model_dump(mode="json")
        coerced["is_original"] = 1
        invalid_provenance = evidence().model_dump(mode="json")
        invalid_provenance["is_original"] = False
        invalid_provenance["quoted_source_name"] = None
        numeric_timestamp = evidence().model_dump(mode="json")
        numeric_timestamp["collected_at"] = 0

        coerced_response = self.client.post(
            "/api/reason/v1/evidence-episodes",
            headers=self.headers,
            json={"evidences": [coerced]},
        )
        provenance_response = self.client.post(
            "/api/reason/v1/evidence-episodes",
            headers=self.headers,
            json={"evidences": [invalid_provenance]},
        )
        timestamp_response = self.client.post(
            "/api/reason/v1/evidence-episodes",
            headers=self.headers,
            json={"evidences": [numeric_timestamp]},
        )

        self.assertEqual(coerced_response.status_code, 422, coerced_response.text)
        self.assertEqual(provenance_response.status_code, 422, provenance_response.text)
        self.assertEqual(timestamp_response.status_code, 422, timestamp_response.text)

    def test_same_evidence_is_an_idempotent_duplicate(self) -> None:
        payload = {"evidences": [evidence().model_dump(mode="json")]}
        first = self.client.post(
            "/api/reason/v1/evidence-episodes", headers=self.headers, json=payload
        )
        second = self.client.post(
            "/api/reason/v1/evidence-episodes", headers=self.headers, json=payload
        )

        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 202)
        self.assertEqual(second.json()["result"]["accepted_ids"], [])
        self.assertEqual(second.json()["result"]["duplicate_ids"], [EVIDENCE_ID])

    def test_lifespan_worker_processes_evidence_and_closes_provider(self) -> None:
        writer = APITestWriter()
        with tempfile.TemporaryDirectory() as directory:
            app = create_app(
                state_path=Path(directory) / "state.sqlite3",
                service_token="test-reason-token",
                writer=writer,
                worker_poll_interval_seconds=0.01,
            )
            with TestClient(app) as client:
                health = client.get("/healthz")
                self.assertEqual(health.status_code, 200)
                readiness = client.get("/readyz")
                self.assertEqual(readiness.status_code, 200)
                self.assertEqual(readiness.json(), {"status": "ready"})
                response = client.post(
                    "/api/reason/v1/evidence-episodes",
                    headers=self.headers,
                    json={"evidences": [evidence().model_dump(mode="json")]},
                )
                self.assertEqual(response.status_code, 202, response.text)

                deadline = time.monotonic() + 1
                status = None
                while time.monotonic() < deadline:
                    status = client.get(
                        f"/api/reason/v1/evidence-episodes/{EVIDENCE_ID}",
                        headers=self.headers,
                    ).json()
                    if status["status"] == "SUCCEEDED":
                        break
                    time.sleep(0.01)
                self.assertIsNotNone(status)
                assert status is not None
                self.assertEqual(status["status"], "SUCCEEDED")

        self.assertTrue(writer.closed)

    def test_conflicting_evidence_identity_rolls_back_the_entire_request(self) -> None:
        original = evidence().model_dump(mode="json")
        self.client.post(
            "/api/reason/v1/evidence-episodes",
            headers=self.headers,
            json={"evidences": [original]},
        )
        new_evidence = evidence().model_copy(
            update={"id": "EVD44444444-4444-4444-8444-444444444444"}
        )
        conflicting = {**original, "summary": "相同正式身份下的冲突事实。"}

        response = self.client.post(
            "/api/reason/v1/evidence-episodes",
            headers=self.headers,
            json={
                "evidences": [new_evidence.model_dump(mode="json"), conflicting]
            },
        )

        self.assertEqual(response.status_code, 409, response.text)
        rolled_back = self.client.get(
            f"/api/reason/v1/evidence-episodes/{new_evidence.id}",
            headers=self.headers,
        )
        self.assertEqual(rolled_back.status_code, 404)

    def test_request_requires_service_authentication(self) -> None:
        response = self.client.post(
            "/api/reason/v1/evidence-episodes",
            json={"evidences": [evidence().model_dump(mode="json")]},
        )

        self.assertEqual(response.status_code, 401)

    def test_request_contract_rejects_empty_or_duplicate_batches(self) -> None:
        empty = self.client.post(
            "/api/reason/v1/evidence-episodes",
            headers=self.headers,
            json={"evidences": []},
        )
        duplicate = self.client.post(
            "/api/reason/v1/evidence-episodes",
            headers=self.headers,
            json={
                "evidences": [
                    evidence().model_dump(mode="json"),
                    evidence().model_dump(mode="json"),
                ]
            },
        )

        self.assertEqual(empty.status_code, 422)
        self.assertEqual(duplicate.status_code, 422)


if __name__ == "__main__":
    unittest.main()
