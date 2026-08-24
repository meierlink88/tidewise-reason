"""Organization extraction type and its outbound Graphiti relationships."""

from datetime import date

from pydantic import Field

from ontology.entities.base import TidewiseEntity, TidewiseEntityLink
from ontology.enums import BindingPowerLevel, InfluenceRating


class Organization(TidewiseEntity):
    """An authoritative multilateral organization, alliance, association or mechanism."""

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^ORG[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Canonical Tidewise Data Organization ID; never infer or invent this value.",
    )
    code: str | None = Field(
        default=None,
        pattern=r"^[A-Z][A-Z0-9_]*$",
        description="Stable uppercase Organization code.",
    )
    name_en: str | None = Field(
        default=None,
        min_length=1,
        description="Official English Organization name.",
    )
    category_code: str | None = Field(
        default=None,
        pattern=r"^[A-Z][A-Z0-9_]*$",
        description="Canonical Organization Category code supplied by Tidewise Data.",
    )
    function_code: str | None = Field(
        default=None,
        pattern=r"^[A-Z][A-Z0-9_]*$",
        description="Canonical core Organization Function code supplied by Tidewise Data.",
    )
    domain_tag_codes: list[str] = Field(
        default_factory=list,
        description="Canonical Organization Domain Tag codes supplied by Tidewise Data.",
    )
    legal_entity_code: str | None = Field(
        default=None,
        min_length=1,
        description="Optional ISO 17442 LEI for an Organization that is a legal entity.",
    )
    binding_power_level: BindingPowerLevel | None = Field(
        default=None,
        description="Canonical strength of the Organization's binding authority.",
    )
    influence_rating: InfluenceRating | None = Field(
        default=None,
        description="Canonical global or domain influence rating.",
    )
    strategic_positioning: str | None = Field(
        default=None,
        min_length=1,
        description="Canonical description of the Organization's strategic positioning.",
    )
    core_impact_scope: str | None = Field(
        default=None,
        min_length=1,
        description="Canonical description of the Organization's core impact scope.",
    )
    founding_document: str | None = Field(
        default=None,
        min_length=1,
        description="Treaty or document that established the Organization.",
    )
    established_date: date | None = Field(
        default=None,
        description="Calendar date on which the Organization was established.",
    )
    headquarters_city: str | None = Field(
        default=None,
        min_length=1,
        description="City in which the Organization is headquartered.",
    )
    headquarters_subdivision_id: str | None = Field(
        default=None,
        min_length=1,
        description="Reserved subdivision identifier from the Data contract; it is not a graph relation yet.",
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        description="Canonical supplemental Organization description.",
    )


class OrganizationInRegion(TidewiseEntityLink):
    """A regional Organization belongs to a stable Region."""


ENTITY_TYPES = {"Organization": Organization}
EDGE_TYPES = {"OrganizationInRegion": OrganizationInRegion}
EDGE_TYPE_MAP = {
    ("Organization", "Region"): ["OrganizationInRegion"],
}
