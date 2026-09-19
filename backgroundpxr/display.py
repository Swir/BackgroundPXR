from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WindowPlacement:
    """Pixel geometry chosen for the application's first visible window."""

    width: int
    height: int
    x: int
    y: int
    min_width: int
    min_height: int

    @property
    def geometry(self) -> str:
        return f"{self.width}x{self.height}+{self.x}+{self.y}"


def plan_window(screen_width: int, screen_height: int) -> WindowPlacement:
    """Fit the established Studio layout inside the available desktop.

    BackgroundPXR historically targeted a 1320-1760 by 820-980 window.
    On Windows laptops with display scaling, Tk can report a smaller logical
    desktop than the panel's old hard-coded minimum.  The old policy could
    therefore request an 800px-tall minimum on a ~720px logical desktop and
    leave footer/actions off screen.

    Keep the existing preferred size on normal desktops, but clamp both the
    initial geometry and the minimum size to the reported screen.
    """
    sw = max(1, int(screen_width))
    sh = max(1, int(screen_height))

    margin_x = min(25, max(8, sw // 50))
    margin_y = min(36, max(8, sh // 30))
    usable_w = max(1, sw - (margin_x * 2))
    usable_h = max(1, sh - (margin_y * 2))

    preferred_w = min(1760, max(1320, sw - 50))
    preferred_h = min(980, max(820, sh - 90))

    width = min(preferred_w, usable_w)
    height = min(preferred_h, usable_h)

    min_width = min(1240, width)
    min_height = min(800, height)

    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2)

    return WindowPlacement(
        width=width,
        height=height,
        x=x,
        y=y,
        min_width=min_width,
        min_height=min_height,
    )


def enable_windows_dpi_awareness(
    *, _platform: str | None = None, _ctypes=None
) -> str:
    """Enable the best Windows DPI mode available before Tk is created.

    Returns a small status string for diagnostics/tests.  The function is
    deliberately best-effort: older Windows builds and already-configured
    frozen runtimes must still launch normally.
    """
    platform = sys.platform if _platform is None else _platform
    if platform != "win32":
        return "not-windows"

    if _ctypes is None:
        import ctypes as _ctypes  # type: ignore[no-redef]

    windll = getattr(_ctypes, "windll", None)
    if windll is None:
        return "unavailable"

    user32 = getattr(windll, "user32", None)
    if user32 is not None:
        set_context = getattr(user32, "SetProcessDpiAwarenessContext", None)
        if callable(set_context):
            try:
                c_void_p = getattr(_ctypes, "c_void_p", lambda value: value)
                if set_context(c_void_p(-4)):
                    return "per-monitor-v2"
            except OSError as exc:
                if getattr(exc, "winerror", None) == 5:
                    return "already-configured"
            except Exception:
                pass

    shcore = getattr(windll, "shcore", None)
    if shcore is not None:
        setter = getattr(shcore, "SetProcessDpiAwareness", None)
        if callable(setter):
            try:
                result = int(setter(2))
                if result == 0:
                    return "per-monitor"
                if result & 0xFFFFFFFF == 0x80070005:
                    return "already-configured"
            except OSError as exc:
                if getattr(exc, "winerror", None) == 5:
                    return "already-configured"
            except Exception:
                pass

    if user32 is not None:
        fallback = getattr(user32, "SetProcessDPIAware", None)
        if callable(fallback):
            try:
                if fallback():
                    return "system"
            except Exception:
                pass

    return "unavailable"
