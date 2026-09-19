from __future__ import annotations

from .studio_v044 import BackgroundPXRStudio044App


EDIT_TOOLS = frozenset({"restore", "erase"})
LIVE_RECOMPOSE_INTERVAL_MS = 55


def manual_preview_source(tool: str, mask_overlay: bool, has_composite: bool) -> str:
    """Return the preferred preview source while manually editing a mask.

    The policy stays deliberately small and testable: overlay mode wins when it
    is enabled, otherwise a current composed result is preferred so users can
    judge the brush stroke against the real background/style. The legacy
    cutout/default path remains the fallback when no composed preview exists.
    """
    if tool not in EDIT_TOOLS:
        return "default"
    if mask_overlay:
        return "overlay"
    if has_composite:
        return "composite"
    return "default"


class BackgroundPXRStudio045App(BackgroundPXRStudio044App):
    """Studio Pro manual editor with responsive live-composite feedback."""

    def __init__(self, root):
        self._live_recompose_after_id = None
        super().__init__(root)

    def _after_image(self):
        source = manual_preview_source(
            self.tool,
            bool(self.mask_overlay.get()),
            self.preview_after is not None,
        )
        if source == "composite":
            return self.preview_after
        return super()._after_image()

    def _paint_at(self, canvas_x, canvas_y):
        super()._paint_at(canvas_x, canvas_y)
        self._schedule_live_recompose()

    def _schedule_live_recompose(self) -> None:
        """Throttle expensive composition work while a brush stroke is active.

        A pending callback is reused instead of being reset for every mouse
        event. This keeps the final background/style preview updating during a
        continuous drag without trying to compose on every high-frequency input
        event.
        """
        if (
            self._live_recompose_after_id is not None
            or self.editor is None
            or self.tool not in EDIT_TOOLS
            or bool(self.mask_overlay.get())
        ):
            return
        self._live_recompose_after_id = self.root.after(
            LIVE_RECOMPOSE_INTERVAL_MS, self._run_live_recompose
        )

    def _run_live_recompose(self) -> None:
        self._live_recompose_after_id = None
        if (
            self.editor is None
            or self.tool not in EDIT_TOOLS
            or bool(self.mask_overlay.get())
        ):
            return
        self._recompose()
        self._refresh_after_only()

    def _cancel_live_recompose(self) -> None:
        pending = self._live_recompose_after_id
        self._live_recompose_after_id = None
        if pending is None:
            return
        try:
            self.root.after_cancel(pending)
        except Exception:
            # Tk can reject cancellation during shutdown; there is nothing left
            # to refresh in that case, so cancellation remains best-effort.
            pass

    def _on_after_release(self, event):
        # The inherited release path performs one authoritative full recompose.
        # Cancel any throttled intermediate frame to avoid duplicate work.
        self._cancel_live_recompose()
        super()._on_after_release(event)

    def _on_after_motion(self, event):
        if self.tool not in EDIT_TOOLS:
            return
        # Cursor-only motion must not rebuild the full PIL/Tk preview. Deleting
        # the tagged cursor items is enough and keeps hover feedback fluid on
        # large photographs and high-DPI displays.
        self.after_canvas.delete("cursor")
        self._draw_brush_cursor(event.x, event.y)

    def _on_mask_overlay_change(self):
        if bool(self.mask_overlay.get()):
            self._cancel_live_recompose()
        super()._on_mask_overlay_change()
        if not bool(self.mask_overlay.get()) and self.editor is not None:
            # Switching from the diagnostic overlay to live result should show
            # the latest manual mask immediately, not the previous composition.
            self._recompose()
            self._refresh_after_only()

    def _select_file(self, index):
        self._cancel_live_recompose()
        return super()._select_file(index)

    def _clear_files(self):
        self._cancel_live_recompose()
        return super()._clear_files()

    def _on_close(self):
        self._cancel_live_recompose()
        return super()._on_close()
