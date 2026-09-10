from __future__ import annotations

import os
import sys
import traceback
from importlib.metadata import version
from pathlib import Path

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

    from backgroundpxr.studio_v034_fix import BackgroundPXRStudio034FixedApp
    from backgroundpxr.ui import create_root

    root = create_root()
    BackgroundPXRStudio034FixedApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
