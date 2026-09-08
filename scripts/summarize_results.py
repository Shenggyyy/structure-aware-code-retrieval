"""Validate and summarize saved retrieval results without rerunning experiments."""

import argparse
from pathlib import Path

from structure_aware_retrieval.evaluation.overview import build_overview, write_overview


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("reports/m6c"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/overview"))
    parser.add_argument("--check", action="store_true", help="Check existing output without writes")
    args = parser.parse_args()
    try:
        summary = build_overview(args.results)
        write_overview(summary, args.output, check=args.check)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    action = "Checked" if args.check else "Wrote"
    print(f"{action} overview of {summary['scope']['validated_runs']} validated saved runs.")


if __name__ == "__main__":
    main()
