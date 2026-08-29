from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime

from reasoning.investment.comparison import compare_results
from reasoning.investment.adapters import GraphitiLLMInvestmentReasoner
from reasoning.investment.contracts import (
    AnalysisDraft,
    ChainNodeSnapshot,
    ChainTrendView,
    Confidence,
    Direction,
    EventSnapshot,
    FactSnapshot,
    Horizon,
    IndustryChainSnapshot,
    InvestmentAnalysisContext,
    InvestmentAnalysisRequest,
    InvestmentAssessment,
    NodeTrendView,
    ReviewResult,
    TopologyEdgeSnapshot,
    TransmissionBatch,
    TransmissionProposal,
    Trend,
)
from reasoning.investment.pipeline import InvestmentReasoningPipeline


DECISION_AT = datetime(2026, 8, 27, tzinfo=UTC)


def context() -> InvestmentAnalysisContext:
    return InvestmentAnalysisContext(
        request=InvestmentAnalysisRequest(
            question="这些事件如何影响测试产业链？",
            decision_at=DECISION_AT,
            max_hops=2,
        ),
        events=[
            EventSnapshot(
                episode_uuid="episode-1",
                event_id="event-1",
                title="上游产能下降",
                summary="上游产能短期下降。",
                modality="FACT",
                occurred_at=DECISION_AT,
            )
        ],
        facts=[
            FactSnapshot(
                uuid="fact-1",
                kind="SIGNAL",
                name="SIGNAL_ON",
                fact="有效产能下降。",
                source_uuid="variable-1",
                source_name="有效产能",
                source_labels=["Entity", "Variable"],
                target_uuid="node-a-uuid",
                target_name="上游节点",
                target_business_id="node-a",
                target_labels=["Entity", "ChainNode"],
                source_event_ids=["event-1"],
                variable_id="effective_capacity",
                direction=Direction.DOWN,
                horizons=[Horizon.SHORT],
                valid_at=DECISION_AT,
            )
        ],
        chains=[
            IndustryChainSnapshot(
                uuid="chain-uuid",
                business_id="chain-1",
                name="测试产业链",
                anchor_match_count=1,
                matched_node_ids=["node-a"],
                nodes=[
                    ChainNodeSnapshot(
                        uuid="node-a-uuid", business_id="node-a", name="上游节点"
                    ),
                    ChainNodeSnapshot(
                        uuid="node-b-uuid", business_id="node-b", name="下游节点"
                    ),
                ],
                edges=[
                    TopologyEdgeSnapshot(
                        uuid="edge-uuid",
                        business_id="edge-1",
                        name="ChainNodeInputTo",
                        source_node_id="node-a",
                        source_name="上游节点",
                        target_node_id="node-b",
                        target_name="下游节点",
                        fact="上游节点向下游节点提供投入。",
                    )
                ],
            )
        ],
    )


def node_view(trend: Trend = Trend.COOLING) -> NodeTrendView:
    return NodeTrendView(
        chain_id="chain-1",
        node_id="node-a",
        node_name="上游节点",
        short=trend,
        medium=Trend.INSUFFICIENT_EVIDENCE,
        long=Trend.INSUFFICIENT_EVIDENCE,
        confidence=Confidence.MEDIUM,
        investment_assessment=InvestmentAssessment.RISK_POINT,
        rationale="有效产能下降形成短期交付风险。",
        supporting_fact_ids=["fact-1"],
    )


class FakeReasoner:
    name = "fake"

    async def propagate(self, _context, accepted, *, round_number):
        if round_number != 1:
            return TransmissionBatch()
        return TransmissionBatch(
            proposals=[
                TransmissionProposal(
                    chain_id="chain-1",
                    topology_edge_id="edge-1",
                    source_node_id="node-a",
                    target_node_id="node-b",
                    flow="ALONG_EDGE",
                    target_variable="delivery_ability",
                    direction=Direction.DOWN,
                    horizon=Horizon.SHORT,
                    confidence=Confidence.MEDIUM,
                    mechanism="上游有效产能下降可能削弱下游可交付量。",
                    source_fact_ids=["fact-1"],
                ),
                TransmissionProposal(
                    chain_id="chain-1",
                    topology_edge_id="invented-edge",
                    source_node_id="node-a",
                    target_node_id="node-b",
                    flow="ALONG_EDGE",
                    target_variable="invented",
                    direction=Direction.UP,
                    horizon=Horizon.SHORT,
                    confidence=Confidence.HIGH,
                    mechanism="这条提案应被边白名单拒绝。",
                    source_fact_ids=["fact-1"],
                ),
            ]
        )

    async def aggregate(self, _context, transmissions):
        return AnalysisDraft(
            one_sentence_conclusion="上游节点短期降温。",
            chains=[
                ChainTrendView(
                    chain_id="chain-1",
                    chain_name="测试产业链",
                    short=Trend.COOLING,
                    medium=Trend.INSUFFICIENT_EVIDENCE,
                    long=Trend.INSUFFICIENT_EVIDENCE,
                    confidence=Confidence.MEDIUM,
                    summary="上游产能下降，下游传导有待验证。",
                    nodes=[node_view()],
                )
            ],
        )

    async def review(self, _context, transmissions, draft):
        return ReviewResult(
            accepted=True,
            confidence=Confidence.MEDIUM,
            review_summary="结论与已知事实和传导范围一致。",
        )


class InvestmentReasoningPipelineTest(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_invented_edge_and_fills_missing_node(self):
        result = await InvestmentReasoningPipeline(FakeReasoner()).run(context())
        self.assertEqual(len(result.transmissions), 1)
        self.assertEqual(result.transmissions[0].topology_edge_id, "edge-1")
        self.assertEqual(len(result.draft.chains[0].nodes), 2)
        missing = result.draft.chains[0].nodes[1]
        self.assertEqual(missing.node_id, "node-b")
        self.assertEqual(missing.short, Trend.INSUFFICIENT_EVIDENCE)

    async def test_normalizes_unsupported_horizons(self):
        class OverreachingReasoner(FakeReasoner):
            async def aggregate(self, _context, transmissions):
                draft = await super().aggregate(_context, transmissions)
                node = draft.chains[0].nodes[0].model_copy(
                    update={
                        "short": Trend.WARMING,
                        "medium": Trend.WARMING,
                        "long": Trend.WARMING,
                    }
                )
                return draft.model_copy(
                    update={
                        "chains": [
                            draft.chains[0].model_copy(update={"nodes": [node]})
                        ]
                    }
                )

        result = await InvestmentReasoningPipeline(OverreachingReasoner()).run(
            context()
        )
        node = result.draft.chains[0].nodes[0]
        self.assertEqual(node.short, Trend.WARMING)
        self.assertEqual(node.medium, Trend.INSUFFICIENT_EVIDENCE)
        self.assertEqual(node.long, Trend.INSUFFICIENT_EVIDENCE)

    async def test_comparison_marks_warming_vs_cooling_material(self):
        left = await InvestmentReasoningPipeline(FakeReasoner()).run(context())
        warming_node = node_view(Trend.WARMING)
        right = left.model_copy(
            update={
                "executor": "other",
                "draft": left.draft.model_copy(
                    update={
                        "chains": [
                            left.draft.chains[0].model_copy(
                                update={
                                    "nodes": [warming_node, left.draft.chains[0].nodes[1]]
                                }
                            )
                        ]
                    }
                ),
            }
        )
        report = compare_results(left, right)
        self.assertTrue(report.same_context)
        self.assertEqual(report.material_contradictions, 1)
        self.assertFalse(report.basically_consistent)


class InvestmentReasoningPackageTest(unittest.TestCase):
    def test_package_exports_only_pipeline(self):
        import reasoning.investment as package

        self.assertEqual(package.__all__, ["InvestmentReasoningPipeline"])

    def test_compact_fact_payload_is_json_serializable(self):
        payload = GraphitiLLMInvestmentReasoner._fact_prompt_payload(
            context().facts[0]
        )
        serialized = json.dumps(payload)
        self.assertIn('"valid_at": "2026-08-27T00:00:00Z"', serialized)


if __name__ == "__main__":
    unittest.main()
