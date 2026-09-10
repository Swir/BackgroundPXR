from __future__ import annotations

import os, queue, subprocess, threading, webbrowser
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps, ImageTk

from . import __version__
from .branding import ensure_app_icon
from .editor import BrushSettings, MaskEditor
from .engine import BackgroundEngine, ProcessOptions, ProcessResult, collect_images, is_supported_image, output_path_for
from .i18n import tr
from .settings import SettingsStore
from .ui_icons import make_icon

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class BackgroundPXRApp:
    BG = "#06101E"; HEADER = "#08172A"; CARD = "#0C2038"; LINE = "#173858"
    ACCENT = "#35CFFF"; VIOLET = "#704CFF"; GREEN = "#28E09A"; TEXT = "#F3F7FF"; MUTED = "#8AA3BF"; DANGER = "#D94B68"
    GITHUB_URL = "https://github.com/Swir"

    def __init__(self, root) -> None:
        self.root = root; self.engine = BackgroundEngine(); self.settings_store = SettingsStore(); cfg = self.settings_store.load()
        self.files: list[Path] = []; self.selected_index: int | None = None; self.worker: threading.Thread | None = None
        self.events: queue.Queue = queue.Queue(); self.cancel_event = threading.Event(); self.preview_after: Image.Image | None = None
        self.editor: MaskEditor | None = None; self.current_result: ProcessResult | None = None; self.bg_image_path: str | None = None
        self.bg_color = str(cfg.get("background_color", "#FFFFFF")); self._thumb_refs = []; self._icons = {}
        self.tool = "pan"; self.view_zoom = 1.0; self.pan_x = 0.0; self.pan_y = 0.0; self._pan_anchor = None; self._after_transform = None; self._painting = False

        self.language = ctk.StringVar(value=str(cfg.get("language", "English"))); self.model = ctk.StringVar(value=str(cfg.get("model", "High Quality v2")))
        self.background_mode = ctk.StringVar(value=str(cfg.get("background_mode", "transparent"))); self.export_format = ctk.StringVar(value=str(cfg.get("export_format", "PNG")))
        self.edge_refine = ctk.IntVar(value=int(cfg.get("edge_refine", 0))); self.edge_softness = ctk.DoubleVar(value=float(cfg.get("edge_softness", 0.4))); self.edge_contrast = ctk.IntVar(value=int(cfg.get("edge_contrast", 8)))
        self.alpha_matting = ctk.BooleanVar(value=bool(cfg.get("alpha_matting", True))); self.background_blur = ctk.DoubleVar(value=float(cfg.get("background_blur", 18)))
        self.shadow = ctk.BooleanVar(value=bool(cfg.get("shadow", False))); self.trim = ctk.BooleanVar(value=bool(cfg.get("trim", False))); self.padding = ctk.IntVar(value=int(cfg.get("padding", 24)))
        self.canvas_preset = ctk.StringVar(value=str(cfg.get("canvas_preset", "Original"))); self.output_suffix = ctk.StringVar(value=str(cfg.get("output_suffix", "_pxr")))
        self.output_dir = ctk.StringVar(value=str(cfg.get("output_dir", Path.home() / "Pictures" / "BackgroundPXR"))); self.auto_open_output = ctk.BooleanVar(value=bool(cfg.get("auto_open_output", False)))
        self.brush_size = ctk.IntVar(value=int(cfg.get("brush_size", 48))); self.brush_hardness = ctk.IntVar(value=int(cfg.get("brush_hardness", 75)))
        self.progress = ctk.DoubleVar(value=0); self.status_text = ctk.StringVar(value="")
        self._configure_root(); self._build_ui(); self._apply_language(); self._poll_events(); self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_root(self):
        self.root.title("BackgroundPXR — Power eXtreme Remover"); sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w = min(1760, max(1320, sw - 50)); h = min(980, max(820, sh - 90)); self.root.geometry(f"{w}x{h}+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2-8)}"); self.root.minsize(1240, 800); self.root.configure(bg=self.BG)
        try:
            png, ico = ensure_app_icon(); self.root.iconbitmap(str(ico)); self._brand_png = Image.open(png).convert("RGBA")
        except Exception:
            self._brand_png = None

    def _icon(self, name, color=None, size=20):
        key = (name, color or self.ACCENT, size)
        if key not in self._icons:
            pil = make_icon(name, size, color or self.ACCENT); self._icons[key] = ctk.CTkImage(light_image=pil, dark_image=pil, size=(size, size))
        return self._icons[key]

    def _build_ui(self):
        self.root.grid_rowconfigure(1, weight=1); self.root.grid_columnconfigure(0, weight=1); self._build_header()
        body = ctk.CTkFrame(self.root, fg_color=self.BG, corner_radius=0); body.grid(row=1, column=0, sticky="nsew"); body.grid_rowconfigure(0, weight=1); body.grid_columnconfigure(1, weight=1)
        self._build_sidebar(body); self._build_center(body); self._build_right(body); self._build_footer()

    def _build_header(self):
        f = ctk.CTkFrame(self.root, height=74, corner_radius=0, fg_color=self.HEADER); f.grid(row=0, column=0, sticky="ew"); f.grid_propagate(False); f.grid_columnconfigure(2, weight=1)
        if self._brand_png is not None:
            logo = ctk.CTkImage(light_image=self._brand_png, dark_image=self._brand_png, size=(52, 52)); l = ctk.CTkLabel(f, text="", image=logo); l.image = logo; l.grid(row=0, column=0, padx=(18,10), pady=10)
        title = ctk.CTkFrame(f, fg_color="transparent"); title.grid(row=0, column=1, sticky="w")
        self.title_label = ctk.CTkLabel(title, text="", font=ctk.CTkFont("Segoe UI", 24, "bold"), text_color=self.TEXT); self.title_label.pack(anchor="w")
        self.tagline_label = ctk.CTkLabel(title, text="", font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color="#70DFFF"); self.tagline_label.pack(anchor="w")
        badges = ctk.CTkFrame(f, fg_color="transparent"); badges.grid(row=0, column=2, sticky="e", padx=10)
        self.badge_local = self._badge(badges, self.GREEN); self.badge_local.pack(side="left", padx=4); self.badge_private = self._badge(badges, "#B7C7DD"); self.badge_private.pack(side="left", padx=4); self.badge_batch = self._badge(badges, self.ACCENT); self.badge_batch.pack(side="left", padx=4)
        self.lang = ctk.CTkSegmentedButton(f, values=["English", "Polski"], variable=self.language, command=lambda _: self._apply_language(), width=160, height=34, selected_color=self.VIOLET, selected_hover_color="#5D3EE0"); self.lang.grid(row=0, column=3, padx=(8,18))

    def _badge(self, parent, color):
        return ctk.CTkLabel(parent, text="", height=27, corner_radius=9, fg_color="#0A2635", text_color=color, font=ctk.CTkFont("Segoe UI", 9, "bold"))

    def _build_sidebar(self, parent):
        side = ctk.CTkFrame(parent, width=270, corner_radius=14, fg_color="#08182B", border_width=1, border_color=self.LINE); side.grid(row=0, column=0, sticky="nsew", padx=(14,8), pady=12); side.grid_propagate(False); side.grid_rowconfigure(6, weight=1)
        self.files_project = ctk.CTkLabel(side, text="", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color="#8DCFFF"); self.files_project.grid(row=0, column=0, sticky="w", padx=14, pady=(14,9))
        self.add_images_btn = ctk.CTkButton(side, text="", image=self._icon("plus", "#FFFFFF", 18), command=self._add_images, height=42, fg_color=self.VIOLET, hover_color="#5C3EE0", font=ctk.CTkFont("Segoe UI", 11, "bold")); self.add_images_btn.grid(row=1, column=0, sticky="ew", padx=14, pady=(0,7))
        self.add_folder_btn = ctk.CTkButton(side, text="", image=self._icon("folder", "#A9D8FF", 18), command=self._add_folder, height=39, fg_color="#0D2742", hover_color="#123555", border_width=1, border_color="#28557D"); self.add_folder_btn.grid(row=2, column=0, sticky="ew", padx=14)
        self.drop_zone = ctk.CTkFrame(side, height=102, corner_radius=12, fg_color="#0A213A", border_width=1, border_color="#2A5A84"); self.drop_zone.grid(row=3, column=0, sticky="ew", padx=14, pady=12); self.drop_zone.grid_propagate(False)
        self.drop_icon = ctk.CTkLabel(self.drop_zone, text="", image=self._icon("image", "#5CB9FF", 28)); self.drop_icon.pack(pady=(15,4)); self.drop_label = ctk.CTkLabel(self.drop_zone, text="", text_color="#A6BED5", font=ctk.CTkFont("Segoe UI", 9), justify="center"); self.drop_label.pack(); self.drop_zone.bind("<Button-1>", lambda _: self._add_images()); self.drop_label.bind("<Button-1>", lambda _: self._add_images()); self._setup_drop_target()
        self.quick_label = ctk.CTkLabel(side, text="", font=ctk.CTkFont("Segoe UI", 9, "bold"), text_color=self.MUTED); self.quick_label.grid(row=4, column=0, sticky="w", padx=14, pady=(0,6))
        p = ctk.CTkFrame(side, fg_color="transparent"); p.grid(row=5, column=0, sticky="ew", padx=12); p.grid_columnconfigure((0,1), weight=1); self.preset_buttons = []
        for i, (kind, icon) in enumerate([("product","image"),("portrait","pan"),("object","fit"),("transparent","magic")]):
            b = ctk.CTkButton(p, text="", image=self._icon(icon, "#69CFFF", 19), compound="top", command=lambda k=kind: self._apply_preset(k), height=58, fg_color="#0B2139", hover_color="#10304F", border_width=1, border_color="#244C71", font=ctk.CTkFont("Segoe UI", 9)); b.grid(row=i//2, column=i%2, sticky="ew", padx=3, pady=3); self.preset_buttons.append(b)
        listwrap = ctk.CTkFrame(side, fg_color="transparent"); listwrap.grid(row=6, column=0, sticky="nsew", padx=8, pady=(9,8)); listwrap.grid_rowconfigure(1, weight=1); listwrap.grid_columnconfigure(0, weight=1)
        hdr = ctk.CTkFrame(listwrap, fg_color="transparent"); hdr.grid(row=0, column=0, sticky="ew", padx=6); hdr.grid_columnconfigure(0, weight=1)
        self.project_files = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont("Segoe UI", 9, "bold"), text_color=self.MUTED); self.project_files.grid(row=0, column=0, sticky="w")
        self.clear_btn = ctk.CTkButton(hdr, text="", width=58, height=24, command=self._clear_files, fg_color="transparent", hover_color="#142B44", text_color="#6EBFFF"); self.clear_btn.grid(row=0, column=1)
        self.file_list = ctk.CTkScrollableFrame(listwrap, fg_color="transparent", scrollbar_button_color="#1B4264"); self.file_list.grid(row=1, column=0, sticky="nsew", pady=(4,0))

    def _build_center(self, parent):
        center = ctk.CTkFrame(parent, fg_color="transparent"); center.grid(row=0, column=1, sticky="nsew", padx=6, pady=12); center.grid_rowconfigure(1, weight=1); center.grid_columnconfigure(0, weight=1)
        bar = ctk.CTkFrame(center, height=58, corner_radius=12, fg_color="#0A1D33", border_width=1, border_color=self.LINE); bar.grid(row=0, column=0, sticky="ew", pady=(0,8)); bar.grid_propagate(False)
        tools = [("pan","pan",self._tool_pan),("zoom_out","zoom_out",lambda:self._zoom_by(.82)),("zoom_in","zoom_in",lambda:self._zoom_by(1.22)),("fit","fit",self._fit_view),("restore","brush",lambda:self._set_tool("restore")),("erase","eraser",lambda:self._set_tool("erase")),("undo","undo",self._undo),("redo","redo",self._redo)]
        self.tool_buttons = {}
        for i, (key, icon, cmd) in enumerate(tools):
            b = ctk.CTkButton(bar, text="", image=self._icon(icon, "#A9D7FF", 18), compound="top", command=cmd, width=76, height=48, fg_color="transparent", hover_color="#122F50", font=ctk.CTkFont("Segoe UI", 8), text_color="#C6D6E8"); b.grid(row=0, column=i, padx=(8 if i==0 else 1,1), pady=5); self.tool_buttons[key] = b
        self.zoom_label = ctk.CTkLabel(bar, text="100%", width=58, font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color="#DDEAFF", fg_color="#0D2845", corner_radius=8); self.zoom_label.grid(row=0, column=len(tools), padx=(8,10))
        area = ctk.CTkFrame(center, fg_color="transparent"); area.grid(row=1, column=0, sticky="nsew"); area.grid_columnconfigure((0,1), weight=1); area.grid_rowconfigure(0, weight=1)
        self.before_card, self.before_canvas, self.before_badge = self._preview_card(area, 0, False); self.after_card, self.after_canvas, self.after_badge = self._preview_card(area, 1, True)
        self.before_canvas.bind("<MouseWheel>", self._on_wheel); self.after_canvas.bind("<MouseWheel>", self._on_wheel); self.after_canvas.bind("<ButtonPress-1>", self._on_after_press); self.after_canvas.bind("<B1-Motion>", self._on_after_drag); self.after_canvas.bind("<ButtonRelease-1>", self._on_after_release); self.after_canvas.bind("<Motion>", self._on_after_motion)
        strip = ctk.CTkFrame(center, height=82, corner_radius=12, fg_color="#091C31", border_width=1, border_color=self.LINE); strip.grid(row=2, column=0, sticky="ew", pady=(8,0)); strip.grid_propagate(False); strip.grid_columnconfigure(1, weight=1)
        self.project_count = ctk.CTkLabel(strip, text="", font=ctk.CTkFont("Segoe UI", 9), text_color="#9EB3C9"); self.project_count.grid(row=0, column=0, padx=12, pady=(8,0), sticky="w")
        self.fit_all_btn = ctk.CTkButton(strip, text="", image=self._icon("fit", "#B7DFFF", 15), command=self._fit_view, width=82, height=26, fg_color="transparent", hover_color="#13304D"); self.fit_all_btn.grid(row=0, column=2, padx=10, pady=(6,0), sticky="e")
        self.filmstrip = ctk.CTkFrame(strip, fg_color="transparent"); self.filmstrip.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

    def _preview_card(self, parent, column, after):
        card = ctk.CTkFrame(parent, corner_radius=13, fg_color="#091A2D", border_width=1, border_color="#27577E" if after else "#23425F"); card.grid(row=0, column=column, sticky="nsew", padx=(0,5) if column==0 else (5,0)); card.grid_rowconfigure(0, weight=1); card.grid_columnconfigure(0, weight=1)
        canvas = ctk.CTkCanvas(card, bg="#0A1828", highlightthickness=0); canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        badge = ctk.CTkLabel(card, text="", height=28, corner_radius=8, fg_color=self.VIOLET if after else "#20354B", text_color="#FFFFFF", font=ctk.CTkFont("Segoe UI", 10, "bold")); badge.place(x=14, y=14)
        return card, canvas, badge

    def _build_right(self, parent):
        right = ctk.CTkFrame(parent, width=352, corner_radius=14, fg_color="#08182B", border_width=1, border_color=self.LINE); right.grid(row=0, column=2, sticky="nsew", padx=(8,14), pady=12); right.grid_propagate(False); right.grid_columnconfigure(0, weight=1)
        self._build_ai_card(right); self._build_refine_card(right); self._build_manual_card(right); self._build_export_card(right)

    def _card(self, parent, row):
        f = ctk.CTkFrame(parent, corner_radius=12, fg_color=self.CARD, border_width=1, border_color="#1A4062"); f.grid(row=row, column=0, sticky="ew", padx=10, pady=(10 if row==0 else 5,0)); f.grid_columnconfigure(0, weight=1); return f

    def _card_title(self, f, icon, name_attr, sub_attr=None):
        h = ctk.CTkFrame(f, fg_color="transparent"); h.grid(row=0, column=0, sticky="ew", padx=10, pady=(8,3)); h.grid_columnconfigure(1, weight=1)
        c = ctk.CTkLabel(h, text="", image=self._icon(icon, self.ACCENT, 20)); c.grid(row=0, column=0, rowspan=2, padx=(0,7))
        setattr(self, name_attr, ctk.CTkLabel(h, text="", font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color=self.TEXT)); getattr(self, name_attr).grid(row=0, column=1, sticky="w")
        if sub_attr:
            setattr(self, sub_attr, ctk.CTkLabel(h, text="", font=ctk.CTkFont("Segoe UI", 8), text_color=self.MUTED)); getattr(self, sub_attr).grid(row=1, column=1, sticky="w")

    def _build_ai_card(self, parent):
        f = self._card(parent, 0); self._card_title(f, "magic", "ai_title", "ai_sub")
        grid = ctk.CTkFrame(f, fg_color="transparent"); grid.grid(row=1, column=0, sticky="ew", padx=10); grid.grid_columnconfigure((0,1), weight=1)
        self.model_label = ctk.CTkLabel(grid, text="", text_color=self.MUTED, font=ctk.CTkFont("Segoe UI", 8)); self.model_label.grid(row=0, column=0, sticky="w")
        self.output_label = ctk.CTkLabel(grid, text="", text_color=self.MUTED, font=ctk.CTkFont("Segoe UI", 8)); self.output_label.grid(row=0, column=1, sticky="w", padx=(6,0))
        self.model_menu = ctk.CTkOptionMenu(grid, variable=self.model, values=[], height=30, fg_color="#102A49", button_color=self.VIOLET, button_hover_color="#5D3EE0"); self.model_menu.grid(row=1, column=0, sticky="ew", padx=(0,4))
        self.bg_menu = ctk.CTkOptionMenu(grid, values=[], command=self._on_bg_choice, height=30, fg_color="#102A49", button_color="#137A92", button_hover_color="#1695B1"); self.bg_menu.grid(row=1, column=1, sticky="ew", padx=(4,0))
        opt = ctk.CTkFrame(f, fg_color="transparent"); opt.grid(row=2, column=0, sticky="ew", padx=10, pady=(6,0)); opt.grid_columnconfigure((0,1), weight=1)
        self.color_btn = ctk.CTkButton(opt, text="", command=self._pick_color, height=26, fg_color="#0F2946", hover_color="#143B61"); self.color_btn.grid(row=0, column=0, sticky="ew", padx=(0,3))
        self.bg_image_btn = ctk.CTkButton(opt, text="", command=self._pick_background_image, height=26, fg_color="#0F2946", hover_color="#143B61"); self.bg_image_btn.grid(row=0, column=1, sticky="ew", padx=(3,0))
        self.remove_btn = ctk.CTkButton(f, text="", image=self._icon("magic", "#FFFFFF", 18), command=self._process_selected, height=37, fg_color=self.VIOLET, hover_color="#5D3EE0", font=ctk.CTkFont("Segoe UI", 10, "bold")); self.remove_btn.grid(row=3, column=0, sticky="ew", padx=10, pady=(7,9))

    def _build_refine_card(self, parent):
        f = self._card(parent, 1); self._card_title(f, "fit", "refine_title")
        labels = ctk.CTkFrame(f, fg_color="transparent"); labels.grid(row=1, column=0, sticky="ew", padx=10); labels.grid_columnconfigure((0,1,2), weight=1)
        self.edge_label = ctk.CTkLabel(labels, text="", font=ctk.CTkFont("Segoe UI", 8), text_color=self.MUTED); self.edge_label.grid(row=0, column=0, sticky="w")
        self.feather_label = ctk.CTkLabel(labels, text="", font=ctk.CTkFont("Segoe UI", 8), text_color=self.MUTED); self.feather_label.grid(row=0, column=1)
        self.contrast_label = ctk.CTkLabel(labels, text="", font=ctk.CTkFont("Segoe UI", 8), text_color=self.MUTED); self.contrast_label.grid(row=0, column=2, sticky="e")
        sliders = ctk.CTkFrame(f, fg_color="transparent"); sliders.grid(row=2, column=0, sticky="ew", padx=8); sliders.grid_columnconfigure((0,1,2), weight=1)
        self.edge_slider = ctk.CTkSlider(sliders, from_=-5, to=5, number_of_steps=10, variable=self.edge_refine, progress_color=self.ACCENT, height=13); self.edge_slider.grid(row=0, column=0, sticky="ew", padx=3)
        self.feather_slider = ctk.CTkSlider(sliders, from_=0, to=3, number_of_steps=30, variable=self.edge_softness, progress_color=self.ACCENT, height=13); self.feather_slider.grid(row=0, column=1, sticky="ew", padx=3)
        self.contrast_slider = ctk.CTkSlider(sliders, from_=0, to=50, number_of_steps=50, variable=self.edge_contrast, progress_color=self.VIOLET, height=13); self.contrast_slider.grid(row=0, column=2, sticky="ew", padx=3)
        toggles = ctk.CTkFrame(f, fg_color="transparent"); toggles.grid(row=3, column=0, sticky="ew", padx=10, pady=(5,8)); toggles.grid_columnconfigure((0,1), weight=1)
        self.matting_switch = ctk.CTkSwitch(toggles, text="", variable=self.alpha_matting, progress_color=self.VIOLET, font=ctk.CTkFont("Segoe UI", 8)); self.matting_switch.grid(row=0, column=0, columnspan=2, sticky="w")
        self.shadow_switch = ctk.CTkSwitch(toggles, text="", variable=self.shadow, command=self._recompose_refresh, progress_color=self.VIOLET, font=ctk.CTkFont("Segoe UI", 8)); self.shadow_switch.grid(row=1, column=0, sticky="w", pady=(5,0))
        self.trim_switch = ctk.CTkSwitch(toggles, text="", variable=self.trim, command=self._recompose_refresh, progress_color=self.ACCENT, font=ctk.CTkFont("Segoe UI", 8)); self.trim_switch.grid(row=1, column=1, sticky="w", pady=(5,0))

    def _build_manual_card(self, parent):
        f = self._card(parent, 2); self._card_title(f, "brush", "manual_title", "manual_sub")
        buttons = ctk.CTkFrame(f, fg_color="transparent"); buttons.grid(row=1, column=0, sticky="ew", padx=8); buttons.grid_columnconfigure((0,1,2), weight=1)
        self.restore_btn = ctk.CTkButton(buttons, text="", image=self._icon("brush", "#FFFFFF", 16), command=lambda:self._set_tool("restore"), height=34, fg_color=self.VIOLET, hover_color="#5D3EE0", font=ctk.CTkFont("Segoe UI", 8)); self.restore_btn.grid(row=0, column=0, sticky="ew", padx=2)
        self.erase_btn = ctk.CTkButton(buttons, text="", image=self._icon("eraser", "#BFEAFF", 16), command=lambda:self._set_tool("erase"), height=34, fg_color="#102B49", hover_color="#173C61", font=ctk.CTkFont("Segoe UI", 8)); self.erase_btn.grid(row=0, column=1, sticky="ew", padx=2)
        self.smart_btn = ctk.CTkButton(buttons, text="", image=self._icon("magic", "#BFEAFF", 16), command=self._smart_cleanup, height=34, fg_color="#102B49", hover_color="#173C61", font=ctk.CTkFont("Segoe UI", 8)); self.smart_btn.grid(row=0, column=2, sticky="ew", padx=2)
        buttons2 = ctk.CTkFrame(f, fg_color="transparent"); buttons2.grid(row=2, column=0, sticky="ew", padx=8, pady=(5,0)); buttons2.grid_columnconfigure((0,1), weight=1)
        self.islands_btn = ctk.CTkButton(buttons2, text="", command=self._remove_islands, height=27, fg_color="#0F2946", hover_color="#163A5D", font=ctk.CTkFont("Segoe UI", 8)); self.islands_btn.grid(row=0, column=0, sticky="ew", padx=2)
        self.reset_btn = ctk.CTkButton(buttons2, text="", command=self._reset_mask, height=27, fg_color="#0F2946", hover_color="#163A5D", font=ctk.CTkFont("Segoe UI", 8)); self.reset_btn.grid(row=0, column=1, sticky="ew", padx=2)
        self.brush_size_label = ctk.CTkLabel(f, text="", font=ctk.CTkFont("Segoe UI", 8), text_color=self.MUTED); self.brush_size_label.grid(row=3, column=0, sticky="w", padx=10, pady=(5,0))
        self.brush_size_slider = ctk.CTkSlider(f, from_=8, to=220, number_of_steps=106, variable=self.brush_size, progress_color=self.ACCENT, height=13); self.brush_size_slider.grid(row=4, column=0, sticky="ew", padx=10)
        self.brush_hard_label = ctk.CTkLabel(f, text="", font=ctk.CTkFont("Segoe UI", 8), text_color=self.MUTED); self.brush_hard_label.grid(row=5, column=0, sticky="w", padx=10, pady=(3,0))
        self.brush_hard_slider = ctk.CTkSlider(f, from_=0, to=100, number_of_steps=20, variable=self.brush_hardness, progress_color=self.VIOLET, height=13); self.brush_hard_slider.grid(row=6, column=0, sticky="ew", padx=10, pady=(0,7))

    def _build_export_card(self, parent):
        f = self._card(parent, 3); self._card_title(f, "export", "export_title", "export_sub")
        row = ctk.CTkFrame(f, fg_color="transparent"); row.grid(row=1, column=0, sticky="ew", padx=10); row.grid_columnconfigure((0,1), weight=1)
        self.format_menu = ctk.CTkSegmentedButton(row, values=["PNG","JPG","WEBP"], variable=self.export_format, height=28, selected_color=self.VIOLET, selected_hover_color="#5D3EE0"); self.format_menu.grid(row=0, column=0, sticky="ew", padx=(0,4))
        self.canvas_menu = ctk.CTkOptionMenu(row, variable=self.canvas_preset, values=[], command=lambda _v:self._recompose_refresh(), height=28, fg_color="#102A49", button_color="#137A92"); self.canvas_menu.grid(row=0, column=1, sticky="ew", padx=(4,0))
        row2 = ctk.CTkFrame(f, fg_color="transparent"); row2.grid(row=2, column=0, sticky="ew", padx=10, pady=(5,0)); row2.grid_columnconfigure(1, weight=1)
        self.suffix_entry = ctk.CTkEntry(row2, textvariable=self.output_suffix, width=76, height=27); self.suffix_entry.grid(row=0, column=0, padx=(0,5))
        self.output_entry = ctk.CTkEntry(row2, textvariable=self.output_dir, height=27); self.output_entry.grid(row=0, column=1, sticky="ew", padx=(0,4)); self.output_btn = ctk.CTkButton(row2, text="…", width=30, height=27, command=self._choose_output, fg_color="#12304E"); self.output_btn.grid(row=0, column=2)
        row3 = ctk.CTkFrame(f, fg_color="transparent"); row3.grid(row=3, column=0, sticky="ew", padx=10, pady=(5,0)); row3.grid_columnconfigure(0, weight=1)
        self.auto_open_switch = ctk.CTkSwitch(row3, text="", variable=self.auto_open_output, progress_color=self.ACCENT, font=ctk.CTkFont("Segoe UI", 8)); self.auto_open_switch.grid(row=0, column=0, sticky="w")
        self.open_folder_btn = ctk.CTkButton(row3, text="", command=self._open_output_folder, width=84, height=25, fg_color="#102B49", font=ctk.CTkFont("Segoe UI", 8)); self.open_folder_btn.grid(row=0, column=1)
        self.progress_bar = ctk.CTkProgressBar(f, variable=self.progress, height=6, progress_color=self.ACCENT, fg_color="#10243C"); self.progress_bar.grid(row=4, column=0, sticky="ew", padx=10, pady=(6,2)); self.progress_bar.set(0)
        self.status_label = ctk.CTkLabel(f, textvariable=self.status_text, text_color="#9BB2C9", font=ctk.CTkFont("Segoe UI", 8), anchor="w"); self.status_label.grid(row=5, column=0, sticky="ew", padx=10)
        actions = ctk.CTkFrame(f, fg_color="transparent"); actions.grid(row=6, column=0, sticky="ew", padx=10, pady=(4,9)); actions.grid_columnconfigure((0,1), weight=1)
        self.export_btn = ctk.CTkButton(actions, text="", image=self._icon("export", "#FFFFFF", 17), command=self._export_current, height=34, fg_color=self.VIOLET, hover_color="#5D3EE0", font=ctk.CTkFont("Segoe UI", 9, "bold")); self.export_btn.grid(row=0, column=0, sticky="ew", padx=(0,3))
        self.process_all_btn = ctk.CTkButton(actions, text="", command=self._process_all, height=34, fg_color="#12304E", hover_color="#19446D", font=ctk.CTkFont("Segoe UI", 9, "bold")); self.process_all_btn.grid(row=0, column=1, sticky="ew", padx=(3,0))

    def _build_footer(self):
        f = ctk.CTkFrame(self.root, height=28, corner_radius=0, fg_color="#050D18"); f.grid(row=2, column=0, sticky="ew"); f.grid_propagate(False); f.grid_columnconfigure(1, weight=1)
        self.footer_left = ctk.CTkLabel(f, text="", font=ctk.CTkFont("Segoe UI", 8), text_color="#627991"); self.footer_left.grid(row=0, column=0, padx=14, pady=3)
        self.footer_by = ctk.CTkLabel(f, text="", font=ctk.CTkFont("Segoe UI", 8, "bold"), text_color="#91A5B9"); self.footer_by.grid(row=0, column=1, sticky="e")
        self.footer_github = ctk.CTkButton(f, text="", command=lambda:webbrowser.open(self.GITHUB_URL), height=20, width=95, fg_color="transparent", hover_color="#10243A", text_color=self.ACCENT, font=ctk.CTkFont(family="Segoe UI", size=8, underline=True)); self.footer_github.grid(row=0, column=2, padx=(5,12))

    def _apply_language(self):
        L = self.language.get(); self.title_label.configure(text=tr(L,"app_title")); self.tagline_label.configure(text=tr(L,"tagline")); self.badge_local.configure(text=f"  {tr(L,'local_badge')}  "); self.badge_private.configure(text=f"  {tr(L,'private_badge')}  "); self.badge_batch.configure(text=f"  {tr(L,'batch_badge')}  ")
        self.files_project.configure(text=tr(L,"files_project")); self.add_images_btn.configure(text=tr(L,"add_images")); self.add_folder_btn.configure(text=tr(L,"add_folder")); self.drop_label.configure(text=tr(L,"drop_here")); self.quick_label.configure(text=tr(L,"quick_presets")); self.project_files.configure(text=tr(L,"project_files")); self.clear_btn.configure(text=tr(L,"clear_all"))
        for b,k in zip(self.preset_buttons,["preset_product","preset_portrait","preset_object","preset_transparent"]): b.configure(text=tr(L,k))
        for k,b in self.tool_buttons.items(): b.configure(text=tr(L,k))
        self.before_badge.configure(text=tr(L,"before")); self.after_badge.configure(text=tr(L,"after")); self.fit_all_btn.configure(text=tr(L,"fit_all")); self.project_count.configure(text=tr(L,"project_count",count=len(self.files)))
        self.ai_title.configure(text=tr(L,"ai_removal")); self.ai_sub.configure(text=tr(L,"ai_sub")); self.model_label.configure(text=tr(L,"model")); self.output_label.configure(text=tr(L,"output")); self.color_btn.configure(text=tr(L,"color")); self.bg_image_btn.configure(text=tr(L,"background_image")); self.remove_btn.configure(text=tr(L,"remove_bg"))
        cur = self._model_key(self.model.get()); vals = [tr(L,k) for k in ["model_hq","model_quality","model_fast","model_portrait"]]; self.model_menu.configure(values=vals); self.model.set(tr(L,cur))
        bgvals = [tr(L,k) for k in ["bg_transparent","bg_white","bg_color","bg_image","bg_blur"]]; self.bg_menu.configure(values=bgvals); self.bg_menu.set(tr(L,{"transparent":"bg_transparent","white":"bg_white","color":"bg_color","image":"bg_image","blur":"bg_blur"}.get(self.background_mode.get(),"bg_transparent")))
        self.refine_title.configure(text=tr(L,"refine_edges")); self.edge_label.configure(text=tr(L,"edge_refinement")); self.feather_label.configure(text=tr(L,"feather")); self.contrast_label.configure(text=tr(L,"contrast")); self.matting_switch.configure(text=tr(L,"alpha_matting")); self.shadow_switch.configure(text=tr(L,"soft_shadow")); self.trim_switch.configure(text=tr(L,"auto_crop"))
        self.manual_title.configure(text=tr(L,"manual_cleanup")); self.manual_sub.configure(text=tr(L,"manual_sub")); self.restore_btn.configure(text=tr(L,"restore")); self.erase_btn.configure(text=tr(L,"erase")); self.smart_btn.configure(text=tr(L,"smart_cleanup")); self.islands_btn.configure(text=tr(L,"remove_islands")); self.reset_btn.configure(text=tr(L,"reset_mask")); self.brush_size_label.configure(text=tr(L,"brush_size")); self.brush_hard_label.configure(text=tr(L,"brush_hardness"))
        self.export_title.configure(text=tr(L,"export")); self.export_sub.configure(text=tr(L,"export_sub")); canvas_key = self._canvas_key(self.canvas_preset.get()); cvals = [tr(L,k) for k in ["canvas_original","canvas_square","canvas_portrait","canvas_story","canvas_landscape","canvas_product"]]; self.canvas_menu.configure(values=cvals); self.canvas_preset.set(tr(L,canvas_key)); self.auto_open_switch.configure(text=tr(L,"auto_open")); self.open_folder_btn.configure(text=tr(L,"open_folder")); self.export_btn.configure(text=tr(L,"export_image")); self.process_all_btn.configure(text=tr(L,"process_all"))
        self.footer_left.configure(text=tr(L,"footer_left",version=__version__)); self.footer_by.configure(text=tr(L,"footer_by")); self.footer_github.configure(text=tr(L,"footer_github")); self.status_text.set(tr(L,"ready")); self._render_file_list(); self._render_filmstrip(); self._refresh_previews(); self._save_settings()

    @staticmethod
    def _model_key(v):
        if v in {"High Quality v2","Najwyższa jakość v2"}: return "model_hq"
        if v in {"Quality","Jakość"}: return "model_quality"
        if v in {"Fast","Szybki"}: return "model_fast"
        return "model_portrait"

    @staticmethod
    def _canvas_key(v):
        m={"Original":"canvas_original","Oryginał":"canvas_original","Original Size":"canvas_original","Oryginalny rozmiar":"canvas_original","Square 1:1":"canvas_square","Kwadrat 1:1":"canvas_square","Portrait 4:5":"canvas_portrait","Portret 4:5":"canvas_portrait","Story 9:16":"canvas_story","Relacja 9:16":"canvas_story","Landscape 16:9":"canvas_landscape","Poziomo 16:9":"canvas_landscape","Product 2000":"canvas_product","Produkt 2000":"canvas_product","Product 2000×2000":"canvas_product","Produkt 2000×2000":"canvas_product"}; return m.get(v,"canvas_original")

    def _on_bg_choice(self,v):
        L=self.language.get(); lookup={tr(L,"bg_transparent"):"transparent",tr(L,"bg_white"):"white",tr(L,"bg_color"):"color",tr(L,"bg_image"):"image",tr(L,"bg_blur"):"blur"}; self.background_mode.set(lookup.get(v,"transparent")); self._save_settings(); self._recompose_refresh()

    def _apply_preset(self,k):
        L=self.language.get()
        if k=="product": self.model.set(tr(L,"model_hq")); self.background_mode.set("white"); self.canvas_preset.set(tr(L,"canvas_product")); self.shadow.set(True)
        elif k=="portrait": self.model.set(tr(L,"model_portrait")); self.background_mode.set("blur"); self.canvas_preset.set(tr(L,"canvas_portrait")); self.shadow.set(False)
        elif k=="object": self.model.set(tr(L,"model_hq")); self.background_mode.set("transparent"); self.canvas_preset.set(tr(L,"canvas_original")); self.edge_contrast.set(12)
        else: self.background_mode.set("transparent"); self.canvas_preset.set(tr(L,"canvas_original")); self.shadow.set(False)
        self._apply_language()

    def _tool_pan(self): self._set_tool("pan")
    def _set_tool(self,tool):
        if tool in {"restore","erase"} and not self.editor: self.status_text.set(tr(self.language.get(),"run_ai_first")); return
        self.tool=tool
        for key,b in self.tool_buttons.items(): b.configure(fg_color=self.VIOLET if key==tool else "transparent")
        self.restore_btn.configure(fg_color=self.VIOLET if tool=="restore" else "#102B49"); self.erase_btn.configure(fg_color=self.VIOLET if tool=="erase" else "#102B49")
        if tool in {"restore","erase"}: self.status_text.set(tr(self.language.get(),"mask_edit_mode"))
        self._refresh_previews()
    def _zoom_by(self,factor): self.view_zoom=max(.25,min(8.0,self.view_zoom*factor)); self.zoom_label.configure(text=f"{round(self.view_zoom*100)}%"); self._refresh_previews()
    def _fit_view(self): self.view_zoom=1.0; self.pan_x=self.pan_y=0.0; self.zoom_label.configure(text="100%"); self._refresh_previews()
    def _on_wheel(self,e): self._zoom_by(1.12 if e.delta>0 else .89)

    def _on_after_press(self,e):
        if self.tool=="pan": self._pan_anchor=(e.x,e.y,self.pan_x,self.pan_y); return
        if self.tool in {"restore","erase"} and self.editor: self.editor.begin_stroke(); self._painting=True; self._paint_at(e.x,e.y)
    def _on_after_drag(self,e):
        if self.tool=="pan" and self._pan_anchor:
            x,y,px,py=self._pan_anchor; self.pan_x=px+(e.x-x); self.pan_y=py+(e.y-y); self._refresh_previews()
        elif self._painting: self._paint_at(e.x,e.y)
    def _on_after_release(self,e):
        if self._painting and self.editor: self.editor.end_stroke(); self._painting=False; self._recompose(); self._refresh_previews()
        self._pan_anchor=None
    def _on_after_motion(self,e):
        if self.tool not in {"restore","erase"}: return
        self._refresh_after_only(); r=max(4,self.brush_size.get()/2*(self._after_transform[2] if self._after_transform else 1)); self.after_canvas.create_oval(e.x-r,e.y-r,e.x+r,e.y+r,outline="#FFFFFF",width=1,dash=(3,2),tags="cursor")
    def _paint_at(self,cx,cy):
        if not self.editor or not self._after_transform: return
        ox,oy,scale=self._after_transform; x=(cx-ox)/scale; y=(cy-oy)/scale; self.editor.paint(x,y,self.tool,BrushSettings(self.brush_size.get(),self.brush_hardness.get())); self._refresh_after_only()
    def _undo(self):
        if self.editor and self.editor.undo(): self._recompose(); self._refresh_previews()
    def _redo(self):
        if self.editor and self.editor.redo(): self._recompose(); self._refresh_previews()
    def _smart_cleanup(self):
        if not self.editor: self.status_text.set(tr(self.language.get(),"run_ai_first")); return
        self.editor.smart_cleanup(40); self._recompose(); self.status_text.set(tr(self.language.get(),"cleanup_done")); self._refresh_previews()
    def _remove_islands(self):
        if not self.editor: self.status_text.set(tr(self.language.get(),"run_ai_first")); return
        n=self.editor.remove_small_islands(); self._recompose(); self.status_text.set(tr(self.language.get(),"islands_done",count=n)); self._refresh_previews()
    def _reset_mask(self):
        if self.editor: self.editor.reset(); self._recompose(); self._refresh_previews()

    def _setup_drop_target(self):
        if DND_FILES is None: return
        try:
            for w in (self.drop_zone,self.drop_label): w.drop_target_register(DND_FILES); w.dnd_bind("<<Drop>>",lambda e:self._append_paths(self.root.tk.splitlist(e.data)))
        except Exception: pass
    def _pick_color(self):
        r=colorchooser.askcolor(color=self.bg_color)
        if r and r[1]: self.bg_color=r[1]; self.background_mode.set("color"); self._apply_language(); self._recompose_refresh()
    def _pick_background_image(self):
        p=filedialog.askopenfilename(filetypes=[(tr(self.language.get(),"bg_files"),"*.png *.jpg *.jpeg *.webp *.bmp")])
        if p: self.bg_image_path=p; self.background_mode.set("image"); self._apply_language(); self._recompose_refresh()
    def _add_images(self): self._append_paths(filedialog.askopenfilenames(filetypes=[(tr(self.language.get(),"all_images"),"*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff")]))
    def _add_folder(self):
        p=filedialog.askdirectory()
        if p: self._append_paths(collect_images(p))
    def _append_paths(self,paths):
        existing={str(p.resolve()).lower() for p in self.files}
        for raw in paths:
            p=Path(raw); cand=collect_images(p) if p.is_dir() else [p]
            for q in cand:
                key=str(q.resolve()).lower()
                if q.is_file() and is_supported_image(q) and key not in existing: self.files.append(q); existing.add(key)
        self.files.sort(key=lambda p:p.name.lower()); self._render_file_list(); self._render_filmstrip(); self.project_count.configure(text=tr(self.language.get(),"project_count",count=len(self.files)))
        if self.files and self.selected_index is None: self._select_file(0)
    def _clear_files(self):
        if self.worker and self.worker.is_alive(): return
        self.files.clear(); self.selected_index=None; self.editor=None; self.current_result=None; self.preview_after=None; self._render_file_list(); self._render_filmstrip(); self._refresh_previews(); self.project_count.configure(text=tr(self.language.get(),"project_count",count=0))
    def _thumb(self,path,size=(44,44)):
        try:
            with Image.open(path) as im: p=ImageOps.fit(ImageOps.exif_transpose(im).convert("RGB"),size,Image.Resampling.LANCZOS)
            t=ctk.CTkImage(light_image=p,dark_image=p,size=size); self._thumb_refs.append(t); return t
        except Exception: return None
    def _render_file_list(self):
        self._thumb_refs=[]
        for c in self.file_list.winfo_children(): c.destroy()
        for i,p in enumerate(self.files):
            selected=i==self.selected_index; row=ctk.CTkFrame(self.file_list,height=52,corner_radius=9,fg_color="#123152" if selected else "#0A1C31",border_width=1,border_color=self.VIOLET if selected else "#173955"); row.pack(fill="x",padx=2,pady=2)
            img=self._thumb(p); b=ctk.CTkButton(row,text=p.name[:24],image=img,compound="left",anchor="w",command=lambda n=i:self._select_file(n),height=46,fg_color="transparent",hover_color="#163858",font=ctk.CTkFont("Segoe UI",8)); b.pack(fill="x",padx=3,pady=2)
    def _render_filmstrip(self):
        for c in self.filmstrip.winfo_children(): c.destroy()
        for i,p in enumerate(self.files[:8]):
            img=self._thumb(p,(46,46)); b=ctk.CTkButton(self.filmstrip,text="",image=img,command=lambda n=i:self._select_file(n),width=50,height=50,fg_color=self.VIOLET if i==self.selected_index else "#0C2742",hover_color="#163B61"); b.pack(side="left",padx=3)
        ctk.CTkButton(self.filmstrip,text="+",command=self._add_images,width=48,height=48,fg_color="#0C2742",hover_color="#163B61",font=ctk.CTkFont("Segoe UI",20)).pack(side="left",padx=3)
    def _select_file(self,i):
        if not 0<=i<len(self.files): return
        self.selected_index=i; self.editor=None; self.current_result=None; self.preview_after=None; self._fit_view(); self._render_file_list(); self._render_filmstrip(); self._refresh_previews()

    def _checker(self,size,tile=18):
        im=Image.new("RGB",size,"#13243A"); d=ImageDraw.Draw(im)
        for y in range(0,size[1],tile):
            for x in range(0,size[0],tile):
                if (x//tile+y//tile)%2: d.rectangle((x,y,x+tile,y+tile),fill="#1D314B")
        return im
    def _display_image(self,canvas,image,checker=True,store=False):
        canvas.delete("all"); w=max(100,canvas.winfo_width()); h=max(100,canvas.winfo_height())
        if image is None:
            canvas.create_text(w/2,h/2-8,text="PXR",fill="#4AD9FF",font=("Segoe UI",22,"bold")); canvas.create_text(w/2,h/2+24,text="AI STUDIO",fill="#617D98",font=("Segoe UI",9)); return
        base=ImageOps.contain(image.copy(),(max(20,w-30),max(20,h-30)),Image.Resampling.LANCZOS); nw=max(1,round(base.width*self.view_zoom)); nh=max(1,round(base.height*self.view_zoom)); base=base.resize((nw,nh),Image.Resampling.LANCZOS)
        bg=(self._checker((w,h)) if checker else Image.new("RGB",(w,h),"#091827")).convert("RGBA"); ox=round((w-nw)/2+self.pan_x); oy=round((h-nh)/2+self.pan_y); bg.alpha_composite(base.convert("RGBA"),(ox,oy)); ph=ImageTk.PhotoImage(bg); canvas.create_image(w/2,h/2,image=ph); canvas.image_ref=ph
        if store: self._after_transform=(ox,oy,nw/image.width)
    def _before_image(self):
        if self.selected_index is None: return None
        try:
            with Image.open(self.files[self.selected_index]) as im: return ImageOps.exif_transpose(im).convert("RGBA")
        except Exception: return None
    def _after_image(self):
        if self.tool in {"restore","erase"} and self.editor: return self.editor.current_cutout()
        return self.preview_after
    def _refresh_previews(self): self._display_image(self.before_canvas,self._before_image(),False,False); self._display_image(self.after_canvas,self._after_image(),True,True)
    def _refresh_after_only(self): self._display_image(self.after_canvas,self._after_image(),True,True)

    def _options(self):
        try: pad=max(0,min(1000,int(self.padding.get())))
        except Exception: pad=24
        return ProcessOptions(self.model.get(),self.background_mode.get(),self.bg_color,self.bg_image_path,float(self.background_blur.get()),int(self.edge_refine.get()),float(self.edge_softness.get()),int(self.edge_contrast.get()),bool(self.alpha_matting.get()),bool(self.shadow.get()),bool(self.trim.get()),pad,self.canvas_preset.get(),self.export_format.get(),self.output_suffix.get())
    def _validate(self):
        L=self.language.get()
        if not self.files: messagebox.showwarning(tr(L,"error"),tr(L,"no_files")); return False
        if not self.output_dir.get().strip(): messagebox.showwarning(tr(L,"error"),tr(L,"no_output")); return False
        if self.background_mode.get()=="image" and not self.bg_image_path: messagebox.showwarning(tr(L,"error"),tr(L,"choose_background")); return False
        return True
    def _process_selected(self):
        if self.selected_index is not None and self._validate(): self._start_worker([self.selected_index],False)
    def _process_all(self):
        if self._validate(): self._start_worker(list(range(len(self.files))),True)
    def _start_worker(self,indices,save):
        if self.worker and self.worker.is_alive(): self.cancel_event.set(); return
        self.cancel_event.clear(); self.progress.set(0); self.remove_btn.configure(state="disabled"); self.process_all_btn.configure(text=tr(self.language.get(),"cancel"),fg_color=self.DANGER); self.status_text.set(tr(self.language.get(),"starting")); opts=self._options(); self._save_settings()
        self.worker=threading.Thread(target=self._worker,args=([(i,self.files[i]) for i in indices],opts,save),daemon=True); self.worker.start()
    def _worker(self,items,opts,save):
        ok=fail=0; total=len(items)
        for pos,(idx,path) in enumerate(items,1):
            if self.cancel_event.is_set(): break
            self.events.put(("status",pos,total,path.name))
            try:
                res=self.engine.process_layers(path,opts); dest=None
                if save:
                    dest=output_path_for(path,self.output_dir.get(),opts.export_format,opts.output_suffix); self.engine.save(res.output,dest,opts.export_format); ok+=1
                self.events.put(("result",idx,res,str(dest) if dest else None))
            except Exception as exc: fail+=1; self.events.put(("error",path.name,str(exc)))
            self.events.put(("progress",pos/total))
        self.events.put(("done",ok,fail,self.cancel_event.is_set(),save))
    def _poll_events(self):
        try:
            while True:
                e=self.events.get_nowait(); k=e[0]; L=self.language.get()
                if k=="status": _,a,b,n=e; self.status_text.set(tr(L,"processing",current=a,total=b,name=n))
                elif k=="progress": self.progress.set(e[1])
                elif k=="result":
                    _,idx,res,dest=e
                    if idx==self.selected_index: self.current_result=res; self.editor=MaskEditor(res.original,res.cutout); self.preview_after=res.output; self._set_tool("pan")
                    if dest: self.status_text.set(tr(L,"saved",name=Path(dest).name))
                elif k=="error": _,n,msg=e; self.status_text.set(tr(L,"failed",name=n)); print("BackgroundPXR:",msg)
                elif k=="done":
                    _,ok,fail,cancelled,save=e; self.remove_btn.configure(state="normal"); self.process_all_btn.configure(text=tr(L,"process_all"),fg_color="#12304E"); self.status_text.set(tr(L,"ready") if cancelled or not save else tr(L,"complete",ok=ok,fail=fail))
                    if save and not cancelled and ok and self.auto_open_output.get(): self._open_output_folder()
        except queue.Empty: pass
        self.root.after(80,self._poll_events)
    def _recompose_refresh(self): self._recompose(); self._save_settings(); self._refresh_previews()
    def _recompose(self):
        if self.editor:
            try: self.preview_after=self.engine.compose(self.editor.original,self.editor.current_cutout(),self._options())
            except Exception: pass
    def _export_current(self):
        if self.selected_index is None or not self._validate(): return
        if self.preview_after is None: messagebox.showwarning(tr(self.language.get(),"error"),tr(self.language.get(),"no_result")); return
        self._recompose(); opts=self._options(); dest=output_path_for(self.files[self.selected_index],self.output_dir.get(),opts.export_format,opts.output_suffix); self.engine.save(self.preview_after,dest,opts.export_format); self.status_text.set(tr(self.language.get(),"saved",name=dest.name))
        if self.auto_open_output.get(): self._open_output_folder()
    def _choose_output(self):
        p=filedialog.askdirectory(initialdir=self.output_dir.get())
        if p: self.output_dir.set(p); self._save_settings()
    def _open_output_folder(self):
        p=Path(self.output_dir.get()).expanduser(); p.mkdir(parents=True,exist_ok=True)
        try:
            if os.name=="nt": os.startfile(p)  # type: ignore[attr-defined]
            else: subprocess.Popen(["xdg-open",str(p)])
        except Exception: pass
    def _save_settings(self):
        try: pad=int(self.padding.get())
        except Exception: pad=24
        self.settings_store.save({"language":self.language.get(),"model":self.model.get(),"background_mode":self.background_mode.get(),"background_color":self.bg_color,"background_blur":float(self.background_blur.get()),"export_format":self.export_format.get(),"edge_refine":int(self.edge_refine.get()),"edge_softness":float(self.edge_softness.get()),"edge_contrast":int(self.edge_contrast.get()),"alpha_matting":bool(self.alpha_matting.get()),"shadow":bool(self.shadow.get()),"trim":bool(self.trim.get()),"padding":pad,"canvas_preset":self.canvas_preset.get(),"output_suffix":self.output_suffix.get(),"auto_open_output":bool(self.auto_open_output.get()),"output_dir":self.output_dir.get(),"brush_size":int(self.brush_size.get()),"brush_hardness":int(self.brush_hardness.get())})
    def _on_close(self): self._save_settings(); self.root.destroy()


def create_root():
    return TkinterDnD.Tk() if TkinterDnD is not None else ctk.CTk()
