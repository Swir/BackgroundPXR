from __future__ import annotations

import customtkinter as ctk

from .inspection import wipe_compare_image
from .settings import SettingsStore
from .studio_v040 import ptx
from .studio_v041 import BackgroundPXRStudio041App


COMPARE_TX = {
    "English": {
        "label": "Compare",
        "wipe": "Before / After",
    },
    "Polski": {
        "label": "Porównaj",
        "wipe": "Przed / Po",
    },
}


class BackgroundPXRStudio042App(BackgroundPXRStudio041App):
    """Studio Pro with an interactive non-destructive Before/After wipe."""

    def __init__(self, root):
        cfg = SettingsStore().load()
        self.wipe_position = ctk.DoubleVar(
            master=root, value=float(cfg.get("wipe_position", 50.0))
        )
        super().__init__(root)

    def _compare_text(self, key: str) -> str:
        table = COMPARE_TX.get(self.language.get(), COMPARE_TX["English"])
        return table.get(key, COMPARE_TX["English"].get(key, key))

    def _compare_label(self) -> str:
        return self._compare_text("label")

    def _preview_values(self) -> list[str]:
        language = self.language.get()
        return [
            ptx(language, "preview_result"),
            self._compare_label(),
            ptx(language, "preview_mask"),
            self._edge_label(),
            ptx(language, "preview_black"),
            ptx(language, "preview_white"),
        ]

    def _build_style_card(self, parent):
        super()._build_style_card(parent)

        # Reuse the preset row instead of making the inspector taller. In
        # Compare mode the presets are temporarily replaced by a compact wipe
        # control, so the 1600x900 layout keeps the same vertical footprint.
        self.style_presets = self.sticker_preset_btn.master
        self.wipe_frame = ctk.CTkFrame(self.style_card, fg_color="transparent")
        self.wipe_frame.grid(row=7, column=0, sticky="ew", padx=8, pady=(7, 8))
        self.wipe_frame.grid_columnconfigure(1, weight=1)

        self.wipe_label = ctk.CTkLabel(
            self.wipe_frame,
            text="",
            height=24,
            width=76,
            anchor="w",
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
            text_color=self.MUTED,
        )
        self.wipe_label.grid(row=0, column=0, sticky="w", padx=(2, 7))

        self.wipe_slider = ctk.CTkSlider(
            self.wipe_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            variable=self.wipe_position,
            command=self._on_wipe_change,
            progress_color=self.ACCENT,
            height=14,
        )
        self.wipe_slider.grid(row=0, column=1, sticky="ew")

        self.wipe_value_label = ctk.CTkLabel(
            self.wipe_frame,
            text="",
            width=42,
            height=24,
            anchor="e",
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
            text_color="#B8DFFF",
        )
        self.wipe_value_label.grid(row=0, column=2, padx=(7, 2))
        self._sync_compare_controls()

    def _apply_language(self):
        super()._apply_language()
        if not hasattr(self, "wipe_frame"):
            return
        self.wipe_label.configure(text=self._compare_text("wipe"))
        self.wipe_value_label.configure(text=f"{int(round(self.wipe_position.get()))}%")
        self.preview_selector.configure(values=self._preview_values())
        self.preview_selector.set(self._preview_label(self.preview_mode.get()))
        self._sync_compare_controls()

    def _preview_label(self, key: str) -> str:
        if key == "compare":
            return self._compare_label()
        return super()._preview_label(key)

    def _on_preview_mode(self, label: str):
        if label == self._compare_label():
            self.preview_mode.set("compare")
            self._save_settings()
            self._sync_compare_controls()
            self._refresh_after_only()
            return
        super()._on_preview_mode(label)
        self._sync_compare_controls()

    def _sync_compare_controls(self):
        if not hasattr(self, "wipe_frame"):
            return
        if self.preview_mode.get() == "compare":
            self.style_presets.grid_remove()
            self.wipe_frame.grid()
        else:
            self.wipe_frame.grid_remove()
            self.style_presets.grid()

    def _on_wipe_change(self, _value=None):
        if hasattr(self, "wipe_value_label"):
            self.wipe_value_label.configure(
                text=f"{int(round(float(self.wipe_position.get())))}%"
            )
        if self.preview_mode.get() == "compare":
            self._refresh_after_only()

    def _after_image(self):
        if self.tool in {"restore", "erase"}:
            return super()._after_image()

        if self.preview_mode.get() == "compare":
            before = self._before_image()
            after = self.preview_after
            if after is None:
                return before
            if before is None:
                return after
            return wipe_compare_image(before, after, self.wipe_position.get())

        return super()._after_image()

    def _save_settings(self):
        super()._save_settings()
        if not hasattr(self, "wipe_position") or not hasattr(self, "settings_store"):
            return
        data = self.settings_store.load()
        data["wipe_position"] = float(self.wipe_position.get())
        self.settings_store.save(data)
