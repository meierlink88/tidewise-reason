from __future__ import annotations

import json
import unittest

from pydantic import BaseModel, ValidationError

from ontology import (
    EDGE_TYPE_MAP,
    EDGE_TYPES,
    ENTITY_TYPES,
    ONTOLOGY_VERSION,
    ChainNodeBelongsToIndustryChain,
    Country,
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
                "IndustryChainMappedToIndustry",
                "IndustryChainMappedToConcept",
                "ChainNodeBelongsToIndustryChain",
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
            EDGE_TYPE_MAP[("ChainNode", "IndustryChain")],
            ["ChainNodeBelongsToIndustryChain"],
        )
        self.assertNotIn(("IndustryChain", "ChainNode"), EDGE_TYPE_MAP)
        self.assertNotIn(("IndustryChain", "Country"), EDGE_TYPE_MAP)
        self.assertEqual(
            EDGE_TYPE_MAP[("IndustryChain", "Industry")],
            ["IndustryChainMappedToIndustry"],
        )
        self.assertEqual(
            EDGE_TYPE_MAP[("IndustryChain", "Concept")],
            ["IndustryChainMappedToConcept"],
        )
        self.assertEqual(ONTOLOGY_VERSION, "reasoning-ontology/v1")

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

    def test_canonical_identity_is_validated_but_not_required_from_extraction(self) -> None:
        self.assertIsNone(Country().data_object_id)
        country = Country(
            data_object_id="COU11111111-1111-4111-8111-111111111111",
            code="CN",
            name_en="China",
        )
        self.assertEqual(country.code, "CN")
        with self.assertRaises(ValidationError):
            Country(data_object_id="ENT11111111-1111-4111-8111-111111111111")

    def test_membership_stage_is_owned_by_the_chain_node_link(self) -> None:
        link = ChainNodeBelongsToIndustryChain(
            position=1,
            contextual_stage="upstream",
        )
        self.assertEqual(link.contextual_stage.value, "upstream")
        self.assertEqual(
            set(ChainNodeBelongsToIndustryChain.model_fields),
            {"position", "contextual_stage"},
        )
        with self.assertRaises(ValidationError):
            ChainNodeBelongsToIndustryChain(position=0)

    def test_catalog_is_serializable_and_exposes_source_target_pairs(self) -> None:
        catalog = ontology_catalog()
        json.dumps(catalog)
        self.assertEqual(catalog["version"], "reasoning-ontology/v1")
        self.assertEqual(
            catalog["entity_links"]["CountryInRegion"]["source_targets"],
            [{"source": "Country", "target": "Region"}],
        )

    def test_region_and_organization_descriptions_exclude_domestic_entities(self) -> None:
        catalog = ontology_catalog()

        region_description = " ".join(
            catalog["entities"]["Region"]["description"].split()
        )
        organization_description = " ".join(
            catalog["entities"]["Organization"]["description"].split()
        )
        self.assertIn("province", region_description)
        self.assertIn("Sichuan", region_description)
        self.assertIn("company", organization_description)
        self.assertIn("listed issuer", organization_description)

    def test_each_edge_is_owned_by_its_source_entity_schema(self) -> None:
        self.assertEqual(
            EDGE_TYPE_MAP[("Country", "Region")],
            ["CountryInRegion"],
        )
        self.assertEqual(
            EDGE_TYPE_MAP[("Organization", "Region")],
            ["OrganizationInRegion"],
        )

    def test_chain_node_topology_links_expose_only_reasoning_identity(self) -> None:
        expected = {"data_object_id", "industry_chain_id"}
        for name in (
            "ChainNodeInputTo",
            "ChainNodeIsComponentOf",
            "ChainNodeDependsOn",
        ):
            self.assertEqual(set(EDGE_TYPES[name].model_fields), expected)


if __name__ == "__main__":
    unittest.main()
