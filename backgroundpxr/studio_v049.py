from __future__ import annotations

from .studio_v048 import BackgroundPXRStudio048App


class BackgroundPXRStudio049App(BackgroundPXRStudio048App):
    """Studio Pro with a responsive compact inspector for short desktops.

    A 1280x720 logical Windows desktop leaves substantially less vertical work
    area than 1600x900. Keep every editor action visible without shrinking text
    below the project's 9pt accessibility floor by removing secondary card
    subtitles and tightening only non-essential spacing on short screens.
    """

    COMPACT_SCREEN_HEIGHT = 720

    def _build_right(self, parent):
        super()._build_right(parent)
        self._compact_inspector = (
            int(self.root.winfo_screenheight()) <= self.COMPACT_SCREEN_HEIGHT
        )
        if self._compact_inspector:
            self._apply_compact_inspector_layout()

    def _apply_compact_inspector_layout(self) -> None:
        # Preserve every control and its font size. Secondary explanatory copy
        # is the first thing to yield when vertical space is constrained.
        self.pro_title.configure(height=18)
        self.pro_title.grid_configure(pady=(4, 1))
        self.inspector_tabs.configure(height=28)
        self.inspector_tabs.grid_configure(pady=(0, 4))

        for card in (self.manual_card, self.subject_card, self.style_card):
            card.grid_configure(pady=(2, 0))

        for title_name, subtitle_name in (
            ("manual_title", "manual_sub"),
            ("subject_title", "subject_sub"),
            ("style_title", "style_sub"),
        ):
            title = getattr(self, title_name, None)
            subtitle = getattr(self, subtitle_name, None)
            if subtitle is not None:
                subtitle.grid_remove()
            if title is not None:
                # The title's parent is the shared icon/title header frame.
                title.master.grid_configure(pady=(3, 1))

        # Recover a few additional pixels from decorative gaps, not controls.
        self.brush_size_slider.master.grid_configure(pady=(0, 3))
        self.subject_scale_label.master.grid_configure(pady=(1, 4))
        self.subject_scale_slider.grid_configure(pady=(0, 3))
        self.outline_width_label.grid_configure(pady=(3, 0))
        self.preview_label.grid_configure(pady=(3, 1))
        self.style_presets.grid_configure(pady=(4, 5))
        self.wipe_frame.grid_configure(pady=(4, 5))
