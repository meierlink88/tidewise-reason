"""Shared Graphiti validation policy for Tidewise entity and edge types."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


NonBlankText = Annotated[str, StringConstraints(pattern=r"\S")]


class TidewiseEntity(BaseModel):
    """Base validation policy for Graphiti custom entity attributes."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class TidewiseEntityLink(BaseModel):
    """Base validation policy for Graphiti custom edge attributes."""

    model_config = ConfigDict(extra="forbid", frozen=True)
