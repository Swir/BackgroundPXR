from __future__ import annotations

import os
import queue
import subprocess
import threading
import webbrowser
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps, ImageTk

from . import __version__
from .branding import ensure_app_icon
from .engine import BackgroundEngine, ProcessOptions, collect_images, is_supported_image, output_path_for
from .i18n import tr
from .settings import SettingsStore

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class BackgroundPXRApp:
    ACCENT = "#24D9FF"
    ACCENT_2 = "#7A5CFF"
    ACCENT_HOVER = "#12B9E0"
    BG = "#070B13"
    HEADER = "#09111F"
    PANEL_2 = "#121D2F"
    CARD = "#111C2D"
    MUTED = "#8290A7"
    TEXT = "#F4F7FC"
    GITHUB_URL = "https://github.com/Swir"

    def __init__(self, root) -> None:
        self.root = root
        self.engine = BackgroundEngine()
        self.settings_store = SettingsStore()
        cfg = self.settings_store.load()
        self.files: list[Path] = []
        self.selected_index: int | None = None
        self.preview_after: Image.Image | None = None
        self.worker: threading.Thread | None = None
        self.cancel_event = threading.Event()
        self.events: queue.Queue = queue.Queue()
        self.bg_image_path: str | None = None
        self.bg_color = str(cfg.get("background_color", "#FFFFFF"))

        self.language = ctk.StringVar(value=str(cfg.get("language", "English")))
        self.model = ctk.StringVar(value=str(cfg.get("model", "Quality")))
        self.background_mode = ctk.StringVar(value=str(cfg.get("background_mode", "transparent")))
        self.export_format = ctk.StringVar(value=str(cfg.get("export_format", "PNG")))
        self.edge_softness = ctk.DoubleVar(value=float(cfg.get("edge_softness", 0.8)))
        self.background_blur = ctk.DoubleVar(value=float(cfg.get("background_blur", 18)))
        self.shadow = ctk.BooleanVar(value=bool(cfg.get("shadow", False)))
        self.trim = ctk.BooleanVar(value=bool(cfg.get("trim", False)))
        self.padding = ctk.IntVar(value=int(cfg.get("padding", 24)))
        self.canvas_preset = ctk.StringVar(value=str(cfg.get("canvas_preset", "Original")))
        self.output_suffix = ctk.StringVar(value=str(cfg.get("output_suffix", "_pxr")))
        default_out = Path.home() / "Pictures" / "BackgroundPXR"
        self.output_dir = ctk.StringVar(value=str(cfg.get("output_dir", default_out)))
        self.auto_open_output = ctk.BooleanVar(value=bool(cfg.get("auto_open_output", False)))
        self.progress = ctk.DoubleVar(value=0)
        self.status_text = ctk.StringVar(value="")

        self._configure_root()
        self._build_ui()
        self._apply_language()
        self._poll_events()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_root(self) -> None:
        self.root.title("BackgroundPXR — Power eXtreme Remover")
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        width = min(1580, max(1180, sw - 80))
        height = min(920, max(760, sh - 120))
        x = max(0, (sw - width) // 2)
        y = max(0, (sh - height) // 2 - 10)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(1180, 760)
        self.root.configure(bg=self.BG)
        try:
            png, ico = ensure_app_icon()
            self.root.iconbitmap(str(ico))
            self._brand_png = Image.open(png).convert("RGBA")
        except Exception:
            self._brand_png = None

    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_sidebar()
        self._build_workspace()
        self._build_footer()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self.root, height=78, corner_radius=0, fg_color=self.HEADER)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(2, weight=1)

        if self._brand_png is not None:
            logo = ctk.CTkImage(light_image=self._brand_png, dark_image=self._brand_png, size=(54, 54))
            self.logo_label = ctk.CTkLabel(header, text="", image=logo)
            self.logo_label.image = logo
            self.logo_label.grid(row=0, column=0, padx=(20, 12), pady=10)
        else:
            mark = ctk.CTkCanvas(header, width=54, height=54, bg=self.HEADER, highlightthickness=0)
            mark.grid(row=0, column=0, padx=(20, 12), pady=10)
            mark.create_oval(5, 5, 49, 49, outline=self.ACCENT, width=3)
            mark.create_text(27, 27, text="PXR", fill="white", font=("Segoe UI", 11, "bold"))

        titlebox = ctk.CTkFrame(header, fg_color="transparent")
        titlebox.grid(row=0, column=1, sticky="w")
        self.title_label = ctk.CTkLabel(titlebox, text="", font=ctk.CTkFont("Segoe UI", 25, "bold"), text_color=self.TEXT)
        self.title_label.pack(anchor="w")
        self.tagline_label = ctk.CTkLabel(titlebox, text="", font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color="#77DFFF")
        self.tagline_label.pack(anchor="w", pady=(1, 0))

        badges = ctk.CTkFrame(header, fg_color="transparent")
        badges.grid(row=0, column=2, sticky="e", padx=(15, 10))
        self.badge_local = self._badge(badges); self.badge_local.pack(side="left", padx=4)
        self.badge_private = self._badge(badges); self.badge_private.pack(side="left", padx=4)
        self.badge_batch = self._badge(badges); self.badge_batch.pack(side="left", padx=4)

        self.lang = ctk.CTkSegmentedButton(header, values=["English", "Polski"], variable=self.language,
                                           command=lambda _v: self._on_language_change(), width=170,
                                           selected_color=self.ACCENT_2, selected_hover_color="#6849EB")
        self.lang.grid(row=0, column=3, padx=(10, 20))

    def _badge(self, parent):
        return ctk.CTkLabel(parent, text="", height=26, corner_radius=13, fg_color="#0D2B3A",
                            text_color="#7DE8FF", font=ctk.CTkFont("Segoe UI", 9, "bold"))

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self.root, width=286, corner_radius=0, fg_color="#0A101B")
        sidebar.grid(row=1, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(4, weight=1)

        top = ctk.CTkFrame(sidebar, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 7))
        top.grid_columnconfigure((0, 1), weight=1)
        self.add_images_btn = ctk.CTkButton(top, text="", command=self._add_images, fg_color=self.ACCENT_2,
                                            hover_color="#6849EB", height=34, font=ctk.CTkFont("Segoe UI", 11, "bold"))
        self.add_images_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.add_folder_btn = ctk.CTkButton(top, text="", command=self._add_folder, fg_color=self.PANEL_2,
                                            hover_color="#1B2B43", height=34)
        self.add_folder_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.drop_zone = ctk.CTkFrame(sidebar, height=86, fg_color="#0E1A2A", border_width=1,
                                      border_color="#27405F", corner_radius=14)
        self.drop_zone.grid(row=1, column=0, sticky="ew", padx=14, pady=(4, 11))
        self.drop_zone.grid_propagate(False)
        self.drop_label = ctk.CTkLabel(self.drop_zone, text="", text_color="#6F87A8",
                                       font=ctk.CTkFont("Segoe UI", 10, "bold"), justify="center")
        self.drop_label.place(relx=.5, rely=.5, anchor="center")
        self._setup_drop_target()

        self.quick_presets_label = ctk.CTkLabel(sidebar, text="", text_color=self.MUTED,
                                                 font=ctk.CTkFont("Segoe UI", 9, "bold"))
        self.quick_presets_label.grid(row=2, column=0, sticky="w", padx=16)

        presets = ctk.CTkFrame(sidebar, fg_color="transparent")
        presets.grid(row=3, column=0, sticky="ew", padx=14, pady=(6, 11))
        presets.grid_columnconfigure((0, 1, 2), weight=1)
        self.preset_product_btn = self._mini_button(presets, lambda: self._apply_preset("product"))
        self.preset_product_btn.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self.preset_portrait_btn = self._mini_button(presets, lambda: self._apply_preset("portrait"))
        self.preset_portrait_btn.grid(row=0, column=1, sticky="ew", padx=3)
        self.preset_social_btn = self._mini_button(presets, lambda: self._apply_preset("social"))
        self.preset_social_btn.grid(row=0, column=2, sticky="ew", padx=(3, 0))

        list_wrap = ctk.CTkFrame(sidebar, fg_color="transparent")
        list_wrap.grid(row=4, column=0, sticky="nsew", padx=8, pady=(0, 8))
        list_wrap.grid_columnconfigure(0, weight=1)
        list_wrap.grid_rowconfigure(1, weight=1)
        row = ctk.CTkFrame(list_wrap, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew", padx=8, pady=(0, 3))
        row.grid_columnconfigure(0, weight=1)
        self.files_label = ctk.CTkLabel(row, text="", font=ctk.CTkFont("Segoe UI", 9, "bold"), text_color=self.MUTED)
        self.files_label.grid(row=0, column=0, sticky="w")
        self.clear_btn = ctk.CTkButton(row, text="", width=54, height=24, command=self._clear_files,
                                       fg_color="transparent", hover_color="#1A2434", border_width=1, border_color="#2D3C53")
        self.clear_btn.grid(row=0, column=1)
        self.file_list = ctk.CTkScrollableFrame(list_wrap, fg_color="transparent", scrollbar_button_color="#223149",
                                                scrollbar_button_hover_color="#31496B")
        self.file_list.grid(row=1, column=0, sticky="nsew")

    def _mini_button(self, parent, command):
        return ctk.CTkButton(parent, text="", command=command, height=30, fg_color="#111D2F",
                             hover_color="#192A42", border_width=1, border_color="#233A58",
                             font=ctk.CTkFont("Segoe UI", 9, "bold"))

    def _build_workspace(self) -> None:
        workspace = ctk.CTkFrame(self.root, corner_radius=0, fg_color=self.BG)
        workspace.grid(row=1, column=1, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_columnconfigure(1, minsize=410)
        workspace.grid_rowconfigure(0, weight=1)

        preview = ctk.CTkFrame(workspace, fg_color=self.BG)
        preview.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=14)
        preview.grid_columnconfigure((0, 1), weight=1)
        preview.grid_rowconfigure(1, weight=1)
        self.before_title = self._preview_title(preview, 0)
        self.after_title = self._preview_title(preview, 1)
        self.before_canvas = ctk.CTkCanvas(preview, bg="#0B1422", highlightthickness=1, highlightbackground="#203651")
        self.before_canvas.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.after_canvas = ctk.CTkCanvas(preview, bg="#0B1422", highlightthickness=1, highlightbackground="#204B64")
        self.after_canvas.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        self.before_canvas.bind("<Configure>", lambda _e: self._refresh_previews())
        self.after_canvas.bind("<Configure>", lambda _e: self._refresh_previews())

        controls = ctk.CTkFrame(workspace, width=410, fg_color="#0B1320", corner_radius=18,
                                border_width=1, border_color="#1B2C43")
        controls.grid(row=0, column=1, sticky="nsew", padx=(8, 14), pady=14)
        controls.grid_propagate(False)
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_rowconfigure(3, weight=1)
        self._build_remove_card(controls)
        self._build_refine_card(controls)
        self._build_export_card(controls)
        self._build_action_card(controls)

    def _preview_title(self, parent, column):
        label = ctk.CTkLabel(parent, text="", font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color="#7891B2")
        label.grid(row=0, column=column, sticky="w", padx=8, pady=(0, 7))
        return label

    def _card(self, parent, row):
        frame = ctk.CTkFrame(parent, fg_color=self.CARD, corner_radius=13, border_width=1, border_color="#1C2C42")
        frame.grid(row=row, column=0, sticky="ew", padx=12, pady=(12 if row == 0 else 5, 0))
        frame.grid_columnconfigure((0, 1), weight=1)
        title = ctk.CTkLabel(frame, text="", text_color="#DCEAFF", font=ctk.CTkFont("Segoe UI", 10, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=13, pady=(9, 5))
        return frame, title

    def _build_remove_card(self, parent) -> None:
        card, self.settings_title = self._card(parent, 0)
        self.model_label = self._small_label(card, 1, 0)
        self.background_label = self._small_label(card, 1, 1)
        self.model_menu = ctk.CTkOptionMenu(card, variable=self.model, values=["Quality", "Fast", "Portrait"],
                                            fg_color="#16263C", button_color=self.ACCENT_2, button_hover_color="#6849EB", height=31)
        self.model_menu.grid(row=2, column=0, sticky="ew", padx=(13, 5), pady=(0, 9))
        self.bg_menu = ctk.CTkOptionMenu(card, values=[], command=self._on_bg_choice, fg_color="#16263C",
                                         button_color="#176C80", button_hover_color="#16839B", height=31)
        self.bg_menu.grid(row=2, column=1, sticky="ew", padx=(5, 13), pady=(0, 9))
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", padx=13, pady=(0, 10))
        actions.grid_columnconfigure((0, 1), weight=1)
        self.color_btn = ctk.CTkButton(actions, text="", command=self._pick_color, height=28,
                                       fg_color="#14243A", hover_color="#1C324E")
        self.color_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.bg_image_btn = ctk.CTkButton(actions, text="", command=self._pick_background_image, height=28,
                                          fg_color="#14243A", hover_color="#1C324E")
        self.bg_image_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _build_refine_card(self, parent) -> None:
        card, self.refine_title = self._card(parent, 1)
        self.edge_label = self._small_label(card, 1, 0)
        self.blur_label = self._small_label(card, 1, 1)
        self.edge_slider = ctk.CTkSlider(card, from_=0, to=5, number_of_steps=50, variable=self.edge_softness,
                                         progress_color=self.ACCENT, button_color="#BDF6FF", height=14)
        self.edge_slider.grid(row=2, column=0, sticky="ew", padx=(13, 8))
        self.blur_slider = ctk.CTkSlider(card, from_=2, to=60, number_of_steps=58, variable=self.background_blur,
                                         progress_color=self.ACCENT_2, button_color="#D6CEFF", height=14)
        self.blur_slider.grid(row=2, column=1, sticky="ew", padx=(8, 13))
        toggles = ctk.CTkFrame(card, fg_color="transparent")
        toggles.grid(row=3, column=0, columnspan=2, sticky="ew", padx=13, pady=(10, 10))
        toggles.grid_columnconfigure((0, 1), weight=1)
        self.shadow_switch = ctk.CTkSwitch(toggles, text="", variable=self.shadow, progress_color=self.ACCENT_2)
        self.shadow_switch.grid(row=0, column=0, sticky="w")
        self.trim_switch = ctk.CTkSwitch(toggles, text="", variable=self.trim, command=self._update_padding_state,
                                         progress_color=self.ACCENT)
        self.trim_switch.grid(row=0, column=1, sticky="w")
        self.padding_entry = ctk.CTkEntry(toggles, width=60, height=26, textvariable=self.padding, justify="center")
        self.padding_entry.grid(row=1, column=1, sticky="e", pady=(7, 0))
        self.padding_label = ctk.CTkLabel(toggles, text="", text_color=self.MUTED, font=ctk.CTkFont("Segoe UI", 9))
        self.padding_label.grid(row=1, column=1, sticky="w", pady=(7, 0))
        self._update_padding_state()

    def _build_export_card(self, parent) -> None:
        card, self.export_title = self._card(parent, 2)
        self.format_label = self._small_label(card, 1, 0)
        self.canvas_label = self._small_label(card, 1, 1)
        self.format_menu = ctk.CTkSegmentedButton(card, values=["PNG", "JPG", "WEBP"], variable=self.export_format,
                                                  selected_color=self.ACCENT_2, selected_hover_color="#6849EB", height=30)
        self.format_menu.grid(row=2, column=0, sticky="ew", padx=(13, 5))
        self.canvas_menu = ctk.CTkOptionMenu(card, variable=self.canvas_preset, values=[], fg_color="#16263C",
                                             button_color="#176C80", button_hover_color="#16839B", height=30)
        self.canvas_menu.grid(row=2, column=1, sticky="ew", padx=(5, 13))
        self.suffix_label = self._small_label(card, 3, 0)
        self.output_label = self._small_label(card, 3, 1)
        self.suffix_entry = ctk.CTkEntry(card, textvariable=self.output_suffix, height=29)
        self.suffix_entry.grid(row=4, column=0, sticky="ew", padx=(13, 5), pady=(0, 8))
        outrow = ctk.CTkFrame(card, fg_color="transparent")
        outrow.grid(row=4, column=1, sticky="ew", padx=(5, 13), pady=(0, 8))
        outrow.grid_columnconfigure(0, weight=1)
        self.output_entry = ctk.CTkEntry(outrow, textvariable=self.output_dir, height=29)
        self.output_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.output_btn = ctk.CTkButton(outrow, text="…", width=34, height=29, command=self._choose_output, fg_color="#17283F")
        self.output_btn.grid(row=0, column=1)
        lower = ctk.CTkFrame(card, fg_color="transparent")
        lower.grid(row=5, column=0, columnspan=2, sticky="ew", padx=13, pady=(0, 10))
        lower.grid_columnconfigure(0, weight=1)
        self.auto_open_switch = ctk.CTkSwitch(lower, text="", variable=self.auto_open_output, progress_color=self.ACCENT)
        self.auto_open_switch.grid(row=0, column=0, sticky="w")
        self.open_folder_btn = ctk.CTkButton(lower, text="", command=self._open_output_folder, height=27,
                                             width=100, fg_color="#14243A")
        self.open_folder_btn.grid(row=0, column=1, sticky="e")

    def _build_action_card(self, parent) -> None:
        card = ctk.CTkFrame(parent, fg_color="transparent")
        card.grid(row=4, column=0, sticky="sew", padx=12, pady=10)
        card.grid_columnconfigure((0, 1), weight=1)
        self.progress_bar = ctk.CTkProgressBar(card, variable=self.progress, progress_color=self.ACCENT,
                                               fg_color="#152238", height=7)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        self.progress_bar.set(0)
        self.status_label = ctk.CTkLabel(card, textvariable=self.status_text, text_color="#99AAC2",
                                         font=ctk.CTkFont("Segoe UI", 9), anchor="w")
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.process_selected_btn = ctk.CTkButton(card, text="", command=self._process_selected, fg_color="#17283F",
                                                  hover_color="#203755", height=42, font=ctk.CTkFont("Segoe UI", 10, "bold"))
        self.process_selected_btn.grid(row=2, column=0, sticky="ew", padx=(0, 4))
        self.process_all_btn = ctk.CTkButton(card, text="", command=self._process_all, fg_color=self.ACCENT_2,
                                             hover_color="#6849EB", height=42, font=ctk.CTkFont("Segoe UI", 10, "bold"))
        self.process_all_btn.grid(row=2, column=1, sticky="ew", padx=(4, 0))

    def _small_label(self, parent, row, column):
        label = ctk.CTkLabel(parent, text="", text_color=self.MUTED, font=ctk.CTkFont("Segoe UI", 9, "bold"))
        label.grid(row=row, column=column, sticky="w", padx=(13 if column == 0 else 5, 5), pady=(0, 4))
        return label

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self.root, height=30, corner_radius=0, fg_color="#060A11")
        footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        footer.grid_propagate(False)
        footer.grid_columnconfigure(1, weight=1)
        self.footer_left = ctk.CTkLabel(footer, text="", font=ctk.CTkFont("Segoe UI", 9), text_color="#526177")
        self.footer_left.grid(row=0, column=0, padx=14, pady=4, sticky="w")
        self.footer_by = ctk.CTkLabel(footer, text="", font=ctk.CTkFont("Segoe UI", 9, "bold"), text_color="#75859C")
        self.footer_by.grid(row=0, column=1, pady=4, sticky="e")
        self.footer_github = ctk.CTkButton(footer, text="", command=lambda: webbrowser.open(self.GITHUB_URL), height=22,
                                          fg_color="transparent", hover_color="#101A28", text_color="#4EDCFF",
                                          font=ctk.CTkFont("Segoe UI", 9, "underline"), width=100)
        self.footer_github.grid(row=0, column=2, padx=(6, 14), pady=4, sticky="e")

    def _apply_language(self) -> None:
        lang = self.language.get()
        self.title_label.configure(text=tr(lang, "app_title")); self.tagline_label.configure(text=tr(lang, "tagline"))
        self.badge_local.configure(text=f"  {tr(lang, 'local_badge')}  ")
        self.badge_private.configure(text=f"  {tr(lang, 'private_badge')}  ")
        self.badge_batch.configure(text=f"  {tr(lang, 'batch_badge')}  ")
        self.add_images_btn.configure(text=tr(lang, "add_images")); self.add_folder_btn.configure(text=tr(lang, "add_folder"))
        self.clear_btn.configure(text=tr(lang, "clear")); self.files_label.configure(text=tr(lang, "files")); self.drop_label.configure(text=tr(lang, "drop_here"))
        self.quick_presets_label.configure(text=tr(lang, "quick_presets")); self.preset_product_btn.configure(text=tr(lang, "preset_product")); self.preset_portrait_btn.configure(text=tr(lang, "preset_portrait")); self.preset_social_btn.configure(text=tr(lang, "preset_social"))
        self.settings_title.configure(text=tr(lang, "settings")); self.refine_title.configure(text=tr(lang, "edge_softness")); self.export_title.configure(text=tr(lang, "export"))
        self.model_label.configure(text=tr(lang, "model")); self.background_label.configure(text=tr(lang, "background")); self.color_btn.configure(text=tr(lang, "pick_color")); self.bg_image_btn.configure(text=tr(lang, "pick_bg"))
        self.edge_label.configure(text=tr(lang, "edge_softness")); self.blur_label.configure(text=tr(lang, "blur_strength")); self.shadow_switch.configure(text=tr(lang, "shadow")); self.trim_switch.configure(text=tr(lang, "trim")); self.padding_label.configure(text=tr(lang, "padding"))
        self.format_label.configure(text=tr(lang, "format")); self.canvas_label.configure(text=tr(lang, "canvas")); self.suffix_label.configure(text=tr(lang, "suffix")); self.output_label.configure(text=tr(lang, "output")); self.auto_open_switch.configure(text=tr(lang, "auto_open")); self.open_folder_btn.configure(text=tr(lang, "open_folder"))
        self.process_selected_btn.configure(text=tr(lang, "process_selected")); self.process_all_btn.configure(text=tr(lang, "process_all")); self.before_title.configure(text=tr(lang, "before")); self.after_title.configure(text=tr(lang, "after"))
        self.footer_left.configure(text=tr(lang, "footer_left", version=__version__)); self.footer_by.configure(text=tr(lang, "footer_by")); self.footer_github.configure(text=tr(lang, "footer_github"))

        current_model = self.model.get()
        key = "model_quality" if current_model in {"Quality", "Jakość"} else "model_fast" if current_model in {"Fast", "Szybki"} else "model_portrait"
        models = [tr(lang, "model_quality"), tr(lang, "model_fast"), tr(lang, "model_portrait")]
        self.model_menu.configure(values=models); self.model.set(tr(lang, key))
        bg_values = [tr(lang, "bg_transparent"), tr(lang, "bg_white"), tr(lang, "bg_color"), tr(lang, "bg_image"), tr(lang, "bg_blur")]
        self.bg_menu.configure(values=bg_values)
        mode_to_key = {"transparent": "bg_transparent", "white": "bg_white", "color": "bg_color", "image": "bg_image", "blur": "bg_blur"}
        self.bg_menu.set(tr(lang, mode_to_key.get(self.background_mode.get(), "bg_transparent")))
        canvas_key = self._canvas_key(self.canvas_preset.get())
        canvas_values = [tr(lang, k) for k in ["canvas_original", "canvas_square", "canvas_portrait", "canvas_story", "canvas_landscape", "canvas_product"]]
        self.canvas_menu.configure(values=canvas_values); self.canvas_preset.set(tr(lang, canvas_key))
        if not self.worker or not self.worker.is_alive(): self.status_text.set(tr(lang, "ready"))
        self._render_file_list(); self._refresh_previews(); self._save_settings()

    @staticmethod
    def _canvas_key(value: str) -> str:
        mapping = {"Original": "canvas_original", "Oryginał": "canvas_original", "Square 1:1": "canvas_square", "Kwadrat 1:1": "canvas_square",
                   "Portrait 4:5": "canvas_portrait", "Portret 4:5": "canvas_portrait", "Story 9:16": "canvas_story", "Relacja 9:16": "canvas_story",
                   "Landscape 16:9": "canvas_landscape", "Poziomo 16:9": "canvas_landscape", "Product 2000": "canvas_product", "Produkt 2000": "canvas_product"}
        return mapping.get(value, "canvas_original")

    def _on_bg_choice(self, value: str) -> None:
        lang = self.language.get()
        lookup = {tr(lang, "bg_transparent"): "transparent", tr(lang, "bg_white"): "white", tr(lang, "bg_color"): "color",
                  tr(lang, "bg_image"): "image", tr(lang, "bg_blur"): "blur"}
        self.background_mode.set(lookup.get(value, "transparent")); self._save_settings()

    def _apply_preset(self, preset: str) -> None:
        lang = self.language.get()
        if preset == "product":
            self.model.set(tr(lang, "model_quality")); self.background_mode.set("white"); self.bg_menu.set(tr(lang, "bg_white")); self.canvas_preset.set(tr(lang, "canvas_product")); self.shadow.set(True); self.edge_softness.set(0.7)
        elif preset == "portrait":
            self.model.set(tr(lang, "model_portrait")); self.background_mode.set("blur"); self.bg_menu.set(tr(lang, "bg_blur")); self.canvas_preset.set(tr(lang, "canvas_portrait")); self.shadow.set(False); self.edge_softness.set(0.4)
        else:
            self.model.set(tr(lang, "model_quality")); self.background_mode.set("transparent"); self.bg_menu.set(tr(lang, "bg_transparent")); self.canvas_preset.set(tr(lang, "canvas_story")); self.shadow.set(False); self.edge_softness.set(0.6)
        self._save_settings()

    def _setup_drop_target(self) -> None:
        if DND_FILES is None: return
        try:
            for widget in (self.drop_zone, self.drop_label):
                widget.drop_target_register(DND_FILES); widget.dnd_bind("<<Drop>>", self._on_drop)
        except Exception: pass

    def _on_drop(self, event) -> None: self._append_paths(self.root.tk.splitlist(event.data))
    def _on_language_change(self) -> None: self._apply_language()

    def _pick_color(self) -> None:
        result = colorchooser.askcolor(color=self.bg_color, title=tr(self.language.get(), "pick_color"))
        if result and result[1]:
            self.bg_color = result[1]; self.background_mode.set("color"); self.bg_menu.set(tr(self.language.get(), "bg_color")); self.color_btn.configure(border_width=2, border_color=self.bg_color); self._save_settings()

    def _pick_background_image(self) -> None:
        path = filedialog.askopenfilename(filetypes=[(tr(self.language.get(), "bg_files"), "*.png *.jpg *.jpeg *.webp *.bmp")])
        if path:
            self.bg_image_path = path; self.background_mode.set("image"); self.bg_menu.set(tr(self.language.get(), "bg_image")); self.bg_image_btn.configure(text=Path(path).name[:19])

    def _update_padding_state(self) -> None: self.padding_entry.configure(state="normal" if self.trim.get() else "disabled")
    def _add_images(self) -> None: self._append_paths(filedialog.askopenfilenames(filetypes=[(tr(self.language.get(), "all_images"), "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff")]))
    def _add_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder: self._append_paths(collect_images(folder))

    def _append_paths(self, paths) -> None:
        existing = {str(p.resolve()).lower() for p in self.files}; changed = False
        for raw in paths:
            p = Path(raw); candidates = collect_images(p) if p.is_dir() else [p]
            for candidate in candidates:
                if candidate.is_file() and is_supported_image(candidate):
                    key = str(candidate.resolve()).lower()
                    if key not in existing: self.files.append(candidate); existing.add(key); changed = True
        if changed:
            self.files.sort(key=lambda p: p.name.lower()); self._render_file_list()
            if self.selected_index is None and self.files: self._select_file(0)

    def _clear_files(self) -> None:
        if self.worker and self.worker.is_alive(): return
        self.files.clear(); self.selected_index = None; self.preview_after = None; self._render_file_list(); self._refresh_previews()

    def _render_file_list(self) -> None:
        for child in self.file_list.winfo_children(): child.destroy()
        for i, path in enumerate(self.files):
            selected = i == self.selected_index
            frame = ctk.CTkFrame(self.file_list, fg_color="#14243A" if selected else "transparent", corner_radius=9)
            frame.pack(fill="x", padx=3, pady=2)
            btn = ctk.CTkButton(frame, text=path.name, anchor="w", command=lambda idx=i: self._select_file(idx),
                                fg_color="transparent", hover_color="#182C46", text_color="#E7EDF7", height=28,
                                font=ctk.CTkFont("Segoe UI", 9))
            btn.pack(fill="x", padx=3, pady=1)

    def _select_file(self, index: int) -> None:
        if 0 <= index < len(self.files): self.selected_index = index; self.preview_after = None; self._render_file_list(); self._refresh_previews()

    def _checker(self, size: tuple[int, int], tile: int = 18) -> Image.Image:
        w, h = size; img = Image.new("RGB", size, "#0D1725"); draw = ImageDraw.Draw(img)
        for y in range(0, h, tile):
            for x in range(0, w, tile):
                if (x // tile + y // tile) % 2: draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill="#142238")
        return img

    def _draw_preview(self, canvas, image: Image.Image | None, empty_text: str = "") -> None:
        canvas.delete("all"); w = max(canvas.winfo_width(), 100); h = max(canvas.winfo_height(), 100)
        if image is None:
            canvas.create_oval(w/2-55, h/2-55, w/2+55, h/2+55, outline="#173A55", width=2)
            canvas.create_oval(w/2-38, h/2-38, w/2+38, h/2+38, outline="#25304B", width=1)
            canvas.create_text(w/2, h/2-5, text="PXR", fill="#55DFFF", font=("Segoe UI", 18, "bold"))
            canvas.create_text(w/2, h/2+80, text=empty_text, fill="#61728C", font=("Segoe UI", 10)); canvas.image_ref = None; return
        display = ImageOps.contain(image.copy(), (max(20, w - 28), max(20, h - 28)), Image.Resampling.LANCZOS)
        if display.mode != "RGBA": display = display.convert("RGBA")
        checker = self._checker((w, h)).convert("RGBA"); x = (w - display.width)//2; y = (h-display.height)//2; checker.alpha_composite(display, (x,y))
        photo = ImageTk.PhotoImage(checker); canvas.create_image(w/2, h/2, image=photo); canvas.image_ref = photo

    def _refresh_previews(self) -> None:
        before = None
        if self.selected_index is not None and 0 <= self.selected_index < len(self.files):
            try:
                with Image.open(self.files[self.selected_index]) as img: before = ImageOps.exif_transpose(img).convert("RGBA")
            except Exception: before = None
        text = tr(self.language.get(), "select_file"); self._draw_preview(self.before_canvas, before, text); self._draw_preview(self.after_canvas, self.preview_after, text)

    def _choose_output(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.output_dir.get())
        if folder: self.output_dir.set(folder); self._save_settings()

    def _open_output_folder(self) -> None:
        folder = Path(self.output_dir.get()).expanduser(); folder.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt": os.startfile(folder)  # type: ignore[attr-defined]
            elif os.name == "posix": subprocess.Popen(["xdg-open", str(folder)])
        except Exception: pass

    def _options(self) -> ProcessOptions:
        try: pad = max(0, min(1000, int(self.padding.get())))
        except Exception: pad = 24
        return ProcessOptions(model_label=self.model.get(), background_mode=self.background_mode.get(), background_color=self.bg_color,
                              background_image=self.bg_image_path, background_blur=float(self.background_blur.get()),
                              edge_softness=float(self.edge_softness.get()), shadow=bool(self.shadow.get()), trim=bool(self.trim.get()),
                              padding=pad, canvas_preset=self.canvas_preset.get(), export_format=self.export_format.get(),
                              output_suffix=self.output_suffix.get())

    def _validate_run(self) -> bool:
        lang = self.language.get()
        if not self.files: messagebox.showwarning(tr(lang, "error"), tr(lang, "no_files")); return False
        if not self.output_dir.get().strip(): messagebox.showwarning(tr(lang, "error"), tr(lang, "no_output")); return False
        if self.background_mode.get() == "image" and not self.bg_image_path: messagebox.showwarning(tr(lang, "error"), tr(lang, "choose_background")); return False
        return True

    def _process_selected(self) -> None:
        if self.selected_index is not None and self._validate_run(): self._start_worker([self.selected_index])
    def _process_all(self) -> None:
        if self._validate_run(): self._start_worker(list(range(len(self.files))))

    def _start_worker(self, indices: list[int]) -> None:
        if self.worker and self.worker.is_alive(): self.cancel_event.set(); return
        self.cancel_event.clear(); self.progress.set(0); self._set_running(True); self._save_settings(); options = self._options(); paths = [(i, self.files[i]) for i in indices]
        self.worker = threading.Thread(target=self._worker_run, args=(paths, options), daemon=True); self.worker.start()

    def _set_running(self, running: bool) -> None:
        lang = self.language.get()
        if running:
            self.status_text.set(tr(lang,"status_model")); self.process_all_btn.configure(text=tr(lang,"cancel"), fg_color="#B33F5C", hover_color="#8E3048"); self.process_selected_btn.configure(state="disabled")
        else:
            self.process_all_btn.configure(text=tr(lang,"process_all"), fg_color=self.ACCENT_2, hover_color="#6849EB"); self.process_selected_btn.configure(state="normal")

    def _worker_run(self, paths: list[tuple[int, Path]], options: ProcessOptions) -> None:
        ok = 0; fail = 0; total = len(paths)
        for pos, (index, path) in enumerate(paths, start=1):
            if self.cancel_event.is_set(): break
            self.events.put(("status", pos, total, path.name))
            try:
                result = self.engine.process(path, options)
                destination = output_path_for(path, self.output_dir.get(), options.export_format, options.output_suffix)
                self.engine.save(result, destination, options.export_format); ok += 1
                self.events.put(("result", index, result.copy(), str(destination)))
            except Exception as exc:
                fail += 1; self.events.put(("item_error", path.name, str(exc)))
            self.events.put(("progress", pos / total if total else 1))
        self.events.put(("complete", ok, fail, self.cancel_event.is_set()))

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait(); kind = event[0]; lang = self.language.get()
                if kind == "status": _, cur, total, name = event; self.status_text.set(tr(lang, "status_image", current=cur, total=total, name=name))
                elif kind == "progress": self.progress.set(float(event[1]))
                elif kind == "result":
                    _, index, image, destination = event
                    if self.selected_index == index: self.preview_after = image; self._refresh_previews()
                    self.status_text.set(f"{tr(lang,'saved')}: {Path(destination).name}")
                elif kind == "item_error": _, name, msg = event; self.status_text.set(f"{tr(lang,'failed')}: {name}"); print(f"BackgroundPXR error [{name}]: {msg}")
                elif kind == "complete":
                    _, ok, fail, cancelled = event; self._set_running(False); self.status_text.set(tr(lang,"ready") if cancelled else tr(lang,"complete",ok=ok,fail=fail))
                    if not cancelled and ok and self.auto_open_output.get(): self._open_output_folder()
        except queue.Empty: pass
        self.root.after(100, self._poll_events)

    def _save_settings(self) -> None:
        self.settings_store.save({"language": self.language.get(), "model": self.model.get(), "background_mode": self.background_mode.get(),
                                  "background_color": self.bg_color, "background_blur": float(self.background_blur.get()),
                                  "export_format": self.export_format.get(), "edge_softness": float(self.edge_softness.get()),
                                  "shadow": bool(self.shadow.get()), "trim": bool(self.trim.get()), "padding": int(self.padding.get()),
                                  "canvas_preset": self.canvas_preset.get(), "output_suffix": self.output_suffix.get(),
                                  "auto_open_output": bool(self.auto_open_output.get()), "output_dir": self.output_dir.get()})

    def _on_close(self) -> None:
        self._save_settings(); self.root.destroy()


def create_root():
    if TkinterDnD is not None: return TkinterDnD.Tk()
    return ctk.CTk()
