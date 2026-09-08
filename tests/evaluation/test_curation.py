import gzip
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from structure_aware_retrieval.evaluation.curation import (
    build_curated_benchmark,
    build_repoqa_subset,
)
from structure_aware_retrieval.evaluation.dataset import corpus_hash, load_benchmark
from structure_aware_retrieval.indexing import build_index, load_index


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def draft_recipe(experiment: Path) -> Path:
    folder = experiment.parent
    manifest = json.loads((folder / "benchmark/benchmark.json").read_text())
    recipe = {k: manifest[k] for k in ("schema_version", "id", "version", "split", "repositories")}
    recipe["annotation_files"] = ["annotation.json"]
    write_json(folder / "recipe.json", recipe)
    write_json(
        folder / "annotation.json",
        {
            "schema_version": 1,
            "repository_id": "fixture",
            "questions": [
                {
                    "id": "q1",
                    "category": "symbol",
                    "family": "checksum",
                    "text": "Locate calculate_checksum",
                    "targets": [
                        {
                            "path": "client.py",
                            "name": "calculate_checksum",
                            "grade": 2,
                            "rationale": "Synthetic target.",
                        }
                    ],
                }
            ],
        },
    )
    shutil.copyfile(folder / "index.sqlite", folder / "fixture.sqlite")
    return folder / "recipe.json"


def test_curated_labels_are_provisional_bound_and_reproducible(draft_recipe):
    folder = draft_recipe.parent
    first = build_curated_benchmark(draft_recipe, folder, folder / "first")
    second = build_curated_benchmark(draft_recipe, folder, folder / "second")
    assert first == second
    assert first["retrieval_executed"] is False
    assert first["annotation_status"] == "provisional"
    assert first["query_count"] == first["judgment_count"] == 1
    for path in (folder / "first").iterdir():
        assert path.read_bytes() == (folder / "second" / path.name).read_bytes()
    with pytest.raises(FileExistsError):
        build_curated_benchmark(draft_recipe, folder, folder / "first")


@pytest.mark.parametrize(
    "change",
    [
        "missing_target",
        "wrong_line",
        "grade",
        "cross_file",
        "escape",
        "missing_repository",
        "duplicate_query",
    ],
)
def test_bad_drafts_are_not_published(draft_recipe, change):
    folder = draft_recipe.parent
    spec = json.loads((folder / "annotation.json").read_text())
    query = spec["questions"][0]
    if change == "missing_target":
        query["targets"][0]["name"] = "absent"
    elif change == "wrong_line":
        query["targets"][0]["start_line"] = 9999
    elif change == "grade":
        query["targets"][0]["grade"] = True
    elif change == "cross_file":
        query["category"] = "cross_file"
    elif change == "escape":
        query["targets"][0]["path"] = "../client.py"
    elif change == "missing_repository":
        spec["repository_id"] = "missing"
    else:
        spec["questions"].append(query)
    write_json(folder / "annotation.json", spec)
    with pytest.raises(ValueError):
        build_curated_benchmark(draft_recipe, folder, folder / "bad")
    assert not (folder / "bad").exists()


def test_initializer_names_and_ambiguous_overloads_require_explicit_location(draft_recipe):
    folder = draft_recipe.parent
    repo = folder / "additional"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg/__init__.py").write_text(
        "def f():\n    return 1\n\ndef f():\n    return 2\n", encoding="utf-8"
    )
    build_index(repo, folder / "overloaded.sqlite")
    index = load_index(folder / "overloaded.sqlite")
    recipe = json.loads(draft_recipe.read_text())
    recipe["repositories"][0]["corpus_hash"] = corpus_hash(index)
    write_json(draft_recipe, recipe)
    shutil.copyfile(folder / "overloaded.sqlite", folder / "fixture.sqlite")
    spec = json.loads((folder / "annotation.json").read_text())
    target = spec["questions"][0]["targets"][0]
    target.update(path="pkg/__init__.py", name="f")
    write_json(folder / "annotation.json", spec)
    with pytest.raises(ValueError, match="uniquely"):
        build_curated_benchmark(draft_recipe, folder, folder / "ambiguous")
    target["start_line"] = 4
    write_json(folder / "annotation.json", spec)
    build_curated_benchmark(draft_recipe, folder, folder / "explicit")
    benchmark = load_benchmark(folder / "explicit/benchmark.json")
    assert benchmark.judgments[0].target.qualified_name == "pkg.f"
    assert benchmark.judgments[0].target.start_line == 4


@pytest.fixture
def public_recipe(experiment: Path):
    folder = experiment.parent
    repo = folder / "public-source"
    repo.mkdir()
    content = (
        "# café\ndef decorate(fn):\n    return fn\n\n@decorate\ndef needle(value):\n"
        '    """café"""\n    return value + 1\n'
    )
    (repo / "source.py").write_text(content, encoding="utf-8", newline="\n")
    build_index(repo, folder / "public.sqlite")
    index = load_index(folder / "public.sqlite")
    needle = {
        "name": "needle",
        "path": "source.py",
        "start_line": 5,
        "end_line": 8,
        "start_byte": content.encode().index(b"def needle"),
        "end_byte": len(content.encode()) - 1,
        "description": "Describe the incrementing function.",
    }
    data = {
        "python": [
            {
                "repo": "example/public",
                "commit_sha": "a" * 40,
                "content": {"source.py": content},
                "needles": [needle],
            }
        ]
    }
    archive = folder / "public.json.gz"
    archive.write_bytes(gzip.compress(json.dumps(data).encode()))
    recipe = {
        "schema_version": 1,
        "id": "public-fixture",
        "version": "1",
        "split": "test",
        "repositories": [
            {
                "id": "public",
                "url": "https://github.com/example/public.git",
                "ref": "a" * 40,
                "commit": "a" * 40,
                "license": "fixture",
                "corpus_hash": corpus_hash(index),
            }
        ],
        "source": {
            "url": "https://example.invalid/public.gz",
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "release": "fixture",
            "license": "fixture",
            "language": "python",
            "repository": "example/public",
            "expected_needles": 1,
        },
    }
    path = folder / "public-recipe.json"
    write_json(path, recipe)
    return path, archive, data


def test_public_mapping_accounts_for_utf8_decorators_and_zero_based_lines(public_recipe):
    path, archive, _ = public_recipe
    output = path.parent / "adapted"
    result = build_repoqa_subset(path, archive, path.parent, output)
    benchmark = load_benchmark(output / "benchmark.json")
    assert result["annotation_status"] == "provisional"
    assert benchmark.judgments[0].target.start_line == 5  # decorator included
    assert benchmark.judgments[0].target.end_line == 8
    assert benchmark.queries[0].text == "Describe the incrementing function."


@pytest.mark.parametrize(
    "change",
    ["checksum", "commit", "file", "line", "byte", "name", "count", "duplicate_repository"],
)
def test_public_mismatches_fail_closed(public_recipe, change):
    path, archive, data = public_recipe
    recipe = json.loads(path.read_text())
    upstream = data["python"][0]
    if change == "checksum":
        recipe["source"]["sha256"] = "0" * 64
    elif change == "count":
        recipe["source"]["expected_needles"] = 2
    else:
        if change == "commit":
            upstream["commit_sha"] = "b" * 40
        elif change == "file":
            upstream["content"]["source.py"] += "# changed\n"
        elif change == "line":
            upstream["needles"][0]["start_line"] += 1
        elif change == "byte":
            upstream["needles"][0]["start_byte"] -= 1
        elif change == "name":
            upstream["needles"][0]["name"] = "missing"
        else:
            data["python"].append(upstream)
        archive.write_bytes(gzip.compress(json.dumps(data).encode()))
        recipe["source"]["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    write_json(path, recipe)
    with pytest.raises(ValueError):
        build_repoqa_subset(path, archive, path.parent, path.parent / "bad")
    assert not (path.parent / "bad").exists()
