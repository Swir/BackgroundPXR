from __future__ import annotations

from pathlib import Path
from tkinter import colorchooser, messagebox

import customtkinter as ctk
from PIL import Image

from .settings import SettingsStore
from .studio_v034_fix import BackgroundPXRStudio034FixedApp
from .i18n import tr


PRO_TX = {
    "English": {
        "studio_pro": "STUDIO PRO",
        "tab_ai": "AI",
        "tab_create": "CREATE",
        "tab_export": "EXPORT",
        "subject": "SUBJECT",
        "subject_sub": "Scale and position without rerunning AI",
        "scale": "Scale",
        "position_x": "Position X",
        "position_y": "Position Y",
        "style": "STYLE",
        "style_sub": "Outline, shadow and preview",
        "outline": "Outline / Sticker",
        "outline_width": "Outline width",
        "outline_color": "Outline color",
        "shadow_strength": "Shadow opacity",
        "shadow_blur": "Shadow blur",
        "preview": "Preview",
        "preview_result": "Result",
        "preview_mask": "Mask",
        "preview_black": "Black",
        "preview_white": "White",
        "preset_sticker": "Sticker",
        "preset_product": "Product",
        "preset_portrait": "Portrait",
        "mask_export": "MASK EXPORT",
        "mask_export_sub": "Save the current subject mask as PNG",
        "export_mask": "Export Mask PNG",
        "mask_saved": "Mask saved: {name}",
        "need_ai": "Run AI first to create a mask.",
        "spill_cleanup": "Color Spill Cleanup",
        "spill_strength": "Spill strength",
    },
    "Polski": {
        "studio_pro": "STUDIO PRO",
        "tab_ai": "AI",
        "tab_create": "TWÓRZ",
        "tab_export": "EKSPORT",
        "subject": "OBIEKT",
        "subject_sub": "Skala i pozycja bez ponownego liczenia AI",
        "scale": "Skala",
        "position_x": "Pozycja X",
        "position_y": "Pozycja Y",
        "style": "STYL",
        "style_sub": "Kontur, cień i podgląd",
        "outline": "Kontur / Naklejka",
        "outline_width": "Grubość konturu",
        "outline_color": "Kolor konturu",
        "shadow_strength": "Krycie cienia",
        "shadow_blur": "Rozmycie cienia",
        "preview": "Podgląd",
        "preview_result": "Wynik",
        "preview_mask": "Maska",
        "preview_black": "Czarne",
        "preview_white": "Białe",
        "preset_sticker": "Naklejka",
        "preset_product": "Produkt",
        "preset_portrait": "Portret",
        "mask_export": "EKSPORT MASKI",
        "mask_export_sub": "Zapisz bieżącą maskę obiektu jako PNG",
        "export_mask": "Eksportuj maskę PNG",
        "mask_saved": "Zapisano maskę: {name}",
        "need_ai": "Najpierw uruchom AI, aby utworzyć maskę.",
        "spill_cleanup": "Usuń kolorowe obwódki",
        "spill_strength": "Siła czyszczenia",
    },
}


def ptx(language: str, key: str, **kwargs) -> str:
    table = PRO_TX.get(language, PRO_TX["English"])
    text = table.get(key, PRO_TX["English"].get(key, key))
    return text.format(**kwargs) if kwargs else text


class BackgroundPXRStudio040App(BackgroundPXRStudio034FixedApp):
    """BackgroundPXR 0.4 Studio Pro shell.

    The right inspector is page-based instead of one long vertical stack. This
    keeps controls readable on 1600x900 while adding subject transform, outline,
    improved shadow controls, mask preview and mask export.
    """

    def __init__(self, root):
        cfg = SettingsStore().load()
        self.inspector_page = ctk.StringVar(master=root, value="ai")
        self.subject_scale = ctk.DoubleVar(
            master=root, value=float(cfg.get("subject_scale", 1.0))
        )
        self.subject_offset_x = ctk.DoubleVar(
            master=root, value=float(cfg.get("subject_offset_x", 0.0))
        )
        self.subject_offset_y = ctk.DoubleVar(
            master=root, value=float(cfg.get("subject_offset_y", 0.0))
        )
        self.outline = ctk.BooleanVar(
            master=root, value=bool(cfg.get("outline", False))
        )
        self.outline_width = ctk.IntVar(
            master=root, value=int(cfg.get("outline_width", 6))
        )
        self.outline_color = str(cfg.get("outline_color", "#FFFFFF"))
        self.shadow_opacity = ctk.IntVar(
            master=root, value=int(cfg.get("shadow_opacity", 38))
        )
        self.shadow_blur = ctk.DoubleVar(
            master=root, value=float(cfg.get("shadow_blur", 18.0))
        )
        self.shadow_offset_x = ctk.IntVar(
            master=root, value=int(cfg.get("shadow_offset_x", 12))
        )
        self.shadow_offset_y = ctk.IntVar(
            master=root, value=int(cfg.get("shadow_offset_y", 18))
        )
        self.preview_mode = ctk.StringVar(
            master=root, value=str(cfg.get("preview_mode", "result"))
        )
        self.spill_cleanup = ctk.BooleanVar(
            master=root, value=bool(cfg.get("spill_cleanup", False))
        )
        self.spill_strength = ctk.IntVar(
            master=root, value=int(cfg.get("spill_strength", 55))
        )
        super().__init__(root)

    def _build_header(self):
        super()._build_header()
        try:
            self.tagline_label.configure(
                text_color="#78E7FF",
                font=ctk.CTkFont("Segoe UI", 10, "bold"),
            )
        except Exception:
            pass

    def _build_right(self, parent):
        # Rebuild the inspector as pages rather than adding more cards to the
        # already long 0.3.x stack.
        parent.grid_columnconfigure(2, minsize=430, weight=0)
        self.right_panel = ctk.CTkFrame(
            parent,
            width=430,
            corner_radius=16,
            fg_color="#071728",
            border_width=1,
            border_color="#1D4B70",
        )
        self.right_panel.grid(
            row=0, column=2, sticky="nsew", padx=(8, 12), pady=(6, 6)
        )
        self.right_panel.grid_propagate(False)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(2, weight=1)

        self.pro_title = ctk.CTkLabel(
            self.right_panel,
            text="",
            height=22,
            anchor="w",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color="#6FE4FF",
        )
        self.pro_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(9, 4))

        self.inspector_tabs = ctk.CTkSegmentedButton(
            self.right_panel,
            values=["AI", "CREATE", "EXPORT"],
            command=self._on_inspector_tab,
            height=32,
            selected_color=self.VIOLET,
            selected_hover_color="#5D3EE0",
            unselected_color="#0B2139",
            unselected_hover_color="#123252",
            border_width=1,
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
        )
        self.inspector_tabs.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))

        stack = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        stack.grid(row=2, column=0, sticky="nsew")
        stack.grid_rowconfigure(0, weight=1)
        stack.grid_columnconfigure(0, weight=1)
        self.inspector_stack = stack

        self.ai_page = self._inspector_page(stack)
        self.create_page = self._inspector_page(stack)
        self.export_page = self._inspector_page(stack)

        self._build_ai_card(self.ai_page)
        self._build_refine_card(self.ai_page)

        self._build_manual_card(self.create_page)
        self.manual_card.grid_configure(row=0)
        self._build_subject_card(self.create_page)
        self._build_style_card(self.create_page)

        self._build_export_card(self.export_page)
        self.export_card.grid_configure(row=0)
        self._build_mask_export_card(self.export_page)

        # Keep readable controls; page navigation means we no longer have to
        # crush everything into a single 680px column.
        for button in (
            self.remove_btn,
            self.restore_btn,
            self.erase_btn,
            self.smart_btn,
            self.export_btn,
            self.process_all_btn,
        ):
            button.configure(height=max(30, int(button.cget("height"))))

        self._show_inspector("ai")

    def _inspector_page(self, parent):
        page = ctk.CTkFrame(parent, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        return page

    def _build_refine_card(self, parent):
        super()._build_refine_card(parent)

        spill = ctk.CTkFrame(self.refine_card, fg_color="transparent")
        spill.grid(row=4, column=0, sticky="ew", padx=10, pady=(1, 7))
        spill.grid_columnconfigure(1, weight=1)

        self.spill_switch = ctk.CTkSwitch(
            spill,
            text="",
            variable=self.spill_cleanup,
            command=self._studio_recompose,
            progress_color="#19B7C9",
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
            switch_width=32,
            switch_height=17,
        )
        self.spill_switch.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.spill_strength_slider = ctk.CTkSlider(
            spill,
            from_=0,
            to=100,
            number_of_steps=100,
            variable=self.spill_strength,
            command=lambda _v: self._studio_recompose(),
            progress_color=self.ACCENT,
            height=13,
        )
        self.spill_strength_slider.grid(row=0, column=1, sticky="ew")

        self.spill_strength_label = ctk.CTkLabel(
            spill,
            text="",
            width=92,
            height=18,
            anchor="e",
            font=ctk.CTkFont("Segoe UI", 9),
            text_color=self.MUTED,
        )
        self.spill_strength_label.grid(row=0, column=2, padx=(8, 0))

    def _build_subject_card(self, parent):
        card = self.subject_card = self._card(parent, 1)
        self._card_title(card, "fit", "subject_title", "subject_sub")

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 8))
        body.grid_columnconfigure((0, 1), weight=1)

        self.subject_scale_label = ctk.CTkLabel(
            body, text="", height=18,
            font=ctk.CTkFont("Segoe UI", 9, "bold"), text_color=self.MUTED
        )
        self.subject_scale_label.grid(row=0, column=0, columnspan=2, sticky="w")
        self.subject_scale_slider = ctk.CTkSlider(
            body,
            from_=0.35,
            to=1.50,
            number_of_steps=115,
            variable=self.subject_scale,
            command=lambda _v: self._studio_recompose(),
            progress_color=self.ACCENT,
            height=14,
        )
        self.subject_scale_slider.grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(0, 6)
        )

        self.subject_x_label = ctk.CTkLabel(
            body, text="", height=18,
            font=ctk.CTkFont("Segoe UI", 9), text_color=self.MUTED
        )
        self.subject_x_label.grid(row=2, column=0, sticky="w")
        self.subject_y_label = ctk.CTkLabel(
            body, text="", height=18,
            font=ctk.CTkFont("Segoe UI", 9), text_color=self.MUTED
        )
        self.subject_y_label.grid(row=2, column=1, sticky="w", padx=(8, 0))

        self.subject_x_slider = ctk.CTkSlider(
            body,
            from_=-35,
            to=35,
            number_of_steps=70,
            variable=self.subject_offset_x,
            command=lambda _v: self._studio_recompose(),
            progress_color=self.ACCENT,
            height=14,
        )
        self.subject_x_slider.grid(row=3, column=0, sticky="ew", padx=(0, 4))
        self.subject_y_slider = ctk.CTkSlider(
            body,
            from_=-35,
            to=35,
            number_of_steps=70,
            variable=self.subject_offset_y,
            command=lambda _v: self._studio_recompose(),
            progress_color=self.VIOLET,
            height=14,
        )
        self.subject_y_slider.grid(row=3, column=1, sticky="ew", padx=(4, 0))

    def _build_style_card(self, parent):
        card = self.style_card = self._card(parent, 2)
        self._card_title(card, "magic", "style_title", "style_sub")

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=1, column=0, sticky="ew", padx=10)
        top.grid_columnconfigure(1, weight=1)

        self.style_outline_switch = ctk.CTkSwitch(
            top,
            text="",
            variable=self.outline,
            command=self._studio_recompose,
            progress_color=self.VIOLET,
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
        )
        self.style_outline_switch.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.outline_color_btn = ctk.CTkButton(
            top,
            text="",
            command=self._pick_outline_color,
            width=112,
            height=27,
            fg_color="#102B49",
            hover_color="#173C61",
            font=ctk.CTkFont("Segoe UI", 9),
        )
        self.outline_color_btn.grid(row=0, column=1, sticky="e")

        self.outline_width_label = ctk.CTkLabel(
            card, text="", height=18,
            font=ctk.CTkFont("Segoe UI", 9), text_color=self.MUTED
        )
        self.outline_width_label.grid(
            row=2, column=0, sticky="w", padx=10, pady=(5, 0)
        )
        self.outline_width_slider = ctk.CTkSlider(
            card,
            from_=1,
            to=20,
            number_of_steps=19,
            variable=self.outline_width,
            command=lambda _v: self._studio_recompose(),
            progress_color=self.ACCENT,
            height=13,
        )
        self.outline_width_slider.grid(
            row=3, column=0, sticky="ew", padx=10
        )

        shadow = ctk.CTkFrame(card, fg_color="transparent")
        shadow.grid(row=4, column=0, sticky="ew", padx=10, pady=(6, 0))
        shadow.grid_columnconfigure((0, 1), weight=1)

        self.style_shadow_switch = ctk.CTkSwitch(
            shadow,
            text="",
            variable=self.shadow,
            command=self._studio_recompose,
            progress_color=self.VIOLET,
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
        )
        self.style_shadow_switch.grid(row=0, column=0, columnspan=2, sticky="w")

        self.shadow_opacity_label = ctk.CTkLabel(
            shadow, text="", height=18,
            font=ctk.CTkFont("Segoe UI", 9), text_color=self.MUTED
        )
        self.shadow_opacity_label.grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.shadow_blur_label = ctk.CTkLabel(
            shadow, text="", height=18,
            font=ctk.CTkFont("Segoe UI", 9), text_color=self.MUTED
        )
        self.shadow_blur_label.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(3, 0))

        self.shadow_opacity_slider = ctk.CTkSlider(
            shadow,
            from_=0,
            to=100,
            number_of_steps=100,
            variable=self.shadow_opacity,
            command=lambda _v: self._studio_recompose(),
            progress_color=self.ACCENT,
            height=13,
        )
        self.shadow_opacity_slider.grid(row=2, column=0, sticky="ew", padx=(0, 4))
        self.shadow_blur_slider = ctk.CTkSlider(
            shadow,
            from_=0,
            to=50,
            number_of_steps=50,
            variable=self.shadow_blur,
            command=lambda _v: self._studio_recompose(),
            progress_color=self.VIOLET,
            height=13,
        )
        self.shadow_blur_slider.grid(row=2, column=1, sticky="ew", padx=(4, 0))

        self.preview_label = ctk.CTkLabel(
            card, text="", height=18,
            font=ctk.CTkFont("Segoe UI", 9, "bold"), text_color=self.MUTED
        )
        self.preview_label.grid(row=5, column=0, sticky="w", padx=10, pady=(6, 1))

        self.preview_selector = ctk.CTkSegmentedButton(
            card,
            values=["Result", "Mask", "Black", "White"],
            command=self._on_preview_mode,
            height=28,
            selected_color="#137A92",
            selected_hover_color="#1695B1",
            font=ctk.CTkFont("Segoe UI", 9),
        )
        self.preview_selector.grid(row=6, column=0, sticky="ew", padx=10)

        presets = ctk.CTkFrame(card, fg_color="transparent")
        presets.grid(row=7, column=0, sticky="ew", padx=8, pady=(7, 8))
        presets.grid_columnconfigure((0, 1, 2), weight=1)
        self.sticker_preset_btn = self._small_preset_button(
            presets, 0, self._preset_sticker
        )
        self.product_style_btn = self._small_preset_button(
            presets, 1, self._preset_product_style
        )
        self.portrait_style_btn = self._small_preset_button(
            presets, 2, self._preset_portrait_style
        )

    def _small_preset_button(self, parent, column, command):
        button = ctk.CTkButton(
            parent,
            text="",
            command=command,
            height=28,
            fg_color="#102B49",
            hover_color="#173C61",
            border_width=1,
            border_color="#28557D",
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
        )
        button.grid(row=0, column=column, sticky="ew", padx=2)
        return button

    def _build_mask_export_card(self, parent):
        card = self.mask_export_card = self._card(parent, 1)
        self._card_title(card, "export", "mask_export_title", "mask_export_sub")
        self.export_mask_btn = ctk.CTkButton(
            card,
            text="",
            command=self._export_mask,
            height=38,
            fg_color="#0D6E88",
            hover_color="#1089A8",
            border_width=1,
            border_color="#35CFFF",
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
        )
        self.export_mask_btn.grid(
            row=1, column=0, sticky="ew", padx=10, pady=(4, 10)
        )

    def _show_inspector(self, key: str):
        self.inspector_page.set(key)
        pages = {
            "ai": self.ai_page,
            "create": self.create_page,
            "export": self.export_page,
        }
        for page in pages.values():
            page.grid_remove()
        pages.get(key, self.ai_page).grid()
        self.inspector_tabs.set(self._inspector_label(key))

    def _on_inspector_tab(self, label: str):
        language = self.language.get()
        lookup = {
            ptx(language, "tab_ai"): "ai",
            ptx(language, "tab_create"): "create",
            ptx(language, "tab_export"): "export",
        }
        self._show_inspector(lookup.get(label, "ai"))

    def _inspector_label(self, key: str) -> str:
        return ptx(
            self.language.get(),
            {
                "ai": "tab_ai",
                "create": "tab_create",
                "export": "tab_export",
            }.get(key, "tab_ai"),
        )

    def _apply_language(self):
        super()._apply_language()
        if not hasattr(self, "inspector_tabs"):
            return
        language = self.language.get()
        self.pro_title.configure(text=ptx(language, "studio_pro"))
        self.inspector_tabs.configure(
            values=[
                ptx(language, "tab_ai"),
                ptx(language, "tab_create"),
                ptx(language, "tab_export"),
            ]
        )
        self.inspector_tabs.set(self._inspector_label(self.inspector_page.get()))

        self.spill_switch.configure(text=ptx(language, "spill_cleanup"))
        self.spill_strength_label.configure(text=ptx(language, "spill_strength"))

        self.subject_title.configure(text=ptx(language, "subject"))
        self.subject_sub.configure(text=ptx(language, "subject_sub"))
        self.subject_scale_label.configure(text=ptx(language, "scale"))
        self.subject_x_label.configure(text=ptx(language, "position_x"))
        self.subject_y_label.configure(text=ptx(language, "position_y"))

        self.style_title.configure(text=ptx(language, "style"))
        self.style_sub.configure(text=ptx(language, "style_sub"))
        self.style_outline_switch.configure(text=ptx(language, "outline"))
        self.outline_width_label.configure(text=ptx(language, "outline_width"))
        self.outline_color_btn.configure(text=ptx(language, "outline_color"))
        self.style_shadow_switch.configure(text=tr(language, "soft_shadow"))
        self.shadow_opacity_label.configure(text=ptx(language, "shadow_strength"))
        self.shadow_blur_label.configure(text=ptx(language, "shadow_blur"))
        self.preview_label.configure(text=ptx(language, "preview"))

        preview_values = [
            ptx(language, "preview_result"),
            ptx(language, "preview_mask"),
            ptx(language, "preview_black"),
            ptx(language, "preview_white"),
        ]
        self.preview_selector.configure(values=preview_values)
        self.preview_selector.set(self._preview_label(self.preview_mode.get()))

        self.sticker_preset_btn.configure(text=ptx(language, "preset_sticker"))
        self.product_style_btn.configure(text=ptx(language, "preset_product"))
        self.portrait_style_btn.configure(text=ptx(language, "preset_portrait"))

        self.mask_export_title.configure(text=ptx(language, "mask_export"))
        self.mask_export_sub.configure(text=ptx(language, "mask_export_sub"))
        self.export_mask_btn.configure(text=ptx(language, "export_mask"))

        try:
            self.tagline_label.configure(
                text="AI Background Studio  •  Studio Pro  •  by Swir"
                if language == "English"
                else "AI Background Studio  •  Studio Pro  •  by Swir"
            )
        except Exception:
            pass

    def _preview_label(self, key: str) -> str:
        return ptx(
            self.language.get(),
            {
                "result": "preview_result",
                "mask": "preview_mask",
                "black": "preview_black",
                "white": "preview_white",
            }.get(key, "preview_result"),
        )

    def _on_preview_mode(self, label: str):
        language = self.language.get()
        lookup = {
            ptx(language, "preview_result"): "result",
            ptx(language, "preview_mask"): "mask",
            ptx(language, "preview_black"): "black",
            ptx(language, "preview_white"): "white",
        }
        self.preview_mode.set(lookup.get(label, "result"))
        self._save_settings()
        self._refresh_after_only()

    def _current_cutout(self):
        if self.editor is not None:
            return self.editor.current_cutout()
        if self.current_result is not None:
            return self.current_result.cutout
        return None

    def _after_image(self):
        if self.tool in {"restore", "erase"}:
            return super()._after_image()

        cutout = self._current_cutout()
        mode = self.preview_mode.get()
        if cutout is None or mode == "result":
            return super()._after_image()

        if mode == "mask":
            mask = self.engine.mask_image(cutout)
            return Image.merge("RGBA", (mask, mask, mask, Image.new("L", mask.size, 255)))

        matte = Image.new(
            "RGBA",
            cutout.size,
            (0, 0, 0, 255) if mode == "black" else (255, 255, 255, 255),
        )
        matte.alpha_composite(cutout)
        return matte

    def _options(self):
        opts = super()._options()
        opts.subject_scale = float(self.subject_scale.get())
        opts.subject_offset_x = float(self.subject_offset_x.get())
        opts.subject_offset_y = float(self.subject_offset_y.get())
        opts.outline = bool(self.outline.get())
        opts.outline_width = int(self.outline_width.get())
        opts.outline_color = self.outline_color
        opts.shadow_opacity = int(self.shadow_opacity.get())
        opts.shadow_blur = float(self.shadow_blur.get())
        opts.shadow_offset_x = int(self.shadow_offset_x.get())
        opts.shadow_offset_y = int(self.shadow_offset_y.get())
        opts.spill_cleanup = bool(self.spill_cleanup.get())
        opts.spill_strength = int(self.spill_strength.get())
        return opts

    def _save_settings(self):
        super()._save_settings()
        if not hasattr(self, "subject_scale"):
            return
        data = self.settings_store.load()
        data.update(
            {
                "subject_scale": float(self.subject_scale.get()),
                "subject_offset_x": float(self.subject_offset_x.get()),
                "subject_offset_y": float(self.subject_offset_y.get()),
                "outline": bool(self.outline.get()),
                "outline_width": int(self.outline_width.get()),
                "outline_color": self.outline_color,
                "shadow_opacity": int(self.shadow_opacity.get()),
                "shadow_blur": float(self.shadow_blur.get()),
                "shadow_offset_x": int(self.shadow_offset_x.get()),
                "shadow_offset_y": int(self.shadow_offset_y.get()),
                "preview_mode": self.preview_mode.get(),
                "spill_cleanup": bool(self.spill_cleanup.get()),
                "spill_strength": int(self.spill_strength.get()),
            }
        )
        self.settings_store.save(data)

    def _studio_recompose(self):
        self._recompose()
        self._save_settings()
        self._refresh_after_only()

    def _pick_outline_color(self):
        result = colorchooser.askcolor(color=self.outline_color)
        if result and result[1]:
            self.outline_color = result[1]
            self.outline.set(True)
            self._studio_recompose()


    def _studio_mode_label(self, mode: str) -> str:
        try:
            from .studio_v034 import stx
            return stx(self.language.get(), mode)
        except Exception:
            return {
                "cutout": "Cutout",
                "replace": "Replace",
                "blur": "Blur",
                "studio": "Studio",
            }.get(mode, "Cutout")

    def _preset_sticker(self):
        self.outline.set(True)
        self.outline_width.set(8)
        self.outline_color = "#FFFFFF"
        self.shadow.set(False)
        self.background_mode.set("transparent")
        self.studio_mode.set("cutout")
        self.studio_mode_bar.set(self._studio_mode_label("cutout"))
        self._sync_background_menu()
        self._studio_recompose()

    def _preset_product_style(self):
        self.outline.set(False)
        self.shadow.set(True)
        self.shadow_opacity.set(28)
        self.shadow_blur.set(20)
        self.subject_scale.set(0.86)
        self.subject_offset_x.set(0)
        self.subject_offset_y.set(0)
        self.background_mode.set("white")
        self.studio_mode.set("studio")
        self.studio_mode_bar.set(self._studio_mode_label("studio"))
        self._sync_background_menu()
        self._studio_recompose()

    def _preset_portrait_style(self):
        self.outline.set(False)
        self.shadow.set(False)
        self.subject_scale.set(1.0)
        self.subject_offset_x.set(0)
        self.subject_offset_y.set(0)
        self.background_mode.set("blur")
        self.studio_mode.set("blur")
        self.studio_mode_bar.set(self._studio_mode_label("blur"))
        self._sync_background_menu()
        self._studio_recompose()

    def _export_mask(self):
        cutout = self._current_cutout()
        if cutout is None or self.selected_index is None:
            messagebox.showwarning(
                tr(self.language.get(), "error"),
                ptx(self.language.get(), "need_ai"),
            )
            return

        source = self.files[self.selected_index]
        folder = Path(self.output_dir.get()).expanduser()
        destination = folder / f"{source.stem}_mask.png"
        try:
            self.engine.save_mask(cutout, destination)
            self.status_text.set(
                ptx(self.language.get(), "mask_saved", name=destination.name)
            )
            try:
                self.diagnostics.write(
                    "INFO", "mask-export", f"Mask saved | output={destination}", str(source)
                )
            except Exception:
                pass
        except Exception as exc:
            try:
                self.diagnostics.write(
                    "ERROR", "mask-export", f"{type(exc).__name__}: {exc}", str(source)
                )
            except Exception:
                pass
            messagebox.showerror(tr(self.language.get(), "error"), str(exc))
