from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ingestion.episcode.event.contracts import (
    AtomicityAssessment,
    EventCandidateRequest,
    HistoricalEvent,
)
from ingestion.episcode.event.pipeline import EventCandidatePipeline
from ingestion.episcode.event.resolver import EventHistoryUnavailable, EventResolver
from ingestion.episcode.event.store import EventCandidateStore
from tests.test_event_candidate_api import EVENT_ID, candidate_payload


class History:
    def __init__(self, events):
        self.events = events

    async def retrieve(self, candidate):
        return list(self.events)


class DataPublisher:
    def __init__(self):
        self.calls = 0

    async def publish(self, submission):
        self.calls += 1
        return HistoricalEvent(id=EVENT_ID, event=submission.event)


class EpisodeStage:
    def __init__(self):
        self.calls = 0

    async def execute(self, event):
        self.calls += 1
        return f"episode-{event.id}"

    async def ready(self):
        return True

    async def close(self):
        return None


class AnalysisPipeline:
    def __init__(self):
        self.calls = 0

    def enqueue(self, input_):
        self.calls += 1


class Comparator:
    async def assess_atomicity(self, candidate):
        return AtomicityAssessment(
            atomic=True,
            reason_codes=["SINGLE_REAL_WORLD_ACTION"],
            summary="One independently timed action.",
        )

    async def compare(self, candidate, historical):
        raise AssertionError("exact identity must not require an LLM call")


def submission(request: EventCandidateRequest, identifier: str = "evt-submission-1"):
    return type(
        "Submission",
        (),
        {
            "submission_id": identifier,
            "event": request.event,
            "evidence_ids": request.evidence_ids,
        },
    )()


class EventResolutionTest(unittest.IsolatedAsyncioTestCase):
    async def test_resolution_publishes_new_event_but_cannot_project_it(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        publisher = DataPublisher()

        resolution = await EventResolver(
            History([]), Comparator(), publisher
        ).resolve(submission(request))

        self.assertEqual(resolution.outcome.decision, "NEW_EVENT")
        self.assertEqual(resolution.published_event.id, EVENT_ID)
        self.assertEqual(publisher.calls, 1)

    async def test_same_event_is_ignored_without_any_write(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        publisher = DataPublisher()
        historical = HistoricalEvent(id=EVENT_ID, event=request.event)

        resolution = await EventResolver(
            History([historical]), Comparator(), publisher
        ).resolve(submission(request))

        outcome = resolution.outcome
        self.assertEqual(outcome.decision, "SAME_EVENT")
        self.assertEqual(outcome.event_id, EVENT_ID)
        self.assertIsNone(resolution.published_event)
        self.assertEqual(publisher.calls, 0)
        self.assertEqual(outcome.evidence_link_result, "IGNORED")
        self.assertEqual(outcome.graph_projection_status, "IGNORED")

    async def test_exact_match_short_circuits_unrelated_llm_candidates(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        exact = HistoricalEvent(id=EVENT_ID, event=request.event)
        unrelated = HistoricalEvent(
            id="EVT77777777-7777-4777-8777-777777777777",
            event=request.event.model_copy(
                update={
                    "semantic": request.event.semantic.model_copy(
                        update={"actors": ["Unrelated actor"]}
                    )
                }
            ),
        )

        resolution = await EventResolver(
            History([unrelated, exact]), Comparator(), DataPublisher()
        ).resolve(submission(request))

        self.assertEqual(resolution.outcome.decision, "SAME_EVENT")
        self.assertEqual(
            resolution.outcome.reason_codes, ["SAME_REAL_WORLD_OCCURRENCE"]
        )

    async def test_multiple_exact_matches_fail_closed_without_any_write(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        historical = [
            HistoricalEvent(id=EVENT_ID, event=request.event),
            HistoricalEvent(
                id="EVT66666666-6666-4666-8666-666666666666",
                event=request.event,
            ),
        ]
        publisher = DataPublisher()

        resolution = await EventResolver(
            History(historical), Comparator(), publisher
        ).resolve(submission(request))

        self.assertEqual(resolution.outcome.decision, "NEEDS_REVIEW")
        self.assertIsNone(resolution.published_event)
        self.assertEqual(publisher.calls, 0)

    async def test_non_atomic_candidate_fails_closed_without_history_or_write(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class NonAtomicComparator(Comparator):
            async def assess_atomicity(self, candidate):
                return AtomicityAssessment(
                    atomic=False,
                    reason_codes=["MULTIPLE_REAL_WORLD_ACTIONS"],
                    summary="Announcement and implementation are separate actions.",
                )

        publisher = DataPublisher()
        resolution = await EventResolver(
            History([]), NonAtomicComparator(), publisher
        ).resolve(submission(request))

        self.assertEqual(resolution.outcome.decision, "NEEDS_REVIEW")
        self.assertIsNone(resolution.published_event)
        self.assertEqual(publisher.calls, 0)

    async def test_final_recall_prevents_a_racing_duplicate_publication(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        historical = HistoricalEvent(id=EVENT_ID, event=request.event)

        class RacingHistory:
            def __init__(self):
                self.calls = 0

            async def retrieve(self, candidate):
                self.calls += 1
                return [] if self.calls == 1 else [historical]

        history = RacingHistory()
        publisher = DataPublisher()
        resolution = await EventResolver(
            history, Comparator(), publisher
        ).resolve(submission(request))

        self.assertEqual(resolution.outcome.decision, "SAME_EVENT")
        self.assertEqual(history.calls, 2)
        self.assertEqual(publisher.calls, 0)

    async def test_two_pipeline_submissions_create_first_and_ignore_semantic_duplicate(self) -> None:
        first = EventCandidateRequest.model_validate(candidate_payload())
        second_payload = candidate_payload(
            "Another source describes the same announcement with more detail."
        )
        second_payload["event"]["title"] = "Second source: US HBM control expansion"
        second_payload["evidence_ids"] = [
            "EVD33333333-3333-4333-8333-333333333333"
        ]
        second = EventCandidateRequest.model_validate(second_payload)

        class MutableDataBoundary(History, DataPublisher):
            def __init__(self):
                History.__init__(self, [])
                DataPublisher.__init__(self)

            async def publish(self, claimed):
                event = await DataPublisher.publish(self, claimed)
                self.events.append(event)
                return event

        boundary = MutableDataBoundary()
        episode_stage = EpisodeStage()
        analysis = AnalysisPipeline()
        with tempfile.TemporaryDirectory() as directory:
            pipeline = EventCandidatePipeline(
                EventCandidateStore(Path(directory) / "state.sqlite3"),
                EventResolver(boundary, Comparator(), boundary),
                episode_stage,
                analysis,
                retry_delay_seconds=0,
            )
            first_acceptance = pipeline.submit(first)
            await pipeline.process_pending(limit=1)
            counts_after_first = (
                boundary.calls,
                episode_stage.calls,
                analysis.calls,
            )

            duplicate_acceptance = pipeline.submit(second)
            await pipeline.process_pending(limit=1)
            duplicate_status = pipeline.get_status(duplicate_acceptance.submission_id)

        self.assertFalse(first_acceptance.replayed)
        self.assertFalse(duplicate_acceptance.replayed)
        self.assertEqual(duplicate_status.decision, "SAME_EVENT")
        self.assertEqual(duplicate_status.event_id, EVENT_ID)
        self.assertEqual(counts_after_first, (1, 1, 1))
        self.assertEqual(
            (boundary.calls, episode_stage.calls, analysis.calls),
            counts_after_first,
        )

    async def test_episode_retry_resumes_after_data_publish_without_rededup(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class FlakyEpisodeStage(EpisodeStage):
            async def execute(self, event):
                self.calls += 1
                if self.calls == 1:
                    raise RuntimeError("temporary Graphiti failure")
                return f"episode-{event.id}"

        publisher = DataPublisher()
        episode_stage = FlakyEpisodeStage()
        with tempfile.TemporaryDirectory() as directory:
            pipeline = EventCandidatePipeline(
                EventCandidateStore(Path(directory) / "state.sqlite3"),
                EventResolver(History([]), Comparator(), publisher),
                episode_stage,
                AnalysisPipeline(),
                retry_delay_seconds=0,
            )
            accepted = pipeline.submit(request)
            await pipeline.process_pending(limit=1)
            self.assertEqual(pipeline.get_status(accepted.submission_id).status, "PROJECTING")

            await pipeline.process_pending(limit=1)
            completed = pipeline.get_status(accepted.submission_id)

        self.assertEqual(completed.status, "SUCCEEDED")
        self.assertEqual((publisher.calls, episode_stage.calls), (1, 2))

    async def test_analysis_retry_preserves_episode_success(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class FlakyAnalysis(AnalysisPipeline):
            def enqueue(self, input_):
                self.calls += 1
                if self.calls == 1:
                    raise OSError("state store unavailable")

        publisher = DataPublisher()
        episode_stage = EpisodeStage()
        analysis = FlakyAnalysis()
        with tempfile.TemporaryDirectory() as directory:
            pipeline = EventCandidatePipeline(
                EventCandidateStore(Path(directory) / "state.sqlite3"),
                EventResolver(History([]), Comparator(), publisher),
                episode_stage,
                analysis,
                retry_delay_seconds=0,
            )
            accepted = pipeline.submit(request)
            await pipeline.process_pending(limit=1)
            pending = pipeline.get_status(accepted.submission_id)
            self.assertEqual(pending.status, "PROJECTING")
            self.assertEqual(pending.graph_projection_status, "SUCCEEDED")
            self.assertEqual(pending.last_error, "EVENT_ANALYSIS_SCHEDULING_FAILED")

            await pipeline.process_pending(limit=1)
            completed = pipeline.get_status(accepted.submission_id)

        self.assertEqual(completed.status, "SUCCEEDED")
        self.assertEqual((publisher.calls, episode_stage.calls, analysis.calls), (1, 2, 2))

    async def test_formal_event_is_persisted_before_episode_stage(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class InspectingStage(EpisodeStage):
            async def execute(self, event):
                self.calls += 1
                current = pipeline.get_status(accepted.submission_id)
                self.persisted_before_call = bool(
                    current
                    and current.status == "PROJECTING"
                    and current.event_id == EVENT_ID
                )
                return f"episode-{event.id}"

        publisher = DataPublisher()
        episode_stage = InspectingStage()
        with tempfile.TemporaryDirectory() as directory:
            pipeline = EventCandidatePipeline(
                EventCandidateStore(Path(directory) / "state.sqlite3"),
                EventResolver(History([]), Comparator(), publisher),
                episode_stage,
                AnalysisPipeline(),
                retry_delay_seconds=0,
            )
            accepted = pipeline.submit(request)
            await pipeline.process_pending(limit=1)

        self.assertTrue(episode_stage.persisted_before_call)

    async def test_unavailable_semantic_model_fails_closed_to_review(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class UnavailableComparator(Comparator):
            async def assess_atomicity(self, candidate):
                raise ValueError("invalid structured model output")

        with tempfile.TemporaryDirectory() as directory:
            pipeline = EventCandidatePipeline(
                EventCandidateStore(Path(directory) / "state.sqlite3"),
                EventResolver(History([]), UnavailableComparator(), DataPublisher()),
                EpisodeStage(),
                AnalysisPipeline(),
                max_attempts=1,
                retry_delay_seconds=0,
            )
            accepted = pipeline.submit(request)
            await pipeline.process_pending(limit=1)
            reviewed = pipeline.get_status(accepted.submission_id)

        self.assertEqual(reviewed.status, "NEEDS_REVIEW")
        self.assertEqual(reviewed.decision, "NEEDS_REVIEW")

    async def test_data_history_failure_has_safe_typed_status_and_log(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class UnavailableHistory:
            async def retrieve(self, candidate):
                try:
                    raise ConnectionError("Bearer super-secret-data-token")
                except ConnectionError as cause:
                    raise EventHistoryUnavailable(
                        "response body with private business data"
                    ) from cause

        with tempfile.TemporaryDirectory() as directory:
            pipeline = EventCandidatePipeline(
                EventCandidateStore(Path(directory) / "state.sqlite3"),
                EventResolver(UnavailableHistory(), Comparator(), DataPublisher()),
                EpisodeStage(),
                AnalysisPipeline(),
                max_attempts=1,
                retry_delay_seconds=0,
            )
            accepted = pipeline.submit(request)
            with self.assertLogs(
                "ingestion.episcode.event.pipeline", level="ERROR"
            ) as captured:
                await pipeline.process_pending(limit=1)
            failed = pipeline.get_status(accepted.submission_id)

        self.assertEqual(failed.status, "FAILED")
        self.assertEqual(failed.last_error, "DATA_EVENT_HISTORY_UNAVAILABLE")
        log_output = "\n".join(captured.output)
        self.assertIn(f"submission_id={accepted.submission_id}", log_output)
        self.assertIn("stage=DATA_EVENT_HISTORY_RECALL", log_output)
        self.assertIn("diagnostic_id=", log_output)
        self.assertIn("EventHistoryUnavailable", log_output)
        self.assertIn("ConnectionError", log_output)
        self.assertNotIn("super-secret-data-token", log_output)
        self.assertNotIn("private business data", log_output)


if __name__ == "__main__":
    unittest.main()
