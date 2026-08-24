from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


class IngestionComposeContractTest(unittest.TestCase):
    def test_api_service_is_scoped_pinned_and_persistent(self) -> None:
        compose = (REPO_ROOT / "infra/graphiti/compose.yaml").read_text(encoding="utf-8")
        dockerfile = (REPO_ROOT / "infra/ingestion/Dockerfile").read_text(encoding="utf-8")

        self.assertIn("container_name: reason-graphiti-api", compose)
        self.assertIn("127.0.0.1:${REASON_API_PORT:-8890}:8890", compose)
        self.assertIn("graphiti-api-state:/var/lib/tidewise-reason", compose)
        self.assertIn("name: tidewise-reason_graphiti-api-state", compose)
        self.assertIn("bolt://neo4j:7687", compose)
        self.assertIn("REASON_API_SERVICE_TOKEN", compose)
        self.assertIn("/readyz", compose)
        self.assertIn("python:3.12.11-slim@sha256:", dockerfile)
        self.assertIn("--require-hashes", dockerfile)
        self.assertIn("ingestion.main:app", dockerfile)

    def test_legacy_and_graphiti_service_identities_are_unchanged(self) -> None:
        graphiti_compose = (REPO_ROOT / "infra/graphiti/compose.yaml").read_text(
            encoding="utf-8"
        )
        legacy_compose = (REPO_ROOT / "compose.yaml").read_text(encoding="utf-8")

        self.assertIn("name: tidewise-reasoning", graphiti_compose)
        self.assertIn("container_name: reason-graphiti-neo4j", graphiti_compose)
        self.assertIn("name: tidewise-app", legacy_compose)
        self.assertIn("container_name: reason-server", legacy_compose)


if __name__ == "__main__":
    unittest.main()
