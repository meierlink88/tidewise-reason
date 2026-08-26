from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


class IngestionComposeContractTest(unittest.TestCase):
    def test_api_service_is_scoped_pinned_and_persistent(self) -> None:
        compose = (REPO_ROOT / "infra/graphiti/compose.yaml").read_text(encoding="utf-8")
        dockerfile = (REPO_ROOT / "infra/ingestion/Dockerfile").read_text(encoding="utf-8")

        self.assertIn("container_name: reason-graphiti-api", compose)
        self.assertIn("127.0.0.1:8890:8890", compose)
        self.assertNotIn("REASON_API_PORT", compose)
        self.assertIn("graphiti-api-state:/var/lib/tidewise-reason", compose)
        self.assertIn("name: tidewise-reason_graphiti-api-state", compose)
        self.assertIn("bolt://neo4j:7687", compose)
        self.assertIn("REASON_API_SERVICE_TOKEN", compose)
        self.assertIn("/readyz", compose)
        self.assertIn("TIDEWISE_DATA_BASE_URL: 'http://data-service:9011'", compose)
        self.assertNotIn(
            "TIDEWISE_DATA_BASE_URL: '${TIDEWISE_DATA_BASE_URL", compose
        )
        self.assertIn("python:3.12.11-slim@sha256:", dockerfile)
        self.assertIn("--require-hashes", dockerfile)
        self.assertIn("ingestion.main:app", dockerfile)

    def test_openspg_runtime_is_retired_and_graphiti_identity_is_stable(self) -> None:
        graphiti_compose = (REPO_ROOT / "infra/graphiti/compose.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn("name: tidewise-reasoning", graphiti_compose)
        self.assertIn("container_name: reason-graphiti-neo4j", graphiti_compose)
        for retired_path in (
            "compose.yaml",
            "runtime-overrides",
            "infra/uat",
            "scripts/start.sh",
            "scripts/stop.sh",
            "scripts/verify-runtime.sh",
        ):
            self.assertFalse((REPO_ROOT / retired_path).exists(), retired_path)


if __name__ == "__main__":
    unittest.main()
