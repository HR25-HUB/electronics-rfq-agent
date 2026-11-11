"""Run deterministic synthetic checks; never attest production readiness."""

import argparse
import json
from pathlib import Path

from .eval_contract import evaluate_dataset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    report = evaluate_dataset(args.dataset)
    print(json.dumps(report, indent=2))
    return int(bool(report["failed"]))


if __name__ == "__main__":
    raise SystemExit(main())
