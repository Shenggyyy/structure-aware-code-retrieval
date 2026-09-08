import json
import textwrap
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from structure_aware_retrieval.cli import app
from structure_aware_retrieval.indexing import build_index, load_index
from structure_aware_retrieval.relations import (
    build_graph,
    extract_graph,
    load_graph,
    snapshot_sources,
)


@pytest.fixture
def relation_index(tmp_path: Path):
    sources = {
        "src/pkg/__init__.py": "from .helper import target as exported\n",
        "src/pkg/helper.py": """
            def target():
                return 1
            class Worker:
                def step(self):
                    return target()
                def run(self):
                    return self.step()
                def rebound(self):
                    self = object()
                    return self.step()
                @staticmethod
                def static(self):
                    return self.step()
        """,
        "src/pkg/client.py": """
            from pkg import exported
            import pkg.helper as helper
            def run():
                exported()
                helper.target()
                def nested():
                    return exported()
                nested()
            def shadow(exported):
                return exported()
            def assigned():
                exported = helper
                return exported()
            def dynamic(obj):
                obj.target()
                helper.Worker().step()
            def duplicate(): pass
            def duplicate(): pass
            duplicate()
        """,
        "tests/test_helper.py": """
            from pkg import exported
            def test_target():
                assert exported() == 1
        """,
        "src/pkg/cycle_a.py": "from .cycle_b import thing\n",
        "src/pkg/cycle_b.py": "from .cycle_a import thing\nthing()\n",
    }
    repository = tmp_path / "repo"
    for relative, source in sources.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
    database = tmp_path / "index.sqlite"
    build_index(repository, database, max_chunk_lines=2)
    return load_index(database), database, repository


def test_relative_import_alias_reexport_and_nested_calls(relation_index):
    index, _, _ = relation_index
    graph = extract_graph(index)
    pairs = {
        (index.symbols[e.source].qualified_name, index.symbols[e.target].qualified_name, e.kind)
        for e in graph.edges
    }
    assert ("src.pkg.client.run", "src.pkg.helper.target", "call") in pairs
    assert ("src.pkg.client.run.nested", "src.pkg.helper.target", "call") in pairs
    assert ("src.pkg.client.run", "src.pkg.client.run.nested", "call") in pairs
    assert ("src.pkg.client.run", "src.pkg.client.run.nested", "containment") in pairs
    assert ("tests.test_helper.test_target", "src.pkg.helper.target", "test") in pairs
    assert ("tests.test_helper.test_target", "src.pkg.helper.target", "call") not in pairs
    reasons = {row["reason"] for row in graph.unresolved}
    assert {"alias_cycle_or_depth", "ambiguous_binding", "shadowed_or_dynamic_binding"} <= reasons


def test_shadowing_dynamic_receivers_and_method_confidence(relation_index):
    index, _, _ = relation_index
    graph = extract_graph(index)
    calls = [e for e in graph.edges if e.kind == "call"]
    blocked = {
        "src.pkg.client.shadow",
        "src.pkg.client.assigned",
        "src.pkg.helper.Worker.rebound",
        "src.pkg.helper.Worker.static",
    }
    assert not any(index.symbols[e.source].qualified_name in blocked for e in calls)
    method = next(
        e for e in calls if index.symbols[e.source].qualified_name == "src.pkg.helper.Worker.run"
    )
    assert method.confidence == "heuristic"
    assert index.symbols[method.target].name == "step"
    # A constructor may resolve, but the result object's .step() receiver remains dynamic.
    dynamic = [row for row in graph.unresolved if row["reason"] == "dynamic_receiver"]
    assert any(row["expression"] == "helper.Worker().step" for row in dynamic)


def test_graph_roundtrip_snapshot_only_and_repeatability(relation_index, tmp_path: Path):
    index, _, repository = relation_index
    before = extract_graph(index)
    (repository / "src/pkg/client.py").write_text("raise RuntimeError('changed')\n")
    output = tmp_path / "graph.json"
    build_graph(index, output)
    restored = load_graph(output, index)
    assert restored.edges == before.edges
    assert restored.metadata["graph_hash"] == before.metadata["graph_hash"]
    assert len({e.id for e in restored.edges}) == len(restored.edges)
    assert "def run" in snapshot_sources(index)["src/pkg/client.py"]
    with pytest.raises(FileExistsError):
        build_graph(index, output)
    altered = replace(index, metadata={**index.metadata, "snapshot_id": "changed"})
    with pytest.raises(ValueError, match="cache mismatch"):
        load_graph(output, altered)


def test_tampered_graph_and_overlap_are_rejected(relation_index, tmp_path: Path):
    index, _, _ = relation_index
    output = tmp_path / "graph.json"
    build_graph(index, output)
    data = json.loads(output.read_text())
    data["edges"][0]["target"] = "not-a-symbol"
    output.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="missing symbol"):
        load_graph(output, index)
    with pytest.raises(ValueError, match="Overlapping"):
        extract_graph(replace(index, chunks=[*index.chunks, index.chunks[0]]))


def test_graph_publication_failure_cleans_temporary(relation_index, tmp_path, monkeypatch):
    index, _, _ = relation_index
    before = set(tmp_path.iterdir())

    def fail(*args):
        raise OSError("simulated publication failure")

    monkeypatch.setattr("structure_aware_retrieval.relations.os.link", fail)
    with pytest.raises(OSError, match="simulated"):
        build_graph(index, tmp_path / "failed.json")
    assert set(tmp_path.iterdir()) == before


def test_graph_and_structure_cli_without_model(relation_index, tmp_path):
    _, database, _ = relation_index
    graph = tmp_path / "graph.json"
    args = ["graph", "--index", str(database), "--output", str(graph)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert CliRunner().invoke(app, args).exit_code == 1
    result = CliRunner().invoke(
        app,
        [
            "search",
            "target",
            "--strategy",
            "structure",
            "--seed-strategy",
            "bm25",
            "--index",
            str(database),
            "--graph",
            str(graph),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert '"strategy": "structure"' in result.output


def test_ambiguous_import_roots_and_shadowed_module_attributes(relation_index, tmp_path):
    _, _, repository = relation_index
    (repository / "pkg").mkdir()
    (repository / "pkg/__init__.py").write_text("# conflicting import root\n")
    database = tmp_path / "ambiguous.sqlite"
    build_index(repository, database)
    graph = extract_graph(load_index(database))
    assert any(row["reason"] == "ambiguous_module" for row in graph.unresolved)
    (repository / "pkg/__init__.py").unlink()
    (repository / "src/pkg/__init__.py").write_text("helper = object()\n")
    build_index(repository, tmp_path / "shadow.sqlite")
    graph = extract_graph(load_index(tmp_path / "shadow.sqlite"))
    assert any(row["reason"] == "module_attribute_shadowed" for row in graph.unresolved)


def test_unicode_line_separator_and_wildcard_are_conservative(tmp_path):
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "code.py").write_text(
        "# Unicode separator: \u2028 stays on one Python line\n"
        "from unknown import *\ndef run():\n    missing()\n",
        encoding="utf-8",
    )
    build_index(repository, tmp_path / "index.sqlite")
    graph = extract_graph(load_index(tmp_path / "index.sqlite"))
    assert any(row["reason"] == "wildcard_import" for row in graph.unresolved)
