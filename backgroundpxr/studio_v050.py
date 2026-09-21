from __future__ import annotations

import threading
import time
import traceback
from tkinter import messagebox

from PIL import Image, ImageOps

from .display import effective_ui_screen
from .engine import ProcessResult
from .exporting import AtomicBackgroundEngine, reserve_output_path
from .i18n import tr
from .studio_v040 import ptx
from .studio_v049 import BackgroundPXRStudio049App


EXPORT_TX = {
    "English": {
        "export_failed": (
            "Couldn't export {name}. Nothing was overwritten. "
            "Error ID: {error_id}. Open LOG for technical details."
        ),
        "mask_export_failed": (
            "Couldn't export the mask for {name}. Nothing was overwritten. "
            "Error ID: {error_id}. Open LOG for technical details."
        ),
        "export_failed_status": "Export failed: {name}",
    },
    "Polski": {
        "export_failed": (
            "Nie udało się wyeksportować {name}. Nic nie zostało nadpisane. "
            "ID błędu: {error_id}. Otwórz LOG, aby zobaczyć szczegóły techniczne."
        ),
        "mask_export_failed": (
            "Nie udało się wyeksportować maski dla {name}. Nic nie zostało nadpisane. "
            "ID błędu: {error_id}. Otwórz LOG, aby zobaczyć szczegóły techniczne."
        ),
        "export_failed_status": "Błąd eksportu: {name}",
    },
}


def etx(language: str, key: str, **kwargs) -> str:
    table = EXPORT_TX.get(language, EXPORT_TX["English"])
    text = table.get(key, EXPORT_TX["English"].get(key, key))
    return text.format(**kwargs) if kwargs else text


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
        """Process collision-safe batches without losing diagnostic telemetry."""
        ok = fail = 0
        total = len(items)
        reserved_outputs: set[str] = set()
        for pos, (idx, path) in enumerate(items, 1):
            if self.cancel_event.is_set():
                break

            name = path.name
            self._emit(pos, total, name, 0.03, "open_img")
            self.diagnostics.write("INFO", "open", "Opening source image", str(path))
            try:
                with Image.open(path) as source:
                    original = ImageOps.exif_transpose(source).convert("RGBA")

                self._emit(pos, total, name, 0.16, "ai")
                self.diagnostics.write(
                    "INFO",
                    "ai",
                    (
                        "AI removal started | "
                        f"model={opts.model_label} | alpha_matting={opts.alpha_matting}"
                    ),
                    str(path),
                )

                stop = threading.Event()
                started = time.monotonic()

                def heartbeat():
                    while not stop.wait(1.0):
                        stage = "cancel_wait" if self.cancel_event.is_set() else "ai"
                        self._emit(
                            pos,
                            total,
                            name,
                            0.16,
                            stage,
                            int(time.monotonic() - started),
                        )

                threading.Thread(target=heartbeat, daemon=True).start()
                try:
                    ai = self.engine.remove_background(original, opts)
                    memory_notice = getattr(self.engine, "last_remove_notice", None)
                    if memory_notice:
                        self.diagnostics.write(
                            "WARN",
                            "ai-memory",
                            memory_notice,
                            str(path),
                        )
                finally:
                    stop.set()

                if self.cancel_event.is_set():
                    break

                self._emit(pos, total, name, 0.74, "refine")
                cutout = self.engine.refine_cutout(original, ai, opts)
                self._emit(pos, total, name, 0.84, "compose")
                output = self.engine.compose(original, cutout, opts)
                result = ProcessResult(original, cutout, output)
                destination = None

                if save:
                    self._emit(pos, total, name, 0.92, "save")
                    destination = reserve_output_path(
                        path,
                        self.output_dir.get(),
                        opts.export_format,
                        opts.output_suffix,
                        reserved_outputs,
                    )
                    self.engine.save(output, destination, opts.export_format)

                ok += 1
                self.diagnostics.write(
                    "INFO",
                    "complete",
                    (
                        "Item completed | "
                        f"output={destination if destination else 'preview only'}"
                    ),
                    str(path),
                )
                self.events.put(
                    ("result", idx, result, str(destination) if destination else None)
                )
                self._emit(pos, total, name, 1.0, "done")
            except Exception as exc:
                fail += 1
                trace = traceback.format_exc()
                error_id = self.diagnostics.exception("processing", path, exc, trace)
                self.events.put(
                    (
                        "diag_error",
                        pos,
                        total,
                        name,
                        error_id,
                        type(exc).__name__,
                        str(exc),
                    )
                )
                self.events.put(("progress", pos / total if total else 0.0))

        self.events.put(("done", ok, fail, self.cancel_event.is_set(), save))

    def _show_export_failure(self, stage, source, exc, trace, message_key="export_failed"):
        """Report an export failure without leaking a traceback into the UI."""
        language = self.language.get()
        error_id = "PXR-EXPORT"
        try:
            error_id = self.diagnostics.exception(stage, source, exc, trace)
        except Exception:
            # Error reporting must stay usable even if the local diagnostics
            # directory is unavailable or temporarily locked.
            pass

        try:
            self._error_status(error_id, source.name, type(exc).__name__)
        except Exception:
            self.status_text.set(etx(language, "export_failed_status", name=source.name))

        messagebox.showerror(
            tr(language, "error"),
            etx(language, message_key, name=source.name, error_id=error_id),
        )

    def _export_current(self):
        if self.selected_index is None or not self._validate():
            return
        if self.preview_after is None:
            messagebox.showwarning(
                tr(self.language.get(), "error"),
                tr(self.language.get(), "no_result"),
            )
            return

        source = self.files[self.selected_index]
        try:
            self._recompose()
            opts = self._options()
            dest = reserve_output_path(
                source,
                self.output_dir.get(),
                opts.export_format,
                opts.output_suffix,
            )
            self.engine.save(self.preview_after, dest, opts.export_format)
        except Exception as exc:
            self._show_export_failure(
                "image-export",
                source,
                exc,
                traceback.format_exc(),
            )
            return

        try:
            self.diagnostics.write(
                "INFO", "image-export", f"Image saved | output={dest}", str(source)
            )
        except Exception:
            pass
        self.status_text.set(tr(self.language.get(), "saved", name=dest.name))
        if self.auto_open_output.get():
            self._open_output_folder()

    def _export_mask(self):
        """Export the current mask atomically without overwriting prior masks."""
        cutout = self._current_cutout()
        if cutout is None or self.selected_index is None:
            messagebox.showwarning(
                tr(self.language.get(), "error"),
                ptx(self.language.get(), "need_ai"),
            )
            return

        source = self.files[self.selected_index]
        try:
            destination = reserve_output_path(
                source,
                self.output_dir.get(),
                "PNG",
                "_mask",
            )
            self.engine.save_mask(cutout, destination)
        except Exception as exc:
            self._show_export_failure(
                "mask-export",
                source,
                exc,
                traceback.format_exc(),
                message_key="mask_export_failed",
            )
            return

        try:
            self.diagnostics.write(
                "INFO", "mask-export", f"Mask saved | output={destination}", str(source)
            )
        except Exception:
            pass
        self.status_text.set(
            ptx(self.language.get(), "mask_saved", name=destination.name)
        )
