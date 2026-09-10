from __future__ import annotations

import sys
import traceback
from importlib.metadata import version
from pathlib import Path


def runtime_self_test() -> None:
    """Fail fast if a frozen Windows build is missing AI runtime metadata."""
    import onnxruntime  # noqa: F401
    import pymatting  # noqa: F401
    import rembg  # noqa: F401

    # pymatting imports its own version through importlib.metadata, which is
    # exactly what failed in the 0.3.1 portable release.
    version("pymatting")
    version("rembg")
    version("onnxruntime")


def main() -> None:
    if "--self-test-runtime" in sys.argv:
        report = Path.cwd() / "backgroundpxr_runtime_selftest.txt"
        try:
            runtime_self_test()
            report.write_text("OK\n", encoding="utf-8")
            return
        except Exception:
            report.write_text(traceback.format_exc(), encoding="utf-8")
            raise SystemExit(23)

    from backgroundpxr.pro_ui import BackgroundPXRProApp
    from backgroundpxr.ui import create_root

    root = create_root()
    BackgroundPXRProApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
