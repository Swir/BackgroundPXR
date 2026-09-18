from pathlib import Path

from PIL import Image

from backgroundpxr.branding import create_icon_png
from backgroundpxr.engine import (
    BackgroundEngine,
    ProcessOptions,
    collect_images,
    is_supported_image,
    output_path_for,
)
from backgroundpxr.settings import DEFAULTS


def test_output_paths(tmp_path: Path):
    assert output_path_for("photo.jpg", tmp_path, "PNG").name == "photo_pxr.png"
    assert output_path_for("photo.png", tmp_path, "JPG", "_cut").name == "photo_cut.jpg"
    assert output_path_for("photo.png", tmp_path, "WEBP", "bad/name").name == "photobadname.webp"


def test_collect_images(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    Image.new("RGB", (8, 8), "red").save(tmp_path / "a.png")
    Image.new("RGB", (8, 8), "blue").save(tmp_path / "sub" / "b.jpg")
    (tmp_path / "ignore.txt").write_text("x", encoding="utf-8")
    assert [p.name for p in collect_images(tmp_path)] == ["a.png", "b.jpg"]


def test_supported_image_extensions():
    assert is_supported_image("x.PNG")
    assert is_supported_image("x.webp")
    assert not is_supported_image("x.pdf")


def test_process_options_defaults():
    opts = ProcessOptions()
    assert opts.model_label == "High Quality v2"
    assert opts.background_mode == "transparent"
    assert opts.canvas_preset == "Original"
    assert opts.alpha_matting is True
    assert opts.subject_scale == 1.0
    assert opts.outline is False


def test_canvas_sizes():
    engine = BackgroundEngine()
    assert engine._target_size((1600, 900), "Square 1:1") == (1600, 1600)
    assert engine._target_size((1000, 1000), "Portrait 4:5") == (800, 1000)
    assert engine._target_size((500, 700), "Product 2000") == (2000, 2000)


def test_place_subject_centers_alpha():
    fg = Image.new("RGBA", (100, 50), (255, 0, 0, 255))
    out = BackgroundEngine._place_subject(fg, (200, 200))
    assert out.size == (200, 200)
    assert out.getchannel("A").getbbox() is not None


def test_place_subject_preserves_original_defaults():
    fg = Image.new("RGBA", (120, 80), (255, 0, 0, 255))
    out = BackgroundEngine._place_subject(fg, (120, 80), 1.0, 0.0, 0.0)
    assert out.tobytes() == fg.tobytes()


def test_subject_scale_and_position_change_alpha_bbox():
    fg = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    base = BackgroundEngine._place_subject(fg, (300, 300), 0.7, 0, 0)
    moved = BackgroundEngine._place_subject(fg, (300, 300), 0.7, 15, -10)
    assert base.getchannel("A").getbbox() != moved.getchannel("A").getbbox()


def test_outline_layer_adds_pixels_outside_subject():
    subject = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    subject.paste((255, 0, 0, 255), (25, 25, 55, 55))
    outline = BackgroundEngine._outline_layer(subject, 5, "#FFFFFF")
    assert outline.getchannel("A").getbbox() is not None
    assert outline.getchannel("A").getbbox() != subject.getchannel("A").getbbox()


def test_mask_image_uses_cutout_alpha():
    cutout = Image.new("RGBA", (20, 20), (1, 2, 3, 0))
    alpha = Image.new("L", (20, 20), 0)
    alpha.paste(255, (5, 5, 15, 15))
    cutout.putalpha(alpha)
    mask = BackgroundEngine.mask_image(cutout)
    assert mask.mode == "L"
    assert mask.getbbox() == (5, 5, 15, 15)


def test_save_mask(tmp_path: Path):
    cutout = Image.new("RGBA", (12, 12), (255, 255, 255, 255))
    path = tmp_path / "mask.png"
    BackgroundEngine.save_mask(cutout, path)
    with Image.open(path) as mask:
        assert mask.mode == "L"
        assert mask.size == (12, 12)


def test_compose_white_background():
    engine = BackgroundEngine()
    original = Image.new("RGBA", (40, 30), (255, 0, 0, 255))
    cut = original.copy()
    cut.putalpha(Image.new("L", (40, 30), 128))
    out = engine.compose(original, cut, ProcessOptions(background_mode="white"))
    assert out.size == (40, 30)
    assert out.mode == "RGBA"


def test_compose_outline_shadow_and_transform():
    engine = BackgroundEngine()
    original = Image.new("RGBA", (200, 200), (100, 100, 100, 255))
    cutout = Image.new("RGBA", (200, 200), (255, 0, 0, 0))
    alpha = Image.new("L", (200, 200), 0)
    alpha.paste(255, (60, 40, 140, 170))
    cutout.putalpha(alpha)

    opts = ProcessOptions(
        background_mode="white",
        subject_scale=0.75,
        subject_offset_x=8,
        subject_offset_y=-5,
        outline=True,
        outline_width=4,
        shadow=True,
        shadow_opacity=50,
        shadow_blur=8,
    )
    out = engine.compose(original, cutout, opts)
    assert out.size == (200, 200)
    assert out.mode == "RGBA"


def test_branding_icon():
    icon = create_icon_png(128)
    assert icon.size == (128, 128)
    assert icon.mode == "RGBA"


def test_settings_defaults_have_editor_features():
    assert DEFAULTS["output_suffix"] == "_pxr"
    assert DEFAULTS["model"] == "High Quality v2"
    assert DEFAULTS["alpha_matting"] is True
    assert "brush_size" in DEFAULTS
    assert DEFAULTS["output_dir"].endswith("BackgroundPXR")
    assert DEFAULTS["subject_scale"] == 1.0
    assert DEFAULTS["outline"] is False
    assert DEFAULTS["preview_mode"] == "result"
