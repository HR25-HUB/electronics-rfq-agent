"""psycopg3 PostgreSQL adapter implementing the A1.2 MemoryRepository interface."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from uuid import uuid4
from .core import Evidence, Identity, Proposal, lookup_key

class PostgresRepository:
    def __init__(self, connection):
        """Use an app-owned psycopg Connection, with schema already migrated."""
        self.db = connection

    def propose(self, p: Proposal) -> str:
        proposed_id = str(uuid4())
        with self.db.transaction():
            row = self.db.execute('''INSERT INTO rfq_memory (
                id,tenant_id,rfq_id,line_id,trace_id,original_text,manufacturer,mpn,upi,
                manufacturer_key,mpn_key,status,created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'candidate',%s)
                ON CONFLICT (tenant_id,rfq_id,line_id,manufacturer_key,mpn_key,upi)
                DO UPDATE SET id=rfq_memory.id RETURNING id''',
                (proposed_id,p.tenant_id,p.rfq_id,p.line_id,p.trace_id,p.original_text,
                 p.identity.manufacturer,p.identity.mpn,p.identity.upi,
                 lookup_key(p.identity.manufacturer),lookup_key(p.identity.mpn),
                 datetime.now(timezone.utc))).fetchone()
            mid = str(row[0])
            self._event_once(mid, 'memory.proposed', 'rfq.memory.proposed')
        return mid

    def _event_once(self, mid: str, action: str, topic: str) -> None:
        exists = self.db.execute('''SELECT 1 FROM rfq_memory_audit
            WHERE memory_id=%s AND action=%s LIMIT 1''',(mid,action)).fetchone()
        if exists:
            return
        eid=str(uuid4()); now=datetime.now(timezone.utc)
        self.db.execute('INSERT INTO rfq_memory_audit VALUES (%s,%s,%s,%s)',(eid,mid,action,now))
        self.db.execute('''INSERT INTO rfq_memory_outbox
            (event_id,topic,memory_id,payload) VALUES (%s,%s,%s,%s::jsonb)''',
            (eid,topic,mid,json.dumps({'memory_id':mid})))

    def verify(self, memory_id: str, evidence: Evidence) -> None:
        with self.db.transaction():
            row=self.db.execute('SELECT status FROM rfq_memory WHERE id=%s FOR UPDATE',(memory_id,)).fetchone()
            if row is None: raise KeyError('Memory record not found')
            if row[0]=='superseded': raise ValueError('Cannot verify revoked memory')
            if row[0]=='verified': return
            self.db.execute('''UPDATE rfq_memory SET status='verified', source_type=%s,
                source_id=%s, source_hash=%s, actor_id=%s, verified_at=%s WHERE id=%s''',
                (evidence.source_type,evidence.source_id,evidence.source_hash,
                 evidence.actor_id,datetime.now(timezone.utc),memory_id))
            self._event_once(memory_id,'memory.verified','rfq.memory.verified')

    def find_verified(self, tenant_id: str, manufacturer: str, mpn: str) -> list[tuple[str, Identity]]:
        rows=self.db.execute('''SELECT id,manufacturer,mpn,upi FROM rfq_memory
            WHERE tenant_id=%s AND manufacturer_key=%s AND mpn_key=%s
              AND status='verified' AND source_hash IS NOT NULL''',
            (tenant_id,lookup_key(manufacturer),lookup_key(mpn))).fetchall()
        return [(str(r[0]),Identity(manufacturer=r[1],mpn=r[2],upi=r[3])) for r in rows]

    def revoke(self, memory_id: str) -> None:
        with self.db.transaction():
            row=self.db.execute('''UPDATE rfq_memory SET status='superseded'
                WHERE id=%s AND status<>'superseded' RETURNING id''',(memory_id,)).fetchone()
            if row: self._event_once(memory_id,'memory.superseded','rfq.memory.superseded')
