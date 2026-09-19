from __future__ import annotations

from .display import effective_ui_screen
from .studio_v049 import BackgroundPXRStudio049App


class BackgroundPXRStudio050App(BackgroundPXRStudio049App):
    """Studio Pro with DPI-scale-aware compact inspector selection.

    Windows can expose a physical screen size to a per-monitor-aware process
    while Tk/CustomTkinter render text and controls at 125% or 150%. Choosing
    the compact inspector from raw pixels alone can therefore overestimate the
    vertical workspace. Use the scale-normalized UI height so the same 1280x720
    effective workspace receives the same layout regardless of physical panel
    resolution.
    """

    def _build_right(self, parent):
        super()._build_right(parent)
        effective_width, effective_height, scale = effective_ui_screen(self.root)
        self._effective_ui_screen = (effective_width, effective_height)
        self._ui_scale = scale

        should_compact = effective_height <= self.COMPACT_SCREEN_HEIGHT
        if should_compact and not self._compact_inspector:
            self._compact_inspector = True
            self._apply_compact_inspector_layout()
