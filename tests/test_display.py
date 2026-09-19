from types import SimpleNamespace

from backgroundpxr.display import (
    enable_windows_dpi_awareness,
    plan_window,
)


def test_standard_desktop_keeps_established_backgroundpxr_geometry():
    placement = plan_window(1600, 900)

    assert (placement.width, placement.height) == (1550, 820)
    assert (placement.min_width, placement.min_height) == (1240, 800)
    assert placement.geometry == "1550x820+25+40"


def test_scaled_or_small_desktop_never_gets_an_oversized_minimum():
    placement = plan_window(1280, 720)

    assert 0 < placement.width <= 1280
    assert 0 < placement.height <= 720
    assert 0 < placement.min_width <= placement.width
    assert 0 < placement.min_height <= placement.height
    assert placement.x >= 0
    assert placement.y >= 0


def test_large_desktop_remains_bounded_to_studio_target():
    placement = plan_window(2560, 1440)

    assert (placement.width, placement.height) == (1760, 980)
    assert placement.min_width == 1240
    assert placement.min_height == 800


def test_non_windows_dpi_setup_is_a_noop():
    assert enable_windows_dpi_awareness(_platform="linux") == "not-windows"


def test_windows_prefers_per_monitor_v2_dpi_awareness():
    calls = []

    class User32:
        def SetProcessDpiAwarenessContext(self, context):
            calls.append(("v2", context))
            return 1

        def SetProcessDPIAware(self):
            calls.append(("legacy", None))
            return 1

    fake = SimpleNamespace(
        windll=SimpleNamespace(user32=User32()),
        c_void_p=lambda value: value,
    )

    assert (
        enable_windows_dpi_awareness(_platform="win32", _ctypes=fake)
        == "per-monitor-v2"
    )
    assert calls == [("v2", -4)]


def test_windows_falls_back_to_shcore_when_v2_is_unavailable():
    calls = []

    class User32:
        def SetProcessDPIAware(self):
            calls.append(("legacy", None))
            return 1

    class Shcore:
        def SetProcessDpiAwareness(self, value):
            calls.append(("shcore", value))
            return 0

    fake = SimpleNamespace(
        windll=SimpleNamespace(user32=User32(), shcore=Shcore()),
        c_void_p=lambda value: value,
    )

    assert (
        enable_windows_dpi_awareness(_platform="win32", _ctypes=fake)
        == "per-monitor"
    )
    assert calls == [("shcore", 2)]


def test_app_enables_dpi_awareness_before_creating_tk_root():
    from pathlib import Path

    source = Path("app.py").read_text(encoding="utf-8")
    enable_call = source.index("enable_windows_dpi_awareness()")
    create_call = source.index("root = create_root()")

    assert enable_call < create_call
