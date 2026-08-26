"""GeopoliticRivalry extraction type derived from the Tidewise Data contract."""

from datetime import datetime

from pydantic import BaseModel, Field

from ontology.entities.base import NonBlankText, TidewiseEntity
from ontology.enums import GeopoliticRivalryStatus, GeopoliticRivalryType


class GeopoliticRivalry(TidewiseEntity):
    """A stable geopolitical rivalry or military-war narrative blueprint.

    Actor and region fields remain reviewed text from Tidewise Data. They do not prove or create
    Country, Region, Organization or other authoritative graph relationships.
    """

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^GPR[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description=(
            "Canonical Tidewise Data GeopoliticRivalry ID; never infer or invent this value."
        ),
    )
    name_en: NonBlankText | None = Field(
        default=None,
        max_length=100,
        description="Canonical English name of the geopolitical narrative blueprint.",
    )
    rivalry_type: GeopoliticRivalryType | None = Field(
        default=None,
        description="Controlled geopolitical or military-war blueprint type.",
    )
    description: NonBlankText | None = Field(
        default=None,
        description="Canonical natural-language boundary of the geopolitical narrative blueprint.",
    )
    core_actors: NonBlankText | None = Field(
        default=None,
        description=(
            "Reviewed core-actor text that does not create authoritative Actor relationships."
        ),
    )
    peripheral_actors: str | None = Field(
        default=None,
        min_length=1,
        description="Optional reviewed peripheral-actor text.",
    )
    influenced_regions: list[str] | None = Field(
        default=None,
        description=(
            "Optional reviewed region texts; null and an empty list preserve distinct Data facts "
            "and neither value proves a Region relationship."
        ),
    )
    status: GeopoliticRivalryStatus | None = Field(
        default=None,
        description="Controlled lifecycle status of the geopolitical narrative blueprint.",
    )
    updated_at: datetime | None = Field(
        default=None,
        description=(
            "Canonical Tidewise Data timestamp of the latest blueprint change; never infer it."
        ),
    )

ENTITY_TYPES = {"GeopoliticRivalry": GeopoliticRivalry}
EDGE_TYPES: dict[str, type[BaseModel]] = {}
EDGE_TYPE_MAP: dict[tuple[str, str], list[str]] = {}
