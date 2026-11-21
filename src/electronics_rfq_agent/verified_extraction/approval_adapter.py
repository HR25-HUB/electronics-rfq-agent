"""Local HMAC approval authority with an atomic SQLite replay ledger.

This adapter is opt-in. Keys and reviewer entitlements must be provisioned
through a trusted service, not loaded from RFQ evidence or a model response.
"""

from __future__ import annotations

import hashlib
import hmac
import sqlite3
from collections.abc import Mapping
from pathlib import Path

from electronics_rfq_agent.verified_extraction.approval import ApprovalClaim
from electronics_rfq_agent.verified_extraction.audit import canonical_json


def approval_payload(claim: ApprovalClaim) -> bytes:
    """Canonical signature input includes all claim fields except the proof."""
    return canonical_json(claim.model_dump(mode="json", exclude={"proof"}))


def sign_approval(claim: ApprovalClaim, secret: bytes) -> str:
    """Issuer-side helper. Do not run this in the RFQ extraction process."""
    if len(secret) < 32:  # noqa: PLR2004
        raise ValueError("approval_signing_key_too_short")
    digest = hmac.new(secret, approval_payload(claim), hashlib.sha256).hexdigest()
    return f"hmac-sha256:{digest}"


class SqliteHmacApprovalVerifier:
    """Verify issuer signature and reviewer entitlement; consume exactly once.

    Not a distributed identity service. Production deployment needs managed keys,
    trusted issuer onboarding, tenant-scoped reviewer mapping and durable backups.
    """

    def __init__(
        self,
        ledger_path: Path,
        *,
        issuer_keys: Mapping[str, bytes],
        authorized_reviewers: frozenset[str],
    ) -> None:
        if not issuer_keys or not authorized_reviewers:
            raise ValueError("approval_authority_not_configured")
        if any(len(key) < 32 for key in issuer_keys.values()):  # noqa: PLR2004
            raise ValueError("approval_signing_key_too_short")
        if str(ledger_path) == ":memory:":
            raise ValueError("persistent_ledger_required")
        self._ledger_path = ledger_path
        self._issuer_keys = dict(issuer_keys)
        self._reviewers = authorized_reviewers
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS used_approvals "
                "(approval_id TEXT PRIMARY KEY, issuer_id TEXT NOT NULL, "
                "reviewer_id TEXT NOT NULL, result_sha256 TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._ledger_path), timeout=10.0)

    def verify_and_consume(self, claim: ApprovalClaim) -> bool:
        key = self._issuer_keys.get(claim.issuer_id)
        if key is None or claim.reviewer_id not in self._reviewers:
            return False
        expected = sign_approval(claim, key)
        if not hmac.compare_digest(claim.proof, expected):
            return False
        # SQLite enforces the primary key atomically across connections.
        # The transaction commits only when this context exits successfully.
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO used_approvals "
                    "(approval_id, issuer_id, reviewer_id, result_sha256) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        claim.approval_id,
                        claim.issuer_id,
                        claim.reviewer_id,
                        claim.result_sha256,
                    ),
                )
        except sqlite3.IntegrityError:
            return False
        return True
