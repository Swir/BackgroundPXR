from __future__ import annotations

from collections.abc import Callable

from .studio_v046 import BackgroundPXRStudio046App


STUDIO_RECOMPOSE_INTERVAL_MS = 45
SETTINGS_SAVE_IDLE_MS = 320


class DeferredStudioUpdates:
    """Coalesce expensive Studio preview work on Tk's event loop.

    Render requests are throttled: while one callback is pending, additional
    slider events reuse it. Settings writes are debounced and happen only after
    the user stops moving a control for a short moment. This keeps high-rate
    slider input responsive without changing the final render state.
    """

    def __init__(
        self,
        root,
        render_callback: Callable[[], None],
        save_callback: Callable[[], None],
        *,
        render_delay_ms: int = STUDIO_RECOMPOSE_INTERVAL_MS,
        save_delay_ms: int = SETTINGS_SAVE_IDLE_MS,
    ) -> None:
        self.root = root
        self.render_callback = render_callback
        self.save_callback = save_callback
        self.render_delay_ms = max(1, int(render_delay_ms))
        self.save_delay_ms = max(1, int(save_delay_ms))
        self._render_after_id = None
        self._save_after_id = None

    @property
    def render_pending(self) -> bool:
        return self._render_after_id is not None

    @property
    def save_pending(self) -> bool:
        return self._save_after_id is not None

    def request_render(self) -> None:
        if self._render_after_id is not None:
            return
        self._render_after_id = self.root.after(
            self.render_delay_ms, self._run_render
        )

    def request_save(self) -> None:
        if self._save_after_id is not None:
            try:
                self.root.after_cancel(self._save_after_id)
            except Exception:
                pass
        self._save_after_id = self.root.after(self.save_delay_ms, self._run_save)

    def _run_render(self) -> None:
        self._render_after_id = None
        self.render_callback()

    def _run_save(self) -> None:
        self._save_after_id = None
        self.save_callback()

    def cancel_render(self) -> None:
        pending = self._render_after_id
        self._render_after_id = None
        if pending is None:
            return
        try:
            self.root.after_cancel(pending)
        except Exception:
            pass

    def cancel_save(self) -> None:
        pending = self._save_after_id
        self._save_after_id = None
        if pending is None:
            return
        try:
            self.root.after_cancel(pending)
        except Exception:
            pass

    def flush_render(self) -> None:
        if not self.render_pending:
            return
        self.cancel_render()
        self.render_callback()

    def flush_save(self) -> None:
        if not self.save_pending:
            return
        self.cancel_save()
        self.save_callback()

    def cancel_all(self) -> None:
        self.cancel_render()
        self.cancel_save()


class BackgroundPXRStudio047App(BackgroundPXRStudio046App):
    """Studio Pro with coalesced preview rendering and settings persistence."""

    def __init__(self, root):
        self._studio_updates = DeferredStudioUpdates(
            root,
            self._run_deferred_studio_recompose,
            self._run_deferred_settings_save,
        )
        super().__init__(root)

    def _studio_recompose(self):
        """Schedule one preview update for a burst of high-frequency controls."""
        self._studio_updates.request_render()
        self._studio_updates.request_save()

    def _run_deferred_studio_recompose(self) -> None:
        # Keep this path deliberately narrow: Studio controls only need the
        # current composite and right-hand preview. Manual editing has its own
        # live-composite scheduler in v0.4.5.
        if self.editor is None:
            return
        self._recompose()
        self._refresh_after_only()

    def _run_deferred_settings_save(self) -> None:
        # Call the inherited persistence chain directly so this deferred write
        # cannot recursively schedule another deferred save.
        super()._save_settings()

    def _select_file(self, index):
        # A pending frame belongs to the previous editor/image and must not run
        # after selection changes.
        self._studio_updates.cancel_render()
        return super()._select_file(index)

    def _clear_files(self):
        self._studio_updates.cancel_render()
        return super()._clear_files()

    def _export_current(self):
        # The inherited exporter performs an authoritative synchronous
        # recompose with the latest variable values before saving.
        self._studio_updates.cancel_render()
        return super()._export_current()

    def _on_close(self):
        self._studio_updates.cancel_all()
        return super()._on_close()
