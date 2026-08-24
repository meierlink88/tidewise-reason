from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from projection.runtime import load_config


class ProjectionRuntimeConfigTest(unittest.TestCase):
    def test_shared_private_environment_accepts_declared_reason_service_keys(self) -> None:
        values = {
            "NEO4J_USER": "neo4j",
            "NEO4J_PASSWORD": "neo4j-password",
            "NEO4J_HTTP_PORT": "7474",
            "NEO4J_BOLT_PORT": "7687",
            "GRAPHITI_LLM_API_KEY": "llm-key",
            "GRAPHITI_LLM_BASE_URL": "https://llm.example.com",
            "GRAPHITI_LLM_MODEL": "reason-model",
            "GRAPHITI_EMBEDDING_API_KEY": "embedding-key",
            "GRAPHITI_EMBEDDING_BASE_URL": "https://embedding.example.com",
            "GRAPHITI_EMBEDDING_MODEL": "embedding-model",
            "GRAPHITI_EMBEDDING_DIM": "1024",
            "TIDEWISE_DATA_BASE_URL": "http://127.0.0.1:9011",
            "TIDEWISE_DATA_SERVICE_TOKEN": "data-token",
            "REASON_API_PORT": "8890",
            "REASON_API_SERVICE_TOKEN": "reason-token",
            "REASON_WORKER_POLL_INTERVAL_SECONDS": "1",
            "REASON_WORKER_BATCH_SIZE": "5",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graphiti.env"
            path.write_text(
                "\n".join(f"{key}={value}" for key, value in values.items()) + "\n",
                encoding="utf-8",
            )
            path.chmod(0o600)

            config = load_config(path)

        self.assertEqual(config.neo4j_uri, "bolt://127.0.0.1:7687")
        self.assertEqual(config.tidewise_data_service_token.get_secret_value(), "data-token")


if __name__ == "__main__":
    unittest.main()
