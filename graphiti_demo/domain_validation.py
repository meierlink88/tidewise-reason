from __future__ import annotations

from typing import Any

from contracts import GraphFact
from demo_data import EVIDENCE_EPISODE_UUIDS, EXPECTED_SIGNAL_TARGETS


def validate_domain_facts(graph_facts: list[GraphFact]) -> list[dict[str, Any]]:
    """Surface extraction anomalies for review without deciding signal direction."""
    issues: list[dict[str, Any]] = []
    for evidence_id, expected_targets in EXPECTED_SIGNAL_TARGETS.items():
        episode_uuid = EVIDENCE_EPISODE_UUIDS[evidence_id]
        signals = {
            row.target
            for row in graph_facts
            if row.relation.lower() == "producessignal"
            and episode_uuid in row.episodes
            and "VariableSignal" in row.target_labels
        }
        actual_targets = {
            row.target
            for row in graph_facts
            if row.source in signals
            and row.relation.lower() == "appliesto"
            and "ChainNode" in row.target_labels
        }
        if actual_targets != expected_targets:
            issues.append(
                {
                    "type": "signal_target_alignment",
                    "evidence_id": evidence_id,
                    "signals": sorted(signals),
                    "expected_chain_node_targets": sorted(expected_targets),
                    "actual_chain_node_targets": sorted(actual_targets),
                    "instruction": (
                        "Use the versioned domain target mapping for endpoint repair only."
                    ),
                }
            )
    invalidated_signals: set[tuple[str, str]] = set()
    for row in graph_facts:
        signal = None
        if "VariableSignal" in row.source_labels:
            signal = row.source
        elif "VariableSignal" in row.target_labels:
            signal = row.target
        if signal and row.invalid_at is not None:
            key = (signal, row.invalid_at.isoformat())
            if key in invalidated_signals:
                continue
            invalidated_signals.add(key)
            issues.append(
                {
                    "type": "automatic_signal_invalidation_review",
                    "signal": signal,
                    "invalid_at": row.invalid_at.isoformat(),
                    "episodes": row.episodes,
                    "instruction": (
                        "Retain the source Evidence and aggregate concurrent signals until a "
                        "domain policy explicitly accepts invalidation."
                    ),
                }
            )
    return issues
