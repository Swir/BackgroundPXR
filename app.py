from __future__ import annotations

import sys
from importlib.metadata import version


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
        runtime_self_test()
        return

    from backgroundpxr.pro_ui import BackgroundPXRProApp
    from backgroundpxr.ui import create_root

    root = create_root()
    BackgroundPXRProApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
