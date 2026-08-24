"""Industry extraction type and its outbound Graphiti relationships."""

from datetime import datetime

from pydantic import Field

from ontology.entities.base import TidewiseEntity, TidewiseEntityLink
from ontology.enums import ReviewStatus


class Industry(TidewiseEntity):
    """An industry in a controlled classification hierarchy; not an industry chain."""

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^IND[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Canonical Tidewise Data Industry ID; never infer or invent this value.",
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Stable aliases used to resolve an Industry mention.",
    )
    classification_system: str | None = Field(
        default=None,
        min_length=1,
        description="Controlled classification system that owns the Industry code and hierarchy.",
    )
    industry_code: str | None = Field(
        default=None,
        min_length=1,
        description="Stable Industry code within its classification system.",
    )
    hierarchy_path_codes: list[str] = Field(
        default_factory=list,
        description="Ordered classification codes from the root Industry to this Industry.",
    )
    definition: str | None = Field(
        default=None,
        min_length=1,
        description="Canonical definition of the Industry's business boundary.",
    )
    review_status: ReviewStatus | None = Field(
        default=None,
        description="Whether the Industry fact is a candidate or approved.",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Canonical Tidewise Data timestamp of the latest Industry fact change; never infer it.",
    )


class IndustryHasParent(TidewiseEntityLink):
    """An Industry points to its direct parent in the same classification system."""


ENTITY_TYPES = {"Industry": Industry}
EDGE_TYPES = {"IndustryHasParent": IndustryHasParent}
EDGE_TYPE_MAP = {
    ("Industry", "Industry"): ["IndustryHasParent"],
}
