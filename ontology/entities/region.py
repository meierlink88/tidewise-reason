"""Region extraction type derived from Tidewise Data's Region schema."""

from pydantic import BaseModel, Field

from ontology.entities.base import TidewiseEntity
from ontology.enums import RegionType


class Region(TidewiseEntity):
    """A stable geographic, multilateral or investment region; not a country."""

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^REG[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Canonical Tidewise Data Region ID; never infer or invent this value.",
    )
    code: str | None = Field(
        default=None,
        pattern=r"^[A-Z][A-Z0-9_]*$",
        description="Stable uppercase Region business code.",
    )
    name_en: str | None = Field(
        default=None,
        min_length=1,
        description="Official English Region name.",
    )
    region_type: RegionType | None = Field(
        default=None,
        description="Whether the Region is continental, geographic, multilateral or investment-defined.",
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        description="Canonical explanation of the Region's boundary or business meaning.",
    )


ENTITY_TYPES = {"Region": Region}
EDGE_TYPES: dict[str, type[BaseModel]] = {}
EDGE_TYPE_MAP: dict[tuple[str, str], list[str]] = {}
