from __future__ import annotations

import argparse
from pathlib import Path

from corporate_rfq.evidence import evaluate_golden_cases, load_golden_cases
from corporate_rfq.service import FakeCatalog, ResolveProductIdentity


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Product Identity golden JSONL cases")
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()

    cases = load_golden_cases(args.dataset)
    metrics, evaluations = evaluate_golden_cases(
        cases,
        ResolveProductIdentity(FakeCatalog()),
    )

    print(metrics.model_dump_json(indent=2))
    failed = [item.model_dump(mode="json") for item in evaluations if not item.passed]
    if failed:
        print("failed_cases=")
        for item in failed:
            print(item)

    # Safety is a hard gate even while overall accuracy is still a measured baseline.
    return 1 if metrics.unsafe_auto_substitution_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
