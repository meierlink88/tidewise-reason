from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from ingestion.runtime import create_runtime_app, load_ingestion_config


def runtime_environment() -> dict[str, str]:
    return {
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "neo4j-password",
        "NEO4J_HTTP_PORT": "7474",
        "NEO4J_BOLT_PORT": "7687",
        "NEO4J_URI": "bolt://neo4j:7687",
        "GRAPHITI_LLM_API_KEY": "llm-key",
        "GRAPHITI_LLM_BASE_URL": "https://llm.example.com",
        "GRAPHITI_LLM_MODEL": "reason-model",
        "GRAPHITI_EMBEDDING_API_KEY": "embedding-key",
        "GRAPHITI_EMBEDDING_BASE_URL": "https://embedding.example.com",
        "GRAPHITI_EMBEDDING_MODEL": "embedding-model",
        "GRAPHITI_EMBEDDING_DIM": "1024",
        "REASON_API_SERVICE_TOKEN": "agent-os-token",
        "REASON_STATE_PATH": "/var/lib/tidewise-reason/state.sqlite3",
        "UNRELATED_PROCESS_VALUE": "ignored",
    }


class IngestionRuntimeConfigTest(unittest.TestCase):
    def test_environment_config_uses_container_neo4j_uri(self) -> None:
        config = load_ingestion_config(runtime_environment())

        self.assertEqual(config.neo4j_uri, "bolt://neo4j:7687")
        self.assertEqual(
            config.state_path,
            Path("/var/lib/tidewise-reason/state.sqlite3"),
        )
        self.assertEqual(config.service_token.get_secret_value(), "agent-os-token")

    def test_service_token_must_not_be_blank(self) -> None:
        environment = runtime_environment()
        environment["REASON_API_SERVICE_TOKEN"] = "   "

        with self.assertRaises(ValueError):
            load_ingestion_config(environment)

    def test_graphiti_cross_encoder_reuses_the_configured_llm_provider(self) -> None:
        config = load_ingestion_config(runtime_environment())

        with patch("projection.runtime.Graphiti") as graphiti_type, patch(
            "ingestion.runtime.create_app"
        ) as app_factory:
            graphiti_type.return_value = object()
            app_factory.return_value = object()
            create_runtime_app(config)

        cross_encoder = graphiti_type.call_args.kwargs["cross_encoder"]
        self.assertEqual(cross_encoder.config.api_key, "llm-key")
        self.assertEqual(cross_encoder.config.base_url, "https://llm.example.com")
        self.assertEqual(cross_encoder.config.model, "reason-model")


if __name__ == "__main__":
    unittest.main()
