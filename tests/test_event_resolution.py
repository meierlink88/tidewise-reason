from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

from ingestion.episcode.event.contracts import (
    AtomicityAssessment,
    EventCandidateRequest,
    HistoricalEvent,
    PairComparison,
)
from ingestion.episcode.event.resolver import EventResolver
from ingestion.episcode.event.module import EventCandidateModule
from ingestion.episcode.event.store import EventCandidateStore
from tests.test_event_candidate_api import EVENT_ID, candidate_payload


class History:
    def __init__(self, events): self.events = events
    async def retrieve(self, candidate): return self.events


class DataPublisher:
    def __init__(self): self.calls = 0
    async def publish(self, submission):
        self.calls += 1
        return HistoricalEvent(id=EVENT_ID, event=submission.event)


class Projector:
    def __init__(self): self.calls = 0
    async def project(self, event): self.calls += 1


class Comparator:
    async def assess_atomicity(self, candidate):
        return AtomicityAssessment(
            atomic=True,
            reason_codes=["SINGLE_REAL_WORLD_ACTION"],
            summary="One independently timed action.",
        )

    async def compare(self, candidate, historical):
        raise AssertionError("exact identity must not require an LLM call")


class EventResolutionTest(unittest.IsolatedAsyncioTestCase):
    async def test_new_event_is_published_and_projected(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        publisher, projector = DataPublisher(), Projector()
        outcome = await EventResolver(History([]), Comparator(), publisher, projector).resolve(
            type("Submission", (), {"submission_id": "evt-submission-1", "event": request.event, "evidence_ids": request.evidence_ids})()
        )
        self.assertEqual(outcome.decision, "NEW_EVENT")
        self.assertEqual((publisher.calls, projector.calls), (1, 1))

    async def test_same_event_is_ignored_without_any_write(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        historical = HistoricalEvent(id=EVENT_ID, event=request.event)
        publisher, projector = DataPublisher(), Projector()
        outcome = await EventResolver(History([historical]), Comparator(), publisher, projector).resolve(
            type("Submission", (), {"submission_id": "evt-submission-2", "event": request.event, "evidence_ids": request.evidence_ids})()
        )
        self.assertEqual(outcome.decision, "SAME_EVENT")
        self.assertEqual(outcome.event_id, EVENT_ID)
        self.assertEqual((publisher.calls, projector.calls), (0, 0))
        self.assertEqual(outcome.evidence_link_result, "IGNORED")
        self.assertEqual(outcome.graph_projection_status, "IGNORED")

    async def test_multiple_exact_matches_fail_closed_without_any_write(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        historical = [
            HistoricalEvent(id=EVENT_ID, event=request.event),
            HistoricalEvent(
                id="EVT66666666-6666-4666-8666-666666666666",
                event=request.event,
            ),
        ]
        publisher, projector = DataPublisher(), Projector()

        outcome = await EventResolver(
            History(historical), Comparator(), publisher, projector
        ).resolve(
            type(
                "Submission",
                (),
                {
                    "submission_id": "evt-submission-ambiguous",
                    "event": request.event,
                    "evidence_ids": request.evidence_ids,
                },
            )()
        )

        self.assertEqual(outcome.decision, "NEEDS_REVIEW")
        self.assertEqual((publisher.calls, projector.calls), (0, 0))

    async def test_contradictory_distinct_model_result_fails_closed(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        changed = request.event.model_copy(
            update={
                "summary": "A historical description with different wording.",
                "semantic": request.event.semantic.model_copy(
                    update={"action": "extended controls"}
                ),
            }
        )

        class ContradictoryComparator(Comparator):
            async def compare(self, candidate, historical):
                return PairComparison(
                    decision="RELATED_BUT_DISTINCT",
                    same_actor=True,
                    same_action=True,
                    same_object=True,
                    same_stage=True,
                    same_occurrence_time=True,
                    material_conflicts=[],
                    reason_codes=["MODEL_SAYS_DISTINCT"],
                    summary="Contradictory structured result.",
                )

        publisher, projector = DataPublisher(), Projector()
        outcome = await EventResolver(
            History([HistoricalEvent(id=EVENT_ID, event=changed)]),
            ContradictoryComparator(),
            publisher,
            projector,
        ).resolve(
            type(
                "Submission",
                (),
                {
                    "submission_id": "evt-submission-contradiction",
                    "event": request.event,
                    "evidence_ids": request.evidence_ids,
                },
            )()
        )

        self.assertEqual(outcome.decision, "NEEDS_REVIEW")
        self.assertEqual((publisher.calls, projector.calls), (0, 0))

    async def test_non_atomic_candidate_fails_closed_without_history_or_writes(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class NonAtomicComparator(Comparator):
            async def assess_atomicity(self, candidate):
                return AtomicityAssessment(
                    atomic=False,
                    reason_codes=["MULTIPLE_REAL_WORLD_ACTIONS"],
                    summary="Announcement and implementation are separate actions.",
                )

        history, publisher, projector = History([]), DataPublisher(), Projector()
        outcome = await EventResolver(
            history, NonAtomicComparator(), publisher, projector
        ).resolve(
            type(
                "Submission",
                (),
                {
                    "submission_id": "evt-submission-compound",
                    "event": request.event,
                    "evidence_ids": request.evidence_ids,
                },
            )()
        )

        self.assertEqual(outcome.decision, "NEEDS_REVIEW")
        self.assertEqual((publisher.calls, projector.calls), (0, 0))

    async def test_final_recall_prevents_a_racing_duplicate_publication(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())
        historical = HistoricalEvent(id=EVENT_ID, event=request.event)

        class RacingHistory:
            def __init__(self):
                self.calls = 0

            async def retrieve(self, candidate):
                self.calls += 1
                return [] if self.calls == 1 else [historical]

        history, publisher, projector = RacingHistory(), DataPublisher(), Projector()
        outcome = await EventResolver(
            history, Comparator(), publisher, projector
        ).resolve(
            type(
                "Submission",
                (),
                {
                    "submission_id": "evt-submission-race",
                    "event": request.event,
                    "evidence_ids": request.evidence_ids,
                },
            )()
        )

        self.assertEqual(outcome.decision, "SAME_EVENT")
        self.assertEqual(history.calls, 2)
        self.assertEqual((publisher.calls, projector.calls), (0, 0))

    async def test_two_event_simulation_creates_first_and_ignores_semantic_duplicate(self) -> None:
        first = EventCandidateRequest.model_validate(candidate_payload())
        second_payload = candidate_payload("Another source describes the same announcement with more detail.")
        second_payload["evidence_ids"] = ["EVD33333333-3333-4333-8333-333333333333"]
        second = EventCandidateRequest.model_validate(second_payload)

        class MutableBoundary:
            def __init__(self):
                self.events = []
                self.publish_calls = 0
                self.project_calls = 0
                self.event_ids: set[str] = set()
                self.evidence_link_ids: set[str] = set()
                self.graph_episode_ids: set[str] = set()

            async def retrieve(self, candidate):
                return list(self.events)

            async def publish(self, submission):
                self.publish_calls += 1
                event = HistoricalEvent(id=EVENT_ID, event=submission.event)
                self.events.append(event)
                self.event_ids.add(EVENT_ID)
                for index, _ in enumerate(submission.evidence_ids):
                    self.evidence_link_ids.add(
                        f"EEL44444444-4444-4444-8444-44444444444{index}"
                    )
                return event

            async def project(self, event):
                self.project_calls += 1
                self.graph_episode_ids.add(event.id)

        boundary = MutableBoundary()
        resolver = EventResolver(boundary, Comparator(), boundary, boundary)
        first_outcome = await resolver.resolve(type("Submission", (), {
            "submission_id": "evt-submission-first", "event": first.event, "evidence_ids": first.evidence_ids,
        })())
        counts_after_first = (
            len(boundary.event_ids),
            len(boundary.evidence_link_ids),
            len(boundary.graph_episode_ids),
        )
        duplicate_outcome = await resolver.resolve(type("Submission", (), {
            "submission_id": "evt-submission-second", "event": second.event, "evidence_ids": second.evidence_ids,
        })())

        self.assertEqual(first_outcome.decision, "NEW_EVENT")
        self.assertEqual(duplicate_outcome.decision, "SAME_EVENT")
        self.assertEqual(duplicate_outcome.event_id, EVENT_ID)
        self.assertEqual((boundary.publish_calls, boundary.project_calls), (1, 1))
        self.assertEqual(counts_after_first, (1, 1, 1))
        self.assertEqual(
            (
                len(boundary.event_ids),
                len(boundary.evidence_link_ids),
                len(boundary.graph_episode_ids),
            ),
            counts_after_first,
        )

    async def test_projection_retry_resumes_after_data_publish_without_rededup_or_republish(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class FlakyProjector(Projector):
            async def project(self, event):
                self.calls += 1
                if self.calls == 1:
                    raise RuntimeError("temporary Graphiti failure")

        publisher, projector = DataPublisher(), FlakyProjector()
        with tempfile.TemporaryDirectory() as directory:
            module = EventCandidateModule(
                EventCandidateStore(Path(directory) / "state.sqlite3"),
                EventResolver(History([]), Comparator(), publisher, projector),
                retry_delay_seconds=0,
            )
            accepted = module.accept(request)
            await module.process_pending(limit=1)
            pending = module.get_status(accepted.submission_id)
            self.assertIsNotNone(pending)
            assert pending is not None
            self.assertEqual(pending.status, "PROJECTING")

            await module.process_pending(limit=1)
            completed = module.get_status(accepted.submission_id)
            self.assertIsNotNone(completed)
            assert completed is not None
            self.assertEqual(completed.status, "SUCCEEDED")
            self.assertEqual((publisher.calls, projector.calls), (1, 2))

    async def test_formal_event_is_persisted_before_graph_projection(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class InspectingProjector(Projector):
            def __init__(self):
                super().__init__()
                self.persisted_before_call = False

            async def project(self, event):
                self.calls += 1
                current = module.get_status(accepted.submission_id)
                self.persisted_before_call = bool(
                    current
                    and current.status == "PROJECTING"
                    and current.event_id == EVENT_ID
                )

        publisher, projector = DataPublisher(), InspectingProjector()
        with tempfile.TemporaryDirectory() as directory:
            module = EventCandidateModule(
                EventCandidateStore(Path(directory) / "state.sqlite3"),
                EventResolver(History([]), Comparator(), publisher, projector),
                retry_delay_seconds=0,
            )
            accepted = module.accept(request)
            await module.process_pending(limit=1)

        self.assertTrue(projector.persisted_before_call)

    async def test_publication_intent_reconciles_data_without_repeating_dedup(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class ForbiddenHistory:
            async def retrieve(self, candidate):
                raise AssertionError("dedup must not repeat after publication intent")

        publisher, projector = DataPublisher(), Projector()
        with tempfile.TemporaryDirectory() as directory:
            store = EventCandidateStore(Path(directory) / "state.sqlite3")
            module = EventCandidateModule(
                store,
                EventResolver(ForbiddenHistory(), Comparator(), publisher, projector),
                retry_delay_seconds=0,
            )
            accepted = module.accept(request)
            claimed = store.claim(lease_seconds=0)
            assert claimed is not None
            store.publication_started(accepted.submission_id, "NEW_EVENT")

            await module.process_pending(limit=1)
            completed = module.get_status(accepted.submission_id)

        self.assertIsNotNone(completed)
        assert completed is not None
        self.assertEqual(completed.status, "SUCCEEDED")
        self.assertEqual((publisher.calls, projector.calls), (1, 1))

    async def test_unavailable_semantic_model_fails_closed_to_review(self) -> None:
        request = EventCandidateRequest.model_validate(candidate_payload())

        class UnavailableComparator(Comparator):
            async def assess_atomicity(self, candidate):
                raise ValueError("invalid structured model output")

        with tempfile.TemporaryDirectory() as directory:
            module = EventCandidateModule(
                EventCandidateStore(Path(directory) / "state.sqlite3"),
                EventResolver(
                    History([]),
                    UnavailableComparator(),
                    DataPublisher(),
                    Projector(),
                ),
                max_attempts=1,
                retry_delay_seconds=0,
            )
            accepted = module.accept(request)
            await module.process_pending(limit=1)
            reviewed = module.get_status(accepted.submission_id)

        self.assertIsNotNone(reviewed)
        assert reviewed is not None
        self.assertEqual(reviewed.status, "NEEDS_REVIEW")
        self.assertEqual(reviewed.decision, "NEEDS_REVIEW")


if __name__ == "__main__":
    unittest.main()
