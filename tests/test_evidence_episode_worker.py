from __future__ import annotations

import asyncio
import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from graphiti_core.utils.bulk_utils import RawEpisode

from ingestion.episcode.evidence.delivery_store import EvidenceEpisodeDeliveryStore
from ingestion.episcode.evidence.module import EvidenceEpisodeModule
from tests.test_evidence_episode_converter import EVIDENCE_ID, evidence


SECOND_ID = "EVD55555555-5555-4555-8555-555555555555"


class RecordingWriter:
    def __init__(self, *, failures: int = 0):
        self.failures = failures
        self.episodes: list[RawEpisode] = []

    async def write(self, episode: RawEpisode) -> str:
        self.episodes.append(episode)
        if self.failures > 0:
            self.failures -= 1
            raise RuntimeError("provider leaked secret: should-not-be-visible")
        return f"episode-{episode.name}"


class EvidenceEpisodeWorkerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temporary_directory.name) / "state.sqlite3"
        self.store = EvidenceEpisodeDeliveryStore(self.state_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_pending_evidence_is_processed_in_reference_time_order(self) -> None:
        writer = RecordingWriter()
        module = EvidenceEpisodeModule(self.store, writer=writer)
        later = evidence().model_copy(update={"id": EVIDENCE_ID})
        earlier = evidence().model_copy(
            update={
                "id": SECOND_ID,
                "published_at": datetime(2026, 8, 25, 7, 30, tzinfo=UTC),
            }
        )
        module.accept([later, earlier])

        result = asyncio.run(module.process_pending(limit=10))

        self.assertEqual(result.succeeded_ids, [SECOND_ID, EVIDENCE_ID])
        self.assertEqual([episode.name for episode in writer.episodes], [SECOND_ID, EVIDENCE_ID])
        status = module.get_status(EVIDENCE_ID)
        self.assertIsNotNone(status)
        assert status is not None
        self.assertEqual(status.status, "SUCCEEDED")
        self.assertEqual(status.attempt_count, 1)
        self.assertEqual(status.graphiti_episode_uuid, f"episode-{EVIDENCE_ID}")

    def test_transient_failure_is_sanitized_and_retried(self) -> None:
        writer = RecordingWriter(failures=1)
        module = EvidenceEpisodeModule(
            self.store,
            writer=writer,
            max_attempts=2,
            retry_delay_seconds=0,
        )
        module.accept([evidence()])

        first = asyncio.run(module.process_pending(limit=1))
        first_status = module.get_status(EVIDENCE_ID)
        second = asyncio.run(module.process_pending(limit=1))
        final_status = module.get_status(EVIDENCE_ID)

        self.assertEqual(first.retry_ids, [EVIDENCE_ID])
        self.assertIsNotNone(first_status)
        assert first_status is not None
        self.assertEqual(first_status.status, "ACCEPTED")
        self.assertEqual(first_status.last_error, "GRAPHITI_PROCESSING_FAILED")
        self.assertNotIn("should-not-be-visible", first_status.last_error)
        self.assertEqual(second.succeeded_ids, [EVIDENCE_ID])
        self.assertIsNotNone(final_status)
        assert final_status is not None
        self.assertEqual(final_status.status, "SUCCEEDED")
        self.assertEqual(final_status.attempt_count, 2)

    def test_retry_backoff_blocks_later_reference_times_from_overtaking(self) -> None:
        writer = RecordingWriter(failures=1)
        module = EvidenceEpisodeModule(
            self.store,
            writer=writer,
            max_attempts=2,
            retry_delay_seconds=60,
        )
        earlier = evidence().model_copy(
            update={
                "id": SECOND_ID,
                "published_at": datetime(2026, 8, 25, 7, 30, tzinfo=UTC),
            }
        )
        later = evidence()
        module.accept([later, earlier])

        first = asyncio.run(module.process_pending(limit=10))

        self.assertEqual(first.retry_ids, [SECOND_ID])
        self.assertEqual(writer.episodes[0].name, SECOND_ID)
        later_status = module.get_status(EVIDENCE_ID)
        self.assertIsNotNone(later_status)
        assert later_status is not None
        self.assertEqual(later_status.status, "ACCEPTED")
        self.assertEqual(later_status.attempt_count, 0)

    def test_retry_limit_moves_evidence_to_failed(self) -> None:
        writer = RecordingWriter(failures=2)
        module = EvidenceEpisodeModule(
            self.store,
            writer=writer,
            max_attempts=2,
            retry_delay_seconds=0,
        )
        module.accept([evidence()])

        asyncio.run(module.process_pending(limit=1))
        result = asyncio.run(module.process_pending(limit=1))

        status = module.get_status(EVIDENCE_ID)
        self.assertEqual(result.failed_ids, [EVIDENCE_ID])
        self.assertIsNotNone(status)
        assert status is not None
        self.assertEqual(status.status, "FAILED")
        self.assertEqual(status.attempt_count, 2)
        self.assertEqual(status.last_error, "GRAPHITI_PROCESSING_FAILED")

    def test_expired_processing_lease_is_recovered_after_restart(self) -> None:
        first_module = EvidenceEpisodeModule(self.store, writer=RecordingWriter())
        first_module.accept([evidence()])
        claimed = self.store.claim_next(lease_seconds=300)
        self.assertIsNotNone(claimed)
        with sqlite3.connect(self.state_path) as connection:
            connection.execute(
                "UPDATE evidence_episode_deliveries SET lease_until = ? WHERE evidence_id = ?",
                ("2000-01-01T00:00:00+00:00", EVIDENCE_ID),
            )

        restarted_module = EvidenceEpisodeModule(self.store, writer=RecordingWriter())
        result = asyncio.run(restarted_module.process_pending(limit=1))

        self.assertEqual(result.succeeded_ids, [EVIDENCE_ID])
        status = restarted_module.get_status(EVIDENCE_ID)
        self.assertIsNotNone(status)
        assert status is not None
        self.assertEqual(status.status, "SUCCEEDED")
        self.assertEqual(status.attempt_count, 2)


if __name__ == "__main__":
    unittest.main()
