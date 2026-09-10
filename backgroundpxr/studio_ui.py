from __future__ import annotations

import customtkinter as ctk

from .pro_ui import BackgroundPXRProApp


class BackgroundPXRStudioApp(BackgroundPXRProApp):
    """Final readable studio layout: large text, compact rows, no panel scrollbars."""

    def _build_sidebar(self, parent):
        super()._build_sidebar(parent)
        # Extra room for Polish labels and the project header at Windows DPI.
        parent.grid_columnconfigure(0, minsize=330)
        if self.left_panel is not None:
            self.left_panel.configure(width=330)
        self.clear_btn.configure(width=92)

    def _card_title(self, frame, icon, name_attr, sub_attr=None):
        # CustomTkinter labels default to a relatively tall widget. Explicit
        # heights save vertical space while preserving 11/9 point readable text.
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(4, 1))
        header.grid_columnconfigure(1, weight=1)

        icon_label = ctk.CTkLabel(
            header, text="", image=self._icon(icon, self.ACCENT, 18),
            width=22, height=22,
        )
        icon_label.grid(row=0, column=0, rowspan=2 if sub_attr else 1, padx=(0, 7))

        title = ctk.CTkLabel(
            header, text="", height=18,
            font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=self.TEXT,
        )
        setattr(self, name_attr, title)
        title.grid(row=0, column=1, sticky="w")

        if sub_attr:
            subtitle = ctk.CTkLabel(
                header, text="", height=14,
                font=ctk.CTkFont("Segoe UI", 9), text_color=self.MUTED,
            )
            setattr(self, sub_attr, subtitle)
            subtitle.grid(row=1, column=1, sticky="w")

    def _build_right(self, parent):
        super()._build_right(parent)
        parent.grid_columnconfigure(2, minsize=420)
        self.right_panel.configure(width=420)

        # Compact only vertical geometry. Font sizes intentionally stay >= 9pt.
        for widget in (self.model_label, self.output_label):
            widget.configure(height=16)
        for widget in (self.edge_label, self.feather_label, self.contrast_label):
            widget.configure(height=16)
        for widget in (self.brush_size_label, self.brush_hard_label):
            widget.configure(height=16)

        for switch in (self.matting_switch, self.shadow_switch, self.trim_switch, self.auto_open_switch):
            switch.configure(height=20)

        # Tighten safe gaps that contributed no visual information.
        self.ai_card.grid_configure(pady=(6, 0))
        self.refine_card.grid_configure(pady=(3, 0))
        self.manual_card.grid_configure(pady=(3, 0))
        self.export_card.grid_configure(pady=(3, 0))

    def _build_footer(self):
        super()._build_footer()
        self.footer_left.configure(font=ctk.CTkFont("Segoe UI", 9))
        self.footer_by.configure(font=ctk.CTkFont("Segoe UI", 9, "bold"))
        self.footer_github.configure(font=ctk.CTkFont("Segoe UI", 9, underline=True), width=105)
