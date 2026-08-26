from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from analysis.event.errors import PermanentEventAnalysisFailure
from analysis.event.module import EventAnalysisModule
from analysis.event.store import EventAnalysisStore
from tests.test_event_analysis_pipeline import classification, event_input


class EventAnalysisWorkflowTest(unittest.IsolatedAsyncioTestCase):
    async def test_enqueue_is_idempotent_and_worker_persists_terminal_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = EventAnalysisStore(Path(directory) / "reason.sqlite3")
            outcome = SimpleNamespace(
                status="NO_SIGNAL",
                classification=classification(),
                signal_fact_uuids=[],
                reason_codes=["EVENT_SUPPORTS_NO_DIRECT_SIGNAL"],
                model_dump_json=lambda: "{}",
            )
            pipeline = SimpleNamespace(analyze=AsyncMock(return_value=outcome))
            module = EventAnalysisModule(store, pipeline)

            first = module.enqueue(event_input())
            replay = module.enqueue(event_input())
            self.assertFalse(first.replayed)
            self.assertTrue(replay.replayed)
            self.assertEqual(first.analysis_id, replay.analysis_id)

            self.assertEqual(await module.process_pending(limit=1), 1)
            status = module.get_status(first.analysis_id)
            self.assertIsNotNone(status)
            self.assertEqual(status.status, "NO_SIGNAL")
            self.assertEqual(status.event_id, event_input().event.id)
            self.assertEqual(status.attempt_count, 1)

    async def test_failure_is_retried_without_losing_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = EventAnalysisStore(Path(directory) / "reason.sqlite3")
            pipeline = SimpleNamespace(analyze=AsyncMock(side_effect=RuntimeError("provider down")))
            module = EventAnalysisModule(
                store, pipeline, max_attempts=2, retry_delay_seconds=0
            )
            accepted = module.enqueue(event_input())

            self.assertEqual(await module.process_pending(limit=1), 0)
            status = module.get_status(accepted.analysis_id)
            self.assertEqual(status.status, "FAILED_RETRYING")
            self.assertEqual(status.last_error, "EVENT_ANALYSIS_FAILED")

            self.assertEqual(await module.process_pending(limit=1), 0)
            status = module.get_status(accepted.analysis_id)
            self.assertEqual(status.status, "FAILED")
            self.assertEqual(status.attempt_count, 2)

    async def test_expired_in_progress_lease_is_reclaimed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = EventAnalysisStore(Path(directory) / "reason.sqlite3")
            accepted = store.enqueue(event_input())

            first = store.claim(lease_seconds=0)
            self.assertIsNotNone(first)
            store.set_stage(accepted.analysis_id, "PROJECTING")

            reclaimed = store.claim(lease_seconds=300)

            self.assertIsNotNone(reclaimed)
            self.assertEqual(reclaimed.analysis_id, accepted.analysis_id)
            self.assertEqual(reclaimed.attempt_count, 2)

    async def test_permanent_validation_failure_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = EventAnalysisStore(Path(directory) / "reason.sqlite3")
            pipeline = SimpleNamespace(
                analyze=AsyncMock(
                    side_effect=PermanentEventAnalysisFailure("identity mismatch")
                )
            )
            module = EventAnalysisModule(store, pipeline, max_attempts=5)
            accepted = module.enqueue(event_input())

            self.assertEqual(await module.process_pending(limit=1), 0)
            status = module.get_status(accepted.analysis_id)

            self.assertEqual(status.status, "FAILED")
            self.assertEqual(status.attempt_count, 1)
            self.assertEqual(status.last_error, "EVENT_ANALYSIS_VALIDATION_FAILED")
            self.assertEqual(await module.process_pending(limit=1), 0)


if __name__ == "__main__":
    unittest.main()
