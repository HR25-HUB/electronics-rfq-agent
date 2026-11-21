"""Approval contract. Production trust verification is deliberately NOT implemented.

A real adapter must verify signatures, reviewer identity/role, expiry and replay
against a trusted external approval service. Never use a test fake in production.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from pydantic import Field, model_validator

from electronics_rfq_agent.verified_extraction.audit import (
    canonical_json,
    result_hash,
    sha256,
)
from electronics_rfq_agent.verified_extraction.contracts import (
    EvidenceBundle,
    ExtractionResult,
    GateStatus,
    StrictModel,
    VerificationReport,
    verify,
)


class ApprovalClaim(StrictModel):
    approval_id: str = Field(min_length=1)
    issuer_id: str = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy_version: str = Field(min_length=1)
    approved_at: datetime
    expires_at: datetime
    proof: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_dates(self) -> ApprovalClaim:
        if self.approved_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("Approval timestamps require timezone")
        if self.expires_at <= self.approved_at:
            raise ValueError("Approval must expire after issuance")
        return self


class TrustedApprovalVerifier(Protocol):
    """Trust boundary: verify signature, identity, authorization and replay."""

    def verify_and_consume(self, claim: ApprovalClaim) -> bool:
        """Atomic one-time verification against trusted approval authority."""
        ...


def assess_approval(  # noqa: PLR0913, PLR0911
    bundle: EvidenceBundle,
    result: ExtractionResult,
    report: VerificationReport,
    *,
    run_id: str,
    policy_version: str,
    claim: ApprovalClaim | None,
    verifier: TrustedApprovalVerifier | None = None,
    now: datetime | None = None,
) -> GateStatus:
    """Fail closed without a trusted verifier and matching immutable context."""
    digest = result_hash(result)
    evidence_digest = sha256(canonical_json(bundle))
    replayed = verify(bundle, result, result_sha256=digest)
    if report != replayed or replayed.status == GateStatus.BLOCKED:
        return GateStatus.BLOCKED
    if claim is None or verifier is None:
        return GateStatus.REVIEW_REQUIRED
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        return GateStatus.REVIEW_REQUIRED
    if not (claim.approved_at <= clock < claim.expires_at):
        return GateStatus.REVIEW_REQUIRED
    if (
        claim.document_id != bundle.document_id
        or claim.evidence_sha256 != evidence_digest
        or claim.result_sha256 != digest
        or claim.run_id != run_id
        or claim.policy_version != policy_version
    ):
        return GateStatus.REVIEW_REQUIRED
    try:
        accepted = verifier.verify_and_consume(claim)
    except Exception:
        # An unavailable or faulty authority must never grant approval.
        return GateStatus.REVIEW_REQUIRED
    return GateStatus.VERIFIED if accepted else GateStatus.REVIEW_REQUIRED
