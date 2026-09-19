from __future__ import annotations

from .studio_v050 import BackgroundPXRStudio050App


PREVIEW_RESIZE_DEBOUNCE_MS = 70


class BackgroundPXRStudio051App(BackgroundPXRStudio050App):
    """Studio Pro with resize-safe preview rendering.

    The preview canvas content is drawn in pixel coordinates. Windows can resize
    those canvases after the last render, so stale placeholder/image coordinates
    used to remain clipped until another editor action forced a refresh. Debounce
    Configure events and redraw both previews after their geometry settles.
    """

    def __init__(self, root) -> None:
        self._preview_resize_after_id = None
        self._preview_canvas_sizes: dict[str, tuple[int, int]] = {}
        super().__init__(root)

    def _build_center(self, parent):
        super()._build_center(parent)
        self.before_canvas.bind(
            "<Configure>", self._on_preview_canvas_configure, add="+"
        )
        self.after_canvas.bind(
            "<Configure>", self._on_preview_canvas_configure, add="+"
        )

    def _on_preview_canvas_configure(self, event) -> None:
        width = max(1, int(getattr(event, "width", 1)))
        height = max(1, int(getattr(event, "height", 1)))
        key = str(getattr(event, "widget", "preview"))
        size = (width, height)
        if self._preview_canvas_sizes.get(key) == size:
            return
        self._preview_canvas_sizes[key] = size

        pending = self._preview_resize_after_id
        if pending is not None:
            try:
                self.root.after_cancel(pending)
            except Exception:
                pass
        self._preview_resize_after_id = self.root.after(
            PREVIEW_RESIZE_DEBOUNCE_MS,
            self._refresh_previews_after_resize,
        )

    def _refresh_previews_after_resize(self) -> None:
        self._preview_resize_after_id = None
        try:
            self._refresh_previews()
        except Exception:
            # Resizing must never turn a closing/destroyed Tk window into a crash.
            pass

    def _on_close(self):
        pending = self._preview_resize_after_id
        self._preview_resize_after_id = None
        if pending is not None:
            try:
                self.root.after_cancel(pending)
            except Exception:
                pass
        return super()._on_close()
