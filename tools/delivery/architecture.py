"""Enforce the existing models -> contracts -> adapters/orchestration boundaries.

Checks static Python imports, including relative and function-local imports.
This is a dependency policy, not a sandbox for arbitrary Python execution.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

PACKAGE = "electronics_rfq_agent"
ORCHESTRATION = {"agent", "cli", "mcp_server", "parser"}


def imports(tree: ast.AST, module: str) -> list[str]:
    result: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = module.split(".")[: -node.level]
                base = ".".join(parts + ([base] if base else []))
            result.append(base)
            result.extend(f"{base}.{alias.name}" for alias in node.names)
    return result


def check(root: Path) -> list[str]:
    package = root / "src" / PACKAGE
    paths = sorted(package.rglob("*.py"))
    if not paths:
        return ["No Python package files found"]
    errors: list[str] = []
    for path in paths:
        relative = path.relative_to(package)
        module = ".".join((PACKAGE, *relative.with_suffix("").parts))
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            errors.append(f"{relative}: {exc}")
            continue
        for imported in imports(tree, module):
            top = imported.split(".")[0]
            local = imported.removeprefix(PACKAGE + ".").split(".")[0]
            forbidden = False
            if relative.as_posix() == "models.py":
                forbidden = top not in sys.stdlib_module_names | {"pydantic"}
            elif relative.parts[0] == "mcp":
                forbidden = imported == PACKAGE or (
                    imported.startswith(PACKAGE + ".") and local in ORCHESTRATION
                )
            elif relative.as_posix() == "parser.py":
                forbidden = imported == PACKAGE or (
                    imported.startswith(PACKAGE + ".")
                    and local
                    in {
                        "agent",
                        "cli",
                        "mcp_server",
                        "mcp",
                    }
                )
            if forbidden:
                errors.append(f"{relative}: forbidden dependency {imported}")
    return errors


if __name__ == "__main__":
    violations = check(Path(__file__).resolve().parents[2])
    for violation in violations:
        print(violation, file=sys.stderr)
    print(f"Architecture policy: {'FAIL' if violations else 'PASS'}")
    raise SystemExit(bool(violations))
