-- Apply after migration 001 in a dedicated isolated PostgreSQL test database.
-- Atomic write-once identity for memory business events.
CREATE UNIQUE INDEX IF NOT EXISTS rfq_memory_audit_once_idx
    ON rfq_memory_audit(memory_id, action);
