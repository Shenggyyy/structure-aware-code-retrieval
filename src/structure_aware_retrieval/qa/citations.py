"""Deterministic checks of packed source identities and locations, not semantics."""

import hashlib
import io
import re
from pathlib import PurePosixPath


def validate_source_target(target: object) -> None:
    if not isinstance(target, dict):
        raise ValueError("Invalid source target in QA bundle")
    path = target.get("path")
    if (
        not isinstance(path, str)
        or not path.strip()
        or path == "."
        or "\\" in path
        or re.match(r"^[A-Za-z]:", path)
        or "\x00" in path
        or PurePosixPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
        or PurePosixPath(path).as_posix() != path
        or not isinstance(target.get("qualified_name"), str)
        or not target["qualified_name"].strip()
        or type(target.get("start_line")) is not int
        or target["start_line"] < 1
        or type(target.get("end_line")) is not int
        or target["end_line"] < target["start_line"]
    ):
        raise ValueError("Invalid source path, symbol, or line range in QA bundle")


def audit_evidence(evidence: object) -> dict:
    """Check packed metadata/text; canonical existence is established by the index packer."""
    if not isinstance(evidence, list):
        raise ValueError("Packed evidence must be a list")
    symbols, ranges = set(), {}
    for ordinal, source in enumerate(evidence, 1):
        validate_source_target(source)
        if (
            source.get("id") != f"S{ordinal}"
            or not isinstance(source.get("text"), str)
            or type(source.get("truncated")) is not bool
            or any(
                not isinstance(source.get(key), str)
                or not re.fullmatch(r"[a-f0-9]{64}", source[key])
                for key in ("chunk_id", "symbol_id")
            )
            or source["symbol_id"] in symbols
        ):
            raise ValueError("Prepared evidence has invalid or duplicate source identity")
        text = source["text"]
        if (
            source.get("text_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest()
            or len(io.StringIO(text).readlines()) != source["end_line"] - source["start_line"] + 1
            or any(
                start <= source["end_line"] and source["start_line"] <= end
                for start, end in ranges.get(source["path"], [])
            )
        ):
            raise ValueError("Prepared evidence text, line ranges, or hash are invalid")
        symbols.add(source["symbol_id"])
        ranges.setdefault(source["path"], []).append((source["start_line"], source["end_line"]))
    return {
        "scope": "packed_snapshot_evidence",
        "evidence_count": len(evidence),
        "evidence_ids_valid": True if evidence else None,
        "paths_valid": True if evidence else None,
        "line_ranges_valid": True if evidence else None,
    }
