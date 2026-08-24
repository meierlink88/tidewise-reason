"""ChainNode extraction type and its outbound Graphiti relationships."""

from pydantic import Field

from ontology.entities.base import TidewiseEntity, TidewiseEntityLink
from ontology.enums import RecordStatus, ReviewStatus, SegmentKind


class ChainNode(TidewiseEntity):
    """A reusable business or technical stage; its chain position belongs to membership."""

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^CND[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Canonical Tidewise Data ChainNode ID; never infer or invent this value.",
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Stable aliases used to resolve a ChainNode mention.",
    )
    definition: str | None = Field(
        default=None,
        min_length=1,
        description="Canonical definition and business boundary of the ChainNode.",
    )
    review_status: ReviewStatus | None = Field(
        default=None,
        description="Whether the ChainNode fact is a candidate or approved.",
    )


class ChainNodeTransmission(TidewiseEntityLink):
    """Shared attributes of a directed relationship between two ChainNodes."""

    mechanism: str | None = Field(
        default=None,
        min_length=1,
        description="Direct structural mechanism connecting the source ChainNode to the target.",
    )
    condition_note: str | None = Field(
        default=None,
        min_length=1,
        description="Optional condition under which the relationship holds.",
    )
    segment_kind: SegmentKind | None = Field(
        default=None,
        description="Whether the relation is direct or compresses omitted intermediate steps.",
    )
    omitted_step_note: str | None = Field(
        default=None,
        min_length=1,
        description="Required by Data for a compressed relation; describes omitted intermediate steps.",
    )
    review_status: ReviewStatus | None = Field(
        default=None,
        description="Whether the topology relation is a candidate or approved.",
    )
    status: RecordStatus | None = Field(
        default=None,
        description="Whether the topology relation is active or inactive.",
    )


class ChainNodeInputTo(ChainNodeTransmission):
    """The source ChainNode supplies an input used by the target ChainNode."""


class ChainNodeIsComponentOf(ChainNodeTransmission):
    """The source ChainNode is a physical or functional component of the target ChainNode."""


class ChainNodeDependsOn(ChainNodeTransmission):
    """The source ChainNode structurally depends on the target ChainNode."""


ENTITY_TYPES = {"ChainNode": ChainNode}
EDGE_TYPES = {
    "ChainNodeInputTo": ChainNodeInputTo,
    "ChainNodeIsComponentOf": ChainNodeIsComponentOf,
    "ChainNodeDependsOn": ChainNodeDependsOn,
}
EDGE_TYPE_MAP = {
    ("ChainNode", "ChainNode"): [
        "ChainNodeInputTo",
        "ChainNodeIsComponentOf",
        "ChainNodeDependsOn",
    ],
}
