"""Portable TOML experiment configuration; paths resolve beside the config file."""

import tomllib
from dataclasses import dataclass
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
        set(data) != fields
        or type(data["schema_version"]) is not int
        or data["schema_version"] != 1
    ):
        raise ValueError("Experiment config must use schema_version=1 and the documented fields")
    if data["strategy"] != "bm25" or data["unit"] not in ("symbol", "file"):
        raise ValueError("Supported strategy: bm25; supported units: symbol, file")
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
    )
