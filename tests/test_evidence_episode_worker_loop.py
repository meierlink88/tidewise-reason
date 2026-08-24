from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from graphiti_core.utils.bulk_utils import RawEpisode

from ingestion.episcode.evidence.delivery_store import EvidenceEpisodeDeliveryStore
from ingestion.episcode.evidence.module import EvidenceEpisodeModule
from ingestion.episcode.evidence.worker import run_worker
from tests.test_evidence_episode_converter import EVIDENCE_ID, evidence


class SignallingWriter:
    def __init__(self):
        self.written = asyncio.Event()

    async def write(self, episode: RawEpisode) -> str:
        self.written.set()
        return f"episode-{episode.name}"


class EvidenceEpisodeWorkerLoopTest(unittest.IsolatedAsyncioTestCase):
    async def test_worker_processes_accepted_evidence_and_stops_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = EvidenceEpisodeDeliveryStore(Path(directory) / "state.sqlite3")
            writer = SignallingWriter()
            module = EvidenceEpisodeModule(store, writer=writer)
            module.accept([evidence()])
            stop = asyncio.Event()
            task = asyncio.create_task(
                run_worker(
                    module,
                    stop_event=stop,
                    poll_interval_seconds=0.01,
                    batch_size=5,
                )
            )

            await asyncio.wait_for(writer.written.wait(), timeout=1)
            stop.set()
            await asyncio.wait_for(task, timeout=1)

            result = module.get_status(EVIDENCE_ID)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.status, "SUCCEEDED")


if __name__ == "__main__":
    unittest.main()
