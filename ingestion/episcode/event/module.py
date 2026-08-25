"""Deep interface coordinating durable Event Candidate processing."""

from __future__ import annotations

from ingestion.episcode.event.contracts import EventCandidateAcceptance, EventCandidateRequest, EventCandidateStatus
from ingestion.episcode.event.store import EventCandidateStore
from ingestion.episcode.event.resolver import (
    ComparisonUnavailable,
    ProjectionPending,
    PublicationRejected,
)


class EventCandidateModule:
    def __init__(self, store: EventCandidateStore, resolver=None, *, max_attempts: int = 5, retry_delay_seconds: int = 30):
        self._store, self._resolver, self._max_attempts = store, resolver, max_attempts
        self._retry_delay_seconds = retry_delay_seconds

    def accept(self, request: EventCandidateRequest) -> EventCandidateAcceptance:
        accepted = self._store.accept(request)
        return EventCandidateAcceptance(submission_id=accepted.submission_id, status="ACCEPTED",
            status_url=f"/api/reason/v1/event-candidates/{accepted.submission_id}", replayed=accepted.replayed)

    def get_status(self, submission_id: str) -> EventCandidateStatus | None:
        return self._store.get(submission_id)

    async def process_pending(self, *, limit: int) -> int:
        if self._resolver is None:
            raise RuntimeError("Event resolver is not configured")
        processed = 0
        for _ in range(limit):
            submission = self._store.claim()
            if submission is None:
                break
            try:
                outcome = await self._resolver.resolve(
                    submission,
                    on_published=lambda result, event: self._store.published(
                        submission.submission_id, result, event
                    ),
                    on_publication_started=lambda decision: self._store.publication_started(
                        submission.submission_id, decision
                    ),
                )
            except ProjectionPending as exc:
                self._store.projection_pending(submission.submission_id, exc.outcome, exc.event,
                                               terminal=submission.attempt_count >= self._max_attempts,
                                               retry_delay_seconds=self._retry_delay_seconds)
                continue
            except ComparisonUnavailable:
                if submission.attempt_count >= self._max_attempts:
                    self._store.needs_review(
                        submission.submission_id,
                        "EVENT_SEMANTIC_COMPARISON_UNAVAILABLE",
                    )
                else:
                    self._store.fail(
                        submission.submission_id,
                        "EVENT_SEMANTIC_COMPARISON_UNAVAILABLE",
                        terminal=False,
                        retry_delay_seconds=self._retry_delay_seconds,
                    )
                continue
            except PublicationRejected:
                self._store.fail(
                    submission.submission_id,
                    "DATA_EVENT_PUBLICATION_REJECTED",
                    terminal=True,
                    retry_delay_seconds=self._retry_delay_seconds,
                )
                continue
            except Exception:
                self._store.fail(submission.submission_id, "EVENT_RESOLUTION_FAILED",
                                 terminal=submission.attempt_count >= self._max_attempts,
                                 retry_delay_seconds=self._retry_delay_seconds)
                continue
            self._store.complete(submission.submission_id, outcome)
            processed += 1
        return processed
