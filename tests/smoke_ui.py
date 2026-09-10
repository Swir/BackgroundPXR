from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backgroundpxr.pro_ui import BackgroundPXRProApp
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
    app = BackgroundPXRProApp(root)

    # Reproduce the user's 1600x900 workspace instead of validating only an
    # arbitrary CI desktop size.
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
        app.ai_card,
        app.refine_card,
        app.manual_card,
        app.export_card,
        app.left_panel,
    ]
    assert all(widget is not None and widget.winfo_exists() for widget in required)
    assert app._diag_percent_var.get() == "0%"
    assert app.diagnostics.path.name == "backgroundpxr.log"

    # The left project sidebar must stay wide enough for Polish text instead of
    # clipping labels/buttons at the right edge.
    assert app.left_panel.winfo_width() >= 300, "Left sidebar is too narrow at 1600x900"
    assert app.clear_btn.winfo_width() >= 75, "Clear button is being clipped"
    clear_parent = app.clear_btn.master
    assert app.clear_btn.winfo_x() + app.clear_btn.winfo_width() <= clear_parent.winfo_width() + 2, (
        "Clear button extends beyond its header"
    )

    # The four studio cards must be fully visible and may never overlap.
    cards = [app.ai_card, app.refine_card, app.manual_card, app.export_card]
    for upper, lower in zip(cards, cards[1:]):
        assert upper.winfo_y() + upper.winfo_height() <= lower.winfo_y(), (
            f"Studio cards overlap: {upper} -> {lower}"
        )
    assert app.export_card.winfo_y() + app.export_card.winfo_height() <= app.right_panel.winfo_height(), (
        "Export card extends beyond the visible right panel at 1600x900"
    )

    # Primary controls must remain usable rather than being crushed to a few pixels.
    for button in (app.remove_btn, app.restore_btn, app.erase_btn, app.export_btn, app.process_all_btn):
        assert button.winfo_width() >= 72
        assert button.winfo_height() >= 20

    # 0.3.2 contained multiple 7pt labels. Keep important UI text readable.
    readable_widgets = [
        app.files_project,
        app.add_images_btn,
        app.add_folder_btn,
        app.project_files,
        app.ai_title,
        app.model_label,
        app.manual_title,
        app.restore_btn,
        app.export_title,
        app.status_label,
        app._diag_button,
    ]
    for widget in readable_widgets:
        assert _font_size(widget) >= 9, f"Unreadably small font on {widget}: {_font_size(widget)}pt"

    root.destroy()
    print("BackgroundPXR readable 1600x900 UI smoke test passed")


if __name__ == "__main__":
    main()
