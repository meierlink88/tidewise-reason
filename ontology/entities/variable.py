"""Controlled Variable extraction and projection type owned by Tidewise Reason."""

from collections.abc import Iterable
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

from ontology.entities.base import NonBlankText, TidewiseEntity
from ontology.enums import AnalysisAnchorType


VariableID = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,63}$"),
]


class Variable(TidewiseEntity):
    """A globally reusable, controlled dimension that a Signal may change on an Anchor.

    One Variable identity may apply to several Anchor types. Direction, impact period and the
    concrete Anchor belong to the Signal Fact and never create Anchor-specific Variable copies.
    """

    variable_id: VariableID = Field(
        description="Stable lowercase key in the versioned Reason Variable catalog.",
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Reviewed names that resolve to this same controlled Variable.",
    )
    definition: NonBlankText = Field(
        description="Canonical meaning and boundary of the Variable.",
    )
    measurement_basis: NonBlankText = Field(
        description=(
            "Quantitative measurement or reviewed qualitative basis used to observe changes."
        ),
    )
    unit: NonBlankText | None = Field(
        default=None,
        description="Optional canonical unit; null when the measurement basis is qualitative.",
    )
    allowed_anchor_types: list[AnalysisAnchorType] = Field(
        min_length=1,
        description=(
            "Analysis Anchor types on which this Variable is meaningful; this applicability "
            "metadata does not create Variable-to-Anchor facts."
        ),
    )
    mutually_exclusive_variable_ids: list[VariableID] = Field(
        default_factory=list,
        description="Controlled Variable keys that must not describe the same atomic observation.",
    )
    derived_from_variable_ids: list[VariableID] = Field(
        default_factory=list,
        description="Controlled Variable keys from which this Variable may be explicitly derived.",
    )
    maintenance_owner: NonBlankText = Field(
        description="Domain owner responsible for reviewing the Variable definition.",
    )
    catalog_version: str = Field(
        pattern=r"^variable-catalog/v[1-9][0-9]*$",
        description="Versioned catalog contract under which the Variable is defined.",
    )

    @model_validator(mode="after")
    def validate_local_rules(self) -> "Variable":
        if len(set(self.allowed_anchor_types)) != len(self.allowed_anchor_types):
            raise ValueError("allowed_anchor_types must not contain duplicates")

        mutually_exclusive = set(self.mutually_exclusive_variable_ids)
        derived_from = set(self.derived_from_variable_ids)
        if len(mutually_exclusive) != len(self.mutually_exclusive_variable_ids):
            raise ValueError("mutually_exclusive_variable_ids must not contain duplicates")
        if len(derived_from) != len(self.derived_from_variable_ids):
            raise ValueError("derived_from_variable_ids must not contain duplicates")
        if self.variable_id in mutually_exclusive or self.variable_id in derived_from:
            raise ValueError("Variable must not reference itself")
        if mutually_exclusive & derived_from:
            raise ValueError(
                "one Variable cannot be both mutually exclusive and a derivation source"
            )
        return self


def validate_variable_catalog(variables: Iterable[Variable]) -> tuple[Variable, ...]:
    """Validate cross-record identities and references before catalog initialization."""

    records = tuple(variables)
    identities = [variable.variable_id for variable in records]
    duplicate_identities = sorted(
        identity for identity in set(identities) if identities.count(identity) > 1
    )
    if duplicate_identities:
        raise ValueError(
            "duplicate Variable identity: " + ", ".join(duplicate_identities)
        )

    known_identities = set(identities)
    referenced_identities = {
        reference
        for variable in records
        for reference in (
            *variable.mutually_exclusive_variable_ids,
            *variable.derived_from_variable_ids,
        )
    }
    unknown_references = sorted(referenced_identities - known_identities)
    if unknown_references:
        raise ValueError(
            "unknown Variable reference: " + ", ".join(unknown_references)
        )
    return records


ENTITY_TYPES = {"Variable": Variable}
EDGE_TYPES: dict[str, type[BaseModel]] = {}
EDGE_TYPE_MAP: dict[tuple[str, str], list[str]] = {}
