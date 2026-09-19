from pathlib import Path

import pytest
from PIL import Image

from backgroundpxr.engine import BackgroundEngine
from backgroundpxr.exporting import AtomicBackgroundEngine, reserve_output_path


def test_batch_output_reservation_prevents_same_stem_overwrite(tmp_path: Path):
    reserved: set[str] = set()
    first = reserve_output_path(
        tmp_path / "camera-a" / "portrait.jpg",
        tmp_path / "out",
        "PNG",
        "_pxr",
        reserved,
    )
    second = reserve_output_path(
        tmp_path / "camera-b" / "portrait.webp",
        tmp_path / "out",
        "PNG",
        "_pxr",
        reserved,
    )

    assert first.name == "portrait_pxr.png"
    assert second.name == "portrait_pxr_2.png"


def test_batch_output_reservation_is_windows_case_insensitive(tmp_path: Path):
    reserved: set[str] = set()
    first = reserve_output_path("photo.jpg", tmp_path, "PNG", "_pxr", reserved)
    second = reserve_output_path("PHOTO.jpg", tmp_path, "PNG", "_pxr", reserved)

    assert first.name == "photo_pxr.png"
    assert second.name == "PHOTO_pxr_2.png"


def test_invalid_only_suffix_cannot_target_source_file(tmp_path: Path):
    source = tmp_path / "photo.png"
    source.write_bytes(b"source-image")

    destination = reserve_output_path(source, tmp_path, "PNG", "///\\?*")

    assert destination != source
    assert destination.name == "photo_pxr.png"


def test_atomic_export_writes_valid_image(tmp_path: Path):
    destination = tmp_path / "result.png"
    image = Image.new("RGBA", (12, 10), (10, 20, 30, 180))

    saved = AtomicBackgroundEngine.save(image, destination, "PNG")

    assert saved == destination
    with Image.open(destination) as exported:
        assert exported.size == (12, 10)
        assert exported.mode == "RGBA"
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".result.")]


def test_atomic_export_failure_preserves_previous_file(tmp_path: Path, monkeypatch):
    destination = tmp_path / "result.png"
    destination.write_bytes(b"known-good-output")
    image = Image.new("RGBA", (4, 4), (255, 0, 0, 255))

    def broken_save(_image, temporary, _export_format):
        Path(temporary).write_bytes(b"partial-output")
        raise OSError("simulated encoder failure")

    monkeypatch.setattr(BackgroundEngine, "save", staticmethod(broken_save))

    with pytest.raises(OSError, match="simulated encoder failure"):
        AtomicBackgroundEngine.save(image, destination, "PNG")

    assert destination.read_bytes() == b"known-good-output"
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".result.")]
