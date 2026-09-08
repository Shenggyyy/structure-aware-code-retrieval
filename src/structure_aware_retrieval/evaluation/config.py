"""Portable TOML experiment configuration; paths resolve beside the config file."""

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from structure_aware_retrieval.evaluation.metrics import validate_ks


@dataclass(frozen=True)
class ExperimentConfig:
    source: Path
    benchmark: Path
    indexes: dict[str, Path]
    strategy: str
    unit: str
    ks: tuple[int, ...]
    warmup_queries: int
    repeats: int
    seed: int
    model_cache: Path | None = None
    vectors: dict[str, Path] = field(default_factory=dict)
    graphs: dict[str, Path] = field(default_factory=dict)
    structure: dict = field(default_factory=dict)
    name: str | None = None


def load_config(path: Path) -> ExperimentConfig:
    path = path.resolve()
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    fields = {
        "schema_version",
        "benchmark",
        "indexes",
        "strategy",
        "unit",
        "ks",
        "warmup_queries",
        "repeats",
        "seed",
    }
    if (
        set(data) - {"model_cache", "vectors", "graphs", "structure", "name"} != fields
        or type(data["schema_version"]) is not int
        or data["schema_version"] != 1
    ):
        raise ValueError("Experiment config must use schema_version=1 and the documented fields")
    if data["strategy"] not in ("bm25", "dense", "hybrid", "symbol", "structure") or data[
        "unit"
    ] not in (
        "symbol",
        "file",
    ):
        raise ValueError(
            "Supported strategies: bm25, dense, hybrid, symbol, structure; units: symbol, file"
        )
    seed_strategy = data["strategy"]
    if seed_strategy == "structure":
        from structure_aware_retrieval.structure import parse_structure

        seed_strategy = parse_structure(data.get("structure", {})).seed_strategy
        if not isinstance(data.get("graphs"), dict):
            raise ValueError("Structure retrieval requires graphs")
    elif "structure" in data or "graphs" in data:
        raise ValueError("Only structure retrieval uses graphs or structure settings")
    if "name" in data and (
        not isinstance(data["name"], str)
        or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*", data["name"])
    ):
        raise ValueError("Experiment name must be an identifier")
    if seed_strategy == "bm25":
        if "model_cache" in data or "vectors" in data:
            raise ValueError("BM25 does not use model_cache or vectors")
    elif "model_cache" not in data or not isinstance(data.get("vectors"), dict):
        raise ValueError("Dense strategies require model_cache and vectors")
    for key, minimum in (("warmup_queries", 0), ("repeats", 1), ("seed", 0)):
        if type(data[key]) is not int or data[key] < minimum:
            raise ValueError(f"{key} must be an integer >= {minimum}")
    if not isinstance(data["ks"], list):
        raise ValueError("ks must be a list")
    ks = validate_ks(data["ks"])

    def resolve(value: object) -> Path:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Config paths must be nonblank strings")
        return (path.parent / value).resolve()

    if not isinstance(data["indexes"], dict) or not data["indexes"]:
        raise ValueError("indexes must map repository IDs to SQLite paths")
    if seed_strategy != "bm25" and set(data["vectors"]) != set(data["indexes"]):
        raise ValueError("vectors must exactly match the indexes repository IDs")
    if data["strategy"] == "structure" and set(data["graphs"]) != set(data["indexes"]):
        raise ValueError("graphs must exactly match the indexes repository IDs")
    return ExperimentConfig(
        path,
        resolve(data["benchmark"]),
        {key: resolve(value) for key, value in data["indexes"].items()},
        data["strategy"],
        data["unit"],
        ks,
        data["warmup_queries"],
        data["repeats"],
        data["seed"],
        resolve(data["model_cache"]) if "model_cache" in data else None,
        {key: resolve(value) for key, value in data.get("vectors", {}).items()},
        {key: resolve(value) for key, value in data.get("graphs", {}).items()},
        data.get("structure", {}),
        data.get("name"),
    )
