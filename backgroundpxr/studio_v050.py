from __future__ import annotations

from tkinter import messagebox

from .display import effective_ui_screen
from .exporting import AtomicBackgroundEngine, reserve_output_path
from .i18n import tr
from .studio_v049 import BackgroundPXRStudio049App


class BackgroundPXRStudio050App(BackgroundPXRStudio049App):
    """Studio Pro with DPI-aware layout and release-grade export safety."""

    def __init__(self, root) -> None:
        super().__init__(root)
        # Keep the mature processing engine behaviour while hardening all
        # user-facing image/mask writes against partial-file corruption.
        self.engine = AtomicBackgroundEngine()

    def _build_right(self, parent):
        super()._build_right(parent)
        effective_width, effective_height, scale = effective_ui_screen(self.root)
        self._effective_ui_screen = (effective_width, effective_height)
        self._ui_scale = scale

        should_compact = effective_height <= self.COMPACT_SCREEN_HEIGHT
        if should_compact and not self._compact_inspector:
            self._compact_inspector = True
            self._apply_compact_inspector_layout()

    def _worker(self, items, opts, save):
        """Process a batch without allowing same-stem inputs to overwrite."""
        ok = fail = 0
        total = len(items)
        reserved_outputs: set[str] = set()
        for pos, (idx, path) in enumerate(items, 1):
            if self.cancel_event.is_set():
                break
            self.events.put(("status", pos, total, path.name))
            try:
                res = self.engine.process_layers(path, opts)
                dest = None
                if save:
                    dest = reserve_output_path(
                        path,
                        self.output_dir.get(),
                        opts.export_format,
                        opts.output_suffix,
                        reserved_outputs,
                    )
                    self.engine.save(res.output, dest, opts.export_format)
                    ok += 1
                self.events.put(("result", idx, res, str(dest) if dest else None))
            except Exception as exc:
                fail += 1
                self.events.put(("error", path.name, str(exc)))
            self.events.put(("progress", pos / total))
        self.events.put(("done", ok, fail, self.cancel_event.is_set(), save))

    def _export_current(self):
        if self.selected_index is None or not self._validate():
            return
        if self.preview_after is None:
            messagebox.showwarning(
                tr(self.language.get(), "error"),
                tr(self.language.get(), "no_result"),
            )
            return

        self._recompose()
        opts = self._options()
        dest = reserve_output_path(
            self.files[self.selected_index],
            self.output_dir.get(),
            opts.export_format,
            opts.output_suffix,
        )
        self.engine.save(self.preview_after, dest, opts.export_format)
        self.status_text.set(tr(self.language.get(), "saved", name=dest.name))
        if self.auto_open_output.get():
            self._open_output_folder()
