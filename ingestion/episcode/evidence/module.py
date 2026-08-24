"""Deep Evidence Episode ingestion interface used by HTTP and the worker."""

from __future__ import annotations

from typing import Protocol

from graphiti_core.utils.bulk_utils import RawEpisode

from ingestion.episcode.evidence.contracts import (
    EvidenceDTO,
    EvidenceEpisodeAcceptance,
    EvidenceEpisodeProcessingResult,
    EvidenceEpisodeStatus,
)
from ingestion.episcode.evidence.converter import to_raw_episode
from ingestion.episcode.evidence.delivery_store import EvidenceEpisodeDeliveryStore


class EpisodeWriter(Protocol):
    async def write(self, episode: RawEpisode) -> str: ...


class EvidenceEpisodeModule:
    def __init__(
        self,
        store: EvidenceEpisodeDeliveryStore,
        *,
        writer: EpisodeWriter | None = None,
        max_attempts: int = 5,
        retry_delay_seconds: int = 30,
        lease_seconds: int = 300,
    ):
        if max_attempts <= 0:
            raise ValueError("max attempts must be positive")
        if retry_delay_seconds < 0:
            raise ValueError("retry delay must not be negative")
        if lease_seconds <= 0:
            raise ValueError("lease duration must be positive")
        self._store = store
        self._writer = writer
        self._max_attempts = max_attempts
        self._retry_delay_seconds = retry_delay_seconds
        self._lease_seconds = lease_seconds

    def accept(self, evidences: list[EvidenceDTO]) -> EvidenceEpisodeAcceptance:
        result = self._store.accept(evidences)
        return EvidenceEpisodeAcceptance(
            accepted_ids=list(result.accepted_ids),
            duplicate_ids=list(result.duplicate_ids),
        )

    def get_status(self, evidence_id: str) -> EvidenceEpisodeStatus | None:
        return self._store.get_status(evidence_id)

    async def process_pending(self, *, limit: int) -> EvidenceEpisodeProcessingResult:
        if limit <= 0:
            raise ValueError("processing limit must be positive")
        if self._writer is None:
            raise RuntimeError("Evidence Episode writer is not configured")
        succeeded: list[str] = []
        retries: list[str] = []
        failed: list[str] = []
        for _ in range(limit):
            claimed = self._store.claim_next(lease_seconds=self._lease_seconds)
            if claimed is None:
                break
            evidence_id = claimed.evidence.id
            try:
                episode_uuid = await self._writer.write(to_raw_episode(claimed.evidence))
            except Exception:
                terminal = self._store.mark_failed_attempt(
                    evidence_id,
                    attempt_count=claimed.attempt_count,
                    max_attempts=self._max_attempts,
                    retry_delay_seconds=self._retry_delay_seconds,
                    error_code="GRAPHITI_PROCESSING_FAILED",
                )
                (failed if terminal else retries).append(evidence_id)
                continue
            self._store.mark_succeeded(evidence_id, episode_uuid)
            succeeded.append(evidence_id)
        return EvidenceEpisodeProcessingResult(
            succeeded_ids=succeeded,
            retry_ids=retries,
            failed_ids=failed,
        )
