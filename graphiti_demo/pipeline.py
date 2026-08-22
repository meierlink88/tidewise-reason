from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import ValidationError

from analysis_models import AnalysisArtifact, AnalysisPayload
from artifact_store import ArtifactStore
from contracts import AnalysisModel, EvidenceSource, GraphMemory, GraphState
from demo_data import (
    AS_OF,
    CHAIN,
    EVIDENCE_EPISODE_UUIDS,
    EVIDENCE_IDS,
    EVIDENCE_PUBLISHED_FROM,
    QUESTION,
    TOPOLOGY_EPISODE_UUID,
)
from domain_validation import validate_domain_facts
from models import ontology_catalog
from runtime import DemoError, ErrorCode


RETRIEVAL_QUERIES = [
    "AI数据中心液冷服务器产业链的全部节点和上下游组成关系",
    "未来12个月算力基础设施扩张对AI芯片、液冷服务器和数据中心的影响",
    "液冷渗透率对服务器冷板、液冷服务器和液冷系统的影响",
    "OpenAI数据中心项目融资担保收缩带来的反向风险",
]


def context_run_id(context_without_id: dict[str, Any]) -> str:
    encoded = json.dumps(
        context_without_id,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


class ReasoningDemoPipeline:
    """Orchestrate the provider-neutral Evidence -> Context -> Analysis workflow."""

    def __init__(
        self,
        *,
        evidence_source: EvidenceSource,
        graph_memory: GraphMemory,
        analysis_model: AnalysisModel,
        artifacts: ArtifactStore | None = None,
    ) -> None:
        self._evidence_source = evidence_source
        self._graph = graph_memory
        self._analysis_model = analysis_model
        self._artifacts = artifacts or ArtifactStore()

    async def evidence_smoke(self) -> dict[str, Any]:
        records = await self._evidence_source.load(
            EVIDENCE_IDS,
            published_from=EVIDENCE_PUBLISHED_FROM,
            published_to=AS_OF,
        )
        return {
            "status": "PASS",
            "contract": "data.v1.listAdminEvidence",
            "evidence_ids": [record.evidence_id for record in records],
        }

    async def seed(self, reset: bool) -> dict[str, Any]:
        # Complete the read-only cross-service call before mutating the dedicated graph.
        records = await self._evidence_source.load(
            EVIDENCE_IDS,
            published_from=EVIDENCE_PUBLISHED_FROM,
            published_to=AS_OF,
        )
        result = await self._graph.rebuild(records, reset_all=reset)
        self._artifacts.clear_all()
        return {
            "question": QUESTION,
            **result.model_dump(mode="json"),
        }

    async def retrieve(self) -> dict[str, Any]:
        snapshot = await self._graph.retrieve(RETRIEVAL_QUERIES)
        state = snapshot.graph_state
        context_core = {
            "question": QUESTION,
            "as_of": AS_OF.isoformat(),
            "horizon": "12 months",
            "anchor": CHAIN["name"],
            "required_nodes": [node["name"] for node in CHAIN["nodes"]],
            "episode_uuids": state.episode_uuids,
            "graph_fingerprint": state.fingerprint,
            "ontology_schema": ontology_catalog(),
            "retrieval_queries": RETRIEVAL_QUERIES,
            "hybrid_search_facts": [
                item.model_dump(mode="json") for item in snapshot.hybrid_search_facts
            ],
            "graph_facts": [item.model_dump(mode="json") for item in state.graph_facts],
            "provenance_links": [
                item.model_dump(mode="json") for item in state.provenance_links
            ],
            "domain_validation": {
                "purpose": (
                    "Validate extracted endpoints and temporal conflicts without deciding direction."
                ),
                "issues": validate_domain_facts(state.graph_facts),
            },
        }
        context = {"run_id": context_run_id(context_core), **context_core}
        self._artifacts.write_context(context)
        return context

    async def analyze(self) -> dict[str, Any]:
        context = await self.retrieve()
        output_schema = json.dumps(AnalysisPayload.model_json_schema(), ensure_ascii=False)
        system = """
You are a cautious industry-chain analyst. Use only the supplied ontology_schema, graph-memory
facts, provenance_links and source Episode references. Analyze every required node for the declared
horizon. For each node, return conclusion as 看好, 风险 or 无明显影响; cite Evidence IDs,
Episode UUIDs, ResearchEvent UUIDs and VariableSignal UUIDs; give the full transmission path; list
counter-evidence and invalidation conditions; and give confidence from 0 to 1. Every cited Evidence
must correspond to a cited Event and Signal in provenance_links. Follow domain_validation for
endpoint repair and conflict handling, but never let it decide signal direction. Prefer underlying
Evidence over an unreviewed automatic invalidation. Return JSON with exactly these top-level keys:
as_of, horizon, nodes, summary.
        """.strip()
        raw_result = await self._analysis_model.generate_json(
            system=(
                system
                + "\n\nReturn one data instance matching this JSON Schema exactly; do not return "
                + "or describe the schema itself:\n"
                + output_schema
            ),
            context=context,
        )
        try:
            payload = AnalysisPayload.model_validate_json(raw_result)
        except ValidationError:
            self._artifacts.write_invalid_result(raw_result)
            raise DemoError(
                ErrorCode.ANALYSIS_INVALID,
                "model output does not match the AnalysisPayload contract",
            ) from None
        artifact = AnalysisArtifact(
            run_id=context["run_id"],
            question=QUESTION,
            payload=payload,
        )
        self._artifacts.write_result(artifact)
        return artifact.model_dump(mode="json")

    async def inspect(self) -> dict[str, Any]:
        return {"labels": await self._graph.inspect_labels()}

    async def verify(self) -> dict[str, Any]:
        context = self._artifacts.read_context()
        artifact = self._artifacts.read_result()
        state = await self._graph.state()
        context_core = {key: value for key, value in context.items() if key != "run_id"}
        current_run_id = context_run_id(context_core)
        if context.get("run_id") != current_run_id or artifact.run_id != current_run_id:
            raise DemoError(ErrorCode.ANALYSIS_INVALID, "analysis artifacts are stale")
        if context.get("graph_fingerprint") != state.fingerprint:
            raise DemoError(ErrorCode.ANALYSIS_INVALID, "analysis graph snapshot has changed")

        expected_nodes = {node["name"] for node in CHAIN["nodes"]}
        expected_episodes = {TOPOLOGY_EPISODE_UUID} | set(EVIDENCE_EPISODE_UUIDS.values())
        if context.get("question") != QUESTION or artifact.question != QUESTION:
            raise DemoError(ErrorCode.ANALYSIS_INVALID, "analysis question does not match the demo")
        if (
            context.get("anchor") != CHAIN["name"]
            or context.get("as_of") != AS_OF.isoformat()
            or context.get("horizon") != "12 months"
            or context.get("ontology_schema", {}).get("version") != "liquid-cooling-demo/v1"
        ):
            raise DemoError(ErrorCode.ANALYSIS_INVALID, "analysis context boundary is invalid")
        if set(context.get("episode_uuids", [])) != expected_episodes:
            raise DemoError(ErrorCode.ANALYSIS_INVALID, "context Episode provenance is incomplete")
        if set(artifact.payload.nodes) != expected_nodes:
            raise DemoError(ErrorCode.ANALYSIS_INVALID, "analysis result node coverage mismatch")
        if artifact.payload.as_of != AS_OF or artifact.payload.horizon != "12 months":
            raise DemoError(ErrorCode.ANALYSIS_INVALID, "analysis time boundary does not match the demo")

        provenance = state.provenance_links
        known_events = {item.event_uuid for item in provenance}
        known_signals = {item.signal_uuid for item in provenance}
        for node, conclusion in artifact.payload.nodes.items():
            evidence_ids = set(conclusion.evidence_ids)
            episode_ids = set(conclusion.episode_uuids)
            event_ids = set(conclusion.research_event_uuids)
            signal_ids = set(conclusion.variable_signal_uuids)
            if not evidence_ids.issubset(EVIDENCE_IDS):
                raise DemoError(ErrorCode.ANALYSIS_INVALID, f"{node} cites unknown Evidence")
            if not episode_ids.issubset(expected_episodes):
                raise DemoError(ErrorCode.ANALYSIS_INVALID, f"{node} cites stale Episode provenance")
            if not event_ids.issubset(known_events) or not signal_ids.issubset(known_signals):
                raise DemoError(ErrorCode.ANALYSIS_INVALID, f"{node} cites unknown Event or Signal")
            for evidence_id in evidence_ids:
                if EVIDENCE_EPISODE_UUIDS[evidence_id] not in episode_ids:
                    raise DemoError(
                        ErrorCode.ANALYSIS_INVALID,
                        f"{node} Evidence and Episode provenance do not correspond",
                    )
                if not any(
                    link.evidence_id == evidence_id
                    and link.event_uuid in event_ids
                    and link.signal_uuid in signal_ids
                    for link in provenance
                ):
                    raise DemoError(
                        ErrorCode.ANALYSIS_INVALID,
                        f"{node} Evidence/Event/Signal provenance is disconnected",
                    )
        self._verify_graph_contract(state, expected_nodes, expected_episodes)
        issue_types = sorted(
            {
                issue["type"]
                for issue in context.get("domain_validation", {}).get("issues", [])
            }
        )
        return {
            "status": "PASS",
            "run_id": current_run_id,
            "graph_fingerprint": state.fingerprint,
            "counts": state.counts,
            "result_nodes": sorted(expected_nodes),
            "domain_validation_issue_types": issue_types,
            "online_index_count": state.online_index_count,
        }

    @staticmethod
    def _verify_graph_contract(
        state: GraphState,
        expected_nodes: set[str],
        expected_episodes: set[str],
    ) -> None:
        expected_counts = {
            "chain_nodes": len(expected_nodes),
            "evidence": len(EVIDENCE_IDS),
            "events": len(EVIDENCE_IDS),
            "signals": len(EVIDENCE_IDS),
            "episodes": len(expected_episodes),
        }
        for key, value in expected_counts.items():
            if state.counts[key] != value:
                raise DemoError(
                    ErrorCode.GRAPH_STATE_INVALID,
                    f"expected {value} {key}, got {state.counts[key]}",
                )
        if set(state.episode_uuids) != expected_episodes:
            raise DemoError(ErrorCode.GRAPH_STATE_INVALID, "Episode identities are not deterministic")
        if set(state.chain_nodes) != expected_nodes:
            raise DemoError(ErrorCode.GRAPH_STATE_INVALID, "stable ChainNode identities are incomplete")
        if not state.provider_contract_ready:
            raise DemoError(ErrorCode.GRAPH_STATE_INVALID, "graph memory provider is not ready")
        linked_evidence = {item.evidence_id for item in state.provenance_links}
        if linked_evidence != set(EVIDENCE_IDS):
            raise DemoError(
                ErrorCode.GRAPH_STATE_INVALID,
                "Evidence/Event/Signal link sets are incomplete",
            )
