from __future__ import annotations

from .editor import BrushSettings
from .studio_v042 import BackgroundPXRStudio042App


class BackgroundPXRStudio043App(BackgroundPXRStudio042App):
    """Studio Pro manual editor with gap-free interpolated brush strokes."""

    def __init__(self, root):
        self._last_brush_point: tuple[float, float] | None = None
        super().__init__(root)

    def _on_after_press(self, event):
        self._last_brush_point = None
        super()._on_after_press(event)

    def _on_after_release(self, event):
        try:
            super()._on_after_release(event)
        finally:
            self._last_brush_point = None

    def _paint_at(self, canvas_x, canvas_y):
        if not self.editor or not self._after_transform:
            return
        offset_x, offset_y, scale = self._after_transform
        if scale <= 0:
            return

        image_x = (canvas_x - offset_x) / scale
        image_y = (canvas_y - offset_y) / scale
        settings = BrushSettings(self.brush_size.get(), self.brush_hardness.get())

        if self._last_brush_point is None:
            self.editor.paint(image_x, image_y, self.tool, settings)
        else:
            last_x, last_y = self._last_brush_point
            self.editor.paint_segment(
                last_x,
                last_y,
                image_x,
                image_y,
                self.tool,
                settings,
                include_start=False,
            )

        self._last_brush_point = (image_x, image_y)
        self._refresh_after_only()
