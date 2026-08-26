from __future__ import annotations

import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

from initialization.geopolitic.projection import (
    DemoGeopoliticCatalog,
    DemoGeopoliticRivalry,
    build_plan,
    demo_node_uuid,
    execute_plan,
    load_catalog,
    verify_state,
)
from projection.runtime import ProjectionError


def item(**overrides) -> DemoGeopoliticRivalry:
    values = {
        "catalog_key": "china_us_competition",
        "name": "中美战略与科技竞争",
        "name_en": "China–United States Strategic and Technology Competition",
        "rivalry_type": "GEOPOLITICAL",
        "description": "长期战略与科技竞争。",
        "core_actors": "中国；美国",
        "peripheral_actors": None,
        "influenced_regions": ["东亚", "北美"],
        "status": "ACTIVE",
    }
    values.update(overrides)
    return DemoGeopoliticRivalry.model_validate(values)


def catalog(*items: DemoGeopoliticRivalry) -> DemoGeopoliticCatalog:
    return DemoGeopoliticCatalog(
        catalog_version="demo-geopolitic-rivalry/v1",
        published_at=datetime(2026, 8, 26, 12, tzinfo=UTC),
        items=items,
    )


class GeopoliticDemoInitializationTest(unittest.TestCase):
    def test_packaged_catalog_builds_nine_non_authoritative_nodes(self) -> None:
        plan = build_plan(load_catalog())

        self.assertEqual(len(plan.nodes), 9)
        self.assertEqual(plan.catalog_version, "demo-geopolitic-rivalry/v1")
        self.assertEqual(plan.nodes[0].labels, ["GeopoliticRivalry"])
        self.assertNotIn("data_object_id", plan.nodes[0].attributes)
        self.assertEqual(
            plan.nodes[0].uuid,
            demo_node_uuid("china_us_strategic_technology_competition"),
        )

    def test_catalog_rejects_duplicate_identity_and_non_active_rows(self) -> None:
        first = item()
        with self.assertRaisesRegex(ValidationError, "duplicate geopolitical catalog name"):
            catalog(first, item(catalog_key="another_key", name_en="Another name"))
        with self.assertRaisesRegex(ValidationError, "only ACTIVE"):
            catalog(item(status="DORMANT"))

    def test_catalog_rejects_duplicate_or_blank_regions(self) -> None:
        with self.assertRaises(ValidationError):
            item(influenced_regions=["东亚", "东亚"])
        with self.assertRaises(ValidationError):
            item(influenced_regions=[" "])

    def test_loader_rejects_a_catalog_other_than_the_approved_nine(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(catalog(item()).model_dump_json(), encoding="utf-8")
            with self.assertRaisesRegex(ProjectionError, "approved nine identities"):
                load_catalog(path)

    def test_verification_requires_exact_nodes_without_data_ids(self) -> None:
        plan = build_plan(catalog(item()))
        node = plan.nodes[0]
        valid = {
            "nodes": [
                {
                    "uuid": node.uuid,
                    "name": node.name,
                    "summary": node.summary,
                    **node.attributes,
                    "data_object_id": None,
                    "created_at_epoch_ms": int(node.created_at.timestamp() * 1000),
                    "labels": ["Entity", "GeopoliticRivalry"],
                    "embedding_dimension": 1024,
                    "relationship_count": 0,
                }
            ]
        }
        self.assertTrue(verify_state(plan, valid)["verified"])

        invalid = {"nodes": [{**valid["nodes"][0], "data_object_id": "GPR-invalid"}]}
        with self.assertRaisesRegex(ProjectionError, "claims a Data object ID"):
            verify_state(plan, invalid)

        related = {"nodes": [{**valid["nodes"][0], "relationship_count": 1}]}
        with self.assertRaisesRegex(ProjectionError, "must not create relationships"):
            verify_state(plan, related)

        corrupted = {"nodes": [{**valid["nodes"][0], "description": "corrupted"}]}
        with self.assertRaisesRegex(ProjectionError, "properties differ"):
            verify_state(plan, corrupted)

        wrong_time = {"nodes": [{**valid["nodes"][0], "created_at_epoch_ms": 0}]}
        with self.assertRaisesRegex(ProjectionError, "creation time differs"):
            verify_state(plan, wrong_time)


class GeopoliticDemoExecutionTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_is_node_only_and_never_replaces_graph_state(self) -> None:
        plan = build_plan(catalog(item()))
        with patch(
            "initialization.geopolitic.projection.write_projection",
            new=AsyncMock(return_value=(1, 0, {"nodes": 0, "relationships": 0})),
        ) as writer:
            result = await execute_plan(object(), plan)

        self.assertEqual(result, (1, 0, {"nodes": 0, "relationships": 0}))
        call = writer.await_args.kwargs
        self.assertEqual(call["edges"], ())
        self.assertFalse(call["replace"])


if __name__ == "__main__":
    unittest.main()
