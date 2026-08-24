from __future__ import annotations

import json
import unittest

from pydantic import BaseModel, ValidationError

from ontology import (
    EDGE_TYPE_MAP,
    EDGE_TYPES,
    ENTITY_TYPES,
    ONTOLOGY_VERSION,
    Country,
    IndustryChainContainsNode,
    ontology_catalog,
)


class OntologyContractTest(unittest.TestCase):
    def test_first_batch_registration_contract(self) -> None:
        self.assertEqual(
            list(ENTITY_TYPES),
            [
                "Country",
                "Region",
                "Organization",
                "Industry",
                "Concept",
                "IndustryChain",
                "ChainNode",
            ],
        )
        self.assertEqual(
            set(EDGE_TYPES),
            {
                "CountryInRegion",
                "CountryMemberOfOrganization",
                "OrganizationInRegion",
                "IndustryHasParent",
                "IndustryChainPrimaryCountry",
                "IndustryChainContainsNode",
                "IndustryChainMappedToIndustry",
                "IndustryChainMappedToConcept",
                "ChainNodeInputTo",
                "ChainNodeIsComponentOf",
                "ChainNodeDependsOn",
            },
        )
        self.assertEqual(
            EDGE_TYPE_MAP[("ChainNode", "ChainNode")],
            ["ChainNodeInputTo", "ChainNodeIsComponentOf", "ChainNodeDependsOn"],
        )
        self.assertEqual(
            EDGE_TYPE_MAP[("IndustryChain", "Industry")],
            ["IndustryChainMappedToIndustry"],
        )
        self.assertEqual(
            EDGE_TYPE_MAP[("IndustryChain", "Concept")],
            ["IndustryChainMappedToConcept"],
        )
        self.assertEqual(ONTOLOGY_VERSION, "evidence-curation/v1")

    def test_graphiti_models_are_pydantic_classes_without_protected_fields(self) -> None:
        protected = {
            "uuid",
            "name",
            "group_id",
            "labels",
            "created_at",
            "summary",
            "attributes",
            "name_embedding",
        }
        for model in [*ENTITY_TYPES.values(), *EDGE_TYPES.values()]:
            self.assertTrue(issubclass(model, BaseModel))
            self.assertTrue(model.__doc__ and model.__doc__.strip())
            self.assertFalse(protected.intersection(model.model_fields))
            for field in model.model_fields.values():
                self.assertTrue(field.description)

    def test_canonical_identity_is_validated_but_not_required_from_evidence(self) -> None:
        self.assertIsNone(Country().data_object_id)
        country = Country(
            data_object_id="COU11111111-1111-4111-8111-111111111111",
            code="CN",
            name_en="China",
        )
        self.assertEqual(country.code, "CN")
        with self.assertRaises(ValidationError):
            Country(data_object_id="ENT11111111-1111-4111-8111-111111111111")

    def test_membership_stage_is_scoped_to_the_contains_node_link(self) -> None:
        link = IndustryChainContainsNode(
            position=1,
            contextual_stage="upstream",
            review_status="approved",
            status="active",
        )
        self.assertEqual(link.contextual_stage.value, "upstream")
        with self.assertRaises(ValidationError):
            IndustryChainContainsNode(position=0)

    def test_catalog_is_serializable_and_exposes_source_target_pairs(self) -> None:
        catalog = ontology_catalog()
        json.dumps(catalog)
        self.assertEqual(catalog["version"], "evidence-curation/v1")
        self.assertEqual(
            catalog["entity_links"]["CountryInRegion"]["source_targets"],
            [{"source": "Country", "target": "Region"}],
        )

    def test_each_edge_is_owned_by_its_source_entity_schema(self) -> None:
        self.assertEqual(
            EDGE_TYPE_MAP[("Country", "Region")],
            ["CountryInRegion"],
        )
        self.assertEqual(
            EDGE_TYPE_MAP[("Organization", "Region")],
            ["OrganizationInRegion"],
        )


if __name__ == "__main__":
    unittest.main()
