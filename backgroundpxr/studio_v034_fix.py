from __future__ import annotations

import customtkinter as ctk

from .studio_ui import BackgroundPXRStudioApp
from .studio_v034 import BackgroundPXRStudio034App


class BackgroundPXRStudio034FixedApp(BackgroundPXRStudio034App):
    """Correct 0.3.4 sidebar composition on CustomTkinter scrollable frames."""

    def _build_sidebar(self, parent):
        # Intentionally bypass BackgroundPXRStudio034App._build_sidebar here.
        # CTkScrollableFrame owns internal canvas widgets, so its .master chain
        # is not the visible project card. Build the proven 0.3.3 sidebar first
        # and attach Studio controls to the real column-0 frame.
        BackgroundPXRStudioApp._build_sidebar(self, parent)

        candidates = parent.grid_slaves(row=0, column=0)
        side = candidates[0] if candidates else self.left_panel
        self.left_panel = side
        parent.grid_columnconfigure(0, minsize=336, weight=0)
        if side is None:
            return
        side.configure(width=336)

        # Existing list wrapper is the visible child in row 6.
        list_candidates = side.grid_slaves(row=6, column=0)
        listwrap = list_candidates[0] if list_candidates else None
        if listwrap is None:
            return

        side.grid_rowconfigure(6, weight=0)
        side.grid_rowconfigure(8, weight=1)
        listwrap.grid_configure(row=8, pady=(7, 8))

        self.studio_modes_label = ctk.CTkLabel(
            side,
            text="",
            height=18,
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color="#8DCFFF",
        )
        self.studio_modes_label.grid(row=6, column=0, sticky="w", padx=14, pady=(6, 4))

        self.studio_mode_bar = ctk.CTkSegmentedButton(
            side,
            values=["Cutout", "Replace", "Blur", "Studio"],
            command=self._on_studio_mode,
            height=31,
            selected_color=self.VIOLET,
            selected_hover_color="#5D3EE0",
            unselected_color="#0B2139",
            unselected_hover_color="#123252",
            border_width=1,
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
        )
        self.studio_mode_bar.grid(row=7, column=0, sticky="ew", padx=14)
