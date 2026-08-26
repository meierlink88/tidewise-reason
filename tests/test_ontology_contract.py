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
    GeopoliticRivalry,
    MacroEconomic,
    Variable,
    ontology_catalog,
)
from ontology.entities.variable import validate_variable_catalog
from ontology.enums import (
    GeopoliticRivalryStatus,
    GeopoliticRivalryType,
    MacroEconomicStatus,
    MacroEconomicType,
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
                "Variable",
                "GeopoliticRivalry",
                "MacroEconomic",
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
        self.assertEqual(ONTOLOGY_VERSION, "reasoning-ontology/v2")

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
        self.assertEqual(catalog["version"], "reasoning-ontology/v2")
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

    def test_variable_is_one_controlled_dimension_for_multiple_anchor_types(self) -> None:
        variable = Variable(
            variable_id="selling_price",
            aliases=["销售价格", "ASP"],
            definition="The realized or anticipated selling price for the scoped output.",
            measurement_basis="Currency per scoped output unit or a reviewed qualitative trend.",
            allowed_anchor_types=["ChainNode", "Company"],
            maintenance_owner="Reasoning",
            catalog_version="variable-catalog/v1",
        )

        self.assertEqual(variable.variable_id, "selling_price")
        self.assertEqual(
            [anchor.value for anchor in variable.allowed_anchor_types],
            ["ChainNode", "Company"],
        )
        with self.assertRaises(ValidationError):
            Variable(
                variable_id="SELLING_PRICE",
                definition="Invalid uppercase identity.",
                measurement_basis="Qualitative trend.",
                allowed_anchor_types=["ChainNode"],
                maintenance_owner="Reasoning",
                catalog_version="variable-catalog/v1",
            )
        with self.assertRaises(ValidationError):
            Variable(
                variable_id="selling_price",
                definition="Selling price.",
                measurement_basis="Qualitative trend.",
                allowed_anchor_types=["ChainNode", "ChainNode"],
                maintenance_owner="Reasoning",
                catalog_version="variable-catalog/v1",
            )
        with self.assertRaises(ValidationError):
            Variable(
                variable_id="selling_price",
                definition="Selling price.",
                measurement_basis="Qualitative trend.",
                allowed_anchor_types=["ChainNode"],
                derived_from_variable_ids=["INVALID-ID"],
                maintenance_owner="Reasoning",
                catalog_version="variable-catalog/v1",
            )
        with self.assertRaises(ValidationError):
            Variable(
                variable_id="selling_price",
                definition="Selling price.",
                measurement_basis="Qualitative trend.",
                allowed_anchor_types=["ChainNode"],
                derived_from_variable_ids=["selling_price"],
                maintenance_owner="Reasoning",
                catalog_version="variable-catalog/v1",
            )

    def test_variable_catalog_validates_identity_and_rule_references(self) -> None:
        source = Variable(
            variable_id="market_supply",
            definition="Available market supply.",
            measurement_basis="Reviewed qualitative or quantitative supply.",
            allowed_anchor_types=["ChainNode"],
            maintenance_owner="Reasoning",
            catalog_version="variable-catalog/v1",
        )
        derived = Variable(
            variable_id="selling_price",
            definition="Selling price.",
            measurement_basis="Currency per output unit.",
            allowed_anchor_types=["ChainNode"],
            derived_from_variable_ids=["market_supply"],
            maintenance_owner="Reasoning",
            catalog_version="variable-catalog/v1",
        )

        self.assertEqual(validate_variable_catalog([source, derived]), (source, derived))
        with self.assertRaisesRegex(ValueError, "duplicate Variable identity"):
            validate_variable_catalog([source, source])
        with self.assertRaisesRegex(ValueError, "unknown Variable reference"):
            validate_variable_catalog([derived])
        with self.assertRaises(ValidationError):
            Variable(
                variable_id="selling_price",
                definition=" ",
                measurement_basis="Qualitative trend.",
                allowed_anchor_types=["ChainNode"],
                maintenance_owner="Reasoning",
                catalog_version="variable-catalog/v1",
            )
        with self.assertRaises(ValidationError):
            Variable(
                variable_id="selling_price",
                definition="Missing anchor applicability.",
                measurement_basis="Qualitative trend.",
                allowed_anchor_types=[],
                maintenance_owner="Reasoning",
                catalog_version="variable-catalog/v1",
            )

    def test_narrative_blueprints_mirror_data_identity_and_enum_contracts(self) -> None:
        rivalry = GeopoliticRivalry(
            data_object_id="GPR11111111-1111-4111-8111-111111111111",
            name_en="China-US technology competition",
            rivalry_type="GEOPOLITICAL",
            description="A persistent strategic technology rivalry.",
            core_actors="China; United States",
            influenced_regions=[],
            status="ACTIVE",
        )
        macro = MacroEconomic(
            data_object_id="MEC11111111-1111-4111-8111-111111111111",
            name_en="Federal Reserve monetary policy cycle",
            macro_type="MONETARY",
            description="A stable blueprint for changes in United States monetary policy.",
            status="ACTIVE",
        )

        self.assertEqual(rivalry.rivalry_type.value, "GEOPOLITICAL")
        self.assertEqual(rivalry.influenced_regions, [])
        self.assertEqual(macro.macro_type.value, "MONETARY")
        self.assertEqual(
            set(GeopoliticRivalry.model_fields),
            {
                "data_object_id",
                "name_en",
                "rivalry_type",
                "description",
                "core_actors",
                "peripheral_actors",
                "influenced_regions",
                "status",
                "updated_at",
            },
        )
        self.assertEqual(
            set(MacroEconomic.model_fields),
            {
                "data_object_id",
                "name_en",
                "macro_type",
                "description",
                "status",
                "updated_at",
            },
        )
        self.assertEqual(
            {item.value for item in GeopoliticRivalryType},
            {"GEOPOLITICAL", "MILITARY_WAR"},
        )
        self.assertEqual(
            {item.value for item in GeopoliticRivalryStatus},
            {"ACTIVE", "DORMANT", "RESOLVED"},
        )
        self.assertEqual(
            {item.value for item in MacroEconomicType},
            {"MONETARY", "FISCAL", "TRADE_POLICY", "REGULATORY", "DATA_ECONOMIC"},
        )
        self.assertEqual(
            {item.value for item in MacroEconomicStatus},
            {"ACTIVE", "DORMANT", "ARCHIVED"},
        )
        self.assertIsNone(GeopoliticRivalry().data_object_id)
        self.assertIsNone(MacroEconomic().data_object_id)
        with self.assertRaises(ValidationError):
            GeopoliticRivalry(rivalry_type="CONFLICT")
        with self.assertRaises(ValidationError):
            MacroEconomic(macro_type="INFLATION")
        with self.assertRaises(ValidationError):
            MacroEconomic(
                data_object_id="GPR11111111-1111-4111-8111-111111111111"
            )
        with self.assertRaises(ValidationError):
            GeopoliticRivalry(name_en=" ")
        with self.assertRaises(ValidationError):
            MacroEconomic(description=" ")


if __name__ == "__main__":
    unittest.main()
