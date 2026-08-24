"""HTTP adapter for the Evidence Episode ingestion module."""

from __future__ import annotations

import hmac
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, status

from ingestion.episcode.evidence.contracts import (
    EvidenceEpisodeAcceptanceEnvelope,
    EvidenceEpisodeBatchRequest,
    EvidenceEpisodeStatus,
)
from ingestion.episcode.evidence.delivery_store import EvidencePayloadConflict
from ingestion.episcode.evidence.module import EvidenceEpisodeModule


def create_router(
    module: EvidenceEpisodeModule,
    *,
    service_token: str,
) -> APIRouter:
    router = APIRouter(prefix="/api/reason/v1/evidence-episodes")

    def authorize(authorization: str | None = Header(default=None)) -> None:
        expected = f"Bearer {service_token}"
        if authorization is None or not hmac.compare_digest(authorization, expected):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    @router.post("", status_code=status.HTTP_202_ACCEPTED)
    def accept_evidence(
        request: EvidenceEpisodeBatchRequest,
        authorization: str | None = Header(default=None),
    ) -> EvidenceEpisodeAcceptanceEnvelope:
        authorize(authorization)
        try:
            result = module.accept(request.evidences)
        except EvidencePayloadConflict as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Evidence payload conflicts with accepted identity: {exc}",
            ) from None
        return EvidenceEpisodeAcceptanceEnvelope(request_id=str(uuid4()), result=result)

    @router.get("/{evidence_id}")
    def get_evidence_status(
        evidence_id: str,
        authorization: str | None = Header(default=None),
    ) -> EvidenceEpisodeStatus:
        authorize(authorization)
        result = module.get_status(evidence_id)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
        return result

    return router
