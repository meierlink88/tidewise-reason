from __future__ import annotations

import unittest
from datetime import UTC, date, datetime

from projection.industry_chain import (
    DataIndustryChainDTO,
    DataMappingDTO,
    DataResearchEntityDTO,
    IndustryChainFacts,
    build_plan,
)
from projection.runtime import ProjectionError


NOW = datetime(2026, 8, 24, tzinfo=UTC)
CHAIN_ID = "ICH11111111-1111-4111-8111-111111111111"
INDUSTRY_ID = "IND22222222-2222-4222-8222-222222222222"
CONCEPT_ID = "CON33333333-3333-4333-8333-333333333333"
COUNTRY_ID = "COU44444444-4444-4444-8444-444444444444"
INDUSTRY_LINK_ID = "ERL55555555-5555-4555-8555-555555555555"
CONCEPT_LINK_ID = "ERL66666666-6666-4666-8666-666666666666"


def chain() -> DataIndustryChainDTO:
    return DataIndustryChainDTO(
        id=CHAIN_ID,
        name="AI算力产业链",
        aliases=["人工智能算力产业链"],
        scope="芯片、服务器、数据中心到算力服务",
        target_output="AI算力",
        end_use="模型训练与推理",
        geography="china",
        primary_country_id=COUNTRY_ID,
        as_of_date=date(2026, 8, 24),
        review_status="approved",
        review_note="测试产业链",
        technology_route_qualifier="GPU集群",
        observable_variables=["交付量", "上架率"],
        created_at=NOW,
        updated_at=NOW,
    )


def entity(identifier: str, entity_type: str, name: str) -> DataResearchEntityDTO:
    return DataResearchEntityDTO(
        entity_id=identifier,
        entity_type=entity_type,
        name=name,
        canonical_name=name,
        aliases=[],
        status="active",
    )


def mapping(
    identifier: str,
    target_id: str,
    relation_type: str,
) -> DataMappingDTO:
    return DataMappingDTO(
        entity_relation_id=identifier,
        from_entity_id=CHAIN_ID,
        to_entity_id=target_id,
        relation_type=relation_type,
        status="active",
    )


def valid_facts() -> IndustryChainFacts:
    return IndustryChainFacts(
        industry_chains=(chain(),),
        entities=(
            entity(INDUSTRY_ID, "industry", "IT服务"),
            entity(CONCEPT_ID, "concept", "人工智能"),
        ),
        mappings=(
            mapping(INDUSTRY_LINK_ID, INDUSTRY_ID, "mapped_to_industry"),
            mapping(CONCEPT_LINK_ID, CONCEPT_ID, "mapped_to_concept"),
        ),
    )


class IndustryChainProjectionTest(unittest.TestCase):
    def test_plan_contains_chain_and_only_declared_mapping_relations(self) -> None:
        plan = build_plan(valid_facts())

        self.assertEqual(plan.industry_chain_count, 1)
        self.assertEqual(plan.industry_mapping_count, 1)
        self.assertEqual(plan.concept_mapping_count, 1)
        self.assertEqual(plan.nodes[0].labels, ["IndustryChain"])
        self.assertEqual(plan.nodes[0].attributes["primary_country_id"], COUNTRY_ID)
        self.assertEqual(
            {edge.name for edge in plan.edges},
            {"IndustryChainMappedToIndustry", "IndustryChainMappedToConcept"},
        )
        self.assertNotIn("IndustryChainPrimaryCountry", {edge.name for edge in plan.edges})
        self.assertEqual(
            {edge.attributes["data_object_id"] for edge in plan.edges},
            {INDUSTRY_LINK_ID, CONCEPT_LINK_ID},
        )

    def test_chain_without_industry_mapping_fails_preflight(self) -> None:
        facts = valid_facts().model_copy(
            update={"mappings": (mapping(CONCEPT_LINK_ID, CONCEPT_ID, "mapped_to_concept"),)}
        )

        with self.assertRaisesRegex(ProjectionError, "without mapped Industry"):
            build_plan(facts)

    def test_mapping_target_type_must_match_relation(self) -> None:
        facts = valid_facts().model_copy(
            update={
                "entities": (entity(INDUSTRY_ID, "concept", "IT服务"),),
                "mappings": (
                    mapping(INDUSTRY_LINK_ID, INDUSTRY_ID, "mapped_to_industry"),
                ),
            }
        )

        with self.assertRaisesRegex(ProjectionError, "target type is invalid"):
            build_plan(facts)


if __name__ == "__main__":
    unittest.main()
