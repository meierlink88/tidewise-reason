from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime

from graphiti_core.nodes import EpisodeType

from ingestion.episcode.evidence.contracts import EvidenceDTO
from ingestion.episcode.evidence.converter import SOURCE_DESCRIPTION, to_raw_episode


EVIDENCE_ID = "EVD11111111-1111-4111-8111-111111111111"
RAW_EVIDENCE_ID = "RAW22222222-2222-4222-8222-222222222222"
PUBLISHED_AT = datetime(2026, 8, 25, 8, 30, tzinfo=UTC)
COLLECTED_AT = datetime(2026, 8, 25, 8, 35, tzinfo=UTC)


def evidence(*, published_at: datetime | None = PUBLISHED_AT) -> EvidenceDTO:
    return EvidenceDTO.model_validate(
        {
            "id": EVIDENCE_ID,
            "raw_evidence_id": RAW_EVIDENCE_ID,
            "title": "某国发布人工智能基础设施政策",
            "summary": "某国发布政策支持人工智能基础设施建设。",
            "semantic": {
                "who": "某国政府",
                "what": "发布人工智能基础设施支持政策",
                "when": "2026年8月25日",
                "where": "某国",
                "why": "提升人工智能产业竞争力",
                "how": "提供财政补贴和算力设施投资",
            },
            "categories": [
                {
                    "id": "EVC33333333-3333-4333-8333-333333333333",
                    "code": "ECONOMIC_POLICY",
                    "name": "经济政策",
                    "description": "国家或地区经济政策事实",
                }
            ],
            "source_id": "official-source",
            "source_name": "某国政府官网",
            "source_level": "L1_OFFICIAL",
            "source_url": "https://example.gov/policy/ai-infrastructure",
            "is_original": True,
            "quoted_source_name": None,
            "keywords": ["人工智能", "基础设施"],
            "is_split": True,
            "published_at": published_at,
            "collected_at": COLLECTED_AT,
        }
    )


class EvidenceEpisodeConverterTest(unittest.TestCase):
    def test_complete_evidence_becomes_one_json_episode(self) -> None:
        source = evidence()

        episode = to_raw_episode(source)

        self.assertEqual(episode.name, EVIDENCE_ID)
        self.assertIsNone(episode.uuid)
        self.assertEqual(episode.source, EpisodeType.json)
        self.assertEqual(episode.source_description, SOURCE_DESCRIPTION)
        self.assertEqual(episode.reference_time, PUBLISHED_AT)
        self.assertEqual(json.loads(episode.content), source.model_dump(mode="json"))

    def test_collection_time_is_used_when_publication_time_is_unknown(self) -> None:
        episode = to_raw_episode(evidence(published_at=None))

        self.assertEqual(episode.reference_time, COLLECTED_AT)


if __name__ == "__main__":
    unittest.main()
