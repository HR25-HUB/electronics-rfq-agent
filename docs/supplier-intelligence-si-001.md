# SI-001 — Supplier Intelligence Vertical Slice

## Purpose

Extend the current RFQ pipeline from product lookup toward an auditable supplier
decision while keeping all business side effects outside the AI/agent boundary.

The reference pattern is informed by the AWS sample RFQ assistant:
`aws-samples/sample-rfq-agent-strands-multi-agent`.

## Business model

The value chain is:

```text
Verified RFQ product
→ gather supplier evidence
→ normalize supplier candidates
→ deterministic policy
→ human-reviewable SupplierDecision
```

The goal is to reduce manual supplier research and comparison time without allowing
an LLM to become the authority for purchasing, pricing, or ERP mutations.

## What we adopt from the AWS sample

- supplier performance as explicit tools/capabilities;
- compliance evidence as a first-class input;
- tool-oriented integration rather than a single giant prompt;
- MCP as a potential boundary to external enterprise systems;
- persistent context only as convenience, not as system-of-record state.

## What we deliberately do not copy

- AWS-specific infrastructure (Bedrock AgentCore, Athena, Glue, Cognito);
- unrestricted SQL tools for production agents;
- regex extraction as the primary structured-data mechanism;
- direct agent-to-ERP mutations;
- large monolithic agent modules.

## SI-001 contract

Input:

- one verified product identity;
- requested quantity;
- one or more normalized supplier candidates;
- evidence IDs attached to every candidate.

Output:

- `ACCEPTED`;
- `REVIEW_REQUIRED`;
- `NO_SUPPLIER_FOUND`.

The initial policy is intentionally narrow:

1. candidate must pass compliance;
2. candidate stock must cover requested quantity;
3. confidence must be at least 0.85;
4. among eligible candidates select lowest unit price;
5. break price ties by lead time, then confidence, then supplier ID.

This ordering is a prototype policy, not a final commercial policy.

## Production evolution

Later slices should replace mock/normalized candidates with ports/adapters for:

- Catalog.App / PIM;
- 1C KA 2.5 read models;
- supplier APIs;
- OpenSearch evidence retrieval;
- Prefect evidence collection;
- Redpanda lifecycle events.

Any action that changes price, customer data, purchase commitments, or 1C state must
use:

```text
AI proposes
→ typed validation
→ policy-as-code
→ deterministic gate
→ human approval when required
→ execution
→ audit
```

## Definition of Done

- Pydantic v2 contracts validate supplier evidence and decisions.
- All terminal outcomes have unit tests.
- No new dependency is introduced.
- No ERP write path is added.
- Existing RFQ/quote API remains unchanged.
- ruff, type checking, and pytest remain green.
