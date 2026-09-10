from __future__ import annotations

import queue
import threading
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps, ImageTk

from .engine import BackgroundEngine, ProcessOptions, collect_images, is_supported_image, output_path_for
from .i18n import tr

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class BackgroundPXRApp:
    ACCENT = "#4C7DFF"
    ACCENT_HOVER = "#3566E6"
    PANEL = "#121825"
    PANEL_2 = "#181F2D"
    MUTED = "#8A94A7"

    def __init__(self, root) -> None:
        self.root = root
        self.engine = BackgroundEngine()
        self.files: list[Path] = []
        self.selected_index: int | None = None
        self.preview_after: Image.Image | None = None
        self.worker: threading.Thread | None = None
        self.cancel_event = threading.Event()
        self.events: queue.Queue = queue.Queue()
        self.bg_image_path: str | None = None
        self.bg_color = "#FFFFFF"

        self.language = ctk.StringVar(value="English")
        self.model = ctk.StringVar(value="Quality")
        self.background_mode = ctk.StringVar(value="transparent")
        self.export_format = ctk.StringVar(value="PNG")
        self.edge_softness = ctk.DoubleVar(value=0.8)
        self.shadow = ctk.BooleanVar(value=False)
        self.trim = ctk.BooleanVar(value=False)
        self.padding = ctk.IntVar(value=24)
        self.output_dir = ctk.StringVar(value=str(Path.home() / "Pictures" / "BackgroundPXR"))
        self.progress = ctk.DoubleVar(value=0)
        self.status_text = ctk.StringVar(value="Ready")

        self._configure_root()
        self._build_ui()
        self._apply_language()
        self._poll_events()

    def _configure_root(self) -> None:
        self.root.title("BackgroundPXR — Power eXtreme Remover")
        self.root.geometry("1480x900")
        self.root.minsize(1180, 720)
        self.root.configure(bg="#0B0F17")

    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_sidebar()
        self._build_workspace()
        self._build_footer()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self.root, height=84, corner_radius=0, fg_color="#0D121C")
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        mark = ctk.CTkCanvas(header, width=56, height=56, bg="#0D121C", highlightthickness=0)
        mark.grid(row=0, column=0, padx=(24, 14), pady=14)
        mark.create_oval(5, 5, 51, 51, outline=self.ACCENT, width=3)
        mark.create_arc(12, 12, 44, 44, start=35, extent=285, style="arc", outline="#A9C0FF", width=5)
        mark.create_text(28, 28, text="PXR", fill="white", font=("Segoe UI", 11, "bold"))

        titlebox = ctk.CTkFrame(header, fg_color="transparent")
        titlebox.grid(row=0, column=1, sticky="w")
        self.title_label = ctk.CTkLabel(titlebox, text="", font=ctk.CTkFont("Segoe UI", 25, "bold"), text_color="#F5F7FB")
        self.title_label.pack(anchor="w")
        self.tagline_label = ctk.CTkLabel(titlebox, text="", font=ctk.CTkFont("Segoe UI", 12), text_color=self.MUTED)
        self.tagline_label.pack(anchor="w", pady=(1, 0))

        lang = ctk.CTkSegmentedButton(
            header,
            values=["English", "Polski"],
            variable=self.language,
            command=lambda _v: self._on_language_change(),
            width=185,
            selected_color=self.ACCENT,
            selected_hover_color=self.ACCENT_HOVER,
        )
        lang.grid(row=0, column=2, padx=24)

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self.root, width=320, corner_radius=0, fg_color="#0F141E")
        sidebar.grid(row=1, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(3, weight=1)

        top = ctk.CTkFrame(sidebar, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(18, 8))
        top.grid_columnconfigure((0, 1), weight=1)
        self.add_images_btn = ctk.CTkButton(top, text="", command=self._add_images, fg_color=self.ACCENT, hover_color=self.ACCENT_HOVER)
        self.add_images_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.add_folder_btn = ctk.CTkButton(top, text="", command=self._add_folder, fg_color=self.PANEL_2)
        self.add_folder_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        row = ctk.CTkFrame(sidebar, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=18, pady=(7, 7))
        row.grid_columnconfigure(0, weight=1)
        self.files_label = ctk.CTkLabel(row, text="", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=self.MUTED)
        self.files_label.grid(row=0, column=0, sticky="w")
        self.clear_btn = ctk.CTkButton(row, text="", width=70, height=26, command=self._clear_files, fg_color="transparent", border_width=1, border_color="#30394A")
        self.clear_btn.grid(row=0, column=1)

        self.drop_zone = ctk.CTkFrame(sidebar, height=70, fg_color="#121927", border_width=1, border_color="#283248")
        self.drop_zone.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))
        self.drop_zone.grid_propagate(False)
        self.drop_label = ctk.CTkLabel(self.drop_zone, text="", text_color=self.MUTED, wraplength=270)
        self.drop_label.place(relx=.5, rely=.5, anchor="center")
        self._setup_drop_target()

        self.file_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.file_list.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0, 8))

    def _build_workspace(self) -> None:
        workspace = ctk.CTkFrame(self.root, corner_radius=0, fg_color="#0B0F17")
        workspace.grid(row=1, column=1, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=5)
        workspace.grid_columnconfigure(1, weight=3)
        workspace.grid_rowconfigure(0, weight=1)

        preview = ctk.CTkFrame(workspace, fg_color="#0B0F17")
        preview.grid(row=0, column=0, sticky="nsew", padx=(18, 10), pady=18)
        preview.grid_columnconfigure((0, 1), weight=1)
        preview.grid_rowconfigure(1, weight=1)

        self.before_title = ctk.CTkLabel(preview, text="", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=self.MUTED)
        self.before_title.grid(row=0, column=0, sticky="w", padx=10, pady=(0, 8))
        self.after_title = ctk.CTkLabel(preview, text="", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=self.MUTED)
        self.after_title.grid(row=0, column=1, sticky="w", padx=18, pady=(0, 8))

        self.before_canvas = ctk.CTkCanvas(preview, bg="#111722", highlightthickness=1, highlightbackground="#273044")
        self.before_canvas.grid(row=1, column=0, sticky="nsew", padx=(0, 7))
        self.after_canvas = ctk.CTkCanvas(preview, bg="#111722", highlightthickness=1, highlightbackground="#273044")
        self.after_canvas.grid(row=1, column=1, sticky="nsew", padx=(7, 0))
        self.before_canvas.bind("<Configure>", lambda _e: self._refresh_previews())
        self.after_canvas.bind("<Configure>", lambda _e: self._refresh_previews())

        controls = ctk.CTkScrollableFrame(workspace, width=390, fg_color=self.PANEL, corner_radius=16)
        controls.grid(row=0, column=1, sticky="nsew", padx=(10, 18), pady=18)
        controls.grid_columnconfigure(0, weight=1)

        self.settings_title = ctk.CTkLabel(controls, text="", font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color="#DDE5F5")
        self.settings_title.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 10))

        self.model_label = self._label(controls, 1)
        self.model_menu = ctk.CTkOptionMenu(controls, variable=self.model, values=["Quality", "Fast", "Portrait"], fg_color="#20293A", button_color=self.ACCENT, button_hover_color=self.ACCENT_HOVER)
        self.model_menu.grid(row=2, column=0, sticky="ew", padx=18)

        self.background_label = self._label(controls, 3)
        self.bg_segment = ctk.CTkSegmentedButton(controls, values=["Transparent", "White", "Color", "Image"], command=self._on_bg_segment, selected_color=self.ACCENT, selected_hover_color=self.ACCENT_HOVER)
        self.bg_segment.grid(row=4, column=0, sticky="ew", padx=18)
        self.bg_segment.set("Transparent")

        bg_actions = ctk.CTkFrame(controls, fg_color="transparent")
        bg_actions.grid(row=5, column=0, sticky="ew", padx=18, pady=(8, 0))
        bg_actions.grid_columnconfigure((0, 1), weight=1)
        self.color_btn = ctk.CTkButton(bg_actions, text="", command=self._pick_color, fg_color="#20293A")
        self.color_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.bg_image_btn = ctk.CTkButton(bg_actions, text="", command=self._pick_background_image, fg_color="#20293A")
        self.bg_image_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        self.edge_label = self._label(controls, 6)
        edge_row = ctk.CTkFrame(controls, fg_color="transparent")
        edge_row.grid(row=7, column=0, sticky="ew", padx=18)
        edge_row.grid_columnconfigure(0, weight=1)
        self.edge_slider = ctk.CTkSlider(edge_row, from_=0, to=5, number_of_steps=50, variable=self.edge_softness, progress_color=self.ACCENT)
        self.edge_slider.grid(row=0, column=0, sticky="ew")
        self.edge_value = ctk.CTkLabel(edge_row, text="0.8", width=40, text_color=self.MUTED)
        self.edge_value.grid(row=0, column=1, padx=(8, 0))
        self.edge_slider.configure(command=lambda v: self.edge_value.configure(text=f"{v:.1f}"))

        toggles = ctk.CTkFrame(controls, fg_color="transparent")
        toggles.grid(row=8, column=0, sticky="ew", padx=18, pady=(16, 2))
        toggles.grid_columnconfigure(0, weight=1)
        self.shadow_switch = ctk.CTkSwitch(toggles, text="", variable=self.shadow, progress_color=self.ACCENT)
        self.shadow_switch.grid(row=0, column=0, sticky="w")
        self.trim_switch = ctk.CTkSwitch(toggles, text="", variable=self.trim, command=self._update_padding_state, progress_color=self.ACCENT)
        self.trim_switch.grid(row=1, column=0, sticky="w", pady=(10, 0))

        padrow = ctk.CTkFrame(controls, fg_color="transparent")
        padrow.grid(row=9, column=0, sticky="ew", padx=18, pady=(8, 0))
        padrow.grid_columnconfigure(0, weight=1)
        self.padding_label = ctk.CTkLabel(padrow, text="", text_color=self.MUTED)
        self.padding_label.grid(row=0, column=0, sticky="w")
        self.padding_entry = ctk.CTkEntry(padrow, width=82, textvariable=self.padding)
        self.padding_entry.grid(row=0, column=1)
        self._update_padding_state()

        self.format_label = self._label(controls, 10)
        self.format_menu = ctk.CTkSegmentedButton(controls, values=["PNG", "JPG", "WEBP"], variable=self.export_format, selected_color=self.ACCENT, selected_hover_color=self.ACCENT_HOVER)
        self.format_menu.grid(row=11, column=0, sticky="ew", padx=18)
        self.format_menu.set("PNG")

        self.output_label = self._label(controls, 12)
        outrow = ctk.CTkFrame(controls, fg_color="transparent")
        outrow.grid(row=13, column=0, sticky="ew", padx=18)
        outrow.grid_columnconfigure(0, weight=1)
        self.output_entry = ctk.CTkEntry(outrow, textvariable=self.output_dir)
        self.output_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.output_btn = ctk.CTkButton(outrow, text="…", width=44, command=self._choose_output, fg_color="#20293A")
        self.output_btn.grid(row=0, column=1)

        self.info_label = ctk.CTkLabel(controls, text="", text_color=self.MUTED, justify="left", wraplength=330, font=ctk.CTkFont("Segoe UI", 11))
        self.info_label.grid(row=14, column=0, sticky="ew", padx=18, pady=(14, 8))

        self.progress_bar = ctk.CTkProgressBar(controls, variable=self.progress, progress_color=self.ACCENT)
        self.progress_bar.grid(row=15, column=0, sticky="ew", padx=18, pady=(8, 6))
        self.progress_bar.set(0)
        self.status_label = ctk.CTkLabel(controls, textvariable=self.status_text, text_color="#B9C4D8")
        self.status_label.grid(row=16, column=0, sticky="w", padx=18, pady=(0, 10))

        actions = ctk.CTkFrame(controls, fg_color="transparent")
        actions.grid(row=17, column=0, sticky="ew", padx=18, pady=(4, 18))
        actions.grid_columnconfigure((0, 1), weight=1)
        self.process_selected_btn = ctk.CTkButton(actions, text="", command=self._process_selected, fg_color="#20293A", height=42)
        self.process_selected_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.process_all_btn = ctk.CTkButton(actions, text="", command=self._process_all, fg_color=self.ACCENT, hover_color=self.ACCENT_HOVER, height=42)
        self.process_all_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self.root, height=30, corner_radius=0, fg_color="#090D14")
        footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.footer_label = ctk.CTkLabel(footer, text="", font=ctk.CTkFont("Segoe UI", 10), text_color="#657086")
        self.footer_label.pack(pady=5)

    def _label(self, parent, row: int):
        label = ctk.CTkLabel(parent, text="", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=self.MUTED)
        label.grid(row=row, column=0, sticky="w", padx=18, pady=(15, 6))
        return label

    def _setup_drop_target(self) -> None:
        if DND_FILES is None:
            return
        try:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self._on_drop)
            self.drop_label.drop_target_register(DND_FILES)
            self.drop_label.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass

    def _on_drop(self, event) -> None:
        paths = self.root.tk.splitlist(event.data)
        self._append_paths(paths)

    def _on_language_change(self) -> None:
        self._apply_language()

    def _apply_language(self) -> None:
        lang = self.language.get()
        self.title_label.configure(text=tr(lang, "app_title"))
        self.tagline_label.configure(text=tr(lang, "tagline"))
        self.add_images_btn.configure(text=tr(lang, "add_images"))
        self.add_folder_btn.configure(text=tr(lang, "add_folder"))
        self.files_label.configure(text=tr(lang, "files"))
        self.clear_btn.configure(text=tr(lang, "clear"))
        self.drop_label.configure(text=tr(lang, "drop_here"))
        self.settings_title.configure(text=tr(lang, "settings"))
        self.model_label.configure(text=tr(lang, "model"))
        self.background_label.configure(text=tr(lang, "background"))
        self.color_btn.configure(text=tr(lang, "pick_color"))
        self.bg_image_btn.configure(text=tr(lang, "pick_bg"))
        self.edge_label.configure(text=tr(lang, "edge_softness"))
        self.shadow_switch.configure(text=tr(lang, "shadow"))
        self.trim_switch.configure(text=tr(lang, "trim"))
        self.padding_label.configure(text=tr(lang, "padding"))
        self.format_label.configure(text=tr(lang, "format"))
        self.output_label.configure(text=tr(lang, "output"))
        self.info_label.configure(text=tr(lang, "first_model") + "\n\n" + tr(lang, "remove_tip"))
        self.process_selected_btn.configure(text=tr(lang, "process_selected"))
        self.process_all_btn.configure(text=tr(lang, "process_all"))
        self.before_title.configure(text=tr(lang, "before"))
        self.after_title.configure(text=tr(lang, "after"))
        self.footer_label.configure(text=tr(lang, "footer"))

        current_model = self.model.get()
        model_key = "model_quality" if current_model in {"Quality", "Jakość"} else "model_fast" if current_model in {"Fast", "Szybki"} else "model_portrait"
        translated_model = tr(lang, model_key)
        model_values = [tr(lang, "model_quality"), tr(lang, "model_fast"), tr(lang, "model_portrait")]
        self.model_menu.configure(values=model_values)
        self.model.set(translated_model)

        labels = [tr(lang, "bg_transparent"), tr(lang, "bg_white"), tr(lang, "bg_color"), tr(lang, "bg_image")]
        self.bg_segment.configure(values=labels)
        mode_map = {"transparent": 0, "white": 1, "color": 2, "image": 3}
        self.bg_segment.set(labels[mode_map.get(self.background_mode.get(), 0)])

        if not self.worker or not self.worker.is_alive():
            self.status_text.set(tr(lang, "ready"))
        self._render_file_list()
        self._refresh_previews()

    def _on_bg_segment(self, value: str) -> None:
        lang = self.language.get()
        lookup = {
            tr(lang, "bg_transparent"): "transparent",
            tr(lang, "bg_white"): "white",
            tr(lang, "bg_color"): "color",
            tr(lang, "bg_image"): "image",
        }
        self.background_mode.set(lookup.get(value, "transparent"))

    def _pick_color(self) -> None:
        result = colorchooser.askcolor(color=self.bg_color, title=tr(self.language.get(), "pick_color"))
        if result and result[1]:
            self.bg_color = result[1]
            self.background_mode.set("color")
            self.bg_segment.set(tr(self.language.get(), "bg_color"))
            self.color_btn.configure(border_width=2, border_color=self.bg_color)

    def _pick_background_image(self) -> None:
        path = filedialog.askopenfilename(filetypes=[(tr(self.language.get(), "bg_files"), "*.png *.jpg *.jpeg *.webp *.bmp")])
        if path:
            self.bg_image_path = path
            self.background_mode.set("image")
            self.bg_segment.set(tr(self.language.get(), "bg_image"))
            self.bg_image_btn.configure(text=Path(path).name[:24])

    def _update_padding_state(self) -> None:
        self.padding_entry.configure(state="normal" if self.trim.get() else "disabled")

    def _add_images(self) -> None:
        paths = filedialog.askopenfilenames(filetypes=[(tr(self.language.get(), "all_images"), "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff")])
        self._append_paths(paths)

    def _add_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self._append_paths(collect_images(folder))

    def _append_paths(self, paths) -> None:
        existing = {str(p.resolve()).lower() for p in self.files}
        changed = False
        for raw in paths:
            p = Path(raw)
            candidates = collect_images(p) if p.is_dir() else [p]
            for candidate in candidates:
                if candidate.is_file() and is_supported_image(candidate):
                    key = str(candidate.resolve()).lower()
                    if key not in existing:
                        self.files.append(candidate)
                        existing.add(key)
                        changed = True
        if changed:
            self.files.sort(key=lambda p: p.name.lower())
            self._render_file_list()
            if self.selected_index is None and self.files:
                self._select_file(0)

    def _clear_files(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        self.files.clear()
        self.selected_index = None
        self.preview_after = None
        self._render_file_list()
        self._refresh_previews()

    def _render_file_list(self) -> None:
        for child in self.file_list.winfo_children():
            child.destroy()
        for i, path in enumerate(self.files):
            selected = i == self.selected_index
            frame = ctk.CTkFrame(self.file_list, fg_color="#1B2638" if selected else "transparent", corner_radius=10)
            frame.pack(fill="x", padx=4, pady=3)
            btn = ctk.CTkButton(frame, text=path.name, anchor="w", command=lambda idx=i: self._select_file(idx), fg_color="transparent", hover_color="#1B2638", text_color="#E9EDF5")
            btn.pack(fill="x", padx=4, pady=2)

    def _select_file(self, index: int) -> None:
        if not (0 <= index < len(self.files)):
            return
        self.selected_index = index
        self.preview_after = None
        self._render_file_list()
        self._refresh_previews()

    def _checker(self, size: tuple[int, int], tile: int = 18) -> Image.Image:
        w, h = size
        img = Image.new("RGB", size, "#1A2230")
        draw = ImageDraw.Draw(img)
        other = "#222C3D"
        for y in range(0, h, tile):
            for x in range(0, w, tile):
                if (x // tile + y // tile) % 2:
                    draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill=other)
        return img

    def _draw_preview(self, canvas, image: Image.Image | None, empty_text: str = "") -> None:
        canvas.delete("all")
        w = max(canvas.winfo_width(), 100)
        h = max(canvas.winfo_height(), 100)
        if image is None:
            canvas.create_text(w / 2, h / 2, text=empty_text, fill="#6F7B90", font=("Segoe UI", 12))
            canvas.image_ref = None
            return
        display = ImageOps.contain(image.copy(), (max(20, w - 30), max(20, h - 30)), Image.Resampling.LANCZOS)
        checker = self._checker((w, h))
        if display.mode != "RGBA":
            display = display.convert("RGBA")
        x = (w - display.width) // 2
        y = (h - display.height) // 2
        checker_rgba = checker.convert("RGBA")
        checker_rgba.alpha_composite(display, (x, y))
        photo = ImageTk.PhotoImage(checker_rgba)
        canvas.create_image(w / 2, h / 2, image=photo)
        canvas.image_ref = photo

    def _refresh_previews(self) -> None:
        lang = self.language.get()
        before = None
        if self.selected_index is not None and 0 <= self.selected_index < len(self.files):
            try:
                with Image.open(self.files[self.selected_index]) as img:
                    before = ImageOps.exif_transpose(img).convert("RGBA")
            except Exception:
                before = None
        self._draw_preview(self.before_canvas, before, tr(lang, "select_file"))
        self._draw_preview(self.after_canvas, self.preview_after, tr(lang, "select_file"))

    def _choose_output(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.output_dir.get())
        if folder:
            self.output_dir.set(folder)

    def _options(self) -> ProcessOptions:
        try:
            pad = max(0, min(1000, int(self.padding.get())))
        except Exception:
            pad = 24
        return ProcessOptions(
            model_label=self.model.get(),
            background_mode=self.background_mode.get(),
            background_color=self.bg_color,
            background_image=self.bg_image_path,
            edge_softness=float(self.edge_softness.get()),
            shadow=bool(self.shadow.get()),
            trim=bool(self.trim.get()),
            padding=pad,
            export_format=self.export_format.get(),
        )

    def _validate_run(self) -> bool:
        lang = self.language.get()
        if not self.files:
            messagebox.showwarning(tr(lang, "error"), tr(lang, "no_files"))
            return False
        if not self.output_dir.get().strip():
            messagebox.showwarning(tr(lang, "error"), tr(lang, "no_output"))
            return False
        if self.background_mode.get() == "image" and not self.bg_image_path:
            messagebox.showwarning(tr(lang, "error"), tr(lang, "choose_background"))
            return False
        return True

    def _process_selected(self) -> None:
        if self.selected_index is None or not self._validate_run():
            return
        self._start_worker([self.selected_index])

    def _process_all(self) -> None:
        if not self._validate_run():
            return
        self._start_worker(list(range(len(self.files))))

    def _start_worker(self, indices: list[int]) -> None:
        if self.worker and self.worker.is_alive():
            self.cancel_event.set()
            return
        self.cancel_event.clear()
        self.progress.set(0)
        self._set_running(True)
        options = self._options()
        paths = [(i, self.files[i]) for i in indices]
        self.worker = threading.Thread(target=self._worker_run, args=(paths, options), daemon=True)
        self.worker.start()

    def _set_running(self, running: bool) -> None:
        lang = self.language.get()
        if running:
            self.status_text.set(tr(lang, "status_model"))
            self.process_all_btn.configure(text=tr(lang, "cancel"), fg_color="#B64052", hover_color="#973344")
            self.process_selected_btn.configure(state="disabled")
        else:
            self.process_all_btn.configure(text=tr(lang, "process_all"), fg_color=self.ACCENT, hover_color=self.ACCENT_HOVER)
            self.process_selected_btn.configure(state="normal")

    def _worker_run(self, paths: list[tuple[int, Path]], options: ProcessOptions) -> None:
        ok = 0
        fail = 0
        total = len(paths)
        for pos, (index, path) in enumerate(paths, start=1):
            if self.cancel_event.is_set():
                break
            self.events.put(("status", pos, total, path.name))
            try:
                result = self.engine.process(path, options)
                destination = output_path_for(path, self.output_dir.get(), options.export_format)
                self.engine.save(result, destination, options.export_format)
                ok += 1
                self.events.put(("result", index, result.copy(), str(destination)))
            except Exception as exc:
                fail += 1
                self.events.put(("item_error", path.name, str(exc)))
            self.events.put(("progress", pos / total if total else 1))
        self.events.put(("complete", ok, fail, self.cancel_event.is_set()))

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                lang = self.language.get()
                if kind == "status":
                    _, cur, total, name = event
                    self.status_text.set(tr(lang, "status_image", current=cur, total=total, name=name))
                elif kind == "progress":
                    self.progress.set(float(event[1]))
                elif kind == "result":
                    _, index, image, destination = event
                    if self.selected_index == index:
                        self.preview_after = image
                        self._refresh_previews()
                    self.status_text.set(f"{tr(lang, 'saved')}: {Path(destination).name}")
                elif kind == "item_error":
                    _, name, msg = event
                    self.status_text.set(f"{tr(lang, 'failed')}: {name}")
                    print(f"BackgroundPXR error [{name}]: {msg}")
                elif kind == "complete":
                    _, ok, fail, cancelled = event
                    self._set_running(False)
                    self.status_text.set(tr(lang, "ready") if cancelled else tr(lang, "complete", ok=ok, fail=fail))
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)


def create_root():
    if TkinterDnD is not None:
        return TkinterDnD.Tk()
    return ctk.CTk()
