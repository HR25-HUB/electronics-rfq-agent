import pytest
from rfq_memory.agent import DeepSeekExtractionAdapter, ExtractedRFQ
from rfq_memory.core import Identity, Proposal, RFQMemoryService, SqliteRepository
from rfq_memory.pim import IdentityVerificationService, TrustedPIMMatch

class FakePIM:
    def __init__(self, identity=None):
        self.identity = identity

    async def resolve_exact(self, manufacturer, mpn):
        if self.identity and (manufacturer,mpn)==(self.identity.manufacturer,self.identity.mpn):
            return TrustedPIMMatch(self.identity,'synthetic-pim-ref','synthetic-sha256')
        return None

class FakeAuth:
    def assert_can_verify(self, tenant_id, actor_id):
        if (tenant_id,actor_id)!=('T1','approved-verifier'):
            raise PermissionError('Unapproved verifier')

def proposal(upi='UPI-1'):
    return Proposal(tenant_id='T1',rfq_id='R1',line_id='1',trace_id='trace-1',
                    original_text='SYNTHETIC',identity=Identity(manufacturer='ABB',mpn='S203-C16',upi=upi))

@pytest.mark.asyncio
async def test_verified_pim_identity_reused(tmp_path):
    db=SqliteRepository(tmp_path/'memory.db')
    service=IdentityVerificationService(db, FakePIM(proposal().identity), FakeAuth())
    r=await service.verify_and_store(proposal(),actor_id='approved-verifier')
    assert r.status=='HIT'
    assert RFQMemoryService(db).lookup('T1','ABB','S203-C16').llm_matching_calls==0
    db.close()

@pytest.mark.asyncio
async def test_pim_mismatch_never_verified(tmp_path):
    db=SqliteRepository(tmp_path/'memory.db')
    s=IdentityVerificationService(db,FakePIM(Identity(manufacturer='ABB',mpn='S203-C16',upi='OTHER')),FakeAuth())
    assert (await s.verify_and_store(proposal(),actor_id='approved-verifier')).status=='REVIEW'
    assert RFQMemoryService(db).lookup('T1','ABB','S203-C16').status=='MISS'
    db.close()

@pytest.mark.asyncio
async def test_authorization_precedes_pim_access(tmp_path):
    db=SqliteRepository(tmp_path/'memory.db')
    s=IdentityVerificationService(db,FakePIM(proposal().identity),FakeAuth())
    with pytest.raises(PermissionError):
        await s.verify_and_store(proposal(),actor_id='unapproved')
    db.close()

def test_external_model_requires_explicit_opt_in(monkeypatch):
    monkeypatch.delenv('RFQ_ALLOW_EXTERNAL_LLM',raising=False)
    with pytest.raises(RuntimeError,match='RFQ_ALLOW_EXTERNAL_LLM'):
        DeepSeekExtractionAdapter()

def test_extraction_schema_enforces_positive_quantity():
    from pydantic import ValidationError
    with pytest.raises(ValidationError): ExtractedRFQ(quantity=-1)
