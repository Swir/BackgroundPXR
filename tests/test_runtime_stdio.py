from __future__ import annotations

import sys

from app import ensure_writable_stdio


def test_windowed_exe_gets_writable_stdout_and_stderr():
    old_out, old_err = sys.stdout, sys.stderr
    replacements = []
    try:
        sys.stdout = None
        sys.stderr = None
        ensure_writable_stdio()

        assert sys.stdout is not None
        assert sys.stderr is not None
        assert callable(getattr(sys.stdout, "write", None))
        assert callable(getattr(sys.stderr, "write", None))

        # Reproduce the operation tqdm/pooch needs during first model download.
        sys.stderr.write("")
        sys.stderr.flush()
        replacements = [sys.stdout, sys.stderr]
    finally:
        sys.stdout, sys.stderr = old_out, old_err
        for stream in replacements:
            try:
                stream.close()
            except Exception:
                pass
