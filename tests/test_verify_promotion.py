from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.verify_promotion import (
    PromotionVerificationError,
    load_witness,
    validate_hardening_changes,
    validate_promotion_changes,
    validate_witness_record,
    witness_policy_head,
)


def _legacy_witness() -> dict[str, object]:
    return {
        "schema_version": 1,
        "candidate": {
            "version": "1.0.0rc1",
            "source_sha": "a" * 40,
            "channel": "qualification",
            "archive": "BackgroundPXR-1.0.0rc1-Windows.zip",
            "sha256": "b" * 64,
        },
        "environment": {
            "windows_version": "Windows-11-test",
            "display_scaling_percent": 125,
        },
        "ai_model": "u2net",
        "steps": [
            {
                "id": step_id,
                "title": f"step {step_id}",
                "status": "pass",
                "notes": "verified",
            }
            for step_id in range(1, 9)
        ],
    }


def _hybrid_witness() -> dict[str, object]:
    return {
        "schema_version": 2,
        "candidate": {
            "version": "1.0.0rc1",
            "source_sha": "a" * 40,
            "channel": "qualification",
            "archive": "BackgroundPXR-1.0.0rc1-HOTFIX-MemoryFix-Windows.zip",
            "sha256": "b" * 64,
        },
        "policy_head_sha": "c" * 40,
        "manual_attestation": {
            "status": "pass",
            "platform": "Windows 11",
            "observed_path": "High Quality v2 + alpha matting",
            "statement": "Release-blocking Windows AI path completed successfully.",
            "date": "2026-09-21",
        },
    }


def test_complete_legacy_manual_witness_is_accepted_for_promotion() -> None:
    assert validate_witness_record(_legacy_witness()) == "a" * 40
    assert witness_policy_head(_legacy_witness()) == "a" * 40


def test_hybrid_manual_attestation_is_accepted_for_runtime_equivalent_promotion() -> None:
    witness = _hybrid_witness()
    assert validate_witness_record(witness) == "a" * 40
    assert witness_policy_head(witness) == "c" * 40


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("version", "1.0.0", "must qualify 1.0.0rc1"),
        ("source_sha", "short", "40-character"),
        ("archive", "other.zip", "1.0.0rc1 Windows archive"),
        ("sha256", "bad", "SHA-256"),
    ],
)
def test_invalid_candidate_metadata_blocks_promotion(
    field: str, value: str, match: str
) -> None:
    witness = _legacy_witness()
    candidate = witness["candidate"]
    assert isinstance(candidate, dict)
    candidate[field] = value

    with pytest.raises(PromotionVerificationError, match=match):
        validate_witness_record(witness)


def test_pending_legacy_manual_step_blocks_promotion() -> None:
    witness = _legacy_witness()
    steps = witness["steps"]
    assert isinstance(steps, list)
    steps[7]["status"] = "pending"

    with pytest.raises(PromotionVerificationError, match="step 8"):
        validate_witness_record(witness)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("status", "pending", "explicitly pass"),
        ("platform", "Linux", "real Windows"),
        ("observed_path", "Fast", "High Quality v2"),
        ("statement", "ok", "too short"),
        ("date", "21-09-2026", "YYYY-MM-DD"),
    ],
)
def test_invalid_hybrid_attestation_blocks_promotion(
    field: str, value: str, match: str
) -> None:
    witness = _hybrid_witness()
    attestation = witness["manual_attestation"]
    assert isinstance(attestation, dict)
    attestation[field] = value

    with pytest.raises(PromotionVerificationError, match=match):
        validate_witness_record(witness)


def test_hybrid_attestation_requires_policy_head_sha() -> None:
    witness = _hybrid_witness()
    witness["policy_head_sha"] = "short"

    with pytest.raises(PromotionVerificationError, match="policy_head_sha"):
        validate_witness_record(witness)


def test_runtime_changes_after_manual_rc_are_rejected() -> None:
    with pytest.raises(PromotionVerificationError, match="app.py"):
        validate_hardening_changes(
            [
                ".github/workflows/windows.yml",
                "tools/verify_promotion.py",
                "app.py",
            ]
        )


def test_release_gate_hardening_files_are_allowed_before_policy_freeze() -> None:
    validate_hardening_changes(
        [
            ".github/workflows/windows.yml",
            ".github/workflows/witness-kit.yml",
            "docs/acceptance/final-functional-workflow.md",
            "tests/test_alpha_matting_memory.py",
            "tests/test_release_trigger_contract.py",
            "tests/test_release_workflow_contract.py",
            "tests/test_verify_promotion.py",
            "tests/test_windows_witness.py",
            "tools/verify_promotion.py",
            "tools/windows_witness.py",
        ]
    )


def test_final_release_promotion_stays_metadata_only() -> None:
    validate_promotion_changes(
        [
            "backgroundpxr/__init__.py",
            "README.md",
            "RELEASE_NOTES.md",
            "ROADMAP_1_0.md",
            "assets/readme/progress-card.svg",
            "assets/readme/progress-mini.svg",
            "docs/acceptance/final-functional-witness.json",
        ]
    )


def test_final_promotion_rejects_late_workflow_changes() -> None:
    with pytest.raises(PromotionVerificationError, match="windows.yml"):
        validate_promotion_changes([".github/workflows/windows.yml"])


def test_load_witness_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "witness.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(PromotionVerificationError, match="invalid JSON"):
        load_witness(path)


def test_load_witness_accepts_json_object(tmp_path: Path) -> None:
    path = tmp_path / "witness.json"
    expected = _hybrid_witness()
    path.write_text(json.dumps(expected), encoding="utf-8")
    assert load_witness(path) == expected
