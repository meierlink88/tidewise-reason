from __future__ import annotations

import unittest
from collections import Counter
from unittest.mock import AsyncMock, patch

from initialization.macroeconomic.projection import (
    APPROVED_COUNTRY_CODES,
    EXPECTED_CATEGORY_COUNTS,
    DemoMacroEconomicCatalog,
    build_plan,
    demo_edge_uuid,
    demo_node_uuid,
    execute_plan,
    load_catalog,
    resolve_country_nodes,
    verify_state,
)
from projection.runtime import ProjectionError


class _Record:
    def __init__(self, value: dict[str, str]) -> None:
        self.value = value

    def data(self) -> dict[str, str]:
        return self.value


class _Result:
    def __init__(self, records: list[_Record]) -> None:
        self.records = records


class MacroEconomicDemoInitializationTest(unittest.IsolatedAsyncioTestCase):
    def test_packaged_catalog_builds_reviewed_policy_nodes(self) -> None:
        catalog = load_catalog()
        plan = build_plan(catalog)

        self.assertEqual(len(catalog.items), 78)
        self.assertEqual(len(plan.nodes), 78)
        self.assertEqual(plan.relation_count, 346)
        self.assertEqual(
            Counter(item.category for item in catalog.items),
            Counter(EXPECTED_CATEGORY_COUNTS),
        )
        self.assertEqual(
            {code for item in catalog.items for code in item.country_codes},
            APPROVED_COUNTRY_CODES,
        )
        rate_hike = next(item for item in catalog.items if item.policy_key == "RATE_HIKE")
        self.assertEqual(rate_hike.name, "加息")
        self.assertEqual(rate_hike.country_codes, ("CN", "US", "JP", "KR", "GB"))
        rate_hike_node = next(
            node for node in plan.nodes if node.attributes["policy_key"] == "RATE_HIKE"
        )
        self.assertEqual(rate_hike_node.uuid, demo_node_uuid("RATE_HIKE"))
        self.assertEqual(rate_hike_node.labels, ["MacroEconomic"])
        self.assertNotIn("data_object_id", rate_hike_node.attributes)

    def test_catalog_rejects_duplicate_policy_identity(self) -> None:
        catalog = load_catalog()
        values = catalog.model_dump(mode="json")
        values["items"][1]["policy_key"] = values["items"][0]["policy_key"]
        with self.assertRaisesRegex(ValueError, "重复 policy_key"):
            DemoMacroEconomicCatalog.model_validate(values)

    async def test_country_resolution_uses_only_existing_canonical_nodes(self) -> None:
        base = build_plan(load_catalog())
        graphiti = AsyncMock()
        graphiti.driver.execute_query.return_value = _Result(
            [
                _Record(
                    {
                        "uuid": f"uuid-{code}",
                        "data_object_id": f"COU-{code}",
                        "code": code,
                        "name": {
                            "CN": "中国",
                            "US": "美国",
                            "JP": "日本",
                            "KR": "韩国",
                            "GB": "英国",
                        }[code],
                    }
                )
                for code in sorted(APPROVED_COUNTRY_CODES)
            ]
        )

        plan = await resolve_country_nodes(graphiti, base)

        self.assertEqual(len(plan.countries), 5)
        self.assertEqual(len(plan.edges), 346)
        edge = next(
            item
            for item in plan.edges
            if item.uuid == demo_edge_uuid("CN", "RATE_HIKE")
        )
        self.assertEqual(edge.name, "IMPLEMENTS")
        self.assertEqual(edge.source_node_uuid, "uuid-CN")
        self.assertEqual(edge.target_node_uuid, demo_node_uuid("RATE_HIKE"))

    async def test_country_resolution_fails_closed_when_one_country_is_missing(self) -> None:
        base = build_plan(load_catalog())
        graphiti = AsyncMock()
        graphiti.driver.execute_query.return_value = _Result([])
        with self.assertRaisesRegex(ProjectionError, "缺少已批准国家"):
            await resolve_country_nodes(graphiti, base)

    async def test_execute_never_deletes_other_graph_data(self) -> None:
        base = build_plan(load_catalog())
        graphiti = AsyncMock()
        graphiti.driver.execute_query.return_value = _Result(
            [
                _Record(
                    {
                        "uuid": f"uuid-{code}",
                        "data_object_id": f"COU-{code}",
                        "code": code,
                        "name": code,
                    }
                )
                for code in sorted(APPROVED_COUNTRY_CODES)
            ]
        )
        plan = await resolve_country_nodes(graphiti, base)
        with patch(
            "initialization.macroeconomic.projection.write_projection",
            new=AsyncMock(return_value=(78, 346, {"nodes": 0, "relationships": 0})),
        ) as writer:
            result = await execute_plan(object(), plan)

        self.assertEqual(result, (78, 346, {"nodes": 0, "relationships": 0}))
        self.assertFalse(writer.await_args.kwargs["replace"])

    async def test_verification_checks_exact_catalog_state(self) -> None:
        base = build_plan(load_catalog())
        graphiti = AsyncMock()
        graphiti.driver.execute_query.return_value = _Result(
            [
                _Record(
                    {
                        "uuid": f"uuid-{code}",
                        "data_object_id": f"COU-{code}",
                        "code": code,
                        "name": code,
                    }
                )
                for code in sorted(APPROVED_COUNTRY_CODES)
            ]
        )
        plan = await resolve_country_nodes(graphiti, base)
        nodes = [
            {
                "uuid": node.uuid,
                "name": node.name,
                "summary": node.summary,
                **node.attributes,
                "data_object_id": None,
                "labels": ["Entity", "MacroEconomic"],
                "embedding_dimension": 1024,
            }
            for node in plan.base.nodes
        ]
        edges = [
            {
                "uuid": edge.uuid,
                "country_code": edge.fact.split("在其政策体系")[0],
                "policy_key": "unused",
                "name": edge.name,
                "fact": edge.fact,
                "embedding_dimension": 1024,
                **edge.attributes,
            }
            for edge in plan.edges
        ]

        self.assertTrue(verify_state(plan, {"nodes": nodes, "edges": edges})["verified"])
        with self.assertRaisesRegex(ProjectionError, "政策节点身份集"):
            verify_state(plan, {"nodes": nodes[:-1], "edges": edges})


if __name__ == "__main__":
    unittest.main()
