from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backgroundpxr.studio_v040 import BackgroundPXRStudio040App
from backgroundpxr.ui import create_root


def _font_size(widget) -> int:
    font = widget.cget("font")
    try:
        return abs(int(font.cget("size")))
    except Exception:
        return 0


def _page_fits(page, widgets):
    page.update_idletasks()
    height = page.winfo_height()
    bottoms = [w.winfo_y() + w.winfo_height() for w in widgets]
    return height, max(bottoms, default=0)


def main() -> None:
    root = create_root()
    root.withdraw()
    app = BackgroundPXRStudio040App(root)

    try:
        root.state("normal")
    except Exception:
        pass
    root.geometry("1600x900+0+0")
    root.update_idletasks()

    required = [
        app.before_canvas,
        app.after_canvas,
        app.remove_btn,
        app.restore_btn,
        app.erase_btn,
        app.export_btn,
        app.footer_github,
        app._diag_percent_label,
        app._diag_button,
        app.left_panel,
        app.studio_mode_bar,
        app.studio_modes_label,
        app.filmstrip_toggle,
        app.inspector_tabs,
        app.subject_card,
        app.style_card,
        app.preview_selector,
        app.spill_switch,
        app.spill_strength_slider,
        app.export_mask_btn,
    ]
    assert all(widget is not None and widget.winfo_exists() for widget in required)
    assert app._diag_percent_var.get() == "0%"
    assert app.diagnostics.path.name == "backgroundpxr.log"

    # Left side remains readable on the user's 1600x900 class of display.
    assert app.left_panel.winfo_width() >= 326, (
        f"Left sidebar is too narrow: {app.left_panel.winfo_width()}"
    )
    assert app.clear_btn.winfo_width() >= 80
    clear_parent = app.clear_btn.master
    assert (
        app.clear_btn.winfo_x() + app.clear_btn.winfo_width()
        <= clear_parent.winfo_width() + 2
    )

    # 0.3.4 workflow is retained.
    assert app.studio_mode.get() == "cutout"
    assert len(app.studio_mode_bar.cget("values")) == 4
    assert not app._filmstrip_expanded
    app._toggle_filmstrip()
    root.update_idletasks()
    assert app._filmstrip_expanded
    app._toggle_filmstrip()
    root.update_idletasks()
    assert not app._filmstrip_expanded

    # New Studio Pro inspector uses pages so controls do not need to be crushed.
    assert app.right_panel.winfo_width() >= 420
    assert len(app.inspector_tabs.cget("values")) == 3

    app._show_inspector("ai")
    root.update_idletasks()
    ai_h, ai_bottom = _page_fits(app.ai_page, [app.ai_card, app.refine_card])
    assert ai_bottom <= ai_h, f"AI inspector clipped: {ai_bottom}>{ai_h}"

    app._show_inspector("create")
    root.update_idletasks()
    create_h, create_bottom = _page_fits(
        app.create_page, [app.manual_card, app.subject_card, app.style_card]
    )
    assert create_bottom <= create_h, (
        f"Create inspector clipped: {create_bottom}>{create_h}"
    )

    app._show_inspector("export")
    root.update_idletasks()
    export_h, export_bottom = _page_fits(
        app.export_page, [app.export_card, app.mask_export_card]
    )
    assert export_bottom <= export_h, (
        f"Export inspector clipped: {export_bottom}>{export_h}"
    )

    # New creative controls are wired and usable.
    assert app.subject_scale.get() > 0
    assert app.outline_width.get() >= 1
    assert len(app.preview_selector.cget("values")) == 4
    assert 0 <= app.spill_strength.get() <= 100
    assert app.export_mask_btn.winfo_height() >= 30

    for button in (
        app.remove_btn,
        app.restore_btn,
        app.erase_btn,
        app.export_btn,
        app.process_all_btn,
        app.export_mask_btn,
    ):
        assert button.winfo_width() >= 72
        assert button.winfo_height() >= 20

    readable_widgets = [
        app.files_project,
        app.add_images_btn,
        app.add_folder_btn,
        app.project_files,
        app.studio_modes_label,
        app.studio_mode_bar,
        app.pro_title,
        app.inspector_tabs,
        app.subject_title,
        app.style_title,
        app.spill_switch,
        app.spill_strength_label,
        app.export_title,
        app.status_label,
        app._diag_button,
        app.filmstrip_toggle,
    ]
    for widget in readable_widgets:
        assert _font_size(widget) >= 9, (
            f"Unreadably small font on {widget}: {_font_size(widget)}pt"
        )

    root.destroy()
    print("BackgroundPXR Studio Pro 0.4 smoke test passed")


if __name__ == "__main__":
    main()
