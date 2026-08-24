"""Controlled values mirrored from Tidewise Data contracts for graph extraction."""

from enum import StrEnum


class ReviewStatus(StrEnum):
    CANDIDATE = "candidate"
    APPROVED = "approved"


class RecordStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class RegionType(StrEnum):
    CONTINENT = "CONTINENT"
    GEOGRAPHIC = "GEOGRAPHIC"
    MULTILATERAL = "MULTILATERAL"
    INVESTMENT = "INVESTMENT"


class ConceptType(StrEnum):
    TECHNOLOGY = "technology"
    POLICY = "policy"
    APPLICATION = "application"
    DEMAND = "demand"
    BUSINESS_MODEL = "business_model"
    COMPANY_ECOSYSTEM = "company_ecosystem"
    PRODUCT_ECOSYSTEM = "product_ecosystem"
    EVENT_NARRATIVE = "event_narrative"
    MARKET_THEME = "market_theme"


class BindingPowerLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class InfluenceRating(StrEnum):
    S = "S"
    A = "A"
    B = "B"


class MembershipType(StrEnum):
    FULL_MEMBER = "FULL_MEMBER"
    OBSERVER = "OBSERVER"
    ASSOCIATE = "ASSOCIATE"
    PARTNER = "PARTNER"
    CANDIDATE = "CANDIDATE"


class ContextualStage(StrEnum):
    UPSTREAM = "upstream"
    MIDSTREAM = "midstream"
    DOWNSTREAM = "downstream"


class SegmentKind(StrEnum):
    DIRECT_CANDIDATE = "direct_candidate"
    COMPRESSED_CANDIDATE = "compressed_candidate"
