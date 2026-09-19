---
applyTo: "**/*.py"
---

# Python Instructions

- Python 3.11+; corporate CI targets Python 3.12.
- Use Pydantic v2 for external/domain contracts.
- Keep domain logic independent from adapters.
- Never convert technical failures into business NOT_FOUND.
- Use ruff, pyrefly/strict typing where configured, and pytest.
- Never weaken tests or Golden RFQ expected labels merely to obtain green CI.
- No credentials or customer-identifying data in source, tests or logs.
