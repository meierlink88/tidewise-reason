"""Lossless conversion from published Evidence to Graphiti input."""

from __future__ import annotations

import json

from graphiti_core.nodes import EpisodeType
from graphiti_core.utils.bulk_utils import RawEpisode

from ingestion.episcode.evidence.contracts import EvidenceDTO


SOURCE_DESCRIPTION = (
    "经过清洗和原子化拆分的投研 Evidence，包含完整事实、5W1H 语义和来源信息。"
)


def canonical_evidence_json(evidence: EvidenceDTO) -> str:
    """Serialize the complete immutable Evidence with stable key ordering."""

    return json.dumps(
        evidence.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def to_raw_episode(evidence: EvidenceDTO) -> RawEpisode:
    """Build Graphiti's built-in JSON Episode input without leaking it to Agent OS."""

    return RawEpisode(
        name=evidence.id,
        uuid=None,
        content=canonical_evidence_json(evidence),
        source_description=SOURCE_DESCRIPTION,
        source=EpisodeType.json,
        reference_time=evidence.published_at or evidence.collected_at,
    )
