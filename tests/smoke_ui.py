from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backgroundpxr.studio_v034 import BackgroundPXRStudio034App
from backgroundpxr.ui import create_root


def _font_size(widget) -> int:
    font = widget.cget("font")
    try:
        return abs(int(font.cget("size")))
    except Exception:
        return 0


def main() -> None:
    root = create_root()
    root.withdraw()
    app = BackgroundPXRStudio034App(root)

    try:
        root.state("normal")
    except Exception:
        pass
    root.geometry("1600x900+0+0")
    root.update_idletasks()

    required = [
        app.before_canvas, app.after_canvas, app.remove_btn, app.restore_btn,
        app.erase_btn, app.export_btn, app.footer_github, app._diag_percent_label,
        app._diag_button, app.ai_card, app.refine_card, app.manual_card,
        app.export_card, app.left_panel, app.studio_mode_bar,
        app.studio_modes_label, app.filmstrip_toggle,
    ]
    assert all(widget is not None and widget.winfo_exists() for widget in required)
    assert app._diag_percent_var.get() == "0%"
    assert app.diagnostics.path.name == "backgroundpxr.log"

    # Left project area must remain readable and wide enough for Polish labels.
    assert app.left_panel.winfo_width() >= 326, "Left sidebar is too narrow at 1600x900"
    assert app.clear_btn.winfo_width() >= 80, "Clear button is being clipped"
    clear_parent = app.clear_btn.master
    assert app.clear_btn.winfo_x() + app.clear_btn.winfo_width() <= clear_parent.winfo_width() + 2, "Clear button extends beyond its header"

    # The new Studio mode control must be present and default to Cutout.
    assert app.studio_mode.get() == "cutout"
    assert len(app.studio_mode_bar.cget("values")) == 4

    # Filmstrip is collapsed by default to recover vertical room. Expanding it
    # must remain possible without destroying the preview canvas.
    assert not app._filmstrip_expanded
    assert app.filmstrip_strip.cget("height") <= 40
    app._toggle_filmstrip()
    root.update_idletasks()
    assert app._filmstrip_expanded
    assert app.filmstrip_strip.cget("height") >= 80
    app._toggle_filmstrip()
    root.update_idletasks()
    assert not app._filmstrip_expanded

    # The whole right-side Studio stack must fit with additional bottom safety.
    cards = [app.ai_card, app.refine_card, app.manual_card, app.export_card]
    geometry = [(card.winfo_y(), card.winfo_height()) for card in cards]
    print(f"right_panel height={app.right_panel.winfo_height()} card_geometry={geometry}")
    for upper, lower in zip(cards, cards[1:]):
        assert upper.winfo_y() + upper.winfo_height() <= lower.winfo_y(), f"Studio cards overlap: {upper} -> {lower}; {geometry}"
    export_bottom = app.export_card.winfo_y() + app.export_card.winfo_height()
    safety = app.right_panel.winfo_height() - export_bottom
    assert safety >= 30, (
        f"Not enough bottom safety: {safety}px; bottom={export_bottom}, "
        f"panel={app.right_panel.winfo_height()}, cards={geometry}"
    )

    for button in (app.remove_btn, app.restore_btn, app.erase_btn, app.export_btn, app.process_all_btn):
        assert button.winfo_width() >= 72
        assert button.winfo_height() >= 20

    readable_widgets = [
        app.files_project, app.add_images_btn, app.add_folder_btn, app.project_files,
        app.studio_modes_label, app.studio_mode_bar, app.ai_title, app.model_label,
        app.manual_title, app.restore_btn, app.export_title, app.status_label,
        app._diag_button, app.filmstrip_toggle,
    ]
    for widget in readable_widgets:
        assert _font_size(widget) >= 9, f"Unreadably small font on {widget}: {_font_size(widget)}pt"

    root.destroy()
    print("BackgroundPXR AI Background Studio 0.3.4 smoke test passed")


if __name__ == "__main__":
    main()
