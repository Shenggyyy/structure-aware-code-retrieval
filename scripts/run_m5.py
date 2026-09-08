"""Run the fixed M5 ablation suite against already-prepared local artifacts."""

import argparse
from pathlib import Path

from structure_aware_retrieval.evaluation.comparison import compare_runs
from structure_aware_retrieval.evaluation.runner import run_experiment

CONFIGS = (
    "hybrid-seed",
    "symbol-seed",
    "structure-full",
    "structure-none",
    "structure-containment",
    "structure-import",
    "structure-call",
    "structure-test",
    "structure-no-containment",
    "structure-no-import",
    "structure-no-call",
    "structure-no-test",
    "structure-symbol-seed",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New suite output directory")
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("Output already exists; choose a new directory")
    root = Path(__file__).resolve().parents[1]
    runs = []
    for name in CONFIGS:
        output = args.output / name
        print(f"Running {name}...", flush=True)
        summary = run_experiment(root / "configs" / f"{name}.toml", output)
        print(f"  quality={summary['quality_fingerprint']}", flush=True)
        runs.append(output)
    compare_runs(runs, args.output / "comparison")
    print(f"Comparison: {(args.output / 'comparison/report.md').resolve()}")


if __name__ == "__main__":
    main()
