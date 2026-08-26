"""Controlled Variable extraction and projection type owned by Tidewise Reason."""

from collections.abc import Iterable
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

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
    aliases: list[NonBlankText] = Field(
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

    @field_validator("aliases")
    @classmethod
    def canonicalize_aliases(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values]

    @model_validator(mode="after")
    def validate_local_rules(self) -> "Variable":
        if len(set(self.allowed_anchor_types)) != len(self.allowed_anchor_types):
            raise ValueError("allowed_anchor_types must not contain duplicates")

        normalized_aliases = [alias.strip().casefold() for alias in self.aliases]
        if len(normalized_aliases) != len(set(normalized_aliases)):
            raise ValueError("Variable aliases must be unique after normalization")
        if self.variable_id.casefold() in normalized_aliases:
            raise ValueError("Variable alias must not repeat its canonical identity")

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

    catalog_versions = {variable.catalog_version for variable in records}
    if len(catalog_versions) > 1:
        raise ValueError("Variable catalog must contain exactly one catalog_version")

    derivations = {
        variable.variable_id: set(variable.derived_from_variable_ids)
        for variable in records
    }
    visit_state: dict[str, int] = {}

    def visit(variable_id: str) -> None:
        state = visit_state.get(variable_id, 0)
        if state == 1:
            raise ValueError(f"cyclic Variable derivation: {variable_id}")
        if state == 2:
            return
        visit_state[variable_id] = 1
        for source_id in derivations[variable_id]:
            visit(source_id)
        visit_state[variable_id] = 2

    for identity in identities:
        visit(identity)

    resolved_terms: dict[str, str] = {}
    for variable in records:
        for term in (variable.variable_id, *variable.aliases):
            normalized = term.strip().casefold()
            owner = resolved_terms.get(normalized)
            if owner is not None and owner != variable.variable_id:
                raise ValueError(
                    f"ambiguous Variable alias {term!r}: {owner}, {variable.variable_id}"
                )
            resolved_terms[normalized] = variable.variable_id
    return records


ENTITY_TYPES = {"Variable": Variable}
EDGE_TYPES: dict[str, type[BaseModel]] = {}
EDGE_TYPE_MAP: dict[tuple[str, str], list[str]] = {}
