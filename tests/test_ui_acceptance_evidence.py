import pytest

from tools.capture_ui_acceptance import build_review_checklist, parse_size, safe_label


def test_parse_size_accepts_supported_windows_desktop():
    assert parse_size("1600x900") == (1600, 900)
    assert parse_size(" 1366X768 ") == (1366, 768)


def test_parse_size_rejects_malformed_or_unsupported_desktop():
    for value in ("1600", "wide", "800x600", "1600x"):
        with pytest.raises(ValueError):
            parse_size(value)


def test_safe_label_is_deterministic_and_filesystem_safe():
    assert safe_label("1600x900 / 150%") == "1600x900-150"
    assert safe_label("***") == "ui-evidence"


def test_review_checklist_keeps_manual_gate_pending():
    record = {
        "commit": "abc123",
        "app_version": "0.4.0",
        "screen": {"actual": "1600x900"},
        "ui_scale": {"requested": 1.5, "detected": 1.5},
        "dpi_status": "per-monitor-v2",
        "screenshots": ["scale-150-ai.png", "scale-150-export.png"],
    }

    checklist = build_review_checklist(record)

    assert "manual UX item" in checklist
    assert "Result: `PENDING`" in checklist
    assert "Permanent `by Swir` and `github.com/Swir` branding" in checklist
    assert "scale-150-ai.png" in checklist
    assert "abc123" in checklist
