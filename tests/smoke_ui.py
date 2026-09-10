from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backgroundpxr.pro_ui import BackgroundPXRProApp
from backgroundpxr.ui import create_root


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
    ]
    assert all(widget.winfo_exists() for widget in required)
    assert app._diag_percent_var.get() == "0%"
    assert app.diagnostics.path.name == "backgroundpxr.log"

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

    root.destroy()
    print("BackgroundPXR professional 1600x900 UI smoke test passed")


if __name__ == "__main__":
    main()
