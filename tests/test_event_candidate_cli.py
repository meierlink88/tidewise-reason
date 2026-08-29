from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ingestion.episcode.event.cli import _run
from ingestion.episcode.event.contracts import EventResolutionOutcome
from ingestion.episcode.event.pipeline import EventCandidatePipeline
from ingestion.episcode.event.resolver import EventResolution
from ingestion.episcode.event.store import EventCandidateStore
from tests.test_event_candidate_api import EVENT_ID, candidate_payload


class Resolver:
    async def resolve(
        self, submission, on_published=None, on_publication_started=None
    ):
        return EventResolution(
            EventResolutionOutcome(
                decision="SAME_EVENT",
                event_id=EVENT_ID,
                event_created=False,
                evidence_link_result="IGNORED",
                graph_projection_status="IGNORED",
                reason_codes=["SAME_REAL_WORLD_OCCURRENCE"],
                matched_event_ids=[EVENT_ID],
            )
        )


class EventCandidateCLITest(unittest.IsolatedAsyncioTestCase):
    async def test_submit_wait_uses_the_shared_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "candidate.json"
            candidate.write_text(
                json.dumps(candidate_payload()), encoding="utf-8"
            )
            pipeline = EventCandidatePipeline(
                EventCandidateStore(root / "state.sqlite3"), Resolver()
            )
            args = argparse.Namespace(
                command="submit",
                input=str(candidate),
                wait=True,
                timeout=1.0,
            )
            output = io.StringIO()
            with patch(
                "ingestion.episcode.event.cli.load_ingestion_config"
            ), patch(
                "ingestion.episcode.event.cli.create_runtime_pipeline",
                return_value=(pipeline, None, None),
            ), redirect_stdout(output):
                exit_code = await _run(args)

        self.assertEqual(exit_code, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["decision"], "SAME_EVENT")
        self.assertEqual(result["event_id"], EVENT_ID)


if __name__ == "__main__":
    unittest.main()
