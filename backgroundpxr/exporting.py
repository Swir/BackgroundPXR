from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from pathlib import Path

from PIL import Image

from .engine import BackgroundEngine, output_path_for


_INVALID_FILENAME_CHARS = '<>:"/\\|?*'


def _output_key(path: str | Path) -> str:
    """Return a deterministic Windows-safe comparison key for an output path."""
    absolute = os.path.abspath(os.fspath(Path(path).expanduser()))
    return absolute.replace("\\", "/").casefold()


def _safe_suffix(suffix: str) -> str:
    cleaned = (suffix or "").strip()
    cleaned = "".join(char for char in cleaned if char not in _INVALID_FILENAME_CHARS)
    return cleaned or "_pxr"


def reserve_output_path(
    source: str | Path,
    output_dir: str | Path,
    export_format: str,
    suffix: str = "_pxr",
    reserved: set[str] | None = None,
) -> Path:
    """Allocate a safe, collision-free export path.

    Invalid-only suffixes fall back to ``_pxr`` so an export can never collapse
    to the source filename when the output directory is the source directory.
    Within batch export, same-stem inputs receive numbered names rather than
    silently overwriting an earlier result. Comparison is case-insensitive to
    match Windows filesystem behaviour.
    """
    base = output_path_for(source, output_dir, export_format, _safe_suffix(suffix))
    source_key = _output_key(source)
    if _output_key(base) == source_key:
        # Defensive fallback for future output-format/suffix changes.
        base = output_path_for(source, output_dir, export_format, "_pxr")

    if reserved is None:
        return base

    candidate = base
    counter = 2
    while _output_key(candidate) in reserved:
        candidate = base.with_name(f"{base.stem}_{counter}{base.suffix}")
        counter += 1
    reserved.add(_output_key(candidate))
    return candidate


def _atomic_write(destination: str | Path, writer: Callable[[Path], None]) -> Path:
    """Write beside the destination and atomically replace it only on success."""
    path = Path(destination).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}.",
        suffix=f"{path.suffix}.tmp",
        dir=path.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        writer(temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


class AtomicBackgroundEngine(BackgroundEngine):
    """Background engine whose user-facing exports never expose partial files."""

    @staticmethod
    def save(image: Image.Image, destination: str | Path, export_format: str) -> Path:
        return _atomic_write(
            destination,
            lambda temporary: BackgroundEngine.save(image, temporary, export_format),
        )

    @staticmethod
    def save_mask(
        cutout: Image.Image,
        destination: str | Path,
        invert: bool = False,
    ) -> Path:
        return _atomic_write(
            destination,
            lambda temporary: BackgroundEngine.save_mask(cutout, temporary, invert=invert),
        )
