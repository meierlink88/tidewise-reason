"""Country extraction type and its outbound Graphiti relationships."""

from datetime import date

from pydantic import Field

from ontology.entities.base import TidewiseEntity, TidewiseEntityLink
from ontology.enums import MembershipType


class Country(TidewiseEntity):
    """A country with an ISO 3166-1 identity; not a region or organization."""

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^COU[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Canonical Tidewise Data Country ID; never infer or invent this value.",
    )
    code: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}$",
        description="ISO 3166-1 alpha-2 uppercase country code when explicitly known.",
    )
    name_en: str | None = Field(
        default=None,
        min_length=1,
        description="Official English short name from the canonical country fact.",
    )
    strategic_positioning: str | None = Field(
        default=None,
        min_length=1,
        description="Canonical description of the country's strategic positioning.",
    )
    key_resources: str | None = Field(
        default=None,
        min_length=1,
        description="Canonical description of the country's key strategic resources.",
    )


class CountryInRegion(TidewiseEntityLink):
    """A Country belongs to a stable Region."""


class CountryMemberOfOrganization(TidewiseEntityLink):
    """A Country participates in an Organization during an optional closed date interval."""

    membership_type: MembershipType | None = Field(
        default=None,
        description="Controlled type of the Country's Organization membership.",
    )
    effective_date: date | None = Field(
        default=None,
        description="First calendar date on which the membership is effective, when known.",
    )
    expiry_date: date | None = Field(
        default=None,
        description="Last calendar date on which the membership is effective, when known.",
    )


ENTITY_TYPES = {"Country": Country}
EDGE_TYPES = {
    "CountryInRegion": CountryInRegion,
    "CountryMemberOfOrganization": CountryMemberOfOrganization,
}
EDGE_TYPE_MAP = {
    ("Country", "Region"): ["CountryInRegion"],
    ("Country", "Organization"): ["CountryMemberOfOrganization"],
}
