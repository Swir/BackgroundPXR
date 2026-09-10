from __future__ import annotations

import os
import sys
import traceback
from importlib.metadata import version
from pathlib import Path

# PyInstaller --windowed applications on Windows normally start with
# sys.stdout/sys.stderr set to None. rembg -> pooch -> tqdm expects stderr to
# be a writable stream while downloading a model for the first time. Keep the
# replacement streams alive for the whole process so model downloads never
# crash with: AttributeError: 'NoneType' object has no attribute 'write'.
_FALLBACK_STREAMS = []


def ensure_writable_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and callable(getattr(stream, "write", None)):
            continue
        fallback = open(os.devnull, "w", encoding="utf-8", errors="replace")
        setattr(sys, name, fallback)
        _FALLBACK_STREAMS.append(fallback)


def runtime_self_test() -> None:
    """Fail fast if a frozen Windows build is missing the real AI runtime."""
    ensure_writable_stdio()
    assert sys.stdout is not None and callable(getattr(sys.stdout, "write", None))
    assert sys.stderr is not None and callable(getattr(sys.stderr, "write", None))

    import onnxruntime  # noqa: F401
    import pymatting  # noqa: F401
    import rembg  # noqa: F401
    from tqdm import tqdm

    version("pymatting")
    version("rembg")
    version("onnxruntime")

    # Reproduce the exact writer used by pooch while rembg downloads a model.
    probe = tqdm(total=1, file=sys.stderr, leave=False, desc="PXR runtime")
    probe.update(1)
    probe.close()


def main() -> None:
    ensure_writable_stdio()

    if "--self-test-runtime" in sys.argv:
        report = Path.cwd() / "backgroundpxr_runtime_selftest.txt"
        try:
            runtime_self_test()
            report.write_text("OK\n", encoding="utf-8")
            return
        except Exception:
            report.write_text(traceback.format_exc(), encoding="utf-8")
            raise SystemExit(23)

    from backgroundpxr.studio_v034 import BackgroundPXRStudio034App
    from backgroundpxr.ui import create_root

    root = create_root()
    BackgroundPXRStudio034App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
