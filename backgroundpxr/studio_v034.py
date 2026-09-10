from __future__ import annotations

import customtkinter as ctk

from .studio_ui import BackgroundPXRStudioApp
from .i18n import tr


STUDIO_TX = {
    "English": {
        "studio_modes": "AI BACKGROUND STUDIO",
        "cutout": "Cutout",
        "replace": "Replace",
        "blur": "Blur",
        "studio": "Studio",
        "filmstrip_show": "Show thumbnails",
        "filmstrip_hide": "Hide thumbnails",
        "studio_ready": "Studio mode ready — choose a background color or image.",
        "replace_ready": "Replace mode — choose a background image or color.",
    },
    "Polski": {
        "studio_modes": "AI BACKGROUND STUDIO",
        "cutout": "Wytnij",
        "replace": "Podmień",
        "blur": "Rozmyj",
        "studio": "Studio",
        "filmstrip_show": "Pokaż miniatury",
        "filmstrip_hide": "Ukryj miniatury",
        "studio_ready": "Tryb Studio gotowy — wybierz kolor lub obraz tła.",
        "replace_ready": "Tryb Podmień — wybierz obraz lub kolor tła.",
    },
}


def stx(language: str, key: str) -> str:
    return STUDIO_TX.get(language, STUDIO_TX["English"]).get(key, key)


class BackgroundPXRStudio034App(BackgroundPXRStudioApp):
    """BackgroundPXR 0.3.4 shell.

    Goals:
    - keep the proven 0.3.3 AI engine and diagnostics untouched,
    - make 1600x900/high-DPI layouts safer at the bottom,
    - begin the real AI Background Studio workflow,
    - keep all core controls visible without a whole-window scrollbar.
    """

    def __init__(self, root):
        self.studio_mode = ctk.StringVar(master=root, value="cutout")
        self._filmstrip_expanded = False
        super().__init__(root)
        self._bind_studio_shortcuts()

    def _configure_root(self):
        super()._configure_root()
        # Leave extra safety for Windows taskbars / unusual DPI work areas.
        try:
            self.root.minsize(1240, 740)
        except Exception:
            pass

    def _build_header(self):
        super()._build_header()
        # Gain vertical workspace without reducing text size.
        try:
            header = self.title_label.master.master
            header.configure(height=66)
        except Exception:
            pass

    def _build_sidebar(self, parent):
        super()._build_sidebar(parent)

        # Wider project area for Polish labels and long file names.
        parent.grid_columnconfigure(0, minsize=336)
        side = self.file_list.master.master
        side.configure(width=336)
        self.left_panel = side

        # Insert a first-class Studio mode selector above the project list.
        listwrap = self.file_list.master
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

    def _build_center(self, parent):
        super()._build_center(parent)

        # Compact top toolbar while preserving readable 9pt labels.
        try:
            toolbar = self.zoom_label.master
            toolbar.configure(height=52)
            for button in self.tool_buttons.values():
                button.configure(height=42, font=ctk.CTkFont("Segoe UI", 9))
        except Exception:
            pass

        # The old always-visible 82px filmstrip was the easiest place to win
        # vertical space. Keep it available, but collapsed by default.
        strip = self.filmstrip.master
        self.filmstrip_strip = strip
        self.filmstrip.grid_remove()
        strip.configure(height=38)
        strip.grid_configure(pady=(6, 0))

        self.filmstrip_toggle = ctk.CTkButton(
            strip,
            text="",
            command=self._toggle_filmstrip,
            width=118,
            height=24,
            fg_color="#0D2845",
            hover_color="#153B60",
            border_width=1,
            border_color="#28557D",
            text_color="#B8DFFF",
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
        )
        self.filmstrip_toggle.grid(row=0, column=1, sticky="e", padx=4, pady=(6, 0))
        self.fit_all_btn.configure(height=24, width=76)

    def _build_right(self, parent):
        super()._build_right(parent)
        # More bottom safety than 0.3.3. We only compact empty spacing / widget
        # chrome; readable fonts remain intact.
        self.right_panel.grid_configure(pady=(6, 6))
        for card in (self.ai_card, self.refine_card, self.manual_card, self.export_card):
            card.grid_configure(pady=(2, 0))

        self.remove_btn.configure(height=29)
        self.restore_btn.configure(height=27)
        self.erase_btn.configure(height=27)
        self.smart_btn.configure(height=27)
        self.export_btn.configure(height=27)
        self.process_all_btn.configure(height=27)
        self.status_label.configure(height=16)

    def _build_footer(self):
        super()._build_footer()
        footer = self.footer_by.master
        footer.configure(height=23)
        self.footer_left.configure(height=18)
        self.footer_by.configure(height=18)
        self.footer_github.configure(height=19)

    def _apply_language(self):
        super()._apply_language()
        if not hasattr(self, "studio_mode_bar"):
            return

        language = self.language.get()
        self.studio_modes_label.configure(text=stx(language, "studio_modes"))
        values = [
            stx(language, "cutout"),
            stx(language, "replace"),
            stx(language, "blur"),
            stx(language, "studio"),
        ]
        self.studio_mode_bar.configure(values=values)
        self.studio_mode_bar.set(stx(language, self.studio_mode.get()))
        self._update_filmstrip_text()

    def _render_file_list(self):
        # Replaces the old 8pt/24-character rows with readable 10pt rows.
        if not hasattr(self, "file_list"):
            return
        self._thumb_refs = []
        for child in self.file_list.winfo_children():
            child.destroy()

        for index, path in enumerate(self.files):
            selected = index == self.selected_index
            row = ctk.CTkFrame(
                self.file_list,
                height=56,
                corner_radius=9,
                fg_color="#123152" if selected else "#0A1C31",
                border_width=1,
                border_color=self.VIOLET if selected else "#173955",
            )
            row.pack(fill="x", padx=2, pady=2)
            image = self._thumb(path)
            name = path.name
            if len(name) > 34:
                name = name[:31] + "…"
            button = ctk.CTkButton(
                row,
                text=name,
                image=image,
                compound="left",
                anchor="w",
                command=lambda n=index: self._select_file(n),
                height=50,
                fg_color="transparent",
                hover_color="#163858",
                text_color="#DCEBFA",
                font=ctk.CTkFont("Segoe UI", 10),
            )
            button.pack(fill="x", padx=3, pady=2)

    def _toggle_filmstrip(self):
        self._filmstrip_expanded = not self._filmstrip_expanded
        if self._filmstrip_expanded:
            self.filmstrip.grid()
            self.filmstrip_strip.configure(height=90)
        else:
            self.filmstrip.grid_remove()
            self.filmstrip_strip.configure(height=38)
        self._update_filmstrip_text()
        self.root.after_idle(self._refresh_previews)

    def _update_filmstrip_text(self):
        if not hasattr(self, "filmstrip_toggle"):
            return
        key = "filmstrip_hide" if self._filmstrip_expanded else "filmstrip_show"
        prefix = "▴ " if self._filmstrip_expanded else "▾ "
        self.filmstrip_toggle.configure(text=prefix + stx(self.language.get(), key))

    def _on_studio_mode(self, label: str):
        language = self.language.get()
        lookup = {
            stx(language, "cutout"): "cutout",
            stx(language, "replace"): "replace",
            stx(language, "blur"): "blur",
            stx(language, "studio"): "studio",
        }
        mode = lookup.get(label, "cutout")
        self.studio_mode.set(mode)

        if mode == "cutout":
            self.background_mode.set("transparent")
            self.shadow.set(False)
        elif mode == "blur":
            self.background_mode.set("blur")
            self.shadow.set(False)
        elif mode == "replace":
            # Keep an already selected image. If none exists, use color as a
            # safe visible preview until the user chooses an image.
            self.background_mode.set("image" if self.bg_image_path else "color")
            self.shadow.set(False)
            self.status_text.set(stx(language, "replace_ready"))
        else:  # studio
            self.background_mode.set("white")
            self.shadow.set(True)
            self.status_text.set(stx(language, "studio_ready"))

        self._sync_background_menu()
        self._recompose_refresh()

    def _sync_background_menu(self):
        if not hasattr(self, "bg_menu"):
            return
        language = self.language.get()
        key = {
            "transparent": "bg_transparent",
            "white": "bg_white",
            "color": "bg_color",
            "image": "bg_image",
            "blur": "bg_blur",
        }.get(self.background_mode.get(), "bg_transparent")
        self.bg_menu.set(tr(language, key))

    def _on_bg_choice(self, value):
        super()._on_bg_choice(value)
        mode = self.background_mode.get()
        if mode == "transparent":
            self.studio_mode.set("cutout")
        elif mode == "blur":
            self.studio_mode.set("blur")
        elif mode in {"image", "color"}:
            self.studio_mode.set("replace")
        elif mode == "white":
            self.studio_mode.set("studio")
        if hasattr(self, "studio_mode_bar"):
            self.studio_mode_bar.set(stx(self.language.get(), self.studio_mode.get()))

    def _pick_color(self):
        super()._pick_color()
        if self.background_mode.get() == "color":
            self.studio_mode.set("replace")
            if hasattr(self, "studio_mode_bar"):
                self.studio_mode_bar.set(stx(self.language.get(), "replace"))

    def _pick_background_image(self):
        super()._pick_background_image()
        if self.bg_image_path:
            self.studio_mode.set("replace")
            if hasattr(self, "studio_mode_bar"):
                self.studio_mode_bar.set(stx(self.language.get(), "replace"))

    def _bind_studio_shortcuts(self):
        self.root.bind("<Control-z>", lambda _e: self._undo())
        self.root.bind("<Control-y>", lambda _e: self._redo())
        self.root.bind("<Control-plus>", lambda _e: self._zoom_by(1.22))
        self.root.bind("<Control-minus>", lambda _e: self._zoom_by(0.82))
        self.root.bind("<F6>", lambda _e: self._toggle_filmstrip())
        self.root.bind("<Alt-Key-1>", lambda _e: self._select_studio_mode("cutout"))
        self.root.bind("<Alt-Key-2>", lambda _e: self._select_studio_mode("replace"))
        self.root.bind("<Alt-Key-3>", lambda _e: self._select_studio_mode("blur"))
        self.root.bind("<Alt-Key-4>", lambda _e: self._select_studio_mode("studio"))

    def _select_studio_mode(self, mode: str):
        if mode not in {"cutout", "replace", "blur", "studio"}:
            return
        label = stx(self.language.get(), mode)
        self.studio_mode_bar.set(label)
        self._on_studio_mode(label)
