from __future__ import annotations

import unittest
from collections import Counter
from unittest.mock import AsyncMock, patch

from initialization.variable.projection import (
    EXPECTED_GROUP_COUNTS,
    EXPECTED_VARIABLE_COUNT,
    FundamentalVariableCatalog,
    build_plan,
    execute_plan,
    load_catalog,
    variable_node_uuid,
    verify_state,
)
from projection.runtime import ProjectionError


class VariableCatalogInitializationTest(unittest.IsolatedAsyncioTestCase):
    def test_packaged_catalog_builds_only_fundamental_variable_nodes(self) -> None:
        catalog = load_catalog()
        plan = build_plan(catalog)

        self.assertEqual(len(catalog.items), EXPECTED_VARIABLE_COUNT)
        self.assertEqual(len(plan.nodes), EXPECTED_VARIABLE_COUNT)
        self.assertEqual(
            Counter(item.variable_group for item in catalog.items),
            Counter(EXPECTED_GROUP_COUNTS),
        )
        self.assertEqual({node.labels[0] for node in plan.nodes}, {"Variable"})
        self.assertEqual(
            {node.attributes["variable_role"] for node in plan.nodes},
            {"FUNDAMENTAL"},
        )
        self.assertNotIn(
            "INVESTMENT_ASSESSMENT",
            {node.attributes["variable_group"] for node in plan.nodes},
        )
        supply = next(
            node for node in plan.nodes if node.attributes["variable_id"] == "market_supply"
        )
        self.assertEqual(supply.name, "市场供给")
        self.assertEqual(supply.uuid, variable_node_uuid("market_supply"))
        exchange_rate = next(
            node
            for node in plan.nodes
            if node.attributes["variable_id"] == "exchange_rate_pressure"
        )
        self.assertEqual(exchange_rate.name, "本币贬值压力")
        self.assertIn("UP 表示贬值压力上升", exchange_rate.attributes["definition"])

    def test_catalog_rejects_ambiguous_aliases(self) -> None:
        values = load_catalog().model_dump(mode="json")
        values["items"][1]["aliases"][0] = values["items"][0]["name"]
        with self.assertRaisesRegex(ValueError, "同时指向"):
            FundamentalVariableCatalog.model_validate(values)

    def test_catalog_derivations_resolve_inside_the_same_version(self) -> None:
        plan = build_plan(load_catalog())
        variables = {node.attributes["variable_id"]: node for node in plan.nodes}

        self.assertEqual(
            variables["free_cash_flow"].attributes["derived_from_variable_ids"],
            ["operating_cash_flow", "capital_expenditure"],
        )
        self.assertEqual(
            variables["supply_chain_resilience"].attributes[
                "derived_from_variable_ids"
            ],
            ["supplier_concentration", "import_dependency", "chokepoint_exposure"],
        )

    async def test_execute_writes_nodes_only_and_never_replaces_graph_state(self) -> None:
        plan = build_plan(load_catalog())
        with patch(
            "initialization.variable.projection.write_projection",
            new=AsyncMock(
                return_value=(EXPECTED_VARIABLE_COUNT, 0, {"nodes": 0, "relationships": 0})
            ),
        ) as writer:
            result = await execute_plan(object(), plan)

        self.assertEqual(
            result,
            (EXPECTED_VARIABLE_COUNT, 0, {"nodes": 0, "relationships": 0}),
        )
        call = writer.await_args.kwargs
        self.assertEqual(call["edges"], ())
        self.assertFalse(call["replace"])

    def test_verification_requires_exact_isolated_nodes(self) -> None:
        plan = build_plan(load_catalog())
        nodes = [
            {
                "uuid": node.uuid,
                "name": node.name,
                "summary": node.summary,
                **node.attributes,
                "labels": ["Entity", "Variable"],
                "embedding_dimension": 1024,
                "relationship_count": 0,
                "signal_relationship_count": 0,
            }
            for node in plan.nodes
        ]

        result = verify_state(plan, {"nodes": nodes})
        self.assertTrue(result["verified"])
        self.assertEqual(result["catalog_relationship_total"], 0)
        self.assertEqual(result["signal_relationship_total"], 0)

        related = [dict(node) for node in nodes]
        related[0]["relationship_count"] = 1
        with self.assertRaisesRegex(ProjectionError, "只能具有"):
            verify_state(plan, {"nodes": related})

        signal_related = [dict(node) for node in nodes]
        signal_related[0]["relationship_count"] = 1
        signal_related[0]["signal_relationship_count"] = 1
        self.assertTrue(verify_state(plan, {"nodes": signal_related})["verified"])


if __name__ == "__main__":
    unittest.main()
