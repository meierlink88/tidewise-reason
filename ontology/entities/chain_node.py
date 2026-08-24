"""ChainNode extraction type and its outbound Graphiti relationships."""

from datetime import datetime

from pydantic import Field, PositiveInt

from ontology.entities.base import TidewiseEntity, TidewiseEntityLink
from ontology.enums import ContextualStage, ReviewStatus


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
    updated_at: datetime | None = Field(
        default=None,
        description="Canonical Tidewise Data timestamp of the latest ChainNode fact change.",
    )


class ChainNodeBelongsToIndustryChain(TidewiseEntityLink):
    """A ChainNode belongs to an IndustryChain at one contextual stage and position."""

    position: PositiveInt | None = Field(
        default=None,
        description="Positive display or traversal position within this IndustryChain only.",
    )
    contextual_stage: ContextualStage | None = Field(
        default=None,
        description="Upstream, midstream or downstream stage within this IndustryChain only.",
    )


class _ChainScopedTopologyLink(TidewiseEntityLink):
    """Private shared identity contract; never registered as a Graphiti relation type."""

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^IGE[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Canonical Tidewise Data IndustryChainGraphEdge ID.",
    )
    industry_chain_id: str | None = Field(
        default=None,
        pattern=r"^ICH[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="IndustryChain context in which this node-to-node fact holds.",
    )


class ChainNodeInputTo(_ChainScopedTopologyLink):
    """A chain-scoped fact that the source ChainNode supplies an input to the target."""


class ChainNodeIsComponentOf(_ChainScopedTopologyLink):
    """A chain-scoped fact that the source is a component of the target ChainNode."""


class ChainNodeDependsOn(_ChainScopedTopologyLink):
    """A chain-scoped fact that the source structurally depends on the target ChainNode."""


ENTITY_TYPES = {"ChainNode": ChainNode}
EDGE_TYPES = {
    "ChainNodeBelongsToIndustryChain": ChainNodeBelongsToIndustryChain,
    "ChainNodeInputTo": ChainNodeInputTo,
    "ChainNodeIsComponentOf": ChainNodeIsComponentOf,
    "ChainNodeDependsOn": ChainNodeDependsOn,
}
EDGE_TYPE_MAP = {
    ("ChainNode", "IndustryChain"): ["ChainNodeBelongsToIndustryChain"],
    ("ChainNode", "ChainNode"): [
        "ChainNodeInputTo",
        "ChainNodeIsComponentOf",
        "ChainNodeDependsOn",
    ],
}
