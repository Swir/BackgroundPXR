from __future__ import annotations

import sys
import types

import pytest
from PIL import Image

import backgroundpxr.engine as engine_module
from backgroundpxr.engine import BackgroundEngine, ProcessOptions


def _install_fake_rembg(monkeypatch, remove):
    module = types.ModuleType("rembg")
    module.remove = remove
    monkeypatch.setitem(sys.modules, "rembg", module)


def _engine_with_session(monkeypatch) -> BackgroundEngine:
    engine = BackgroundEngine()
    session = object()
    monkeypatch.setattr(engine, "_get_session", lambda _label: session)
    return engine


def test_large_alpha_matting_uses_bounded_working_resolution_and_restores_output(
    monkeypatch,
) -> None:
    monkeypatch.setattr(engine_module, "ALPHA_MATTING_MAX_PIXELS", 100)
    calls: list[tuple[tuple[int, int], dict[str, object]]] = []

    def fake_remove(image, **kwargs):
        calls.append((image.size, kwargs.copy()))
        result = image.convert("RGBA").copy()
        result.putalpha(Image.new("L", image.size, 128))
        return result

    _install_fake_rembg(monkeypatch, fake_remove)
    engine = _engine_with_session(monkeypatch)
    source = Image.new("RGBA", (20, 20), (12, 34, 56, 255))

    result = engine.remove_background(source, ProcessOptions(alpha_matting=True))

    assert calls[0][0] == (10, 10)
    assert calls[0][1]["alpha_matting"] is True
    assert result.size == source.size
    assert result.getpixel((10, 10))[:3] == (12, 34, 56)
    assert 120 <= result.getchannel("A").getpixel((10, 10)) <= 136
    assert engine.last_remove_used_alpha_matting is True
    assert engine.last_remove_notice is not None
    assert "memory-safe working resolution" in engine.last_remove_notice


def test_alpha_matting_memory_error_retries_without_matting(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_remove(image, **kwargs):
        calls.append(kwargs.copy())
        if kwargs.get("alpha_matting"):
            raise MemoryError(
                "Unable to allocate 1.86 GiB for an array with shape (250000000,)"
            )
        result = image.convert("RGBA").copy()
        result.putalpha(Image.new("L", image.size, 222))
        return result

    _install_fake_rembg(monkeypatch, fake_remove)
    engine = _engine_with_session(monkeypatch)
    source = Image.new("RGBA", (32, 24), (90, 80, 70, 255))

    result = engine.remove_background(source, ProcessOptions(alpha_matting=True))

    assert len(calls) == 2
    assert calls[0]["alpha_matting"] is True
    assert "alpha_matting" not in calls[1]
    assert calls[1]["post_process_mask"] is True
    assert result.size == source.size
    assert result.getchannel("A").getpixel((5, 5)) == 222
    assert engine.last_remove_used_alpha_matting is False
    assert engine.last_remove_notice is not None
    assert "exceeded available memory" in engine.last_remove_notice


def test_alpha_matting_disabled_never_downscales_or_sets_notice(monkeypatch) -> None:
    monkeypatch.setattr(engine_module, "ALPHA_MATTING_MAX_PIXELS", 25)
    calls: list[tuple[tuple[int, int], dict[str, object]]] = []

    def fake_remove(image, **kwargs):
        calls.append((image.size, kwargs.copy()))
        return image.convert("RGBA").copy()

    _install_fake_rembg(monkeypatch, fake_remove)
    engine = _engine_with_session(monkeypatch)
    source = Image.new("RGBA", (20, 20), (1, 2, 3, 255))

    result = engine.remove_background(source, ProcessOptions(alpha_matting=False))

    assert result.size == (20, 20)
    assert calls == [((20, 20), {"session": pytest.ANY, "post_process_mask": True})]
    assert engine.last_remove_notice is None
    assert engine.last_remove_used_alpha_matting is False


def test_small_alpha_matting_keeps_native_resolution(monkeypatch) -> None:
    monkeypatch.setattr(engine_module, "ALPHA_MATTING_MAX_PIXELS", 10_000)
    seen: list[tuple[int, int]] = []

    def fake_remove(image, **kwargs):
        assert kwargs["alpha_matting"] is True
        seen.append(image.size)
        return image.convert("RGBA").copy()

    _install_fake_rembg(monkeypatch, fake_remove)
    engine = _engine_with_session(monkeypatch)
    source = Image.new("RGBA", (40, 30), (10, 20, 30, 255))

    result = engine.remove_background(source, ProcessOptions(alpha_matting=True))

    assert seen == [(40, 30)]
    assert result.size == source.size
    assert engine.last_remove_used_alpha_matting is True
    assert engine.last_remove_notice is None
