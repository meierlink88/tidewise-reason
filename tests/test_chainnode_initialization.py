from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime

from initialization.chainnode.projection import (
    ChainNodeFacts,
    DataChainNodeDTO,
    DataGraphEdgeDTO,
    DataMembershipDTO,
    build_plan,
    parse_snapshot,
)
from projection.runtime import ProjectionError


NOW = datetime(2026, 8, 24, tzinfo=UTC)
CHAIN_ID = "ICH11111111-1111-4111-8111-111111111111"
SOURCE_ID = "CND22222222-2222-4222-8222-222222222222"
TARGET_ID = "CND33333333-3333-4333-8333-333333333333"
EDGE_IDS = (
    "IGE44444444-4444-4444-8444-444444444444",
    "IGE55555555-5555-4555-8555-555555555555",
    "IGE66666666-6666-4666-8666-666666666666",
)


def node(identifier: str, name: str) -> DataChainNodeDTO:
    return DataChainNodeDTO(
        id=identifier,
        name=name,
        aliases=[],
        definition=f"{name}定义",
        review_status="approved",
        created_at=NOW,
        updated_at=NOW,
    )


def membership(identifier: str, name: str, position: int) -> DataMembershipDTO:
    return DataMembershipDTO(
        industry_chain_id=CHAIN_ID,
        industry_chain_name="AI算力产业链",
        chain_node_id=identifier,
        chain_node_name=name,
        position=position,
        contextual_stage="upstream" if position == 1 else "midstream",
    )


def graph_edge(identifier: str, relation_type: str) -> DataGraphEdgeDTO:
    return DataGraphEdgeDTO(
        id=identifier,
        industry_chain_id=CHAIN_ID,
        industry_chain_name="AI算力产业链",
        from_chain_node_id=SOURCE_ID,
        from_node_name="AI芯片",
        to_chain_node_id=TARGET_ID,
        to_node_name="AI服务器",
        relation_type=relation_type,
    )


def valid_facts() -> ChainNodeFacts:
    return ChainNodeFacts(
        chain_nodes=(node(SOURCE_ID, "AI芯片"), node(TARGET_ID, "AI服务器")),
        memberships=(
            membership(SOURCE_ID, "AI芯片", 1),
            membership(TARGET_ID, "AI服务器", 2),
        ),
        graph_edges=(
            graph_edge(EDGE_IDS[0], "input_to"),
            graph_edge(EDGE_IDS[1], "is_component_of"),
            graph_edge(EDGE_IDS[2], "depends_on"),
        ),
    )


class ChainNodeInitializationTest(unittest.TestCase):
    def test_plan_keeps_only_minimal_membership_and_topology_attributes(self) -> None:
        plan = build_plan(valid_facts())

        self.assertEqual(plan.chain_node_count, 2)
        self.assertEqual(plan.membership_count, 2)
        self.assertEqual(len(plan.edges), 5)
        membership_edges = [
            edge for edge in plan.edges if edge.name == "ChainNodeBelongsToIndustryChain"
        ]
        self.assertEqual(
            {frozenset(edge.attributes) for edge in membership_edges},
            {frozenset({"position", "contextual_stage"})},
        )
        topology_edges = [edge for edge in plan.edges if edge not in membership_edges]
        self.assertEqual(
            {edge.name for edge in topology_edges},
            {"ChainNodeInputTo", "ChainNodeIsComponentOf", "ChainNodeDependsOn"},
        )
        self.assertEqual(
            {frozenset(edge.attributes) for edge in topology_edges},
            {frozenset({"data_object_id", "industry_chain_id"})},
        )

    def test_topology_endpoint_must_be_a_member_of_the_same_chain(self) -> None:
        facts = valid_facts().model_copy(
            update={"memberships": (membership(SOURCE_ID, "AI芯片", 1),)}
        )

        with self.assertRaisesRegex(ProjectionError, "lacks membership"):
            build_plan(facts)

    def test_snapshot_rejects_fields_outside_the_minimal_contract(self) -> None:
        payload = membership(SOURCE_ID, "AI芯片", 1).model_dump(mode="json")
        payload["status"] = "active"
        line = json.dumps({"kind": "membership", "payload": payload})

        with self.assertRaisesRegex(ProjectionError, "invalid ChainNode snapshot record"):
            parse_snapshot([line])


if __name__ == "__main__":
    unittest.main()
