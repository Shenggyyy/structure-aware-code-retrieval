"""Audit committed five-strategy seed results and create a pending source review bundle."""

import argparse
from pathlib import Path

from structure_aware_retrieval.evaluation.comparison import compare_runs
from structure_aware_retrieval.evaluation.review import check_review, create_pool


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New local audit directory")
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("Output already exists; choose a new directory")
    root = Path(__file__).resolve().parents[1]
    # Reuse frozen retrieval outcomes. This phase does not rerun or tune the models.
    runs = [
        root / path
        for path in (
            "reports/m5/runs/hybrid-seed",
            "reports/m4/bm25",
            "reports/m4/dense",
            "reports/m5/runs/symbol-seed",
            "reports/m5/runs/structure-full",
        )
    ]
    compare_runs(runs, args.output / "comparison")
    bundle = args.output / "review"
    manifest = create_pool(root / "configs/bm25-seed.toml", runs, bundle, depth=10)
    check_review(
        bundle, bundle / "judgments.jsonl", bundle / "queries.jsonl", args.output / "pending-check"
    )
    print(
        f"Pool: {manifest['item_count']} candidates, "
        f"{manifest['unjudged_count']} previously unjudged"
    )
    print(f"Pool digest: {manifest['pool_digest']}")
    print(f"Review pages: {(bundle / 'review.md').resolve()}")
    print("All decisions remain pending. Benchmark labels were not changed.")


if __name__ == "__main__":
    main()
