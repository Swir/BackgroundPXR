from __future__ import annotations

import sys
from pathlib import Path

# Running this file directly makes /tests the first import root. Add the
# repository root explicitly so the smoke test imports the same local package
# that PyInstaller will package for the Windows release.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backgroundpxr.ui import BackgroundPXRApp, create_root


def main() -> None:
    root = create_root()
    root.withdraw()
    app = BackgroundPXRApp(root)
    root.update_idletasks()

    # Verify the key v0.3.0 studio widgets were actually constructed.
    required = [
        app.before_canvas,
        app.after_canvas,
        app.remove_btn,
        app.restore_btn,
        app.erase_btn,
        app.export_btn,
        app.footer_github,
    ]
    assert all(widget.winfo_exists() for widget in required)

    root.destroy()
    print("BackgroundPXR UI smoke test passed")


if __name__ == "__main__":
    main()
