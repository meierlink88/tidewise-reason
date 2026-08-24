from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from pydantic import ValidationError

from projection.country_region import (
    GROUP_ID,
    DataCountryDTO,
    DataRegionDTO,
    build_plan,
    execute_plan,
)
from projection.runtime import ProjectionError


REGION_ID = "REG11111111-1111-4111-8111-111111111111"


def region(*, name: str = "东亚") -> DataRegionDTO:
    return DataRegionDTO(
        id=REGION_ID,
        code="M49_030",
        name=name,
        name_en="Eastern Asia",
        region_type="GEOGRAPHIC",
    )


def country(identifier: str, code: str, name: str) -> DataCountryDTO:
    return DataCountryDTO(
        id=identifier,
        code=code,
        name=name,
        name_en=name,
        strategic_positioning="test positioning",
        key_resources="test resources",
        regions=[region()],
    )


class CountryRegionProjectionTest(unittest.TestCase):
    def test_plan_validates_and_deduplicates_shared_region(self) -> None:
        plan = build_plan(
            [
                country("COU11111111-1111-4111-8111-111111111111", "CN", "中国"),
                country("COU22222222-2222-4222-8222-222222222222", "JP", "日本"),
            ]
        )

        self.assertEqual(plan.country_count, 2)
        self.assertEqual(plan.region_count, 1)
        self.assertEqual(plan.relation_count, 2)
        self.assertEqual(plan.triplets[0].source.labels, ["Country"])
        self.assertEqual(plan.triplets[0].target.labels, ["Region"])
        self.assertEqual(plan.triplets[0].edge.name, "CountryInRegion")
        self.assertEqual(plan.triplets[0].source.group_id, GROUP_ID)
        self.assertEqual(
            plan.triplets[0].source.attributes["data_object_id"],
            "COU11111111-1111-4111-8111-111111111111",
        )

    def test_plan_uses_deterministic_node_and_edge_ids(self) -> None:
        facts = [country("COU11111111-1111-4111-8111-111111111111", "CN", "中国")]
        first = build_plan(facts).triplets[0]
        second = build_plan(facts).triplets[0]

        self.assertEqual(first.source.uuid, second.source.uuid)
        self.assertEqual(first.target.uuid, second.target.uuid)
        self.assertEqual(first.edge.uuid, second.edge.uuid)

    def test_conflicting_region_facts_fail_the_whole_preflight(self) -> None:
        first = country("COU11111111-1111-4111-8111-111111111111", "CN", "中国")
        second = country("COU22222222-2222-4222-8222-222222222222", "JP", "日本")
        second = second.model_copy(update={"regions": [region(name="另一个名称")]})

        with self.assertRaisesRegex(ProjectionError, "conflicting Region facts"):
            build_plan([first, second])

    def test_country_without_region_is_rejected_at_the_data_boundary(self) -> None:
        with self.assertRaises(ValidationError):
            DataCountryDTO(
                id="COU11111111-1111-4111-8111-111111111111",
                code="CN",
                name="中国",
                regions=[],
            )

    def test_same_name_country_and_region_keep_distinct_typed_ids(self) -> None:
        same_name_region = region(name="中非")
        same_name_country = country(
            "COU11111111-1111-4111-8111-111111111111", "CF", "中非"
        ).model_copy(update={"regions": [same_name_region]})
        triplet = build_plan([same_name_country]).triplets[0]

        self.assertNotEqual(triplet.source.uuid, triplet.target.uuid)
        self.assertEqual(triplet.source.labels, ["Country"])
        self.assertEqual(triplet.target.labels, ["Region"])
        self.assertNotEqual(
            triplet.source.attributes["data_object_id"],
            triplet.target.attributes["data_object_id"],
        )


class CountryRegionProjectionExecutionTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_preserves_relationship_creation_time_without_llm(self) -> None:
        plan = build_plan(
            [country("COU11111111-1111-4111-8111-111111111111", "CN", "中国")]
        )
        embedder = SimpleNamespace(
            create_batch=AsyncMock(
                side_effect=lambda values: [[float(index)] for index, _ in enumerate(values)]
            )
        )
        node_writer = SimpleNamespace(save_bulk=AsyncMock())
        edge_writer = SimpleNamespace(save_bulk=AsyncMock())
        driver = SimpleNamespace(execute_query=AsyncMock())
        graphiti = SimpleNamespace(
            embedder=embedder,
            nodes=SimpleNamespace(entity=node_writer),
            edges=SimpleNamespace(entity=edge_writer),
            driver=driver,
        )

        result = await execute_plan(graphiti, plan)

        self.assertEqual(result, (2, 1, {"nodes": 0, "relationships": 0}))
        node_writer.save_bulk.assert_awaited_once()
        edge_writer.save_bulk.assert_not_awaited()
        saved_nodes = node_writer.save_bulk.await_args.args[0]
        saved_edges = driver.execute_query.await_args.kwargs["entity_edges"]
        self.assertTrue(all(node.name_embedding is not None for node in saved_nodes))
        self.assertTrue(all(edge["fact_embedding"] is not None for edge in saved_edges))
        self.assertIn(
            "coalesce(e.created_at, edge.created_at)",
            driver.execute_query.await_args.args[0],
        )
        self.assertFalse(hasattr(graphiti, "llm_client"))


if __name__ == "__main__":
    unittest.main()
