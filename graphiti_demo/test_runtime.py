import json
import os
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

import httpx

from runtime import DemoError, ErrorCode, EvidenceClient, load_config
from providers import unwrap_schema_properties, validate_structured_response
from pydantic import BaseModel
from analysis_models import AnalysisPayload
from artifact_store import ArtifactStore
from pipeline import context_run_id


VALID_ENV = """\
NEO4J_USER=neo4j
NEO4J_PASSWORD=local-secret
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
GRAPHITI_LLM_API_KEY=llm-secret
GRAPHITI_LLM_BASE_URL=https://llm.example.com
GRAPHITI_LLM_MODEL=example-chat
GRAPHITI_EMBEDDING_API_KEY=embedding-secret
GRAPHITI_EMBEDDING_BASE_URL=https://embedding.example.com
GRAPHITI_EMBEDDING_MODEL=example-embedding
GRAPHITI_EMBEDDING_DIM=1024
TIDEWISE_DATA_BASE_URL=http://data.example.com:9011
TIDEWISE_DATA_SERVICE_TOKEN=data-secret
"""


def valid_item(evidence_id: str) -> dict:
    return {
        "id": evidence_id,
        "summary": "validated fact",
        "semantic": {
            "who": None,
            "what": "happened",
            "when": None,
            "where": None,
            "why": None,
            "how": None,
        },
        "source_name": "Official",
        "source_level": "L1_OFFICIAL",
        "source_url": "https://source.example.com/fact",
        "published_at": "2026-08-17T00:00:00Z",
    }


class RuntimeConfigTest(unittest.TestCase):
    def write_env(self, content: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "runtime.env"
        path.write_text(content, encoding="utf-8")
        os.chmod(path, 0o600)
        return path

    def test_loads_typed_config_and_redacts_secrets(self) -> None:
        config = load_config(self.write_env(VALID_ENV))
        self.assertEqual(config.neo4j_bolt_port, 7687)
        self.assertEqual(config.graphiti_embedding_dim, 1024)
        self.assertNotIn("llm-secret", repr(config))
        self.assertNotIn("data-secret", repr(config))

    def test_rejects_missing_required_field_with_stable_code(self) -> None:
        with self.assertRaises(DemoError) as caught:
            load_config(self.write_env(VALID_ENV.replace("NEO4J_USER=neo4j\n", "")))
        self.assertEqual(caught.exception.code, ErrorCode.CONFIG_INVALID)
        self.assertIn("NEO4J_USER", str(caught.exception))
        self.assertNotIn("llm-secret", str(caught.exception))

    def test_rejects_malformed_and_duplicate_entries(self) -> None:
        for suffix in ("not-an-entry\n", "NEO4J_USER=duplicate\n"):
            with self.subTest(suffix=suffix):
                with self.assertRaises(DemoError) as caught:
                    load_config(self.write_env(VALID_ENV + suffix))
                self.assertEqual(caught.exception.code, ErrorCode.CONFIG_INVALID)

    def test_rejects_runtime_file_with_group_or_world_permissions(self) -> None:
        path = self.write_env(VALID_ENV)
        os.chmod(path, 0o644)
        with self.assertRaises(DemoError) as caught:
            load_config(path)
        self.assertEqual(caught.exception.code, ErrorCode.CONFIG_INVALID)
        self.assertIn("0600", str(caught.exception))


class EvidenceClientTest(unittest.IsolatedAsyncioTestCase):
    def config(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "runtime.env"
        path.write_text(VALID_ENV, encoding="utf-8")
        os.chmod(path, 0o600)
        return load_config(path)

    async def test_loads_requested_records_through_versioned_api(self) -> None:
        wanted = "EVD2a67b87e-0eea-5773-ae9c-0acd7d3524bd"

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.headers["authorization"], "Bearer data-secret")
            body = {
                "request_id": "request-1",
                "result": {"items": [valid_item(wanted)], "total": 1, "page": 1, "page_size": 100},
            }
            return httpx.Response(200, json=body)

        records = await EvidenceClient(
            self.config(),
            transport=httpx.MockTransport(handler),
        ).load(
            [wanted],
            published_from=datetime(2026, 8, 16, tzinfo=UTC),
            published_to=datetime(2026, 8, 21, tzinfo=UTC),
        )
        self.assertEqual([record.evidence_id for record in records], [wanted])
        self.assertIsInstance(records[0].published_at, datetime)

    async def test_rejects_invalid_contract_without_echoing_token(self) -> None:
        wanted = "EVD2a67b87e-0eea-5773-ae9c-0acd7d3524bd"

        def handler(_: httpx.Request) -> httpx.Response:
            item = valid_item(wanted)
            item["published_at"] = "not-a-time"
            body = {
                "request_id": "request-1",
                "result": {"items": [item], "total": 1, "page": 1, "page_size": 100},
            }
            return httpx.Response(200, content=json.dumps(body))

        with self.assertRaises(DemoError) as caught:
            await EvidenceClient(
                self.config(),
                transport=httpx.MockTransport(handler),
            ).load(
                [wanted],
                published_from=datetime(2026, 8, 16, tzinfo=UTC),
                published_to=datetime(2026, 8, 21, tzinfo=UTC),
            )
        self.assertEqual(caught.exception.code, ErrorCode.EVIDENCE_INVALID)
        self.assertNotIn("data-secret", str(caught.exception))

    async def test_accepts_nullable_provider_time_but_rejects_it_for_temporal_demo(self) -> None:
        wanted = "EVD2a67b87e-0eea-5773-ae9c-0acd7d3524bd"

        def handler(_: httpx.Request) -> httpx.Response:
            item = valid_item(wanted)
            item["published_at"] = None
            return httpx.Response(
                200,
                json={
                    "request_id": "request-1",
                    "result": {"items": [item], "total": 1, "page": 1, "page_size": 100},
                },
            )

        with self.assertRaises(DemoError) as caught:
            await EvidenceClient(
                self.config(),
                transport=httpx.MockTransport(handler),
            ).load(
                [wanted],
                published_from=datetime(2026, 8, 16, tzinfo=UTC),
                published_to=datetime(2026, 8, 21, tzinfo=UTC),
            )
        self.assertEqual(caught.exception.code, ErrorCode.EVIDENCE_UNUSABLE)

    async def test_rejects_noncanonical_provider_evidence_identity(self) -> None:
        wanted = "EVD2a67b87e-0eea-5773-ae9c-0acd7d3524bd"

        def handler(_: httpx.Request) -> httpx.Response:
            item = valid_item(wanted)
            item["id"] = "EVD------------------------------------"
            return httpx.Response(
                200,
                json={
                    "request_id": "request-1",
                    "result": {"items": [item], "total": 1, "page": 1, "page_size": 100},
                },
            )

        with self.assertRaises(DemoError) as caught:
            await EvidenceClient(
                self.config(),
                transport=httpx.MockTransport(handler),
            ).load(
                [wanted],
                published_from=datetime(2026, 8, 16, tzinfo=UTC),
                published_to=datetime(2026, 8, 21, tzinfo=UTC),
            )
        self.assertEqual(caught.exception.code, ErrorCode.EVIDENCE_INVALID)

    async def test_retries_safe_get_once_for_provider_5xx(self) -> None:
        wanted = "EVD2a67b87e-0eea-5773-ae9c-0acd7d3524bd"
        calls = 0

        def handler(_: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                return httpx.Response(503)
            return httpx.Response(
                200,
                json={
                    "request_id": "request-2",
                    "result": {
                        "items": [valid_item(wanted)],
                        "total": 1,
                        "page": 1,
                        "page_size": 100,
                    },
                },
            )

        records = await EvidenceClient(
            self.config(),
            transport=httpx.MockTransport(handler),
        ).load(
            [wanted],
            published_from=datetime(2026, 8, 16, tzinfo=UTC),
            published_to=datetime(2026, 8, 21, tzinfo=UTC),
        )
        self.assertEqual(calls, 2)
        self.assertEqual(records[0].evidence_id, wanted)


class ProviderCompatibilityTest(unittest.TestCase):
    def test_unwraps_deepseek_schema_properties_only_when_contract_matches(self) -> None:
        class Response(BaseModel):
            duplicate_facts: list[int]
            contradicted_facts: list[int]

        wrapped = {"properties": {"duplicate_facts": [], "contradicted_facts": []}}
        self.assertEqual(
            unwrap_schema_properties(wrapped, Response),
            {"duplicate_facts": [], "contradicted_facts": []},
        )
        malformed = {"properties": {"duplicate_facts": []}}
        self.assertIs(unwrap_schema_properties(malformed, Response), malformed)
        with self.assertRaises(json.JSONDecodeError):
            validate_structured_response(malformed, Response)

    def test_normalizes_named_analysis_nodes_without_weakening_contract(self) -> None:
        node = {
            "node": "AI芯片",
            "conclusion": "看好",
            "evidence_ids": ["EVD2a67b87e-0eea-5773-ae9c-0acd7d3524bd"],
            "episode_uuids": ["0c9055da-fd08-5bc0-96ea-59db736a915a"],
            "research_event_uuids": ["event-uuid"],
            "variable_signal_uuids": ["signal-uuid"],
            "transmission_path": "event -> signal -> node",
            "counter_evidence": "none",
            "invalidation_conditions": "fact changes",
            "confidence": 0.5,
        }
        payload = AnalysisPayload.model_validate(
            {
                "as_of": "2026-08-21T00:00:00Z",
                "horizon": "12 months",
                "nodes": [node],
                "summary": "result",
            }
        )
        self.assertEqual(list(payload.nodes), ["AI芯片"])


class ArtifactCorrelationTest(unittest.TestCase):
    def test_graph_content_changes_run_identity(self) -> None:
        first = context_run_id({"question": "q", "graph_fingerprint": "one"})
        second = context_run_id({"question": "q", "graph_fingerprint": "two"})
        self.assertNotEqual(first, second)

    def test_new_context_invalidates_previous_result(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        store = ArtifactStore(Path(directory.name))
        store.root.mkdir(parents=True, exist_ok=True)
        store.result_path.write_text("stale", encoding="utf-8")
        store.write_context({"run_id": "new"})
        self.assertFalse(store.result_path.exists())


if __name__ == "__main__":
    unittest.main()
