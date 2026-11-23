"""Real PostgreSQL integration tests. Require a deliberately isolated local *_test DB."""
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from rfq_memory.core import Evidence, Identity, Proposal, RFQMemoryService
from rfq_memory.postgres import PostgresRepository

try:
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict
except ImportError:
    psycopg = None

DSN = os.environ.get('RFQ_TEST_POSTGRES_DSN')
MIGRATIONS = Path(__file__).resolve().parents[1] / 'migrations'


def connect(schema):
    con = psycopg.connect(DSN, autocommit=True, connect_timeout=4)
    con.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
    return con


@pytest.fixture
def pg():
    if psycopg is None or not DSN:
        if os.getenv('RFQ_REQUIRE_POSTGRES') == '1':
            pytest.fail('PostgreSQL required: missing psycopg or RFQ_TEST_POSTGRES_DSN')
        pytest.skip('No configured test PostgreSQL')
    params = conninfo_to_dict(DSN)
    if params.get('dbname') != 'rfq_memory_test' or params.get('host') not in ('localhost', '127.0.0.1'):
        pytest.fail('Unsafe DSN: only local rfq_memory_test permitted')
    schema = 'a14_' + uuid4().hex
    admin = psycopg.connect(DSN, autocommit=True, connect_timeout=4)
    admin.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    try:
        con = connect(schema)
        try:
            for name in ('001_memory_postgres.sql', '002_a14_event_idempotency.sql'):
                con.execute((MIGRATIONS / name).read_text(encoding='utf-8'))
            yield con, schema
        finally:
            con.close()
    finally:
        admin.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
        admin.close()


def proposal(rfq='rfq-1', upi='UPI-A'):
    return Proposal(tenant_id='T1', rfq_id=rfq, line_id='1', trace_id='synthetic-trace',
                    original_text='SYNTHETIC ABB RFQ',
                    identity=Identity(manufacturer='ABB', mpn='S203-C16', upi=upi))


def evidence():
    return Evidence(source_type='trusted_pim', source_id='synthetic',
                    source_hash='synthetic-hash', actor_id='test-actor')


def count(con, table):
    assert table in ('rfq_memory', 'rfq_memory_audit', 'rfq_memory_outbox')
    return con.execute(f'SELECT count(*) FROM {table}').fetchone()[0]


def test_verified_identity_persists_across_connections(pg):
    con, schema = pg
    repo = PostgresRepository(con)
    mid = repo.propose(proposal())
    assert RFQMemoryService(repo).lookup('T1','ABB','S203-C16').status == 'MISS'
    repo.verify(mid, evidence())
    with connect(schema) as other:
        result = RFQMemoryService(PostgresRepository(other)).lookup('T1','ABB','S203-C16')
        assert result.status == 'HIT'
        assert result.llm_matching_calls == 0


def test_duplicate_delivery_writes_one_event_per_action(pg):
    con, _ = pg
    repo = PostgresRepository(con)
    mid = repo.propose(proposal())
    assert repo.propose(proposal()) == mid
    repo.verify(mid, evidence())
    repo.verify(mid, evidence())
    assert (count(con,'rfq_memory'),count(con,'rfq_memory_audit'),count(con,'rfq_memory_outbox')) == (1,2,2)


def test_conflicting_verified_upis_go_to_review(pg):
    con, _ = pg
    repo = PostgresRepository(con)
    for rfq, upi in (('r1','UPI-A'),('r2','UPI-B')):
        repo.verify(repo.propose(proposal(rfq=rfq, upi=upi)), evidence())
    assert RFQMemoryService(repo).lookup('T1','ABB','S203-C16').status == 'REVIEW'
    assert RFQMemoryService(repo).lookup('T2','ABB','S203-C16').status == 'MISS'


def test_outbox_failure_rolls_back_proposal(pg):
    con, _ = pg
    con.execute("ALTER TABLE rfq_memory_outbox ADD CONSTRAINT block_proposal CHECK (topic <> 'rfq.memory.proposed')")
    repo = PostgresRepository(con)
    with pytest.raises(psycopg.errors.CheckViolation):
        repo.propose(proposal())
    assert count(con,'rfq_memory') == 0
    assert count(con,'rfq_memory_audit') == 0
    con.execute('ALTER TABLE rfq_memory_outbox DROP CONSTRAINT block_proposal')
    assert repo.propose(proposal())


def test_outbox_failure_rolls_back_verification(pg):
    con, _ = pg
    repo = PostgresRepository(con)
    mid = repo.propose(proposal())
    con.execute("ALTER TABLE rfq_memory_outbox ADD CONSTRAINT block_verification CHECK (topic <> 'rfq.memory.verified')")
    with pytest.raises(psycopg.errors.CheckViolation):
        repo.verify(mid, evidence())
    assert con.execute('SELECT status FROM rfq_memory WHERE id=%s',(mid,)).fetchone()[0] == 'candidate'
    assert RFQMemoryService(repo).lookup('T1','ABB','S203-C16').status == 'MISS'
    con.execute('ALTER TABLE rfq_memory_outbox DROP CONSTRAINT block_verification')
    repo.verify(mid,evidence())
    assert RFQMemoryService(repo).lookup('T1','ABB','S203-C16').status == 'HIT'


def test_concurrent_replay_is_idempotent(pg):
    con, schema = pg
    def worker(_):
        with connect(schema) as connection:
            return PostgresRepository(connection).propose(proposal())
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(worker,range(8)))
    assert len(set(ids)) == 1
    assert (count(con,'rfq_memory'),count(con,'rfq_memory_audit'),count(con,'rfq_memory_outbox')) == (1,1,1)


def test_revoke_and_replay(pg):
    con, _ = pg
    repo = PostgresRepository(con)
    mid = repo.propose(proposal())
    repo.verify(mid,evidence())
    repo.revoke(mid)
    repo.revoke(mid)
    assert RFQMemoryService(repo).lookup('T1','ABB','S203-C16').status == 'MISS'
    assert (count(con,'rfq_memory_audit'),count(con,'rfq_memory_outbox')) == (3,3)
