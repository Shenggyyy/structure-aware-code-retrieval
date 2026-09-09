"""Recheck the published real-response archive entirely offline."""

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

import pytest

from structure_aware_retrieval.models import stable_id
from structure_aware_retrieval.qa.provider import OpenAIModel

REPORT = Path(__file__).resolve().parents[2] / "reports" / "m9c-live"


@pytest.fixture
def saved_archive(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def forbid_generation(*args, **kwargs):
        pytest.fail("Archive verification must never call a model")

    monkeypatch.setattr(OpenAIModel, "complete", forbid_generation)
    specification = importlib.util.spec_from_file_location("m9c_live_verify", REPORT / "verify.py")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    workspace = tmp_path / "saved"
    workspace.mkdir()
    manifest = json.loads((REPORT / "manifest.json").read_text(encoding="utf-8"))
    archive_path = REPORT / "run.zip"
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == manifest["archive"]["sha256"]
    assert archive_path.stat().st_size == manifest["archive"]["bytes"]
    with ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == set(manifest["members"])
        assert len(archive.namelist()) == len(manifest["members"])
        require_total = sum(member.file_size for member in archive.infolist())
        assert require_total < 2 * 1024 * 1024
        for member in archive.infolist():
            relative = PurePosixPath(member.filename)
            assert not relative.is_absolute()
            assert not {"", ".", ".."}.intersection(member.filename.split("/"))
            assert "\\" not in member.filename and ":" not in member.filename
            assert relative.parts[0] in {"generation-plans", "runs", "upstream-licenses"}
            assert not member.is_dir()
            target = workspace.joinpath(*relative.parts)
            assert target.resolve().is_relative_to(workspace.resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            data = archive.read(member)
            expected = manifest["members"][member.filename]
            assert len(data) == expected["bytes"]
            assert hashlib.sha256(data).hexdigest() == expected["sha256"]
            target.write_bytes(data)
    return module, workspace


def checksums(directory):
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*")
        if path.is_file()
    }


def test_published_archive_verifies_without_key_model_resources_or_mutation(saved_archive):
    verifier, workspace = saved_archive
    before = checksums(workspace)
    result = verifier.audit(workspace)
    assert result["audit_status"] == "passed"
    assert result["run_status"] == "generation_complete"
    assert result["api_calls"] == 5 and result["judge_calls"] == 0
    assert result["usage"]["tokens"]["input_tokens"] == 15046
    assert result["usage"]["tokens"]["output_tokens"] == 1131
    assert result["usage"]["cost_usd_at_frozen_uncached_rates"] == pytest.approx(0.016374)
    assert all(row["citation_ids_valid"] is True for row in result["results"])
    assert all(row["raw_response_saved"] is True for row in result["results"])
    assert checksums(workspace) == before


def test_rehashed_token_tampering_is_rejected_against_raw_provider_response(saved_archive):
    verifier, workspace = saved_archive
    claim_path = workspace / "generation-plans" / verifier.PLAN_ID / "execution" / "claim.json"
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    run_path = workspace / "runs" / claim["run_id"] / "run.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    run["results"][0]["tokens"]["input"] += 1
    run["fingerprint"] = stable_id(
        {key: value for key, value in run.items() if key != "fingerprint"}
    )
    run_path.write_text(json.dumps(run), encoding="utf-8")
    before = checksums(workspace)
    with pytest.raises(ValueError, match="token metadata mismatch"):
        verifier.audit(workspace)
    assert checksums(workspace) == before
