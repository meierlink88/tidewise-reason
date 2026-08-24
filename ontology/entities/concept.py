"""Concept extraction type derived from Tidewise Data's Concept schema."""

from datetime import datetime

from pydantic import BaseModel, Field

from ontology.entities.base import TidewiseEntity
from ontology.enums import ConceptType, ReviewStatus


class Concept(TidewiseEntity):
    """A cross-industry technology, policy, demand, application or market concept."""

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^CON[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Canonical Tidewise Data Concept ID; never infer or invent this value.",
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Stable aliases used to resolve a Concept mention.",
    )
    concept_type: ConceptType | None = Field(
        default=None,
        description="Controlled business meaning of the Concept.",
    )
    definition: str | None = Field(
        default=None,
        min_length=1,
        description="Canonical definition and applicable boundary of the Concept.",
    )
    review_status: ReviewStatus | None = Field(
        default=None,
        description="Whether the Concept fact is a candidate or approved.",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Canonical Tidewise Data timestamp of the latest Concept fact change; never infer it.",
    )


ENTITY_TYPES = {"Concept": Concept}
EDGE_TYPES: dict[str, type[BaseModel]] = {}
EDGE_TYPE_MAP: dict[tuple[str, str], list[str]] = {}
