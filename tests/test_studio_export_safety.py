import queue
import threading
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

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


class RecordingBatchEngine:
    def __init__(self, fail_on_remove_call=None):
        self.destinations = []
        self.remove_calls = 0
        self.fail_on_remove_call = fail_on_remove_call

    def remove_background(self, original, _opts):
        self.remove_calls += 1
        if self.remove_calls == self.fail_on_remove_call:
            raise PermissionError("model cache is unavailable")
        return original.copy()

    @staticmethod
    def refine_cutout(_original, ai, _opts):
        return ai.copy()

    @staticmethod
    def compose(_original, cutout, _opts):
        return cutout.copy()

    def save(self, _image, destination, _export_format):
        self.destinations.append(Path(destination))


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


def make_batch_app(tmp_path: Path, engine):
    app = object.__new__(BackgroundPXRStudio050App)
    app.output_dir = FakeVar(str(tmp_path / "out"))
    app.cancel_event = threading.Event()
    app.events = queue.Queue()
    app.diagnostics = FakeDiagnostics()
    app.engine = engine
    return app


def drain_events(app):
    events = []
    while True:
        try:
            events.append(app.events.get_nowait())
        except queue.Empty:
            return events


def write_image(path: Path, color):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "RGB" if path.suffix.lower() in {".jpg", ".jpeg"} else "RGBA"
    fill = color[:3] if mode == "RGB" else color
    Image.new(mode, (8, 8), fill).save(path)


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


def test_batch_export_keeps_collision_safety_and_diagnostic_stage_events(tmp_path):
    first = tmp_path / "a" / "portrait.jpg"
    second = tmp_path / "b" / "portrait.jpg"
    write_image(first, (255, 0, 0, 255))
    write_image(second, (0, 255, 0, 255))
    engine = RecordingBatchEngine()
    app = make_batch_app(tmp_path, engine)
    opts = SimpleNamespace(
        model_label="Fast",
        alpha_matting=False,
        export_format="PNG",
        output_suffix="_pxr",
    )

    app._worker([(0, first), (1, second)], opts, True)
    events = drain_events(app)

    assert [path.name for path in engine.destinations] == [
        "portrait_pxr.png",
        "portrait_pxr_2.png",
    ]
    stages = {event[2] for event in events if event[0] == "diag_stage"}
    assert {"open_img", "ai", "refine", "compose", "save", "done"} <= stages
    assert ("done", 2, 0, False, True) in events
    assert not any(event[0] == "error" for event in events)
    written_stages = {entry[1] for entry in app.diagnostics.writes}
    assert {"open", "ai", "complete"} <= written_stages


def test_batch_failure_gets_error_id_and_does_not_hide_completed_work(tmp_path):
    first = tmp_path / "a" / "one.png"
    second = tmp_path / "b" / "two.png"
    write_image(first, (255, 255, 255, 255))
    write_image(second, (0, 0, 0, 255))
    engine = RecordingBatchEngine(fail_on_remove_call=2)
    app = make_batch_app(tmp_path, engine)
    opts = SimpleNamespace(
        model_label="Fast",
        alpha_matting=False,
        export_format="PNG",
        output_suffix="_pxr",
    )

    app._worker([(0, first), (1, second)], opts, True)
    events = drain_events(app)

    assert len(engine.destinations) == 1
    assert ("done", 1, 1, False, True) in events
    errors = [event for event in events if event[0] == "diag_error"]
    assert len(errors) == 1
    assert errors[0][3] == "two.png"
    assert errors[0][4] == "PXR-TEST-001"
    assert errors[0][5] == "PermissionError"
    assert len(app.diagnostics.exceptions) == 1
    assert app.diagnostics.exceptions[0][0] == "processing"
    assert app.diagnostics.exceptions[0][1] == second
