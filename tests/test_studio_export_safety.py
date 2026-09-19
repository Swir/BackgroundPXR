from pathlib import Path
from types import SimpleNamespace

import backgroundpxr.studio_v050 as studio_v050
from backgroundpxr.studio_v050 import BackgroundPXRStudio050App, etx


class FakeVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeStatus:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value


class FakeDiagnostics:
    def __init__(self):
        self.exceptions = []
        self.writes = []

    def exception(self, stage, source, exc, trace):
        self.exceptions.append((stage, Path(source), type(exc).__name__, str(exc), trace))
        return "PXR-TEST-001"

    def write(self, *args):
        self.writes.append(args)


class FailingImageEngine:
    @staticmethod
    def save(_image, _destination, _export_format):
        raise PermissionError("private low-level path is locked")


class RecordingMaskEngine:
    def __init__(self):
        self.destination = None

    def save_mask(self, _cutout, destination):
        self.destination = Path(destination)


def make_export_app(tmp_path: Path):
    app = object.__new__(BackgroundPXRStudio050App)
    source = tmp_path / "portrait.jpg"
    source.write_bytes(b"source")
    app.selected_index = 0
    app.files = [source]
    app.output_dir = FakeVar(str(tmp_path))
    app.language = FakeVar("English")
    app.status_text = FakeStatus()
    app.preview_after = object()
    app.auto_open_output = FakeVar(False)
    app.diagnostics = FakeDiagnostics()
    app._validate = lambda: True
    app._recompose = lambda: None
    app._options = lambda: SimpleNamespace(export_format="PNG", output_suffix="_pxr")
    app.error_status = []
    app._error_status = lambda error_id, name, error_type: app.error_status.append(
        (error_id, name, error_type)
    )
    app._open_output_folder = lambda: None
    return app, source


def test_image_export_failure_is_logged_and_shown_without_raising(tmp_path, monkeypatch):
    app, source = make_export_app(tmp_path)
    app.engine = FailingImageEngine()
    dialogs = []
    monkeypatch.setattr(
        studio_v050.messagebox,
        "showerror",
        lambda title, message: dialogs.append((title, message)),
    )

    app._export_current()

    assert len(app.diagnostics.exceptions) == 1
    stage, logged_source, error_type, raw_error, trace = app.diagnostics.exceptions[0]
    assert stage == "image-export"
    assert logged_source == source
    assert error_type == "PermissionError"
    assert "private low-level path" in raw_error
    assert "PermissionError" in trace
    assert app.error_status == [("PXR-TEST-001", "portrait.jpg", "PermissionError")]
    assert len(dialogs) == 1
    assert dialogs[0][0] == "Error"
    assert "PXR-TEST-001" in dialogs[0][1]
    assert "Nothing was overwritten" in dialogs[0][1]
    assert "private low-level path" not in dialogs[0][1]


def test_mask_export_reserves_existing_name_instead_of_overwriting(tmp_path, monkeypatch):
    app, _source = make_export_app(tmp_path)
    app.engine = RecordingMaskEngine()
    app._current_cutout = lambda: object()
    existing = tmp_path / "portrait_mask.png"
    existing.write_bytes(b"keep-me")
    monkeypatch.setattr(
        studio_v050.messagebox,
        "showerror",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected error")),
    )

    app._export_mask()

    assert app.engine.destination == tmp_path / "portrait_mask_2.png"
    assert existing.read_bytes() == b"keep-me"
    assert app.status_text.value == "Mask saved: portrait_mask_2.png"
    assert any(entry[1] == "mask-export" for entry in app.diagnostics.writes)


def test_export_failure_copy_is_localized_and_non_technical():
    english = etx("English", "export_failed", name="photo.png", error_id="PXR-1")
    polish = etx("Polski", "export_failed", name="photo.png", error_id="PXR-1")

    assert "Nothing was overwritten" in english
    assert "Open LOG" in english
    assert "Nic nie zostało nadpisane" in polish
    assert "Otwórz LOG" in polish
