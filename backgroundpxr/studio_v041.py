from __future__ import annotations

from .inspection import edge_inspection_image
from .studio_v040 import BackgroundPXRStudio040App, ptx


EDGE_TX = {
    "English": "Edges",
    "Polski": "Krawędzie",
}


class BackgroundPXRStudio041App(BackgroundPXRStudio040App):
    """Studio Pro with a dedicated alpha-edge inspection preview.

    The QA preview is intentionally non-destructive: it only changes what is
    shown on the right preview canvas. The current mask, composition settings,
    manual-editor state, and exported image remain untouched.
    """

    def _edge_label(self) -> str:
        return EDGE_TX.get(self.language.get(), EDGE_TX["English"])

    def _preview_values(self) -> list[str]:
        language = self.language.get()
        return [
            ptx(language, "preview_result"),
            ptx(language, "preview_mask"),
            self._edge_label(),
            ptx(language, "preview_black"),
            ptx(language, "preview_white"),
        ]

    def _build_style_card(self, parent):
        super()._build_style_card(parent)
        self.preview_selector.configure(values=self._preview_values())
        self.preview_selector.set(self._preview_label(self.preview_mode.get()))

    def _apply_language(self):
        super()._apply_language()
        if not hasattr(self, "preview_selector"):
            return
        self.preview_selector.configure(values=self._preview_values())
        self.preview_selector.set(self._preview_label(self.preview_mode.get()))

    def _preview_label(self, key: str) -> str:
        if key == "edge":
            return self._edge_label()
        return super()._preview_label(key)

    def _on_preview_mode(self, label: str):
        if label == self._edge_label():
            self.preview_mode.set("edge")
            self._save_settings()
            self._refresh_after_only()
            return
        super()._on_preview_mode(label)

    def _after_image(self):
        if self.tool in {"restore", "erase"}:
            return super()._after_image()

        cutout = self._current_cutout()
        if cutout is not None and self.preview_mode.get() == "edge":
            return edge_inspection_image(cutout)
        return super()._after_image()
