"""Rebuild frozen draft benchmarks and prepare source review without running retrieval."""

import argparse
import hashlib
import json
import os
import tempfile
import urllib.request
from pathlib import Path

from structure_aware_retrieval.evaluation.curation import (
    build_curated_benchmark,
    build_repoqa_subset,
)
from structure_aware_retrieval.evaluation.preparation import prepare_benchmark
from structure_aware_retrieval.evaluation.review import check_review, create_pool
from structure_aware_retrieval.evaluation.suite import audit_suite


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New local output directory")
    parser.add_argument("--prepare", action="store_true", help="Allow pinned source/data downloads")
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("Output already exists; choose a new directory")
    root = Path(__file__).resolve().parents[1]
    archive = root / "artifacts/upstream/repoqa-2024-06-23.json.gz"
    if args.prepare:
        for name, destination in (
            ("seed-v1", "benchmark"),
            ("expanded-v1", "expanded"),
            ("repoqa-marshmallow-v1", "public"),
        ):
            print(f"Preparing {name}...", flush=True)
            prepare_benchmark(
                root / f"benchmarks/{name}/benchmark.json", root / f"artifacts/{destination}"
            )
        if not archive.exists():
            source = json.loads(
                (root / "benchmarks/repoqa-marshmallow-v1/recipe.json").read_text(encoding="utf-8")
            )["source"]
            archive.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(source["url"], timeout=60) as response:
                payload = response.read(64 * 1024 * 1024 + 1)
            if (
                len(payload) > 64 * 1024 * 1024
                or hashlib.sha256(payload).hexdigest() != source["sha256"]
            ):
                raise ValueError("Downloaded public archive failed size/checksum validation")
            with tempfile.TemporaryDirectory(prefix=".repoqa-", dir=archive.parent) as temporary:
                local = Path(temporary) / "archive.gz"
                local.write_bytes(payload)
                os.link(local, archive)
    stages = [
        (
            "test",
            "expanded-v1",
            build_curated_benchmark(
                root / "benchmarks/expanded-v1/recipe.json",
                root / "artifacts/expanded/indexes",
                args.output / "test",
            ),
        ),
        (
            "public",
            "repoqa-marshmallow-v1",
            build_repoqa_subset(
                root / "benchmarks/repoqa-marshmallow-v1/recipe.json",
                archive,
                root / "artifacts/public/indexes",
                args.output / "public",
            ),
        ),
    ]
    for role, name, result in stages:
        for filename in (
            "benchmark.json",
            "queries.jsonl",
            "qrels.jsonl",
            "provenance.jsonl",
            "freeze.json",
        ):
            # Ignore only platform checkout newline conversion in committed text artifacts.
            if (args.output / role / filename).read_text(encoding="utf-8") != (
                root / f"benchmarks/{name}/{filename}"
            ).read_text(encoding="utf-8"):
                raise ValueError(f"Rebuilt {role}/{filename} differs from the frozen benchmark")
        print(
            f"Reproduced {role}: {result['query_count']} queries; {result['benchmark_digest']}",
            flush=True,
        )
    audit = audit_suite(root / "benchmarks/suite-v1.json", args.output / "audit")
    for role, config in (("test", "bm25-expanded-test"), ("public", "bm25-repoqa-public")):
        review = args.output / f"{role}-review"
        create_pool(root / f"configs/{config}.toml", [], review, depth=0)
        check_review(
            review,
            review / "judgments.jsonl",
            review / "queries.jsonl",
            args.output / f"{role}-pending",
        )
    print(f"Suite: {audit['query_count']} queries / {audit['repository_count']} repositories.")
    print("Retrieval not executed. All independent reviews remain pending.")


if __name__ == "__main__":
    main()
