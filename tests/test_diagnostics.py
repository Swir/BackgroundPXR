from pathlib import Path

from backgroundpxr.diagnostics import BackgroundPXRDiagnosticsApp, DiagnosticsStore


def test_overall_progress_math():
    assert BackgroundPXRDiagnosticsApp._overall(1, 4, 0.0) == 0.0
    assert BackgroundPXRDiagnosticsApp._overall(1, 4, 1.0) == 0.25
    assert BackgroundPXRDiagnosticsApp._overall(2, 4, 0.5) == 0.375
    assert BackgroundPXRDiagnosticsApp._overall(4, 4, 1.0) == 1.0


def test_diagnostics_store_writes_and_clears(tmp_path: Path):
    store = DiagnosticsStore(tmp_path)
    store.write("INFO", "test", "hello", "photo.jpg")
    report = store.report()
    assert "hello" in report
    assert "photo.jpg" in report
    assert store.path.exists()
    store.clear()
    assert store.report() == ""


def test_exception_has_report_id(tmp_path: Path):
    store = DiagnosticsStore(tmp_path)
    exc = ValueError("broken mask")
    error_id = store.exception("processing", "photo.png", exc, "traceback sample")
    assert error_id.startswith("PXR-")
    report = store.report()
    assert error_id in report
    assert "ValueError: broken mask" in report
    assert "traceback sample" in report
