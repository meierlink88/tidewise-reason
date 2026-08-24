"""First-batch Graphiti entity schemas and their outbound relationships."""

from ontology.entities.chain_node import (
    ChainNode,
    ChainNodeBelongsToIndustryChain,
    ChainNodeDependsOn,
    ChainNodeInputTo,
    ChainNodeIsComponentOf,
)
from ontology.entities.concept import Concept
from ontology.entities.country import (
    Country,
    CountryInRegion,
    CountryMemberOfOrganization,
)
from ontology.entities.industry import Industry, IndustryHasParent
from ontology.entities.industry_chain import (
    IndustryChain,
    IndustryChainMappedToConcept,
    IndustryChainMappedToIndustry,
)
from ontology.entities.organization import Organization, OrganizationInRegion
from ontology.entities.region import Region

__all__ = [
    "ChainNode",
    "ChainNodeBelongsToIndustryChain",
    "ChainNodeDependsOn",
    "ChainNodeInputTo",
    "ChainNodeIsComponentOf",
    "Concept",
    "Country",
    "CountryInRegion",
    "CountryMemberOfOrganization",
    "Industry",
    "IndustryHasParent",
    "IndustryChain",
    "IndustryChainMappedToConcept",
    "IndustryChainMappedToIndustry",
    "Organization",
    "OrganizationInRegion",
    "Region",
]
