"""源自 Tidewise Data Concept schema 的概念实体。"""

from datetime import datetime

from pydantic import BaseModel, Field

from ontology.entities.base import TidewiseEntity
from ontology.enums import ConceptType, ReviewStatus


class Concept(TidewiseEntity):
    """跨行业的技术、政策、需求、应用、商业模式或市场主题概念。"""

    data_object_id: str | None = Field(
        default=None,
        pattern=r"^CON[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Tidewise Data 中权威的 Concept ID；禁止推测或编造。",
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="用于将文本提及解析到同一 Concept 的稳定别名。",
    )
    concept_type: ConceptType | None = Field(
        default=None,
        description="Concept 业务含义的受控类型。",
    )
    definition: str | None = Field(
        default=None,
        min_length=1,
        description="Concept 的权威定义和适用边界。",
    )
    review_status: ReviewStatus | None = Field(
        default=None,
        description="Concept 事实是候选状态还是已审核状态。",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Tidewise Data 中 Concept 事实最后变更的权威时间；禁止推测。",
    )


ENTITY_TYPES = {"Concept": Concept}
EDGE_TYPES: dict[str, type[BaseModel]] = {}
EDGE_TYPE_MAP: dict[tuple[str, str], list[str]] = {}
