from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import NAMESPACE_URL, uuid5

from analysis.event.contracts import (
    AnchorCandidate,
    CandidateSet,
    ConfidenceLevel,
    DirectSignalDraft,
    EventAnalysisInput,
    EventClass,
    EventClassification,
    SignalDirection,
    SignalMagnitude,
    SignalProposal,
    VariableCandidate,
)
from analysis.event.pipeline import EventAnalysisPipeline
from ingestion.episcode.event.contracts import EventCandidateRequest, HistoricalEvent
from tests.test_event_candidate_api import EVENT_ID, candidate_payload

EPISODE_UUID = str(uuid5(NAMESPACE_URL, f"urn:tidewise:event-episode:{EVENT_ID}"))
VARIABLE_UUID = "07d8a404-96f8-530b-9f96-66cbf6e2a824"
ANCHOR_UUID = "54413fc9-c830-4783-b81a-da1719594ae0"


def event_input() -> EventAnalysisInput:
    request = EventCandidateRequest.model_validate(candidate_payload())
    return EventAnalysisInput(
        event=HistoricalEvent(id=EVENT_ID, event=request.event),
        episode_uuid=EPISODE_UUID,
        reference_time=datetime(2026, 8, 26, 12, tzinfo=UTC),
    )


def classification(event_class: EventClass = EventClass.CHAIN_NODE) -> EventClassification:
    return EventClassification(
        event_class=event_class,
        confidence=ConfidenceLevel.HIGH,
        anchor_type_hints=["ChainNode", "IndustryChain"],
        variable_group_hints=["DEMAND"],
        retrieval_queries=["AI服务器 订单需求"],
        rationale="Event 的直接对象是 AI 服务器节点的订单变化。",
    )


def candidates() -> CandidateSet:
    return CandidateSet(
        anchors=[
            AnchorCandidate(
                uuid=ANCHOR_UUID,
                name="AI服务器",
                entity_type="ChainNode",
                business_id="CHN-existing",
                summary="AI算力产业链中的AI服务器节点",
            )
        ],
        variables=[
            VariableCandidate(
                uuid=VARIABLE_UUID,
                variable_id="order_visibility",
                name="订单能见度",
                variable_group="DEMAND",
                allowed_anchor_types=["ChainNode", "IndustryChain"],
                definition="未来订单及交付需求的可观察程度。",
            )
        ],
    )


def proposal(*, anchor_uuid: str = ANCHOR_UUID) -> SignalProposal:
    return SignalProposal(
        anchor_uuid=anchor_uuid,
        variable_uuid=VARIABLE_UUID,
        fact="AI服务器节点的订单能见度在未来一个季度上升。",
        direction=SignalDirection.UP,
        magnitude=SignalMagnitude.MEDIUM,
        derivation_type="DERIVED",
        assertion_modality="ANTICIPATED",
        valid_at=datetime(2026, 8, 26, tzinfo=UTC),
        expected_end_earliest=datetime(2026, 11, 1, tzinfo=UTC),
        expected_end_latest=datetime(2026, 12, 31, tzinfo=UTC),
        horizon_tags=["MEDIUM"],
        mechanism="云厂商资本开支增加提高AI服务器订单需求。",
        duration_basis="订单与交付周期",
        assumptions=["资本开支计划能够执行"],
        invalidation_conditions=["云厂商下调资本开支"],
        provenance_confidence=ConfidenceLevel.HIGH,
        mechanism_confidence=ConfidenceLevel.MEDIUM,
        temporal_confidence=ConfidenceLevel.MEDIUM,
    )


class EventAnalysisPipelineTest(unittest.IsolatedAsyncioTestCase):
    async def test_projects_reviewed_signal_only_to_supplied_existing_candidates(self) -> None:
        classifier = SimpleNamespace(classify=AsyncMock(return_value=classification()))
        retriever = SimpleNamespace(retrieve=AsyncMock(return_value=candidates()))
        extractor = SimpleNamespace(extract=AsyncMock(return_value=[proposal()]))
        reviewer = SimpleNamespace(review=AsyncMock(return_value=True))
        projector = SimpleNamespace(project=AsyncMock(return_value="signal-fact-1"))
        pipeline = EventAnalysisPipeline(
            classifier, retriever, extractor, reviewer, projector
        )

        outcome = await pipeline.analyze(event_input())

        self.assertEqual(outcome.status, "SUCCEEDED")
        self.assertEqual(outcome.signal_fact_uuids, ["signal-fact-1"])
        projector.project.assert_awaited_once()
        projected = projector.project.await_args.args
        self.assertEqual(projected[2].uuid, VARIABLE_UUID)
        self.assertEqual(projected[3].uuid, ANCHOR_UUID)

    async def test_rejects_llm_anchor_uuid_outside_candidate_whitelist(self) -> None:
        projector = SimpleNamespace(project=AsyncMock())
        pipeline = EventAnalysisPipeline(
            SimpleNamespace(classify=AsyncMock(return_value=classification())),
            SimpleNamespace(retrieve=AsyncMock(return_value=candidates())),
            SimpleNamespace(
                extract=AsyncMock(return_value=[proposal(anchor_uuid="invented-anchor")])
            ),
            SimpleNamespace(review=AsyncMock(return_value=True)),
            projector,
        )

        outcome = await pipeline.analyze(event_input())

        self.assertEqual(outcome.status, "NEEDS_REVIEW")
        self.assertIn("UNKNOWN_ANCHOR_UUID", outcome.reason_codes)
        projector.project.assert_not_awaited()

    async def test_company_class_is_recorded_without_company_signal_processing(self) -> None:
        retriever = SimpleNamespace(retrieve=AsyncMock())
        pipeline = EventAnalysisPipeline(
            SimpleNamespace(
                classify=AsyncMock(return_value=classification(EventClass.COMPANY))
            ),
            retriever,
            SimpleNamespace(extract=AsyncMock()),
            SimpleNamespace(review=AsyncMock()),
            SimpleNamespace(project=AsyncMock()),
        )

        outcome = await pipeline.analyze(event_input())

        self.assertEqual(outcome.status, "NO_SUPPORTED_ANCHOR")
        self.assertEqual(outcome.classification.event_class, EventClass.COMPANY)
        retriever.retrieve.assert_not_awaited()

    async def test_expected_end_does_not_become_confirmed_graphiti_invalidation(self) -> None:
        item = proposal()
        self.assertIsNotNone(item.expected_end_latest)
        self.assertIsNone(item.invalid_at)
        self.assertGreater(item.expected_end_latest, item.valid_at + timedelta(days=30))

    async def test_signal_detail_preserves_onset_peak_and_distinct_confidence(self) -> None:
        event_time = datetime(2026, 9, 1, tzinfo=UTC)
        item = DirectSignalDraft(
            anchor_uuid=ANCHOR_UUID,
            variable_uuid=VARIABLE_UUID,
            fact="政策生效后出口限制敞口上升。",
            direction="UP",
            magnitude="HIGH",
            impact_onset_days=0,
            impact_peak_days=30,
            expected_duration_days=180,
            mechanism="许可证范围收紧限制可服务市场。",
            duration_basis="政策有效期",
            assumptions=[],
            invalidation_conditions=["政策撤回"],
            provenance_confidence="HIGH",
            mechanism_confidence="MEDIUM",
            temporal_confidence="LOW",
        ).proposal(event_time=event_time, assertion_modality="ANTICIPATED")

        self.assertEqual(item.valid_at, event_time)
        self.assertEqual(item.impact_peak_earliest, event_time + timedelta(days=30))
        self.assertEqual(item.expected_end_latest, event_time + timedelta(days=180))
        self.assertEqual(item.provenance_confidence, ConfidenceLevel.HIGH)
        self.assertEqual(item.mechanism_confidence, ConfidenceLevel.MEDIUM)
        self.assertEqual(item.temporal_confidence, ConfidenceLevel.LOW)


if __name__ == "__main__":
    unittest.main()
