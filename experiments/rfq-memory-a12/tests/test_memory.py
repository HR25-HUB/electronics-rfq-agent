from pathlib import Path

import pytest

from rfq_memory.core import Evidence, Identity, Proposal, RFQMemoryService, SqliteRepository


@pytest.fixture
def repo(tmp_path):
    r=SqliteRepository(tmp_path/'memory.sqlite3')
    yield r
    r.close()


def p(tenant='A',rfq='r1',line='1',mpn='S203-C16',upi='UPI-1'):
    return Proposal(tenant_id=tenant,rfq_id=rfq,line_id=line,trace_id='test-trace',
        original_text='Synthetic ABB example',identity=Identity(manufacturer='ABB',mpn=mpn,upi=upi))


def proof():
    return Evidence(source_type='trusted_pim',source_id='synthetic-PIM-1',
                    source_hash='sha256:synthetic-fixture',actor_id='test-authorized-verifier')


def test_first_miss_then_verified_reuse(repo):
    svc=RFQMemoryService(repo)
    assert svc.lookup('A','ABB','S203-C16').status=='MISS'
    mid=repo.propose(p())
    assert svc.lookup('A','ABB','S203-C16').status=='MISS'
    repo.verify(mid,proof())
    result=svc.lookup('A','abb','s203-c16')
    assert result.status=='HIT' and result.identity.upi=='UPI-1'
    assert result.llm_matching_calls==0


def test_idempotent_proposal_and_verification(repo):
    mid=repo.propose(p()); assert repo.propose(p())==mid
    repo.verify(mid,proof()); count=repo.outbox_count()
    repo.verify(mid,proof()); assert repo.outbox_count()==count


def test_tenant_isolation(repo):
    mid=repo.propose(p()); repo.verify(mid,proof())
    assert RFQMemoryService(repo).lookup('B','ABB','S203-C16').status=='MISS'


def test_different_suffix_never_matches(repo):
    mid=repo.propose(p()); repo.verify(mid,proof())
    assert RFQMemoryService(repo).lookup('A','ABB','S203-C10').status=='MISS'


def test_revoke_removes_reuse(repo):
    mid=repo.propose(p()); repo.verify(mid,proof()); repo.revoke(mid)
    assert RFQMemoryService(repo).lookup('A','ABB','S203-C16').status=='MISS'
    with pytest.raises(ValueError): repo.verify(mid,proof())


def test_conflicting_upi_requires_review(repo):
    mid=repo.propose(p()); repo.verify(mid,proof())
    mid2=repo.propose(p(rfq='r2',upi='UPI-2')); repo.verify(mid2,proof())
    assert RFQMemoryService(repo).lookup('A','ABB','S203-C16').status=='REVIEW'


def test_persistence_restart(tmp_path):
    path=tmp_path/'memory.sqlite3'
    r=SqliteRepository(path); mid=r.propose(p()); r.verify(mid,proof()); r.close()
    r=SqliteRepository(path)
    assert RFQMemoryService(r).lookup('A','ABB','S203-C16').status=='HIT'
    r.close()


def test_unknown_record_fails(repo):
    with pytest.raises(KeyError): repo.verify('missing',proof())


def test_candidate_not_verified_from_embedded_proof(repo):
    proposed=p().model_copy(update={'evidence':proof()})
    repo.propose(proposed)
    assert RFQMemoryService(repo).lookup('A','ABB','S203-C16').status=='MISS'
