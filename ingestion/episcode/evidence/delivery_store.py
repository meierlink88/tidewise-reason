"""Reason-owned durable SQLite state for Evidence Episode delivery."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterable

from ingestion.episcode.evidence.contracts import EvidenceDTO, EvidenceEpisodeStatus
from ingestion.episcode.evidence.converter import canonical_evidence_json


class EvidencePayloadConflict(RuntimeError):
    """A formal Evidence ID was reused with different immutable content."""


@dataclass(frozen=True)
class Acceptance:
    accepted_ids: tuple[str, ...]
    duplicate_ids: tuple[str, ...]


@dataclass(frozen=True)
class ClaimedDelivery:
    evidence: EvidenceDTO
    attempt_count: int


class EvidenceEpisodeDeliveryStore:
    """Persist accepted payloads and processing state behind one transactional interface."""

    def __init__(self, path: Path):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_episode_deliveries (
                    evidence_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (
                        status IN ('ACCEPTED', 'PROCESSING', 'SUCCEEDED', 'FAILED')
                    ),
                    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
                    graphiti_episode_uuid TEXT,
                    last_error TEXT,
                    received_at TEXT NOT NULL,
                    reference_time TEXT NOT NULL,
                    processing_started_at TEXT,
                    completed_at TEXT,
                    next_attempt_at TEXT,
                    lease_until TEXT
                )
                """
            )

    def accept(self, evidences: Iterable[EvidenceDTO]) -> Acceptance:
        accepted: list[str] = []
        duplicates: list[str] = []
        received_at = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            for evidence in evidences:
                payload = canonical_evidence_json(evidence)
                digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
                existing = connection.execute(
                    "SELECT payload_sha256 FROM evidence_episode_deliveries WHERE evidence_id = ?",
                    (evidence.id,),
                ).fetchone()
                if existing is not None:
                    if existing["payload_sha256"] != digest:
                        raise EvidencePayloadConflict(evidence.id)
                    duplicates.append(evidence.id)
                    continue
                connection.execute(
                    """
                    INSERT INTO evidence_episode_deliveries (
                        evidence_id, payload_json, payload_sha256, status,
                        received_at, reference_time
                    ) VALUES (?, ?, ?, 'ACCEPTED', ?, ?)
                    """,
                    (
                        evidence.id,
                        payload,
                        digest,
                        received_at,
                        (evidence.published_at or evidence.collected_at).isoformat(),
                    ),
                )
                accepted.append(evidence.id)
        return Acceptance(accepted_ids=tuple(accepted), duplicate_ids=tuple(duplicates))

    def get_status(self, evidence_id: str) -> EvidenceEpisodeStatus | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT evidence_id, status, attempt_count, graphiti_episode_uuid, last_error
                FROM evidence_episode_deliveries WHERE evidence_id = ?
                """,
                (evidence_id,),
            ).fetchone()
        if row is None:
            return None
        return EvidenceEpisodeStatus.model_validate(dict(row))

    def claim_next(self, *, lease_seconds: int) -> ClaimedDelivery | None:
        now = datetime.now(UTC)
        now_text = now.isoformat()
        lease_until = (now + timedelta(seconds=lease_seconds)).isoformat()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT evidence_id, payload_json, status, next_attempt_at, lease_until
                FROM evidence_episode_deliveries
                WHERE status IN ('ACCEPTED', 'PROCESSING')
                ORDER BY reference_time, evidence_id
                LIMIT 1
                """,
            ).fetchone()
            if row is None:
                return None
            if row["status"] == "ACCEPTED" and (
                row["next_attempt_at"] is not None
                and datetime.fromisoformat(row["next_attempt_at"]) > now
            ):
                return None
            if row["status"] == "PROCESSING" and (
                row["lease_until"] is None
                or datetime.fromisoformat(row["lease_until"]) > now
            ):
                return None
            connection.execute(
                """
                UPDATE evidence_episode_deliveries
                SET status = 'PROCESSING',
                    attempt_count = attempt_count + 1,
                    processing_started_at = ?,
                    lease_until = ?,
                    next_attempt_at = NULL
                WHERE evidence_id = ?
                """,
                (now_text, lease_until, row["evidence_id"]),
            )
            attempt = connection.execute(
                "SELECT attempt_count FROM evidence_episode_deliveries WHERE evidence_id = ?",
                (row["evidence_id"],),
            ).fetchone()["attempt_count"]
        return ClaimedDelivery(
            evidence=EvidenceDTO.model_validate_json(row["payload_json"]),
            attempt_count=attempt,
        )

    def mark_succeeded(self, evidence_id: str, episode_uuid: str) -> None:
        completed_at = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE evidence_episode_deliveries
                SET status = 'SUCCEEDED', graphiti_episode_uuid = ?, last_error = NULL,
                    completed_at = ?, lease_until = NULL, next_attempt_at = NULL
                WHERE evidence_id = ? AND status = 'PROCESSING'
                """,
                (episode_uuid, completed_at, evidence_id),
            )

    def mark_failed_attempt(
        self,
        evidence_id: str,
        *,
        attempt_count: int,
        max_attempts: int,
        retry_delay_seconds: int,
        error_code: str,
    ) -> bool:
        terminal = attempt_count >= max_attempts
        now = datetime.now(UTC)
        backoff_seconds = min(
            retry_delay_seconds * (2 ** max(0, attempt_count - 1)),
            3600,
        )
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE evidence_episode_deliveries
                SET status = ?, last_error = ?, lease_until = NULL,
                    next_attempt_at = ?, completed_at = ?
                WHERE evidence_id = ? AND status = 'PROCESSING'
                """,
                (
                    "FAILED" if terminal else "ACCEPTED",
                    error_code,
                    None
                    if terminal
                    else (now + timedelta(seconds=backoff_seconds)).isoformat(),
                    now.isoformat() if terminal else None,
                    evidence_id,
                ),
            )
        return terminal
