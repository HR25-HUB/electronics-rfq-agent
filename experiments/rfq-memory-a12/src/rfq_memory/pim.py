"""Trusted PIM verification boundary. No LLM result can self-verify."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from .core import Evidence, Identity, MemoryRepository, Proposal, RFQMemoryService, MemoryResult

@dataclass(frozen=True)
class TrustedPIMMatch:
    identity: Identity
    source_id: str
    source_hash: str

class TrustedPIMPort(Protocol):
    async def resolve_exact(self, manufacturer: str, mpn: str) -> TrustedPIMMatch | None: ...

class AuthorizedVerifier(Protocol):
    def assert_can_verify(self, tenant_id: str, actor_id: str) -> None: ...

class IdentityVerificationService:
    def __init__(self, memory: MemoryRepository, pim: TrustedPIMPort, authz: AuthorizedVerifier):
        self.memory = memory
        self.pim = pim
        self.authz = authz

    async def verify_and_store(self, proposal: Proposal, *, actor_id: str) -> MemoryResult:
        self.authz.assert_can_verify(proposal.tenant_id, actor_id)
        match = await self.pim.resolve_exact(proposal.identity.manufacturer, proposal.identity.mpn)
        if match is None:
            return MemoryResult(status='REVIEW', reason='PIM identity not verified')
        if match.identity != proposal.identity:
            return MemoryResult(status='REVIEW', reason='PIM returned different identity')
        if not match.source_id or not match.source_hash:
            return MemoryResult(status='REVIEW', reason='Missing PIM provenance')
        mid = self.memory.propose(proposal)
        self.memory.verify(mid, Evidence(source_type='trusted_pim', source_id=match.source_id,
                                         source_hash=match.source_hash, actor_id=actor_id))
        return RFQMemoryService(self.memory).lookup(
            proposal.tenant_id, proposal.identity.manufacturer, proposal.identity.mpn)
