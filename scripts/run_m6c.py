"""Run fixed retrieval strategies and profile fresh builds using prepared local sources."""

import argparse
from pathlib import Path

from structure_aware_retrieval.evaluation.experiments import run_suite


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New suite output directory")
    parser.add_argument(
        "--allow-provisional",
        action="store_true",
        help="Explicitly permit draft-label scores; does not complete independent review",
    )
    args = parser.parse_args()
    result = run_suite(
        Path(__file__).resolve().parents[1], args.output, allow_provisional=args.allow_provisional
    )
    print(f"Completed {len(result['runs'])} runs; status: {result['result_status']}.")
    print(f"Report: {(args.output / 'report.md').resolve()}")


if __name__ == "__main__":
    main()
