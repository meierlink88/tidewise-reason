"""Run isolated simulated Events through Event Analysis and one chain reasoning pass."""

from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from graphiti_core.prompts.models import Message
from pydantic import BaseModel, ConfigDict, Field

from analysis.event.adapters import GraphitiEventAnalysisLLM
from analysis.event.contracts import EventAnalysisInput
from analysis.event.graphiti import (
    GraphitiCandidateRetriever,
    GraphitiSignalFactProjector,
)
from analysis.event.module import EventAnalysisModule
from analysis.event.pipeline import EventAnalysisPipeline
from analysis.event.review import ControlledSignalReviewer
from analysis.event.store import EventAnalysisStore
from analysis.event.trigger import AnalysisSchedulingEventProjector
from ingestion.episcode.event.contracts import (
    EventCandidateDTO,
    EventSemanticDTO,
    HistoricalEvent,
)
from ingestion.episcode.event.graphiti import GraphitiEventProjector
from projection.runtime import GRAPHITI_GROUP_ID, create_graphiti, load_graphiti_config

CHAIN_NAME = "AI计算芯片产业链"
DEMO_NAMESPACE = "tidewise-ai-compute-event-analysis-demo/v1"


def _event_id(key: str) -> str:
    return f"EVT{uuid5(NAMESPACE_URL, f'urn:{DEMO_NAMESPACE}:{key}')}"


def events() -> tuple[HistoricalEvent, ...]:
    return (
        HistoricalEvent(
            id=_event_id("ai-server-order-visibility"),
            event=EventCandidateDTO(
                title="AI服务器订单能见度连续上升",
                summary=(
                    "AI服务器产业链节点披露未来两个季度的已确认订单覆盖度连续上升，"
                    "AI服务器与AI加速卡排产需求同步增加。"
                ),
                semantic=EventSemanticDTO(
                    actors=["AI服务器产业链节点"],
                    action="确认订单覆盖度连续上升",
                    objects=["AI服务器", "AI加速卡"],
                    stage="UPDATED",
                    jurisdictions=["全球"],
                    effective_at=datetime(2026, 8, 26, tzinfo=UTC),
                    time_precision="DAY",
                ),
                modality="FACT",
                occurred_at=datetime(2026, 8, 26, tzinfo=UTC),
                announced_at=datetime(2026, 8, 26, tzinfo=UTC),
            ),
        ),
        HistoricalEvent(
            id=_event_id("advanced-packaging-node-maintenance-v2"),
            event=EventCandidateDTO(
                title="先进封装产线集中检修导致短期有效产能下降",
                summary=(
                    "主要先进封装产线进入集中设备检修，预计未来六周有效产能和交付能力下降。"
                ),
                semantic=EventSemanticDTO(
                    actors=["先进封装产业链节点"],
                    action="开展集中设备检修",
                    objects=["先进封装", "有效产能", "交付能力"],
                    stage="IMPLEMENTED",
                    jurisdictions=["全球"],
                    effective_at=datetime(2026, 8, 25, tzinfo=UTC),
                    time_precision="DAY",
                ),
                modality="FACT",
                occurred_at=datetime(2026, 8, 25, tzinfo=UTC),
                announced_at=datetime(2026, 8, 25, tzinfo=UTC),
            ),
        ),
        HistoricalEvent(
            id=_event_id("accelerator-node-volume-delivery"),
            event=EventCandidateDTO(
                title="AI加速卡节点进入新一代产品量产交付阶段",
                summary=(
                    "主要AI芯片厂商宣布新一代AI加速卡完成客户验证并进入量产交付阶段，"
                    "未来一个季度供给量预计提高。"
                ),
                semantic=EventSemanticDTO(
                    actors=["AI加速卡产业链节点"],
                    action="启动新一代AI加速卡量产交付",
                    objects=["AI加速卡", "AI芯片"],
                    stage="IMPLEMENTED",
                    jurisdictions=["全球"],
                    effective_at=datetime(2026, 8, 26, tzinfo=UTC),
                    time_precision="DAY",
                ),
                modality="FACT",
                occurred_at=datetime(2026, 8, 26, tzinfo=UTC),
                announced_at=datetime(2026, 8, 26, tzinfo=UTC),
            ),
        ),
        HistoricalEvent(
            id=_event_id("ai-chip-export-control"),
            event=EventCandidateDTO(
                title="美国扩大先进AI芯片出口管制范围",
                summary=(
                    "美国政府宣布扩大先进AI芯片出口管制范围，并收紧部分AI加速卡对华供应许可。"
                ),
                semantic=EventSemanticDTO(
                    actors=["美国政府"],
                    action="扩大先进AI芯片出口管制",
                    objects=["AI芯片", "AI加速卡"],
                    stage="ANNOUNCED",
                    jurisdictions=["中国"],
                    effective_at=datetime(2026, 9, 1, tzinfo=UTC),
                    time_precision="DAY",
                ),
                modality="PLAN",
                occurred_at=datetime(2026, 8, 26, tzinfo=UTC),
                announced_at=datetime(2026, 8, 26, tzinfo=UTC),
            ),
        ),
    )


class NodeView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    node_uuid: str
    node_name: str
    trend: str = Field(pattern=r"^(WARMING|COOLING|DIVERGING|STABLE|INSUFFICIENT)$")
    horizon: str = Field(pattern=r"^(SHORT|MEDIUM|LONG|MULTI_HORIZON)$")
    rationale: str = Field(min_length=1, max_length=300)
    supporting_signal_fact_uuids: list[str]
    risks: list[str] = Field(max_length=2)


class ReasoningStep(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    step: int = Field(ge=1)
    from_item: str
    to_item: str
    mechanism: str
    supporting_signal_fact_uuids: list[str]


class ChainReasoningResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    conclusion: str = Field(min_length=1, max_length=200)
    chain_outlook: str = Field(
        pattern=r"^(WARMING|COOLING|DIVERGING|STABLE|INSUFFICIENT)$"
    )
    node_views: list[NodeView]
    reasoning_tree: list[ReasoningStep]
    limitations: list[str]


class CompactNodeView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    node_key: str = Field(pattern=r"^N[1-9][0-9]*$")
    trend: str = Field(pattern=r"^(WARMING|COOLING|DIVERGING|STABLE|INSUFFICIENT)$")
    horizon: str = Field(pattern=r"^(SHORT|MEDIUM|LONG|MULTI_HORIZON)$")
    rationale: str = Field(min_length=1, max_length=1000)
    supporting_signal_keys: list[str]
    risks: list[str]


class CompactReasoningStep(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    step: int = Field(ge=1)
    from_item: str
    to_item: str
    mechanism: str
    supporting_signal_keys: list[str]


class CompactChainReasoningResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    conclusion: str = Field(min_length=1, max_length=500)
    chain_outlook: str = Field(
        pattern=r"^(WARMING|COOLING|DIVERGING|STABLE|INSUFFICIENT)$"
    )
    node_views: list[CompactNodeView]
    reasoning_tree: list[CompactReasoningStep] = Field(max_length=8)
    limitations: list[str] = Field(max_length=3)


async def _chain_context(graphiti, event_ids: list[str]) -> dict[str, Any]:
    as_of = datetime.now(UTC)
    records, _, _ = await graphiti.driver.execute_query(
        """
        /* ai_compute_demo_chain_context */
        MATCH (chain:IndustryChain {group_id: $group_id, name: $chain_name})
        MATCH (node:ChainNode)-[membership:RELATES_TO]->(chain)
        WHERE membership.name = 'ChainNodeBelongsToIndustryChain'
        OPTIONAL MATCH (variable:Variable)-[signal:RELATES_TO]->(node)
        WHERE signal.name = 'SIGNAL_ON'
          AND any(event_id IN coalesce(signal.source_event_ids, []) WHERE event_id IN $event_ids)
          AND signal.valid_at <= $as_of
          AND (signal.invalid_at IS NULL OR signal.invalid_at > $as_of)
          AND signal.expired_at IS NULL
        WITH chain, node, membership, collect(CASE WHEN signal IS NULL THEN NULL ELSE {
            uuid: signal.uuid,
            fact: signal.fact,
            variable_id: signal.variable_id,
            direction: signal.direction,
            magnitude: signal.magnitude,
            valid_at: toString(signal.valid_at),
            expected_end_latest: signal.expected_end_latest,
            mechanism: signal.mechanism
        } END) AS raw_signals
        RETURN chain.uuid AS chain_uuid, chain.data_object_id AS chain_id,
               chain.name AS chain_name, node.uuid AS node_uuid,
               node.data_object_id AS node_id, node.name AS node_name,
               membership.contextual_stage AS stage,
               [item IN raw_signals WHERE item IS NOT NULL] AS signals
        ORDER BY stage, node.name
        """,
        group_id=GRAPHITI_GROUP_ID,
        chain_name=CHAIN_NAME,
        event_ids=event_ids,
        as_of=as_of,
        routing_="r",
    )
    if not records:
        raise RuntimeError(f"missing graph chain: {CHAIN_NAME}")
    node_uuids = [str(row["node_uuid"]) for row in records]
    topology, _, _ = await graphiti.driver.execute_query(
        """
        /* ai_compute_demo_topology */
        MATCH (source:ChainNode)-[relation:RELATES_TO]->(target:ChainNode)
        WHERE source.uuid IN $node_uuids AND target.uuid IN $node_uuids
          AND relation.name IN ['ChainNodeInputTo', 'ChainNodeIsComponentOf', 'ChainNodeDependsOn']
        RETURN source.uuid AS source_uuid, source.name AS source_name,
               relation.name AS relation, relation.fact AS fact,
               target.uuid AS target_uuid, target.name AS target_name
        ORDER BY source.name, target.name
        """,
        node_uuids=node_uuids,
        routing_="r",
    )
    chain_signals, _, _ = await graphiti.driver.execute_query(
        """
        /* ai_compute_demo_active_chain_signals */
        MATCH (variable:Variable)-[signal:RELATES_TO]->(chain:IndustryChain {
            uuid: $chain_uuid, group_id: $group_id
        })
        WHERE signal.name = 'SIGNAL_ON'
          AND any(event_id IN coalesce(signal.source_event_ids, []) WHERE event_id IN $event_ids)
          AND signal.valid_at <= $as_of
          AND (signal.invalid_at IS NULL OR signal.invalid_at > $as_of)
          AND signal.expired_at IS NULL
        RETURN signal.uuid AS uuid, signal.fact AS fact,
               signal.variable_id AS variable_id, signal.direction AS direction,
               signal.magnitude AS magnitude, toString(signal.valid_at) AS valid_at,
               signal.expected_end_latest AS expected_end_latest,
               signal.mechanism AS mechanism
        ORDER BY signal.uuid
        """,
        chain_uuid=str(records[0]["chain_uuid"]),
        group_id=GRAPHITI_GROUP_ID,
        event_ids=event_ids,
        as_of=as_of,
        routing_="r",
    )
    return {
        "chain": {
            "uuid": str(records[0]["chain_uuid"]),
            "id": str(records[0]["chain_id"]),
            "name": str(records[0]["chain_name"]),
        },
        "nodes": [dict(row) for row in records],
        "topology": [dict(row) for row in topology],
        "chain_signals": [dict(row) for row in chain_signals],
        "as_of": as_of.isoformat(),
    }


async def _reason(graphiti, context: dict[str, Any]) -> ChainReasoningResult:
    nodes = list(context["nodes"])
    node_keys = {
        str(node["node_uuid"]): f"N{index}" for index, node in enumerate(nodes, 1)
    }
    node_by_key = {node_keys[str(node["node_uuid"])]: node for node in nodes}
    signal_uuids: dict[str, str] = {}
    compact_chain_signals = []
    for signal in context.get("chain_signals", []):
        signal_key = f"S{len(signal_uuids) + 1}"
        signal_uuids[signal_key] = str(signal["uuid"])
        compact_chain_signals.append(
            {
                "key": signal_key,
                "variable": signal["variable_id"],
                "direction": signal["direction"],
                "magnitude": signal["magnitude"],
                "fact": signal["fact"],
                "mechanism": str(signal["mechanism"])[:240],
                "expected_end": signal["expected_end_latest"],
            }
        )
    compact_nodes = []
    for node in nodes:
        compact_signals = []
        for signal in node["signals"]:
            signal_key = f"S{len(signal_uuids) + 1}"
            signal_uuids[signal_key] = str(signal["uuid"])
            compact_signals.append(
                {
                    "key": signal_key,
                    "variable": signal["variable_id"],
                    "direction": signal["direction"],
                    "magnitude": signal["magnitude"],
                    "fact": signal["fact"],
                    "mechanism": str(signal["mechanism"])[:240],
                    "expected_end": signal["expected_end_latest"],
                }
            )
        compact_nodes.append(
            {
                "key": node_keys[str(node["node_uuid"])],
                "name": node["node_name"],
                "stage": node["stage"],
                "signals": compact_signals,
            }
        )
    compact_context = {
        "chain": context["chain"]["name"],
        "chain_signals": compact_chain_signals,
        "nodes": compact_nodes,
        "topology": [
            {
                "from": node_keys[str(edge["source_uuid"])],
                "relation": edge["relation"],
                "to": node_keys[str(edge["target_uuid"])],
                "fact": edge["fact"],
            }
            for edge in context["topology"]
        ],
    }
    messages = [
        Message(
            role="system",
            content=(
                "Act as a cautious qualitative investment-research analyst. Analyze the supplied "
                "AI-compute IndustryChain using only its active direct Signal Facts and supplied "
                "topology. Determine whether the chain and every listed node are warming, cooling, "
                "diverging, stable, or insufficient. You may propagate effects only along a supplied "
                "topology edge and must state the business mechanism. Do not infer company or security "
                "results, prices, valuation, or facts absent from context. Signal direction describes "
                "its named Variable and is not positive/negative investment polarity. A topology edge "
                "shows structural reachability, not an automatic causal effect. Never translate "
                "export_control_exposure UP into demand DOWN, or into an upstream node cooling, without "
                "an explicit supplied bridge fact. Do not change Variable dimensions during propagation "
                "without such a bridge; mark the node INSUFFICIENT instead. Every non-insufficient node "
                "view and reasoning step must cite supplied Signal keys. Return one concise "
                "Chinese conclusion and an auditable structured reasoning tree. Return one JSON "
                "object with exactly conclusion, chain_outlook, node_views, reasoning_tree and "
                "limitations. chain_outlook and each node trend use WARMING|COOLING|DIVERGING|"
                "STABLE|INSUFFICIENT. Each node_view has node_key, trend, horizon "
                "(SHORT|MEDIUM|LONG|MULTI_HORIZON), rationale, supporting_signal_keys, risks. "
                "Each reasoning_tree item has step, from_item, to_item, mechanism and "
                "supporting_signal_keys. Use only supplied N/S keys and return every node exactly once. "
                "Keep conclusion within 120 Chinese characters, each rationale within 80 Chinese "
                "characters, at most two risks per node, at most eight reasoning steps and at most "
                "three limitations. Return compact JSON without Markdown or extra prose."
            ),
        ),
        Message(
            role="user",
            content=json.dumps(
                compact_context, ensure_ascii=False, sort_keys=True, default=str
            ),
        ),
    ]
    result = await graphiti.clients.llm_client.generate_response(
        messages,
        max_tokens=16000,
        group_id=GRAPHITI_GROUP_ID,
        prompt_name="tidewise_ai_compute_chain_demo_reasoning_v1",
    )
    compact = CompactChainReasoningResult.model_validate(result)
    if {item.node_key for item in compact.node_views} != set(node_by_key):
        raise RuntimeError("reasoning result must cover every supplied ChainNode exactly once")

    def resolved_signals(keys: list[str]) -> list[str]:
        try:
            return [signal_uuids[key] for key in keys]
        except KeyError as exc:
            raise RuntimeError("reasoning result references an unknown Signal key") from exc

    return ChainReasoningResult(
        conclusion=compact.conclusion,
        chain_outlook=compact.chain_outlook,
        node_views=[
            NodeView(
                node_uuid=str(node_by_key[item.node_key]["node_uuid"]),
                node_name=str(node_by_key[item.node_key]["node_name"]),
                trend=item.trend,
                horizon=item.horizon,
                rationale=item.rationale,
                supporting_signal_fact_uuids=resolved_signals(
                    item.supporting_signal_keys
                ),
                risks=item.risks,
            )
            for item in compact.node_views
        ],
        reasoning_tree=[
            ReasoningStep(
                step=item.step,
                from_item=item.from_item,
                to_item=item.to_item,
                mechanism=item.mechanism,
                supporting_signal_fact_uuids=resolved_signals(
                    item.supporting_signal_keys
                ),
            )
            for item in compact.reasoning_tree
        ],
        limitations=compact.limitations,
    )


async def run(output: Path) -> dict[str, object]:
    graphiti = create_graphiti(load_graphiti_config())
    try:
        analysis_llm = GraphitiEventAnalysisLLM(graphiti)
        pipeline = EventAnalysisPipeline(
            analysis_llm,
            GraphitiCandidateRetriever(graphiti),
            analysis_llm,
            ControlledSignalReviewer(),
            GraphitiSignalFactProjector(graphiti),
        )
        with tempfile.TemporaryDirectory(prefix="tidewise-event-analysis-") as directory:
            module = EventAnalysisModule(
                EventAnalysisStore(Path(directory) / "state.sqlite3"),
                pipeline,
                retry_delay_seconds=1,
            )
            projector = AnalysisSchedulingEventProjector(
                GraphitiEventProjector(graphiti), module
            )
            accepted = []
            for event in events():
                episode_uuid = await projector.project(event)
                accepted.append(
                    module.enqueue(
                        EventAnalysisInput(
                            event=event,
                            episode_uuid=episode_uuid,
                            reference_time=datetime.now(UTC),
                        )
                    )
                )
            terminal = {
                "SUCCEEDED",
                "NO_SIGNAL",
                "NO_SUPPORTED_ANCHOR",
                "NEEDS_REVIEW",
                "FAILED",
            }
            for _ in range(30):
                await module.process_pending(limit=10)
                current = [module.get_status(item.analysis_id) for item in accepted]
                if all(item is not None and item.status in terminal for item in current):
                    break
                await asyncio.sleep(1)
            else:
                raise RuntimeError("Event Analysis demo did not reach terminal states")
            statuses = []
            for acceptance in accepted:
                status = module.get_status(acceptance.analysis_id)
                statuses.append(status.model_dump(mode="json") if status else None)

        context = await _chain_context(graphiti, [event.id for event in events()])
        payload: dict[str, object] = {
            "demo_namespace": DEMO_NAMESPACE,
            "generated_at": datetime.now(UTC).isoformat(),
            "events": [event.model_dump(mode="json") for event in events()],
            "analysis_statuses": statuses,
            "reasoning_context": context,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        reasoning = await _reason(graphiti, context)
        payload["reasoning_result"] = reasoning.model_dump(mode="json")
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        return payload
    finally:
        await graphiti.close()


async def run_reasoning_only(output: Path) -> dict[str, object]:
    """Re-evaluate an already projected demo Signal set without replaying Events."""

    graphiti = create_graphiti(load_graphiti_config())
    try:
        demo_events = events()
        event_ids = [event.id for event in demo_events]
        context = await _chain_context(graphiti, event_ids)
        rows, _, _ = await graphiti.driver.execute_query(
            """
            /* ai_compute_demo_signal_summary */
            MATCH ()-[signal:RELATES_TO]->()
            WHERE signal.name = 'SIGNAL_ON'
              AND any(event_id IN coalesce(signal.source_event_ids, [])
                      WHERE event_id IN $event_ids)
              AND signal.valid_at <= $as_of
              AND (signal.invalid_at IS NULL OR signal.invalid_at > $as_of)
              AND signal.expired_at IS NULL
            RETURN signal.uuid AS uuid, signal.source_event_ids AS source_event_ids
            """,
            event_ids=event_ids,
            as_of=datetime.now(UTC),
            routing_="r",
        )
        signal_ids_by_event = {event_id: [] for event_id in event_ids}
        for row in rows:
            for event_id in row["source_event_ids"]:
                if event_id in signal_ids_by_event:
                    signal_ids_by_event[event_id].append(str(row["uuid"]))
        reasoning = await _reason(graphiti, context)
        payload: dict[str, object] = {
            "demo_namespace": DEMO_NAMESPACE,
            "mode": "REASON_ONLY",
            "generated_at": datetime.now(UTC).isoformat(),
            "events": [event.model_dump(mode="json") for event in demo_events],
            "graph_signal_summary": [
                {
                    "event_id": event.id,
                    "event_title": event.event.title,
                    "signal_fact_uuids": sorted(signal_ids_by_event[event.id]),
                }
                for event in demo_events
            ],
            "reasoning_context": context,
            "reasoning_result": reasoning.model_dump(mode="json"),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        return payload
    finally:
        await graphiti.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".runtime/ai-compute-event-analysis-demo.json"),
    )
    parser.add_argument(
        "--reason-only",
        action="store_true",
        help="Reuse existing demo Signal Facts and only rerun chain reasoning.",
    )
    args = parser.parse_args()
    payload = asyncio.run(
        run_reasoning_only(args.output) if args.reason_only else run(args.output)
    )
    if "analysis_statuses" in payload:
        print(json.dumps(payload["analysis_statuses"], ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload["graph_signal_summary"], ensure_ascii=False, indent=2))
    print(json.dumps(payload["reasoning_result"], ensure_ascii=False, indent=2))
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
