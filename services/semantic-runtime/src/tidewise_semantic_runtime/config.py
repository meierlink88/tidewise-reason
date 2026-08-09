"""Environment-owned Semantic Runtime configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticRuntimeSettings:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str
    qdrant_url: str

    @classmethod
    def from_env(cls) -> "SemanticRuntimeSettings":
        password = os.environ.get("NEO4J_PASSWORD")
        if not password:
            raise RuntimeError("NEO4J_PASSWORD must be set before starting Semantic Runtime")

        return cls(
            neo4j_uri=os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687"),
            neo4j_user=os.environ.get("NEO4J_USER", "neo4j"),
            neo4j_password=password,
            neo4j_database=os.environ.get("NEO4J_DATABASE", "neo4j"),
            qdrant_url=os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"),
        )
