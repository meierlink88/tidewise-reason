from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from ingestion.app import create_app
from ingestion.episcode.event.contracts import EventResolutionOutcome


EVIDENCE_ID = "EVD11111111-1111-4111-8111-111111111111"
EVENT_ID = "EVT22222222-2222-4222-8222-222222222222"


def candidate_payload(summary: str = "The US announced expanded controls.") -> dict:
    return {
        "event": {
            "title": "US expands HBM controls",
            "summary": summary,
            "semantic": {
                "actors": ["US government"],
                "action": "expands export controls",
                "objects": ["HBM"],
                "stage": "ANNOUNCED",
                "jurisdictions": ["China"],
                "effective_at": None,
                "time_precision": "DAY",
            },
            "modality": "FACT",
            "occurred_at": "2026-08-25T00:00:00Z",
            "announced_at": "2026-08-25T00:00:00Z",
        },
        "evidence_ids": [EVIDENCE_ID],
    }


class StubResolver:
    async def resolve(
        self, submission, on_published=None, on_publication_started=None
    ):
        return EventResolutionOutcome(
            decision="NEW_EVENT",
            event_id=EVENT_ID,
            event_created=True,
            evidence_link_result="CREATED",
            graph_projection_status="SUCCEEDED",
            reason_codes=["NO_SAME_OCCURRENCE_FOUND"],
            matched_event_ids=[],
        )


class EventCandidateAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.app = create_app(
            state_path=Path(self.directory.name) / "state.sqlite3",
            service_token="token",
            start_worker=False,
            event_resolver=StubResolver(),
        )
        self.client = TestClient(self.app)
        self.headers = {"Authorization": "Bearer token"}

    def tearDown(self) -> None:
        self.client.close()
        self.directory.cleanup()

    def test_accepts_candidate_and_exposes_auditable_status(self) -> None:
        response = self.client.post(
            "/api/reason/v1/event-candidates", headers=self.headers, json=candidate_payload()
        )
        self.assertEqual(response.status_code, 202, response.text)
        submission_id = response.json()["submission_id"]

        import asyncio

        asyncio.run(self.app.state.event_candidate_module.process_pending(limit=1))
        status = self.client.get(
            f"/api/reason/v1/event-candidates/{submission_id}", headers=self.headers
        )
        self.assertEqual(status.status_code, 200, status.text)
        body = status.json()
        self.assertEqual(body["status"], "SUCCEEDED")
        self.assertEqual(body["decision"], "NEW_EVENT")
        self.assertEqual(body["event_id"], EVENT_ID)

    def test_exact_payload_replay_returns_the_original_submission(self) -> None:
        first = self.client.post(
            "/api/reason/v1/event-candidates", headers=self.headers, json=candidate_payload()
        )
        second = self.client.post(
            "/api/reason/v1/event-candidates", headers=self.headers, json=candidate_payload()
        )
        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 202)
        self.assertEqual(first.json()["submission_id"], second.json()["submission_id"])
        self.assertTrue(second.json()["replayed"])

    def test_evidence_order_does_not_change_request_identity(self) -> None:
        payload = candidate_payload()
        payload["evidence_ids"] = [
            EVIDENCE_ID,
            "EVD33333333-3333-4333-8333-333333333333",
        ]
        reversed_payload = candidate_payload()
        reversed_payload["evidence_ids"] = list(reversed(payload["evidence_ids"]))

        first = self.client.post(
            "/api/reason/v1/event-candidates", headers=self.headers, json=payload
        )
        second = self.client.post(
            "/api/reason/v1/event-candidates", headers=self.headers, json=reversed_payload
        )

        self.assertEqual(first.json()["submission_id"], second.json()["submission_id"])
        self.assertTrue(second.json()["replayed"])

    def test_openapi_declares_bearer_auth_and_error_responses(self) -> None:
        swagger = self.client.get("/docs")
        self.assertEqual(swagger.status_code, 200)
        self.assertIn("swagger-ui", swagger.text)

        contract = self.client.get("/openapi.json").json()
        self.assertNotIn("/api/reason/v1/evidence-episodes", contract["paths"])
        security_schemes = contract["components"]["securitySchemes"]
        self.assertIn("HTTPBearer", security_schemes)
        self.assertEqual(security_schemes["HTTPBearer"]["scheme"], "bearer")

        post = contract["paths"]["/api/reason/v1/event-candidates"]["post"]
        get = contract["paths"]["/api/reason/v1/event-candidates/{submission_id}"]["get"]
        self.assertEqual(post["security"], [{"HTTPBearer": []}])
        self.assertTrue({"401", "413", "422", "500"} <= post["responses"].keys())
        self.assertTrue({"401", "404", "422", "500"} <= get["responses"].keys())

    def test_contract_rejects_agent_owned_workflow_fields(self) -> None:
        payload = candidate_payload()
        payload["candidate_id"] = "agent-owned"
        response = self.client.post(
            "/api/reason/v1/event-candidates", headers=self.headers, json=payload
        )
        self.assertEqual(response.status_code, 422)

    def test_contract_rejects_blank_event_narrative(self) -> None:
        payload = candidate_payload()
        payload["event"]["title"] = "   "
        response = self.client.post(
            "/api/reason/v1/event-candidates", headers=self.headers, json=payload
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
