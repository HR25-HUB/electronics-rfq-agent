# Corporate RFQ Product Identity Development Snapshot

This archive combines:

- upstream electronics-rfq-agent OSS core;
- corporate Product Identity safety layer;
- Golden RFQ 100 adversarial evidence;
- Catalog.App/OpenSearch read-only contracts;
- OpenSearch HTTP transport + EvidencePack;
- manual human-approved live read probe;
- VS Code / GitHub Copilot engineering harness.

## Quick start

### Windows PowerShell

```powershell
./scripts/bootstrap.ps1
./scripts/check.ps1
```

### WSL/Linux/macOS

```bash
bash scripts/bootstrap.sh
bash scripts/check.sh
```

Then open:

`electronics-rfq-agent.code-workspace`

## Corporate focus

Start in `corporate/`.

Key documents:

- corporate/GOLDEN_DATASET.md
- corporate/BASELINE_GOLDEN100.md
- corporate/BASELINE_GOLDEN100_V2.md
- corporate/CATALOG_APP_READ_ONLY_CONTRACT.md
- corporate/OPENSEARCH_READ_ONLY_CONTRACT.md
- corporate/OPENSEARCH_HTTP_EVIDENCE.md
- corporate/LIVE_OPENSEARCH_READ_PROBE.md

## Safety

- Current external integration path is read-only.
- Do not use write-capable production credentials.
- Synthetic Golden RFQ 100 is not production accuracy evidence.
- Human review remains required for security, business policy and production access.

## GitHub source

Repository:
https://github.com/HR25-HUB/electronics-rfq-agent

The ZIP is a development/testing snapshot. Review and merge the corresponding GitHub PR chain before treating it as the repository default branch.
