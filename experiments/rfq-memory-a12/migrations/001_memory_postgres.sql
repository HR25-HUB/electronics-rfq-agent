-- A1.3 schema. Apply only to a dedicated development DB after approval.
CREATE TABLE IF NOT EXISTS rfq_memory (
  id uuid PRIMARY KEY,
  tenant_id text NOT NULL,
  rfq_id text NOT NULL,
  line_id text NOT NULL,
  trace_id text NOT NULL,
  original_text text NOT NULL,
  manufacturer text NOT NULL,
  mpn text NOT NULL,
  upi text NOT NULL,
  manufacturer_key text NOT NULL,
  mpn_key text NOT NULL,
  status text NOT NULL CHECK (status IN ('candidate','verified','superseded')),
  source_type text,
  source_id text,
  source_hash text,
  actor_id text,
  created_at timestamptz NOT NULL,
  verified_at timestamptz,
  UNIQUE (tenant_id, rfq_id, line_id, manufacturer_key, mpn_key, upi),
  CONSTRAINT verified_requires_evidence CHECK (
    status <> 'verified' OR
    (source_type IS NOT NULL AND source_id IS NOT NULL AND source_hash IS NOT NULL AND actor_id IS NOT NULL)
  )
);
CREATE INDEX IF NOT EXISTS rfq_memory_lookup_idx
  ON rfq_memory(tenant_id, manufacturer_key, mpn_key)
  WHERE status = 'verified';
CREATE TABLE IF NOT EXISTS rfq_memory_audit (
  event_id uuid PRIMARY KEY, memory_id uuid NOT NULL REFERENCES rfq_memory(id),
  action text NOT NULL, occurred_at timestamptz NOT NULL
);
CREATE TABLE IF NOT EXISTS rfq_memory_outbox (
  event_id uuid PRIMARY KEY, topic text NOT NULL, memory_id uuid NOT NULL,
  payload jsonb NOT NULL, published_at timestamptz
);
-- Application must enforce tenant ACLs before all lookups and writes.
-- DB role isolation/RLS remains required before production deployment.
