"""Synthetic-only authorization contract tests; no production identity adapter."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from electronics_rfq_agent.verified_extraction.approval import (
    ApprovalClaim,
    assess_approval,
)
from electronics_rfq_agent.verified_extraction.audit import (
    canonical_json,
    result_hash,
    sha256,
)
from electronics_rfq_agent.verified_extraction.contracts import (
    EvidenceBlock,
    EvidenceBundle,
    ExtractedField,
    ExtractedLine,
    ExtractionResult,
    GateStatus,
    SourceLine,
    SourceSpan,
    verify,
)

FIXED_NOW = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)


class SyntheticApprovalAuthority:
    """Test double only. Never use in production."""

    def __init__(self) -> None:
        self.consumed: set[str] = set()

    def verify_and_consume(self, claim: ApprovalClaim) -> bool:
        if claim.approval_id in self.consumed:
            return False
        if claim.reviewer_id != "reviewer-allowed":
            return False
        if claim.proof != "synthetic-authorized-proof":
            return False
        self.consumed.add(claim.approval_id)
        return True


def sample() -> tuple[EvidenceBundle, ExtractionResult]:
    text = "ABB S203-C16 — 100 pcs"
    part_start = text.index("S203-C16")
    qty_start = text.index("100")
    unit_start = text.index("pcs")

    def field(value: str, start: int) -> ExtractedField:
        return ExtractedField(
            value=value,
            span=SourceSpan(
                evidence_id="EV-1",
                start=start,
                end=start + len(value),
            ),
        )

    bundle = EvidenceBundle(
        document_id="D1",
        authorization_id="SYNTHETIC-ONLY",
        synthetic=True,
        evidence=[EvidenceBlock(evidence_id="EV-1", page=1, text=text)],
        source_lines=[
            SourceLine(
                source_line_id="L1",
                evidence_id="EV-1",
                original_text=text,
            )
        ],
    )
    result = ExtractionResult(
        document_id="D1",
        lines=[
            ExtractedLine(
                source_line_id="L1",
                original_text=text,
                part_number=field("S203-C16", part_start),
                quantity_raw=field("100", qty_start),
                unit_raw=field("pcs", unit_start),
            )
        ],
    )
    return bundle, result


def claim_for(
    bundle: EvidenceBundle,
    result: ExtractionResult,
) -> ApprovalClaim:
    return ApprovalClaim(
        approval_id="SYNTH-APPROVAL-1",
        issuer_id="test-issuer",
        reviewer_id="reviewer-allowed",
        run_id="run-001",
        document_id=bundle.document_id,
        evidence_sha256=sha256(canonical_json(bundle)),
        result_sha256=result_hash(result),
        policy_version="a124-v1",
        approved_at=FIXED_NOW - timedelta(minutes=5),
        expires_at=FIXED_NOW + timedelta(hours=1),
        proof="synthetic-authorized-proof",
    )


def decide(
    bundle: EvidenceBundle,
    result: ExtractionResult,
    claim: ApprovalClaim | None,
    authority: SyntheticApprovalAuthority | None,
) -> GateStatus:
    report = verify(bundle, result, result_sha256=result_hash(result))
    return assess_approval(
        bundle,
        result,
        report,
        run_id="run-001",
        policy_version="a124-v1",
        claim=claim,
        verifier=authority,
        now=FIXED_NOW,
    )


def test_missing_authority_never_verifies() -> None:
    bundle, result = sample()
    assert decide(bundle, result, claim_for(bundle, result), None) == (
        GateStatus.REVIEW_REQUIRED
    )


def test_valid_approval_consumed_once() -> None:
    bundle, result = sample()
    authority = SyntheticApprovalAuthority()
    claim = claim_for(bundle, result)
    assert decide(bundle, result, claim, authority) == GateStatus.VERIFIED
    assert decide(bundle, result, claim, authority) == GateStatus.REVIEW_REQUIRED


def test_modified_evidence_cannot_reuse_approval() -> None:
    bundle, result = sample()
    original_claim = claim_for(bundle, result)
    different = bundle.model_copy(
        update={
            "authorization_id": "SYNTHETIC-OTHER",
        }
    )
    assert (
        decide(different, result, original_claim, SyntheticApprovalAuthority())
        == GateStatus.REVIEW_REQUIRED
    )


def test_modified_result_cannot_reuse_approval() -> None:
    bundle, result = sample()
    original_claim = claim_for(bundle, result)
    mutated = result.model_copy(update={"unknowns": ["review note"]})
    assert (
        decide(bundle, mutated, original_claim, SyntheticApprovalAuthority())
        == GateStatus.REVIEW_REQUIRED
    )


def test_expired_approval_is_rejected() -> None:
    bundle, result = sample()
    claim = claim_for(bundle, result).model_copy(
        update={"expires_at": FIXED_NOW - timedelta(seconds=1)}
    )
    assert (
        decide(bundle, result, claim, SyntheticApprovalAuthority())
        == GateStatus.REVIEW_REQUIRED
    )


def test_unprivileged_reviewer_is_rejected() -> None:
    bundle, result = sample()
    claim = claim_for(bundle, result).model_copy(
        update={"reviewer_id": "unknown-reviewer"}
    )
    assert (
        decide(bundle, result, claim, SyntheticApprovalAuthority())
        == GateStatus.REVIEW_REQUIRED
    )


def test_policy_version_mismatch_is_rejected() -> None:
    bundle, result = sample()
    claim = claim_for(bundle, result).model_copy(
        update={"policy_version": "different-policy"}
    )
    assert (
        decide(bundle, result, claim, SyntheticApprovalAuthority())
        == GateStatus.REVIEW_REQUIRED
    )


def test_invalid_evidence_blocks_even_with_approval() -> None:
    bundle, result = sample()
    line = result.lines[0]
    bad_field = line.quantity_raw.model_copy(update={"value": "1000"})
    bad_line = line.model_copy(update={"quantity_raw": bad_field})
    broken_result = result.model_copy(update={"lines": [bad_line]})
    assert (
        decide(
            bundle,
            broken_result,
            claim_for(bundle, result),
            SyntheticApprovalAuthority(),
        )
        == GateStatus.BLOCKED
    )
