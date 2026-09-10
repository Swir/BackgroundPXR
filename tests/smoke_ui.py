from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backgroundpxr.diagnostics import BackgroundPXRDiagnosticsApp
from backgroundpxr.ui import create_root


def main() -> None:
    root = create_root()
    root.withdraw()
    app = BackgroundPXRDiagnosticsApp(root)
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
    ]
    assert all(widget.winfo_exists() for widget in required)
    assert app._diag_percent_var.get() == "0%"
    assert app.diagnostics.path.name == "backgroundpxr.log"

    root.destroy()
    print("BackgroundPXR diagnostics UI smoke test passed")


if __name__ == "__main__":
    main()
