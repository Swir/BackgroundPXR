from __future__ import annotations

from .display import plan_window
from .studio_v047 import BackgroundPXRStudio047App


class BackgroundPXRStudio048App(BackgroundPXRStudio047App):
    """Studio Pro with desktop-safe restored and minimum window bounds.

    Earlier Studio layers reintroduced fixed 1240x740/800 minimums after the
    DPI-aware startup work. On a 1280x720 logical Windows desktop that can
    force footer/actions below the work area. Keep the maximized Windows
    experience while making the restored geometry and minimum size obey the
    actual logical desktop reported by Tk.
    """

    def _configure_root(self):
        super()._configure_root()
        placement = plan_window(
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
        )
        try:
            # When Windows is zoomed, geometry updates restored-window bounds
            # without cancelling maximization. Elsewhere it is the initial size.
            self.root.geometry(placement.geometry)
            self.root.minsize(placement.min_width, placement.min_height)
        except Exception:
            # Window-manager differences must never prevent application startup.
            pass
