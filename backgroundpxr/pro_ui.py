from __future__ import annotations

import os

import customtkinter as ctk

from .diagnostics import BackgroundPXRDiagnosticsApp


class BackgroundPXRProApp(BackgroundPXRDiagnosticsApp):
    """Compact professional shell tuned for 1600x900 and high-DPI Windows displays."""

    def _configure_root(self):
        # CustomTkinter applies Windows DPI scaling on top of widget sizes.  On
        # 900/1080p displays this made the right-side studio cards taller than
        # the available workspace.  Keep text readable, but normalize widget
        # geometry before any widgets are created.
        try:
            sh = self.root.winfo_screenheight()
            ctk.set_widget_scaling(0.88 if sh <= 1080 else 1.0)
        except Exception:
            pass
        super()._configure_root()
        try:
            if os.name == "nt":
                self.root.state("zoomed")
        except Exception:
            pass

    def _build_right(self, parent):
        # Wider controls + substantially less vertical padding.  No whole-panel
        # scrollbar: every core control stays visible at 1600x900.
        self.right_panel = ctk.CTkFrame(
            parent, width=382, corner_radius=14, fg_color="#08182B",
            border_width=1, border_color=self.LINE,
        )
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=(7, 10), pady=8)
        self.right_panel.grid_propagate(False)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self._build_ai_card(self.right_panel)
        self._build_refine_card(self.right_panel)
        self._build_manual_card(self.right_panel)
        self._build_export_card(self.right_panel)

    def _card(self, parent, row):
        f = ctk.CTkFrame(
            parent, corner_radius=11, fg_color=self.CARD,
            border_width=1, border_color="#1A4062",
        )
        f.grid(row=row, column=0, sticky="ew", padx=8, pady=(8 if row == 0 else 4, 0))
        f.grid_columnconfigure(0, weight=1)
        return f

    def _card_title(self, f, icon, name_attr, sub_attr=None):
        h = ctk.CTkFrame(f, fg_color="transparent")
        h.grid(row=0, column=0, sticky="ew", padx=9, pady=(5, 2))
        h.grid_columnconfigure(1, weight=1)
        c = ctk.CTkLabel(h, text="", image=self._icon(icon, self.ACCENT, 18))
        c.grid(row=0, column=0, rowspan=2 if sub_attr else 1, padx=(0, 6))
        setattr(
            self, name_attr,
            ctk.CTkLabel(h, text="", font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color=self.TEXT),
        )
        getattr(self, name_attr).grid(row=0, column=1, sticky="w")
        if sub_attr:
            setattr(
                self, sub_attr,
                ctk.CTkLabel(h, text="", font=ctk.CTkFont("Segoe UI", 7), text_color=self.MUTED),
            )
            getattr(self, sub_attr).grid(row=1, column=1, sticky="w")

    def _build_ai_card(self, parent):
        f = self.ai_card = self._card(parent, 0)
        self._card_title(f, "magic", "ai_title", "ai_sub")
        grid = ctk.CTkFrame(f, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="ew", padx=9)
        grid.grid_columnconfigure((0, 1), weight=1)
        self.model_label = ctk.CTkLabel(grid, text="", text_color=self.MUTED, font=ctk.CTkFont("Segoe UI", 7))
        self.model_label.grid(row=0, column=0, sticky="w")
        self.output_label = ctk.CTkLabel(grid, text="", text_color=self.MUTED, font=ctk.CTkFont("Segoe UI", 7))
        self.output_label.grid(row=0, column=1, sticky="w", padx=(5, 0))
        self.model_menu = ctk.CTkOptionMenu(
            grid, variable=self.model, values=[], height=27,
            fg_color="#102A49", button_color=self.VIOLET, button_hover_color="#5D3EE0",
            font=ctk.CTkFont("Segoe UI", 9), dropdown_font=ctk.CTkFont("Segoe UI", 9),
        )
        self.model_menu.grid(row=1, column=0, sticky="ew", padx=(0, 3))
        self.bg_menu = ctk.CTkOptionMenu(
            grid, values=[], command=self._on_bg_choice, height=27,
            fg_color="#102A49", button_color="#137A92", button_hover_color="#1695B1",
            font=ctk.CTkFont("Segoe UI", 9), dropdown_font=ctk.CTkFont("Segoe UI", 9),
        )
        self.bg_menu.grid(row=1, column=1, sticky="ew", padx=(3, 0))
        opt = ctk.CTkFrame(f, fg_color="transparent")
        opt.grid(row=2, column=0, sticky="ew", padx=9, pady=(4, 0))
        opt.grid_columnconfigure((0, 1), weight=1)
        self.color_btn = ctk.CTkButton(opt, text="", command=self._pick_color, height=24, fg_color="#0F2946", hover_color="#143B61", font=ctk.CTkFont("Segoe UI", 8))
        self.color_btn.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        self.bg_image_btn = ctk.CTkButton(opt, text="", command=self._pick_background_image, height=24, fg_color="#0F2946", hover_color="#143B61", font=ctk.CTkFont("Segoe UI", 8))
        self.bg_image_btn.grid(row=0, column=1, sticky="ew", padx=(2, 0))
        self.remove_btn = ctk.CTkButton(
            f, text="", image=self._icon("magic", "#FFFFFF", 16), command=self._process_selected,
            height=31, fg_color=self.VIOLET, hover_color="#5D3EE0", font=ctk.CTkFont("Segoe UI", 9, "bold"),
        )
        self.remove_btn.grid(row=3, column=0, sticky="ew", padx=9, pady=(5, 6))

    def _build_refine_card(self, parent):
        f = self.refine_card = self._card(parent, 1)
        self._card_title(f, "fit", "refine_title")
        labels = ctk.CTkFrame(f, fg_color="transparent")
        labels.grid(row=1, column=0, sticky="ew", padx=9)
        labels.grid_columnconfigure((0, 1, 2), weight=1)
        self.edge_label = ctk.CTkLabel(labels, text="", font=ctk.CTkFont("Segoe UI", 7), text_color=self.MUTED)
        self.edge_label.grid(row=0, column=0, sticky="w")
        self.feather_label = ctk.CTkLabel(labels, text="", font=ctk.CTkFont("Segoe UI", 7), text_color=self.MUTED)
        self.feather_label.grid(row=0, column=1)
        self.contrast_label = ctk.CTkLabel(labels, text="", font=ctk.CTkFont("Segoe UI", 7), text_color=self.MUTED)
        self.contrast_label.grid(row=0, column=2, sticky="e")
        sliders = ctk.CTkFrame(f, fg_color="transparent")
        sliders.grid(row=2, column=0, sticky="ew", padx=7)
        sliders.grid_columnconfigure((0, 1, 2), weight=1)
        self.edge_slider = ctk.CTkSlider(sliders, from_=-5, to=5, number_of_steps=10, variable=self.edge_refine, progress_color=self.ACCENT, height=11)
        self.edge_slider.grid(row=0, column=0, sticky="ew", padx=3)
        self.feather_slider = ctk.CTkSlider(sliders, from_=0, to=3, number_of_steps=30, variable=self.edge_softness, progress_color=self.ACCENT, height=11)
        self.feather_slider.grid(row=0, column=1, sticky="ew", padx=3)
        self.contrast_slider = ctk.CTkSlider(sliders, from_=0, to=50, number_of_steps=50, variable=self.edge_contrast, progress_color=self.VIOLET, height=11)
        self.contrast_slider.grid(row=0, column=2, sticky="ew", padx=3)
        toggles = ctk.CTkFrame(f, fg_color="transparent")
        toggles.grid(row=3, column=0, sticky="ew", padx=9, pady=(2, 5))
        toggles.grid_columnconfigure((0, 1), weight=1)
        self.matting_switch = ctk.CTkSwitch(toggles, text="", variable=self.alpha_matting, progress_color=self.VIOLET, font=ctk.CTkFont("Segoe UI", 7), switch_width=30, switch_height=16)
        self.matting_switch.grid(row=0, column=0, columnspan=2, sticky="w")
        self.shadow_switch = ctk.CTkSwitch(toggles, text="", variable=self.shadow, command=self._recompose_refresh, progress_color=self.VIOLET, font=ctk.CTkFont("Segoe UI", 7), switch_width=30, switch_height=16)
        self.shadow_switch.grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.trim_switch = ctk.CTkSwitch(toggles, text="", variable=self.trim, command=self._recompose_refresh, progress_color=self.ACCENT, font=ctk.CTkFont("Segoe UI", 7), switch_width=30, switch_height=16)
        self.trim_switch.grid(row=1, column=1, sticky="w", pady=(2, 0))

    def _build_manual_card(self, parent):
        f = self.manual_card = self._card(parent, 2)
        self._card_title(f, "brush", "manual_title", "manual_sub")
        buttons = ctk.CTkFrame(f, fg_color="transparent")
        buttons.grid(row=1, column=0, sticky="ew", padx=7)
        buttons.grid_columnconfigure((0, 1, 2), weight=1)
        self.restore_btn = ctk.CTkButton(buttons, text="", image=self._icon("brush", "#FFFFFF", 14), command=lambda: self._set_tool("restore"), height=29, fg_color=self.VIOLET, hover_color="#5D3EE0", font=ctk.CTkFont("Segoe UI", 7))
        self.restore_btn.grid(row=0, column=0, sticky="ew", padx=2)
        self.erase_btn = ctk.CTkButton(buttons, text="", image=self._icon("eraser", "#BFEAFF", 14), command=lambda: self._set_tool("erase"), height=29, fg_color="#102B49", hover_color="#173C61", font=ctk.CTkFont("Segoe UI", 7))
        self.erase_btn.grid(row=0, column=1, sticky="ew", padx=2)
        self.smart_btn = ctk.CTkButton(buttons, text="", image=self._icon("magic", "#BFEAFF", 14), command=self._smart_cleanup, height=29, fg_color="#102B49", hover_color="#173C61", font=ctk.CTkFont("Segoe UI", 7))
        self.smart_btn.grid(row=0, column=2, sticky="ew", padx=2)
        buttons2 = ctk.CTkFrame(f, fg_color="transparent")
        buttons2.grid(row=2, column=0, sticky="ew", padx=7, pady=(3, 0))
        buttons2.grid_columnconfigure((0, 1), weight=1)
        self.islands_btn = ctk.CTkButton(buttons2, text="", command=self._remove_islands, height=23, fg_color="#0F2946", hover_color="#163A5D", font=ctk.CTkFont("Segoe UI", 7))
        self.islands_btn.grid(row=0, column=0, sticky="ew", padx=2)
        self.reset_btn = ctk.CTkButton(buttons2, text="", command=self._reset_mask, height=23, fg_color="#0F2946", hover_color="#163A5D", font=ctk.CTkFont("Segoe UI", 7))
        self.reset_btn.grid(row=0, column=1, sticky="ew", padx=2)
        values = ctk.CTkFrame(f, fg_color="transparent")
        values.grid(row=3, column=0, sticky="ew", padx=9, pady=(3, 0))
        values.grid_columnconfigure((0, 1), weight=1)
        self.brush_size_label = ctk.CTkLabel(values, text="", font=ctk.CTkFont("Segoe UI", 7), text_color=self.MUTED)
        self.brush_size_label.grid(row=0, column=0, sticky="w")
        self.brush_hard_label = ctk.CTkLabel(values, text="", font=ctk.CTkFont("Segoe UI", 7), text_color=self.MUTED)
        self.brush_hard_label.grid(row=0, column=1, sticky="w")
        sliders = ctk.CTkFrame(f, fg_color="transparent")
        sliders.grid(row=4, column=0, sticky="ew", padx=7, pady=(0, 5))
        sliders.grid_columnconfigure((0, 1), weight=1)
        self.brush_size_slider = ctk.CTkSlider(sliders, from_=8, to=220, number_of_steps=106, variable=self.brush_size, progress_color=self.ACCENT, height=11)
        self.brush_size_slider.grid(row=0, column=0, sticky="ew", padx=3)
        self.brush_hard_slider = ctk.CTkSlider(sliders, from_=0, to=100, number_of_steps=20, variable=self.brush_hardness, progress_color=self.VIOLET, height=11)
        self.brush_hard_slider.grid(row=0, column=1, sticky="ew", padx=3)

    def _build_export_card(self, parent):
        f = self.export_card = self._card(parent, 3)
        self._card_title(f, "export", "export_title", "export_sub")
        row = ctk.CTkFrame(f, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=9)
        row.grid_columnconfigure((0, 1), weight=1)
        self.format_menu = ctk.CTkSegmentedButton(row, values=["PNG", "JPG", "WEBP"], variable=self.export_format, height=25, selected_color=self.VIOLET, selected_hover_color="#5D3EE0", font=ctk.CTkFont("Segoe UI", 8))
        self.format_menu.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self.canvas_menu = ctk.CTkOptionMenu(row, variable=self.canvas_preset, values=[], command=lambda _v: self._recompose_refresh(), height=25, fg_color="#102A49", button_color="#137A92", font=ctk.CTkFont("Segoe UI", 8), dropdown_font=ctk.CTkFont("Segoe UI", 8))
        self.canvas_menu.grid(row=0, column=1, sticky="ew", padx=(3, 0))
        row2 = ctk.CTkFrame(f, fg_color="transparent")
        row2.grid(row=2, column=0, sticky="ew", padx=9, pady=(3, 0))
        row2.grid_columnconfigure(1, weight=1)
        self.suffix_entry = ctk.CTkEntry(row2, textvariable=self.output_suffix, width=67, height=24, font=ctk.CTkFont("Segoe UI", 8))
        self.suffix_entry.grid(row=0, column=0, padx=(0, 4))
        self.output_entry = ctk.CTkEntry(row2, textvariable=self.output_dir, height=24, font=ctk.CTkFont("Segoe UI", 8))
        self.output_entry.grid(row=0, column=1, sticky="ew", padx=(0, 3))
        self.output_btn = ctk.CTkButton(row2, text="…", width=27, height=24, command=self._choose_output, fg_color="#12304E")
        self.output_btn.grid(row=0, column=2)
        row3 = ctk.CTkFrame(f, fg_color="transparent")
        row3.grid(row=3, column=0, sticky="ew", padx=9, pady=(3, 0))
        row3.grid_columnconfigure(0, weight=1)
        self.auto_open_switch = ctk.CTkSwitch(row3, text="", variable=self.auto_open_output, progress_color=self.ACCENT, font=ctk.CTkFont("Segoe UI", 7), switch_width=30, switch_height=16)
        self.auto_open_switch.grid(row=0, column=0, sticky="w")
        self.open_folder_btn = ctk.CTkButton(row3, text="", command=self._open_output_folder, width=78, height=22, fg_color="#102B49", font=ctk.CTkFont("Segoe UI", 7))
        self.open_folder_btn.grid(row=0, column=1)
        self.progress_bar = ctk.CTkProgressBar(f, variable=self.progress, height=5, progress_color=self.ACCENT, fg_color="#10243C")
        self.progress_bar.grid(row=4, column=0, sticky="ew", padx=9, pady=(4, 1))
        self.progress_bar.set(0)
        self.status_label = ctk.CTkLabel(f, textvariable=self.status_text, text_color="#9BB2C9", font=ctk.CTkFont("Segoe UI", 7), anchor="w", height=18)
        self.status_label.grid(row=5, column=0, sticky="ew", padx=9)
        actions = ctk.CTkFrame(f, fg_color="transparent")
        actions.grid(row=6, column=0, sticky="ew", padx=9, pady=(2, 6))
        actions.grid_columnconfigure((0, 1), weight=1)
        self.export_btn = ctk.CTkButton(actions, text="", image=self._icon("export", "#FFFFFF", 15), command=self._export_current, height=29, fg_color=self.VIOLET, hover_color="#5D3EE0", font=ctk.CTkFont("Segoe UI", 8, "bold"))
        self.export_btn.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        self.process_all_btn = ctk.CTkButton(actions, text="", command=self._process_all, height=29, fg_color="#12304E", hover_color="#19446D", font=ctk.CTkFont("Segoe UI", 8, "bold"))
        self.process_all_btn.grid(row=0, column=1, sticky="ew", padx=(2, 0))
