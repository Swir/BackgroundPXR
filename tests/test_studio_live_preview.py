from backgroundpxr.studio_v045 import manual_preview_source


def test_manual_preview_prefers_overlay_when_enabled():
    assert manual_preview_source("restore", True, True) == "overlay"
    assert manual_preview_source("erase", True, False) == "overlay"


def test_manual_preview_prefers_composite_when_overlay_is_off():
    assert manual_preview_source("restore", False, True) == "composite"
    assert manual_preview_source("erase", False, True) == "composite"


def test_manual_preview_preserves_default_paths_outside_live_result_case():
    assert manual_preview_source("restore", False, False) == "default"
    assert manual_preview_source("pan", False, True) == "default"
