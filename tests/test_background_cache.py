from pathlib import Path

from PIL import Image

from backgroundpxr.engine import (
    BACKGROUND_CACHE_LIMIT,
    BackgroundEngine,
    ProcessOptions,
)


def test_blur_background_cache_reuses_prepared_frame(monkeypatch):
    engine = BackgroundEngine()
    original = Image.new("RGBA", (96, 64), (35, 95, 155, 255))
    options = ProcessOptions(background_mode="blur", background_blur=14)

    calls = 0
    render_background = engine._render_background

    def tracked_render(size, opts, source):
        nonlocal calls
        calls += 1
        return render_background(size, opts, source)

    monkeypatch.setattr(engine, "_render_background", tracked_render)

    first = engine._make_background((96, 64), options, original)
    second = engine._make_background((96, 64), options, original)

    assert calls == 1
    assert first.tobytes() == second.tobytes()
    assert len(engine._background_cache) == 1

    first.putpixel((0, 0), (255, 0, 0, 255))
    third = engine._make_background((96, 64), options, original)
    assert calls == 1
    assert third.getpixel((0, 0)) != (255, 0, 0, 255)

    options.background_blur = 28
    engine._make_background((96, 64), options, original)
    assert calls == 2

    engine.clear_background_cache()
    assert len(engine._background_cache) == 0
    engine._make_background((96, 64), options, original)
    assert calls == 3


def test_replacement_background_cache_invalidates_when_file_changes(
    tmp_path: Path, monkeypatch
):
    background_path = tmp_path / "background.png"
    Image.new("RGB", (48, 48), "red").save(background_path)

    engine = BackgroundEngine()
    original = Image.new("RGBA", (64, 64), (0, 0, 0, 255))
    options = ProcessOptions(
        background_mode="image",
        background_image=str(background_path),
    )

    calls = 0
    render_background = engine._render_background

    def tracked_render(size, opts, source):
        nonlocal calls
        calls += 1
        return render_background(size, opts, source)

    monkeypatch.setattr(engine, "_render_background", tracked_render)

    first = engine._make_background((64, 64), options, original)
    again = engine._make_background((64, 64), options, original)
    assert calls == 1
    assert first.getpixel((20, 20))[:3] == (255, 0, 0)
    assert again.getpixel((20, 20))[:3] == (255, 0, 0)

    old_stat = background_path.stat()
    Image.new("RGB", (48, 48), "blue").save(background_path)
    background_path.touch()
    current_stat = background_path.stat()
    if current_stat.st_mtime_ns == old_stat.st_mtime_ns:
        import os

        os.utime(
            background_path,
            ns=(current_stat.st_atime_ns, current_stat.st_mtime_ns + 1_000_000),
        )

    changed = engine._make_background((64, 64), options, original)
    assert calls == 2
    assert changed.getpixel((20, 20))[:3] == (0, 0, 255)


def test_background_cache_is_lru_bounded():
    engine = BackgroundEngine()
    original = Image.new("RGBA", (80, 60), (70, 90, 110, 255))

    for blur in range(2, BACKGROUND_CACHE_LIMIT + 5):
        engine._make_background(
            (80, 60),
            ProcessOptions(background_mode="blur", background_blur=blur),
            original,
        )

    assert len(engine._background_cache) == BACKGROUND_CACHE_LIMIT
