from __future__ import annotations

import math
import sys
from dataclasses import dataclass


WINDOWS_BASE_DPI = 96.0
TK_POINTS_PER_INCH = 72.0
WINDOWS_TK_BASE_SCALING = WINDOWS_BASE_DPI / TK_POINTS_PER_INCH


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


def windows_ui_scale(root, *, _platform: str | None = None) -> float:
    """Return the effective Windows UI scale derived from Tk's DPI setting.

    Tk exposes pixels-per-point via ``tk scaling``. Windows at 100% uses
    96 DPI, which is 96/72 Tk units. Dividing by that baseline turns the value
    into the familiar Windows display scale (1.0, 1.25, 1.5, ...).

    The result is intentionally best-effort and bounded. It is used only for
    responsive layout decisions; failures fall back to 100% so startup can
    never be blocked by a window-manager or Tk quirk.
    """
    platform = sys.platform if _platform is None else _platform
    if platform != "win32":
        return 1.0

    try:
        tk_scale = float(root.tk.call("tk", "scaling"))
        scale = tk_scale / WINDOWS_TK_BASE_SCALING
    except Exception:
        return 1.0

    if not math.isfinite(scale) or scale <= 0:
        return 1.0
    return max(1.0, min(3.0, scale))


def effective_ui_screen(root, *, _platform: str | None = None) -> tuple[int, int, float]:
    """Return screen dimensions in UI-equivalent pixels plus the scale factor.

    Per-monitor-aware Windows processes can see physical display pixels while
    fonts/widgets are scaled for 125%/150% displays. Responsive decisions based
    on the raw height alone can therefore choose a layout that is too tall.
    This helper keeps geometry untouched and only exposes a scale-normalized
    size for deciding whether compact controls are required.
    """
    scale = windows_ui_scale(root, _platform=_platform)
    try:
        width = max(1, int(root.winfo_screenwidth()))
        height = max(1, int(root.winfo_screenheight()))
    except Exception:
        return 1, 1, scale

    return (
        max(1, int(round(width / scale))),
        max(1, int(round(height / scale))),
        scale,
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
