"""Synthetic tests for signed approvals; no live keys or customer records."""

from __future__ import annotations

from pathlib import Path

import pytest

from electronics_rfq_agent.verified_extraction.approval_adapter import (
    SqliteHmacApprovalVerifier,
    sign_approval,
)
from electronics_rfq_agent.verified_extraction.contracts import GateStatus
from tests.unit.test_verified_approval import FIXED_NOW, claim_for, sample

TEST_SECRET = b"synthetic-approval-secret-32-bytes-minimum"


def signed_claim():
    bundle, result = sample()
    unsigned = claim_for(bundle, result)
    return (
        bundle,
        result,
        unsigned.model_copy(update={"proof": sign_approval(unsigned, TEST_SECRET)}),
    )


def authority(path: Path) -> SqliteHmacApprovalVerifier:
    return SqliteHmacApprovalVerifier(
        path,
        issuer_keys={"test-issuer": TEST_SECRET},
        authorized_reviewers=frozenset({"reviewer-allowed"}),
    )


def test_signature_is_bound_to_all_claim_fields(tmp_path: Path) -> None:
    _, _, claim = signed_claim()
    a = authority(tmp_path / "approvals.db")
    assert a.verify_and_consume(claim)
    assert not a.verify_and_consume(claim)


def test_replay_fails_across_verifier_instances(tmp_path: Path) -> None:
    _, _, claim = signed_claim()
    path = tmp_path / "approvals.db"
    assert authority(path).verify_and_consume(claim)
    assert not authority(path).verify_and_consume(claim)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("reviewer_id", "other-reviewer"),
        ("issuer_id", "fake-issuer"),
        ("document_id", "other-document"),
        ("run_id", "other-run"),
        ("policy_version", "other-policy"),
        ("result_sha256", "f" * 64),
        ("evidence_sha256", "0" * 64),
    ],
)
def test_changed_claim_rejected_without_new_signature(
    tmp_path: Path, field: str, replacement: str
) -> None:
    _, _, claim = signed_claim()
    changed = claim.model_copy(update={field: replacement})
    assert not authority(tmp_path / "approvals.db").verify_and_consume(changed)


def test_wrong_signing_key_rejected(tmp_path: Path) -> None:
    _, _, claim = signed_claim()
    verifier = SqliteHmacApprovalVerifier(
        tmp_path / "approvals.db",
        issuer_keys={"test-issuer": b"wrong-authority-key-with-minimum-length"},
        authorized_reviewers=frozenset({"reviewer-allowed"}),
    )
    assert not verifier.verify_and_consume(claim)


def test_untrusted_reviewer_rejected_even_with_valid_signature(
    tmp_path: Path,
) -> None:
    _, _, claim = signed_claim()
    changed = claim.model_copy(update={"reviewer_id": "unprivileged"})
    newly_signed = changed.model_copy(
        update={"proof": sign_approval(changed, TEST_SECRET)}
    )
    assert not authority(tmp_path / "approvals.db").verify_and_consume(newly_signed)


def test_short_key_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="approval_signing_key_too_short"):
        SqliteHmacApprovalVerifier(
            tmp_path / "approvals.db",
            issuer_keys={"test-issuer": b"short"},
            authorized_reviewers=frozenset({"reviewer-allowed"}),
        )


def test_end_to_end_requires_valid_approval_context(tmp_path: Path) -> None:
    from electronics_rfq_agent.verified_extraction.approval import assess_approval
    from electronics_rfq_agent.verified_extraction.audit import (
        result_hash,
    )
    from electronics_rfq_agent.verified_extraction.contracts import verify

    bundle, result, claim = signed_claim()
    report = verify(bundle, result, result_sha256=result_hash(result))
    verifier = authority(tmp_path / "approvals.db")
    kwargs = {
        "run_id": "run-001",
        "policy_version": "a124-v1",
        "claim": claim,
        "verifier": verifier,
        "now": FIXED_NOW,
    }
    assert assess_approval(bundle, result, report, **kwargs) == GateStatus.VERIFIED
    assert (
        assess_approval(bundle, result, report, **kwargs) == GateStatus.REVIEW_REQUIRED
    )


def test_invalid_run_never_consumes_valid_approval(tmp_path: Path) -> None:
    from electronics_rfq_agent.verified_extraction.approval import assess_approval
    from electronics_rfq_agent.verified_extraction.audit import result_hash
    from electronics_rfq_agent.verified_extraction.contracts import verify

    bundle, result, claim = signed_claim()
    verifier = authority(tmp_path / "approvals.db")
    report = verify(bundle, result, result_sha256=result_hash(result))
    denied = assess_approval(
        bundle,
        result,
        report,
        run_id="different-run",
        policy_version="a124-v1",
        claim=claim,
        verifier=verifier,
        now=FIXED_NOW,
    )
    assert denied == GateStatus.REVIEW_REQUIRED
    assert verifier.verify_and_consume(claim)
