# Toolchain Freshness — checked 2026-09-19

Verified at export time:

- VS Code 1.134 was released 2026-08-19 and includes side-by-side chats, Prompt Timeline and Agent Host capabilities.
- actions/checkout latest surfaced release: v7.0.1.
- astral-sh/setup-uv latest surfaced release: v10.1.0.
- uv latest surfaced release: 0.12.17 (2026-09-18).
- OpenSearch latest stable surfaced release: 3.8.0; 3.9.0 is still in its September release window.

Engineering decision:
- Existing project workflows are preserved as tested evidence.
- The export workflow uses current action majors.
- Upgrade existing CI action versions in a dedicated PR, not silently inside tested product changes.
