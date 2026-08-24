from __future__ import annotations

import unittest
from datetime import UTC, datetime

from projection.authoritative_writer import node_uuid
from projection.concept import ConceptFacts, DataConceptDTO, build_plan
from projection.runtime import ProjectionError


NOW = datetime(2026, 8, 24, tzinfo=UTC)
CONCEPT_ID = "CON11111111-1111-4111-8111-111111111111"


def concept(*, identifier: str = CONCEPT_ID, name: str = "人工智能") -> DataConceptDTO:
    return DataConceptDTO(
        id=identifier,
        name=name,
        aliases=["AI"],
        concept_type="technology",
        definition="跨行业人工智能投研概念",
        review_status="approved",
        created_at=NOW,
        updated_at=NOW,
    )


class ConceptProjectionTest(unittest.TestCase):
    def test_plan_contains_only_concept_nodes_and_no_relations(self) -> None:
        plan = build_plan(ConceptFacts(concepts=(concept(),)))

        self.assertEqual(plan.concept_count, 1)
        self.assertEqual(plan.nodes[0].labels, ["Concept"])
        self.assertEqual(plan.nodes[0].attributes["concept_type"], "technology")
        self.assertEqual(plan.nodes[0].uuid, node_uuid(CONCEPT_ID))

    def test_duplicate_concept_id_fails_preflight(self) -> None:
        facts = ConceptFacts(concepts=(concept(), concept(name="AI产业")))

        with self.assertRaisesRegex(ProjectionError, "duplicate Concept ID"):
            build_plan(facts)


if __name__ == "__main__":
    unittest.main()
