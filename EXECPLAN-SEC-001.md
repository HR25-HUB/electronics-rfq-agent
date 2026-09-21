# EXECPLAN — SEC-001

## Goal

Restore a trustworthy green repository security gate by identifying the exact Trivy HIGH/CRITICAL findings on the current `main` baseline and applying the smallest safe remediation.

## Task Contract

### Scope

- reproduce Trivy failure from current `main`;
- capture exact vulnerable package / CVE / installed version / fixed version;
- determine whether the finding is runtime or dev-only;
- apply the smallest dependency or CI correction required;
- preserve current application behavior;
- validate lint, format, strict mypy, tests, optional extras, and Trivy.

### Non-goals

- procurement-domain changes;
- Saleor / 1C / UI work;
- unrelated dependency upgrades;
- architecture refactoring;
- relaxing HIGH/CRITICAL policy to make CI green;
- suppressing a finding without evidence.

### Affected components

Only dependency/security baseline files if required:

```text
pyproject.toml
uv.lock
.github/workflows/ci.yml
```

Diagnostic CI changes must be removed before completion unless they are themselves the justified fix.

### Acceptance criteria

1. Exact Trivy finding is recorded with package, CVE, severity, installed and fixed versions.
2. Root cause is classified as:
   - vulnerable production dependency,
   - vulnerable dev dependency,
   - scanner/configuration defect,
   - false positive with documented evidence.
3. No HIGH/CRITICAL Trivy failure remains.
4. No security policy is weakened merely to pass CI.
5. `uv run ruff check .` PASS.
6. `uv run ruff format --check .` PASS.
7. `uv run mypy src/ --strict` PASS.
8. Full pytest + coverage gate PASS.
9. Optional extras smoke tests PASS.
10. Final diff contains only the minimal security remediation.

## Implementation steps

1. Create a diagnostic Trivy output on this branch.
2. Record the exact finding.
3. Compare it with dependency declarations / lock resolution.
4. Apply minimal remediation.
5. Restore normal SARIF workflow.
6. Run full CI.
7. Reviewer checks for downgrade, suppression, regression and scope expansion.
8. Human approval before merge.

## Risks

- upgrading a transitive dependency may change runtime behavior;
- resolving only one Python matrix may hide version-specific resolution;
- scanner output can be misread if dev dependencies are excluded;
- weakening the gate would create false assurance.

## Rollback

Revert the bounded SEC-001 commits. No application-domain state or data is touched.
