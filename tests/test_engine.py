from pathlib import Path

from PIL import Image

from backgroundpxr.engine import ProcessOptions, collect_images, is_supported_image, output_path_for


def test_output_paths(tmp_path: Path):
    assert output_path_for("photo.jpg", tmp_path, "PNG").name == "photo_pxr.png"
    assert output_path_for("photo.png", tmp_path, "JPG").name == "photo_pxr.jpg"
    assert output_path_for("photo.png", tmp_path, "WEBP").name == "photo_pxr.webp"


def test_collect_images(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    Image.new("RGB", (8, 8), "red").save(tmp_path / "a.png")
    Image.new("RGB", (8, 8), "blue").save(tmp_path / "sub" / "b.jpg")
    (tmp_path / "ignore.txt").write_text("x", encoding="utf-8")
    names = [p.name for p in collect_images(tmp_path)]
    assert names == ["a.png", "b.jpg"]


def test_supported_image_extensions():
    assert is_supported_image("x.PNG")
    assert is_supported_image("x.webp")
    assert not is_supported_image("x.pdf")


def test_process_options_defaults():
    opts = ProcessOptions()
    assert opts.model_label == "Quality"
    assert opts.background_mode == "transparent"
