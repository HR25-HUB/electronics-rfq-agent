"""Verified product identity memory; minimal experimental reference implementation."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Evidence(BaseModel):
    source_type: Literal['trusted_pim', 'human_review']
    source_id: str = Field(min_length=1)
    source_hash: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)


class Identity(BaseModel):
    manufacturer: str = Field(min_length=1)
    mpn: str = Field(min_length=1)
    upi: str = Field(min_length=1)


class Proposal(BaseModel):
    tenant_id: str = Field(min_length=1)
    rfq_id: str = Field(min_length=1)
    line_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    original_text: str = Field(min_length=1)
    identity: Identity
    evidence: Evidence | None = None


class MemoryResult(BaseModel):
    status: Literal['HIT', 'MISS', 'REVIEW']
    identity: Identity | None = None
    memory_id: str | None = None
    reason: str
    llm_matching_calls: int = 0


class MemoryRepository(Protocol):
    def propose(self, proposal: Proposal) -> str: ...
    def verify(self, memory_id: str, evidence: Evidence) -> None: ...
    def find_verified(self, tenant_id: str, manufacturer: str, mpn: str) -> list[tuple[str, Identity]]: ...
    def revoke(self, memory_id: str) -> None: ...


def lookup_key(value: str) -> str:
    # Normalize only whitespace / Unicode case. Do not erase meaningful MPN punctuation.
    return ' '.join(value.strip().upper().split())


class SqliteRepository:
    """Durable local test adapter, NOT a substitute for production PostgreSQL."""
    def __init__(self, location: str | Path):
        self.db = sqlite3.connect(str(location))
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS memories (
          id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL,
          rfq_id TEXT NOT NULL, line_id TEXT NOT NULL,
          trace_id TEXT NOT NULL, original_text TEXT NOT NULL,
          manufacturer TEXT NOT NULL, mpn TEXT NOT NULL, upi TEXT NOT NULL,
          manufacturer_key TEXT NOT NULL, mpn_key TEXT NOT NULL,
          status TEXT NOT NULL CHECK(status IN ('candidate','verified','superseded')),
          source_type TEXT, source_id TEXT, source_hash TEXT, actor_id TEXT,
          created_at TEXT NOT NULL, verified_at TEXT,
          UNIQUE(tenant_id,rfq_id,line_id,manufacturer_key,mpn_key,upi)
        );
        CREATE INDEX IF NOT EXISTS memory_identity_idx
          ON memories(tenant_id,manufacturer_key,mpn_key,status);
        CREATE TABLE IF NOT EXISTS audit (
          event_id TEXT PRIMARY KEY, memory_id TEXT NOT NULL,
          action TEXT NOT NULL, occurred_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS outbox (
          event_id TEXT PRIMARY KEY, topic TEXT NOT NULL,
          memory_id TEXT NOT NULL, payload TEXT NOT NULL,
          published_at TEXT
        );
        ''')
        self.db.commit()

    def propose(self, p: Proposal) -> str:
        existing = self.db.execute('''SELECT id FROM memories WHERE tenant_id=? AND rfq_id=? AND line_id=?
          AND manufacturer_key=? AND mpn_key=? AND upi=?''',
          (p.tenant_id,p.rfq_id,p.line_id,lookup_key(p.identity.manufacturer),lookup_key(p.identity.mpn),p.identity.upi)).fetchone()
        if existing: return existing[0]
        mid = str(uuid4())
        with self.db:
            self.db.execute('''INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (mid,p.tenant_id,p.rfq_id,p.line_id,p.trace_id,p.original_text,
              p.identity.manufacturer,p.identity.mpn,p.identity.upi,
              lookup_key(p.identity.manufacturer),lookup_key(p.identity.mpn),
              'candidate',None,None,None,None,utcnow(),None))
            self._event(mid,'memory.proposed','rfq.memory.proposed',{'memory_id':mid})
        return mid

    def _event(self, mid: str, action: str, topic: str, payload: dict) -> None:
        eid=str(uuid4())
        self.db.execute('INSERT INTO audit VALUES (?,?,?,?)',(eid,mid,action,utcnow()))
        self.db.execute('INSERT INTO outbox VALUES (?,?,?,?,NULL)',(eid,topic,mid,json.dumps(payload)))

    def verify(self, memory_id: str, evidence: Evidence) -> None:
        with self.db:
            row=self.db.execute('SELECT status FROM memories WHERE id=?',(memory_id,)).fetchone()
            if row is None: raise KeyError('Memory record not found')
            if row[0]=='superseded': raise ValueError('Cannot verify revoked memory')
            if row[0]=='verified': return
            # Security: evidence must be supplied by trusted application, not copied from LLM output.
            self.db.execute('''UPDATE memories SET status='verified',source_type=?,source_id=?,
                 source_hash=?,actor_id=?,verified_at=? WHERE id=?''',
                 (evidence.source_type,evidence.source_id,evidence.source_hash,evidence.actor_id,utcnow(),memory_id))
            self._event(memory_id,'memory.verified','rfq.memory.verified',{'memory_id':memory_id})

    def revoke(self, memory_id: str) -> None:
        with self.db:
            cur=self.db.execute("UPDATE memories SET status='superseded' WHERE id=? AND status!='superseded'",(memory_id,))
            if cur.rowcount:
                self._event(memory_id,'memory.superseded','rfq.memory.superseded',{'memory_id':memory_id})

    def find_verified(self, tenant_id: str, manufacturer: str, mpn: str) -> list[tuple[str,Identity]]:
        rows=self.db.execute('''SELECT id,manufacturer,mpn,upi FROM memories
          WHERE tenant_id=? AND manufacturer_key=? AND mpn_key=? AND status='verified'
          AND source_hash IS NOT NULL''',
          (tenant_id,lookup_key(manufacturer),lookup_key(mpn))).fetchall()
        return [(r[0],Identity(manufacturer=r[1],mpn=r[2],upi=r[3])) for r in rows]

    def outbox_count(self) -> int:
        return self.db.execute('SELECT COUNT(*) FROM outbox').fetchone()[0]

    def close(self) -> None:
        self.db.close()


class RFQMemoryService:
    def __init__(self, repo: MemoryRepository):
        self.repo=repo

    def lookup(self, tenant_id: str, manufacturer: str, mpn: str) -> MemoryResult:
        matches=self.repo.find_verified(tenant_id,manufacturer,mpn)
        # Multiple memory records for identical identity are fine; conflicting UPIs are not.
        unique={m.upi for _,m in matches}
        if not matches:
            return MemoryResult(status='MISS',reason='No verified exact identity')
        if len(unique)>1:
            return MemoryResult(status='REVIEW',reason='Conflicting verified identities')
        mid,identity=matches[0]
        return MemoryResult(status='HIT',identity=identity,memory_id=mid,
                            reason='Verified exact match',llm_matching_calls=0)
