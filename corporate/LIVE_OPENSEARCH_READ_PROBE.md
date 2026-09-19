# Manual Authorized OpenSearch Read Probe

## Purpose

Run exactly one Product Identity probe against an authorized OpenSearch deployment after the read-only transport has been reviewed.

The workflow is **manual only**:

`workflow_dispatch`

It is not triggered by pushes, pull requests or schedules.

## GitHub Environment

Create a protected GitHub Environment:

`rfq-readonly`

Recommended controls:

- required reviewer(s);
- deployment branch restrictions;
- secrets scoped to this environment only.

Required environment secrets:

- `OPENSEARCH_URL`
- `RFQ_LIVE_PROBE_LINE` — one redacted RFQ line

Optional environment secret:

- `OPENSEARCH_AUTHORIZATION` — complete Authorization header value supplied by the approved infrastructure configuration

The repository does not assume Basic, Bearer or another authentication scheme.

## Output

The workflow prints only:

- trace_id
- decision/failure type
- terminal decision status
- relation
- canonical_product_id when accepted
- failure code/retryability when applicable
- non-content OpenSearch EvidencePack

It does **not** print:

- RFQ raw text
- request body
- OpenSearch response body
- Authorization header
- credentials

## Safety constraints

- fixed target index: `gamm_catalog_products`
- HTTP transport exposes search only
- no redirects
- timeout capped at 30 seconds
- no write credential required
- no create/update/delete/bulk API exists in the probe path

## Definition of Done for live execution

A human should approve the Environment deployment, then run the workflow once.

Evidence should show:

- one successful read-only OpenSearch interaction;
- terminal ProductIdentityDecision or classified technical failure;
- trace_id;
- query hash;
- hit count;
- latency/timed_out metadata;
- Golden RFQ 100 remains independently green.

This workflow becomes manually runnable after it exists on the repository default branch.
