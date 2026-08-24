from __future__ import annotations

import unittest
from datetime import UTC, datetime

from projection.industry import DataIndustryDTO, IndustryFacts, build_plan
from projection.runtime import ProjectionError


NOW = datetime(2026, 8, 24, tzinfo=UTC)
ROOT_ID = "IND11111111-1111-4111-8111-111111111111"
CHILD_ID = "IND22222222-2222-4222-8222-222222222222"


def industry(
    *,
    identifier: str,
    name: str,
    code: str,
    parent_id: str | None,
    path: list[str],
) -> DataIndustryDTO:
    return DataIndustryDTO(
        id=identifier,
        name=name,
        aliases=[],
        classification_system="sw",
        industry_code=code,
        parent_industry_id=parent_id,
        hierarchy_path_codes=path,
        definition=f"{name}的正式定义",
        review_status="approved",
        created_at=NOW,
        updated_at=NOW,
    )


def valid_facts() -> IndustryFacts:
    return IndustryFacts(
        industries=(
            industry(
                identifier=ROOT_ID,
                name="计算机",
                code="710000",
                parent_id=None,
                path=["710000"],
            ),
            industry(
                identifier=CHILD_ID,
                name="软件开发",
                code="710101",
                parent_id=ROOT_ID,
                path=["710000", "710101"],
            ),
        )
    )


class IndustryProjectionTest(unittest.TestCase):
    def test_plan_preserves_industry_hierarchy(self) -> None:
        plan = build_plan(valid_facts())

        self.assertEqual(plan.industry_count, 2)
        self.assertEqual(plan.parent_relation_count, 1)
        self.assertEqual([node.labels for node in plan.nodes], [["Industry"], ["Industry"]])
        self.assertEqual(plan.edges[0].name, "IndustryHasParent")
        self.assertEqual(plan.edges[0].source_node_uuid, plan.nodes[1].uuid)
        self.assertEqual(plan.edges[0].target_node_uuid, plan.nodes[0].uuid)

    def test_missing_parent_fails_complete_preflight(self) -> None:
        orphan = industry(
            identifier=CHILD_ID,
            name="软件开发",
            code="710101",
            parent_id="IND33333333-3333-4333-8333-333333333333",
            path=["710000", "710101"],
        )

        with self.assertRaisesRegex(ProjectionError, "missing parent"):
            build_plan(IndustryFacts(industries=(orphan,)))

    def test_parent_must_equal_immediate_hierarchy_path(self) -> None:
        child = industry(
            identifier=CHILD_ID,
            name="软件开发",
            code="710101",
            parent_id=ROOT_ID,
            path=["999999", "710101"],
        )

        with self.assertRaisesRegex(ProjectionError, "does not match hierarchy path"):
            build_plan(IndustryFacts(industries=(valid_facts().industries[0], child)))


if __name__ == "__main__":
    unittest.main()
