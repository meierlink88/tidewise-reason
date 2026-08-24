"""IndustryChain extraction type and its outbound Graphiti relationships."""

from datetime import date, datetime

from pydantic import Field

from ontology.entities.base import TidewiseEntity, TidewiseEntityLink
from ontology.enums import RecordStatus, ReviewStatus


class IndustryChain(TidewiseEntity):
    """A directed research subgraph organized around a target output and end use."""

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^ICH[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Canonical Tidewise Data IndustryChain ID; never infer or invent this value.",
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Stable aliases used to resolve an IndustryChain mention.",
    )
    scope: str | None = Field(
        default=None,
        min_length=1,
        description="Business and product scope covered by the IndustryChain.",
    )
    target_output: str | None = Field(
        default=None,
        min_length=1,
        description="Final target output around which the IndustryChain is organized.",
    )
    end_use: str | None = Field(
        default=None,
        min_length=1,
        description="Primary end use of the IndustryChain target output.",
    )
    geography: str | None = Field(
        default=None,
        min_length=1,
        description="Canonical free-text geographic scope of the IndustryChain.",
    )
    as_of_date: date | None = Field(
        default=None,
        description="Business date for which the IndustryChain topology is valid.",
    )
    review_status: ReviewStatus | None = Field(
        default=None,
        description="Whether the IndustryChain fact is a candidate or approved.",
    )
    review_note: str | None = Field(
        default=None,
        min_length=1,
        description="Optional canonical review note for the IndustryChain.",
    )
    technology_route_qualifier: str | None = Field(
        default=None,
        min_length=1,
        description="Optional technology-route qualifier that bounds the IndustryChain.",
    )
    observable_variables: list[str] = Field(
        default_factory=list,
        description="Stable variable keys used to observe the IndustryChain state.",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Canonical Tidewise Data timestamp of the latest IndustryChain fact change; never infer it.",
    )


class IndustryChainMapping(TidewiseEntityLink):
    """Shared identity and lifecycle fields for a Data-owned IndustryChain mapping."""

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^ERL[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Canonical Tidewise Data EntityRelation ID; never infer or invent this value.",
    )
    status: RecordStatus | None = Field(
        default=None,
        description="Whether the canonical mapping relation is active or inactive.",
    )


class IndustryChainMappedToIndustry(IndustryChainMapping):
    """An IndustryChain maps to an Industry classification fact in Tidewise Data."""


class IndustryChainMappedToConcept(IndustryChainMapping):
    """An IndustryChain maps to a cross-industry Concept fact in Tidewise Data."""


ENTITY_TYPES = {"IndustryChain": IndustryChain}
EDGE_TYPES = {
    "IndustryChainMappedToIndustry": IndustryChainMappedToIndustry,
    "IndustryChainMappedToConcept": IndustryChainMappedToConcept,
}
EDGE_TYPE_MAP = {
    ("IndustryChain", "Industry"): ["IndustryChainMappedToIndustry"],
    ("IndustryChain", "Concept"): ["IndustryChainMappedToConcept"],
}
