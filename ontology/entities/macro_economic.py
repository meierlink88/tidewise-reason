"""MacroEconomic extraction type derived from the Tidewise Data contract."""

from datetime import datetime

from pydantic import BaseModel, Field

from ontology.entities.base import NonBlankText, TidewiseEntity
from ontology.enums import MacroEconomicStatus, MacroEconomicType


class MacroEconomic(TidewiseEntity):
    """A stable monetary, fiscal, trade, regulatory or data-economic narrative blueprint.

    The blueprint has no implied Country, Region, Institution, Storyline or other authoritative
    graph relationship.
    """

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^MEC[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Canonical Tidewise Data MacroEconomic ID; never infer or invent this value.",
    )
    name_en: NonBlankText | None = Field(
        default=None,
        max_length=100,
        description="Canonical English name of the macroeconomic narrative blueprint.",
    )
    macro_type: MacroEconomicType | None = Field(
        default=None,
        description="Controlled macroeconomic narrative type.",
    )
    description: NonBlankText | None = Field(
        default=None,
        description="Canonical natural-language boundary of the macroeconomic narrative blueprint.",
    )
    status: MacroEconomicStatus | None = Field(
        default=None,
        description="Controlled lifecycle status of the macroeconomic narrative blueprint.",
    )
    updated_at: datetime | None = Field(
        default=None,
        description=(
            "Canonical Tidewise Data timestamp of the latest blueprint change; never infer it."
        ),
    )

ENTITY_TYPES = {"MacroEconomic": MacroEconomic}
EDGE_TYPES: dict[str, type[BaseModel]] = {}
EDGE_TYPE_MAP: dict[tuple[str, str], list[str]] = {}
