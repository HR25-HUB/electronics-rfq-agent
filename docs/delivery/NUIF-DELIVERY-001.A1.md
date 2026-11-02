# NUIF DELIVERY 001 A1

## Scope and design

One PR in HR25-HUB/electronics-rfq-agent, based on main at
`fcca4f22b18d71fd1547ddbcf2919b5edad4b29d`. This is an owned fork with
real RFQ source, unit/integration tests, uv.lock and existing CI. The smaller
ai-wholesale-platform has mostly stubs and one trivial test; raytsystem-public-os
is a substantially larger unrelated workspace product. The RFQ repository is
the smallest relevant delivery slice. Work does not target the upstream fork.

Extend existing CI rather than create duplicate quality checks. Preserve Python
3.10/3.11/3.12, Ruff, strict mypy, optional extras, Trivy and 80% coverage.
Use frozen dependency synchronization. Add static import boundaries and negative
controls, secret scanning and a wheel/sdist candidate. No tags, releases,
registry publishing, deployment or production credentials are used by these additions.
Existing release, benchmark/Pages and scorecard workflows remain outside this PR.
Existing benchmark workflow deploys Pages on main pushes; do not merge this PR
as part of this task.

## Inspection on 2026-11-02

- Existing CI: lint, format, strict mypy, full pytest suite with coverage,
  Trivy filesystem scan, optional langchain/agents smoke tests.
- Release: v* tags build distributions, publish PyPI, sign and create releases.
- Benchmark: main pushes can publish GitHub Pages. Scorecard runs separately.
- Branch endpoint reported `protected: false`, required checks disabled.
- Repository rulesets endpoint returned an empty list. The detailed branch
  protection endpoint returned 403 (integration administration permission missing).
- Recent unrelated PR CI failed at lint; that history does not establish this
  branch's result. No existing open PR is changed or merged.

## Added gates and evidence

`Architecture policy` checks static imports at every nesting level, resolves
relative imports, rejects missing source and syntax errors. Domain models may
depend only on Python's standard library and Pydantic. ERP adapters must not
import agent/parser/CLI/MCP server orchestration. The parser must not depend on
ERP adapters or CLI/orchestration. Telemetry retains its existing HTTP exporter.
This is a bounded static dependency check, not a detector for arbitrary dynamic
Python imports or a complete architecture proof. Policy changes require review.

`Secret scan` uses pinned Gitleaks Action with full Git history available and
PR event scanning. It has read-only contents access and PR comments disabled.
`Verified release candidate` runs only after quality, extras, architecture and
secrets pass. It verifies checkout HEAD equals GITHUB_SHA, builds wheel/sdist,
installs the actual wheel without re-resolving dependencies, and runs the tests
against the installed package. The coverage source is the installed package.

The artifact contains wheel, sdist, `release-evidence.json`, wheel JUnit and
coverage reports, uv.lock and exported locked runtime requirements. The manifest
records tested commit SHA, PR head SHA, exact run/attempt URL, prerequisite
results and per-distribution SHA-256. On a PR the tested SHA is GitHub's synthetic
merge commit; it is intentionally distinguished from the PR head SHA. The
upload artifact ID/URL and transport ZIP digest are recorded in the job summary.
Transport ZIP digest and wheel/sdist digests are different identities.

`NUIF delivery gate` uses always() and requires every prerequisite, including
candidate build/upload, to succeed. Skipped and cancelled jobs fail the gate.
There are no path filters on required CI. Merge-group events are included;
merge queue compatibility must still be demonstrated before enabling a queue.

## Ruleset activation and acceptance

`required-ruleset.json` was applied through the authenticated GitHub CLI as
ruleset 26348579, then read back through the API. It is active, has no bypass
actors, and binds the required check to the observed GitHub Actions app (15368).
It requires PR review, the aggregate delivery check and an up-to-date branch,
with no bypass actors. Reviewers must independently inspect workflow and policy
changes; status names alone cannot prevent a malicious rewrite of the gate.

Do not claim merge blocking merely because YAML or JSON exists. Before declaring
A1 complete, demonstrate on the real PR that an intentional architecture failure
makes the required gate fail and GitHub reports merging blocked; restore the
same PR to its correct commit and obtain a green run and candidate. Do not merge.
Negative unit controls prove the checker rejects violations; repository settings
must also enforce it. On this same real PR, temporary commit
`f900661e0cb0c2e94095136acb0963a322b7a67e` introduced a model-to-httpx dependency.
Run 41402909396 rejected it in `Architecture policy`; `NUIF delivery gate` failed
and the candidate was skipped. With draft status removed, GitHub reported
`mergeable_state: blocked`. The test commit is reverted before handoff; no merge
operation was attempted.

## Verification and use

```sh
python -m unittest discover -s tools/delivery -v
python tools/delivery/architecture.py
uv sync --frozen --extra dev
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy src/ --strict
uv run --no-sync pytest tests/ --cov=src --cov-fail-under=80
```

Download the candidate artifact from its exact run, extract it to `dist/`, then
run `python tools/delivery/evidence.py verify` from the matching source checkout.
Independently check the manifest commit and run URL against GitHub. A manifest
and checksum detect corruption relative to trusted evidence; they are not signed
provenance and do not establish publisher authenticity by themselves.

This slice does not claim a deployment, staging qualification, SBOM, signed
attestation or supply-chain certification. Candidate artifacts expire after 30
days; archive audited bundles in the organization's evidence store when adopted.

## Implementation and acceptance plan

- [x] Inspect actual stack, workflows, source, tests and branch/ruleset reads.
- [x] Add negative policy tests; observe failure before checker implementation.
- [x] Add digest corruption/missing/empty-artifact tests before implementation.
- [x] Implement dependency checker and evidence manifest verifier.
- [x] Integrate gates, frozen dependencies, candidate and always-run aggregate.
- [x] Obtain passing source lint/typecheck/tests on the real PR.
- [x] Activate and read back the required-check ruleset with administrator access.
- [x] Demonstrate a rejected architecture violation on the real PR without merging.
- [ ] Obtain a restored fully green commit and candidate on the PR.
- [ ] Verify downloaded artifact digests and retain run links as final evidence.

Local installation was attempted twice but PyPI timed out resolving hatchling;
project typecheck/tests/build are not locally verified. The independent stdlib
gate tests and architecture check can run without project dependencies. Final
execution status belongs in the audit report and PR, not inferred from this plan.

## Observed security blocker

Real PR run 41402529268 passed lint, formatting, strict mypy and source tests on
Python 3.10/3.11/3.12. The Python 3.12 log reports 323 passed, 3 skipped and
90.39% coverage. Architecture, Gitleaks and both optional extras also passed.
Existing Trivy scanning rejected vulnerabilities in the unchanged uv.lock;
the aggregate failed and candidate build was correctly skipped. No verified
candidate, wheel digest or signed provenance is claimed for this run.

The complete paginated GitHub code-scanning snapshot contains 116 findings:
10 critical, 52 high, 48 medium and 6 low. These are scanner findings, not
independently demonstrated exploits. The affected lockfile includes optional
extras as well as runtime dependencies; triage must retain that distinction.

Dependency remediation must preserve the gate: export the complete findings,
group by package and installed/fixed version, update affected direct/transitive
constraints and regenerate uv.lock, then rerun all Python versions and optional
extras. Check API/behavior compatibility of MCP, PyJWT, HTTP/OAuth libraries and
document parsers. Do not add a blanket ignore, lower severity, remove scanning,
or turn a failed build into an approved candidate. The final PR must stay draft
until security remediation and actual candidate verification succeed.
