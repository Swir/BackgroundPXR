from __future__ import annotations

import customtkinter as ctk

from .inspection import mask_overlay_image
from .settings import SettingsStore
from .studio_v043 import BackgroundPXRStudio043App


MASK_OVERLAY_TX = {
    "English": "Mask overlay",
    "Polski": "Nakładka maski",
}


class BackgroundPXRStudio044App(BackgroundPXRStudio043App):
    """Studio Pro manual editor with a live mask overlay and precision cursor."""

    def __init__(self, root):
        cfg = SettingsStore().load()
        self.mask_overlay = ctk.BooleanVar(
            master=root, value=bool(cfg.get("mask_overlay", True))
        )
        super().__init__(root)
        self.root.bind("<Key-m>", self._toggle_mask_overlay)
        self.root.bind("<Key-M>", self._toggle_mask_overlay)

    def _build_manual_card(self, parent):
        super()._build_manual_card(parent)

        values = self.brush_size_label.master
        values.grid_columnconfigure(2, weight=0)
        self.mask_overlay_switch = ctk.CTkSwitch(
            values,
            text="",
            variable=self.mask_overlay,
            command=self._on_mask_overlay_change,
            progress_color="#19B7C9",
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
            switch_width=30,
            switch_height=16,
        )
        self.mask_overlay_switch.grid(
            row=0, column=2, sticky="e", padx=(8, 0)
        )

    def _apply_language(self):
        super()._apply_language()
        if not hasattr(self, "mask_overlay_switch"):
            return
        self.mask_overlay_switch.configure(
            text=MASK_OVERLAY_TX.get(
                self.language.get(), MASK_OVERLAY_TX["English"]
            )
        )

    def _save_settings(self):
        super()._save_settings()
        if not hasattr(self, "mask_overlay") or not hasattr(self, "settings_store"):
            return
        data = self.settings_store.load()
        data["mask_overlay"] = bool(self.mask_overlay.get())
        self.settings_store.save(data)

    def _on_mask_overlay_change(self):
        self._save_settings()
        self._refresh_after_only()

    def _toggle_mask_overlay(self, _event=None):
        if self.tool not in {"restore", "erase"}:
            return
        self.mask_overlay.set(not bool(self.mask_overlay.get()))
        self._on_mask_overlay_change()

    def _after_image(self):
        if (
            self.tool in {"restore", "erase"}
            and bool(self.mask_overlay.get())
        ):
            cutout = self._current_cutout()
            if cutout is not None:
                return mask_overlay_image(cutout)
        return super()._after_image()

    def _on_after_motion(self, event):
        if self.tool not in {"restore", "erase"}:
            return
        self._refresh_after_only()
        self._draw_brush_cursor(event.x, event.y)

    def _draw_brush_cursor(self, x: float, y: float) -> None:
        scale = self._after_transform[2] if self._after_transform else 1.0
        radius = max(4.0, float(self.brush_size.get()) * 0.5 * scale)
        hardness = max(0.0, min(1.0, float(self.brush_hardness.get()) / 100.0))
        inner_radius = max(2.0, radius * hardness)
        accent = "#28E09A" if self.tool == "restore" else "#FF5C8A"

        # A dark backing ring keeps the cursor visible over white, transparent,
        # and high-contrast photographs.
        self.after_canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            outline="#06101E",
            width=4,
            tags="cursor",
        )
        self.after_canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            outline=accent,
            width=2,
            tags="cursor",
        )

        # The inner ring visualizes brush hardness instead of forcing the user
        # to infer it from a slider while painting.
        if inner_radius < radius - 1:
            self.after_canvas.create_oval(
                x - inner_radius,
                y - inner_radius,
                x + inner_radius,
                y + inner_radius,
                outline="#F4F8FF",
                width=1,
                dash=(2, 2),
                tags="cursor",
            )

        cross = min(5.0, max(2.0, radius * 0.12))
        self.after_canvas.create_line(
            x - cross, y, x + cross, y, fill=accent, width=1, tags="cursor"
        )
        self.after_canvas.create_line(
            x, y - cross, x, y + cross, fill=accent, width=1, tags="cursor"
        )
