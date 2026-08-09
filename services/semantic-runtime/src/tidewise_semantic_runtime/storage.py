"""Semantica-backed projection store lifecycle."""

from __future__ import annotations

from typing import Any

from semantica.graph_store.neo4j_store import Neo4jStore
from semantica.vector_store.qdrant_store import QdrantStore

from tidewise_semantic_runtime.config import SemanticRuntimeSettings


class SemanticaProjectionStores:
    """Own the verified Neo4j and Qdrant connections used by Semantic Runtime."""

    def __init__(self, settings: SemanticRuntimeSettings) -> None:
        self._neo4j = Neo4jStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
        self._qdrant = QdrantStore(url=settings.qdrant_url)

    def connect(self) -> None:
        self._neo4j.connect(connection_timeout=5)
        self._qdrant.connect(timeout=5)
        self._verify_qdrant()

    def health(self) -> dict[str, str]:
        with self._neo4j.get_session() as session:
            record = session.run("RETURN 1 AS ok").single()
            if record is None or record["ok"] != 1:
                raise RuntimeError("Neo4j readiness query failed")

        self._verify_qdrant()
        return {"neo4j": "ok", "qdrant": "ok"}

    def close(self) -> None:
        self._neo4j.close()
        client: Any = self._qdrant.client
        if client is not None and hasattr(client, "close"):
            client.close()

    def _verify_qdrant(self) -> None:
        client: Any = self._qdrant.client
        if client is None:
            raise RuntimeError("Qdrant client was not initialized")
        client.get_collections()
