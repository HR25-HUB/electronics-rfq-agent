---
applyTo: "**/*{adapter,client,transport,opensearch,catalog}*.py"
---

# Integration Instructions

- Production-facing integrations are read-only unless a separate approved change explicitly introduces writes.
- Product candidate retrieval is not a ProductIdentityDecision.
- OpenSearch _score is evidence, not probability.
- Do not invent the private Catalog.App API contract.
- External failures must remain explicit and observable.
- Inject credentials/configuration at runtime using least privilege.
