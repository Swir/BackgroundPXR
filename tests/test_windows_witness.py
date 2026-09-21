from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from tools.windows_witness import (
    STEP_INSTRUCTIONS,
    WitnessError,
    extract_candidate,
    new_evidence,
    record_result,
    run_guided_witness,
    verify_evidence,
)


_SOURCE_SHA = "c" * 40


def _package(tmp_path: Path, *, version: str = "1.0.0rc1") -> tuple[Path, Path]:
    archive = tmp_path / f"BackgroundPXR-{version}-Windows.zip"
    checksum = tmp_path / f"{archive.name}.sha256"
    build_info = (
        f"version={version}\n"
        f"source_sha={_SOURCE_SHA}\n"
        "channel=qualification\n"
    )

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("BackgroundPXR/BackgroundPXR.exe", b"MZ\x00witness")
        bundle.writestr("BackgroundPXR/BUILD_INFO.txt", build_info.encode("utf-8"))
        bundle.writestr(
            "BackgroundPXR/README.md",
            b"BackgroundPXR\nby Swir\nhttps://github.com/Swir\n",
        )
        bundle.writestr(
            "BackgroundPXR/RELEASE_NOTES.md",
            f"# BackgroundPXR {version} - qualification\n".encode("utf-8"),
        )

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive, checksum


def _completed_evidence(tmp_path: Path) -> tuple[dict[str, object], Path, Path]:
    archive, checksum = _package(tmp_path)
    evidence = new_evidence(archive, checksum)
    environment = evidence["environment"]
    assert isinstance(environment, dict)
    environment["windows_version"] = "Windows-11-test"
    environment["display_scaling_percent"] = 125
    record_result(evidence, model="u2net")
    for step_id in range(1, 9):
        record_result(
            evidence,
            step_id=step_id,
            status="pass",
            notes=f"verified step {step_id}",
        )
    return evidence, archive, checksum


def test_new_evidence_is_bound_to_exact_package(tmp_path: Path) -> None:
    archive, checksum = _package(tmp_path)
    evidence = new_evidence(archive, checksum)

    candidate = evidence["candidate"]
    assert isinstance(candidate, dict)
    assert candidate["version"] == "1.0.0rc1"
    assert candidate["source_sha"] == _SOURCE_SHA
    assert candidate["archive"] == archive.name
    assert candidate["sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()

    steps = evidence["steps"]
    assert isinstance(steps, list)
    assert [item["id"] for item in steps] == list(range(1, 9))
    assert {item["status"] for item in steps} == {"pending"}


def test_complete_manual_witness_passes(tmp_path: Path) -> None:
    evidence, archive, checksum = _completed_evidence(tmp_path)
    verify_evidence(evidence, archive, checksum)


def test_pending_manual_step_blocks_acceptance(tmp_path: Path) -> None:
    evidence, archive, checksum = _completed_evidence(tmp_path)
    steps = evidence["steps"]
    assert isinstance(steps, list)
    steps[5]["status"] = "pending"

    with pytest.raises(WitnessError, match="step 6"):
        verify_evidence(evidence, archive, checksum)


def test_missing_model_blocks_acceptance(tmp_path: Path) -> None:
    evidence, archive, checksum = _completed_evidence(tmp_path)
    evidence["ai_model"] = ""

    with pytest.raises(WitnessError, match="AI model"):
        verify_evidence(evidence, archive, checksum)


def test_package_mismatch_blocks_stale_evidence(tmp_path: Path) -> None:
    evidence, archive, checksum = _completed_evidence(tmp_path)
    candidate = evidence["candidate"]
    assert isinstance(candidate, dict)
    candidate["source_sha"] = "d" * 40

    with pytest.raises(WitnessError, match="source_sha"):
        verify_evidence(evidence, archive, checksum)


def test_record_result_rejects_invalid_step_and_scaling(tmp_path: Path) -> None:
    archive, checksum = _package(tmp_path)
    evidence = new_evidence(archive, checksum)

    with pytest.raises(WitnessError, match="between 1 and 8"):
        record_result(evidence, step_id=9, status="pass")
    with pytest.raises(WitnessError, match="positive"):
        record_result(evidence, scaling_percent=0)


def test_extract_candidate_returns_expected_executable(tmp_path: Path) -> None:
    archive, _ = _package(tmp_path)
    executable = extract_candidate(archive, tmp_path / "run")
    assert executable == (tmp_path / "run" / "BackgroundPXR" / "BackgroundPXR.exe").resolve()
    assert executable.read_bytes().startswith(b"MZ")


def test_extract_candidate_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../outside.txt", b"unsafe")

    with pytest.raises(WitnessError, match="unsafe path"):
        extract_candidate(archive, tmp_path / "run")
    assert not (tmp_path / "outside.txt").exists()


def test_guided_witness_requires_explicit_human_pass_for_all_steps(tmp_path: Path) -> None:
    archive, checksum = _package(tmp_path)
    evidence_path = tmp_path / "witness.json"
    answers = iter(value for _ in range(8) for value in ("p", "observed"))

    evidence = run_guided_witness(
        archive,
        checksum,
        evidence_path,
        model="u2net",
        scaling_percent=125,
        launch_app=False,
        input_fn=lambda _: next(answers),
    )

    verify_evidence(evidence, archive, checksum)
    saved = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert [item["status"] for item in saved["steps"]] == ["pass"] * 8
    assert [item["notes"] for item in saved["steps"]] == ["observed"] * 8
    assert len(STEP_INSTRUCTIONS) == 8


def test_guided_witness_stops_and_persists_first_failure(tmp_path: Path) -> None:
    archive, checksum = _package(tmp_path)
    evidence_path = tmp_path / "witness.json"
    answers = iter(("f", "preview regression"))

    with pytest.raises(WitnessError, match="step 1 failed"):
        run_guided_witness(
            archive,
            checksum,
            evidence_path,
            model="u2net",
            scaling_percent=125,
            launch_app=False,
            input_fn=lambda _: next(answers),
        )

    saved = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert saved["steps"][0]["status"] == "fail"
    assert saved["steps"][0]["notes"] == "preview regression"
    assert saved["steps"][1]["status"] == "pending"


def test_windows_witness_cli_runs_directly_from_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "tools" / "windows_witness.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Windows manual witness evidence" in proc.stdout
