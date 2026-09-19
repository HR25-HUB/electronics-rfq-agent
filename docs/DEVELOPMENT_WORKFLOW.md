# VS Code + Git + GitHub Copilot Workflow

Open:
`electronics-rfq-agent.code-workspace`.

Recommended side-by-side agent roles:
- Architect
- Implementer
- Reviewer

## Standard change

```text
Requirement
→ Architect plan
→ branch
→ executable contract/tests
→ implementation
→ local quality gates
→ Golden RFQ 100
→ Draft PR
→ CI
→ read-only review
→ human approval
→ merge
```

## Commands

Bootstrap:
`bash scripts/bootstrap.sh`

Full checks:
`bash scripts/check.sh`

Golden:
`make golden`

Corporate tests:
`make corporate-check`

## Git rules

- branch per vertical slice;
- small commits;
- no direct main changes for business policy;
- PR evidence required;
- human merge for policy/security/integration changes.

## Copilot context

Persistent:
- .github/copilot-instructions.md
- AGENTS.md
- .github/instructions/*

Reusable:
- .github/skills/*

Explicit prompts:
- .github/prompts/*

Roles:
- .github/agents/*
