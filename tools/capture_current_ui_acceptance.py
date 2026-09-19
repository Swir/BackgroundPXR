from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import backgroundpxr.studio_v050 as studio_v050
from backgroundpxr.studio_v051 import BackgroundPXRStudio051App
from tools import capture_ui_acceptance as capture


# Keep the evidence harness reusable while making this wrapper follow the exact
# production Studio class selected by app.py.
studio_v050.BackgroundPXRStudio050App = BackgroundPXRStudio051App
_original_capture_window = capture._capture_window


def _capture_after_resize_settles(root, destination: Path) -> None:
    """Allow the production resize debounce to run before preserving evidence."""
    _original_capture_window(root, destination)
    root.update_idletasks()
    root.update()
    _original_capture_window(root, destination)


capture._capture_window = _capture_after_resize_settles


if __name__ == "__main__":
    raise SystemExit(capture.main())
