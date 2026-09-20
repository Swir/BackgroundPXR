from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.verify_promotion import (
    PromotionVerificationError,
    load_witness,
    validate_promotion_changes,
    validate_witness_record,
)


def _witness() -> dict[str, object]:
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


def test_complete_manual_witness_is_accepted_for_promotion() -> None:
    assert validate_witness_record(_witness()) == "a" * 40


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("version", "1.0.0", "must qualify 1.0.0rc1"),
        ("source_sha", "short", "40-character"),
        ("archive", "other.zip", "expected RC1 archive"),
        ("sha256", "bad", "SHA-256"),
    ],
)
def test_invalid_candidate_metadata_blocks_promotion(
    field: str, value: str, match: str
) -> None:
    witness = _witness()
    candidate = witness["candidate"]
    assert isinstance(candidate, dict)
    candidate[field] = value

    with pytest.raises(PromotionVerificationError, match=match):
        validate_witness_record(witness)


def test_pending_manual_step_blocks_promotion() -> None:
    witness = _witness()
    steps = witness["steps"]
    assert isinstance(steps, list)
    steps[7]["status"] = "pending"

    with pytest.raises(PromotionVerificationError, match="step 8"):
        validate_witness_record(witness)


def test_runtime_changes_after_manual_rc_are_rejected() -> None:
    with pytest.raises(PromotionVerificationError, match="app.py"):
        validate_promotion_changes(
            [
                "README.md",
                "backgroundpxr/__init__.py",
                "app.py",
            ]
        )


def test_release_metadata_only_promotion_is_allowed() -> None:
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


def test_load_witness_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "witness.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(PromotionVerificationError, match="invalid JSON"):
        load_witness(path)


def test_load_witness_accepts_json_object(tmp_path: Path) -> None:
    path = tmp_path / "witness.json"
    expected = _witness()
    path.write_text(json.dumps(expected), encoding="utf-8")
    assert load_witness(path) == expected
