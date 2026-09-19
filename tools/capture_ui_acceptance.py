from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backgroundpxr import APP_NAME, __version__
from backgroundpxr.display import (
    WINDOWS_TK_BASE_SCALING,
    effective_ui_screen,
    enable_windows_dpi_awareness,
    plan_window,
)


_SIZE_RE = re.compile(r"^(\d{3,5})x(\d{3,5})$")


def parse_size(value: str) -> tuple[int, int]:
    """Parse and validate a Windows acceptance desktop size."""
    match = _SIZE_RE.fullmatch(value.strip().lower())
    if not match:
        raise ValueError(f"Invalid size {value!r}; expected WIDTHxHEIGHT")
    width, height = (int(part) for part in match.groups())
    if width < 1024 or height < 640:
        raise ValueError(
            f"Acceptance size {value!r} is below the supported 1024x640 floor"
        )
    return width, height


def safe_label(value: str) -> str:
    """Return a deterministic filesystem-safe evidence label."""
    label = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._")
    return label or "ui-evidence"


def build_review_checklist(record: dict[str, object]) -> str:
    """Create the human-review witness that accompanies automated screenshots."""
    screenshots = record.get("screenshots", [])
    lines = [
        "# BackgroundPXR Windows UI acceptance evidence",
        "",
        "This package is automated visual evidence only. The roadmap HiDPI/manual UX item",
        "must remain unchecked until these captures are visually reviewed and the reviewer",
        "records a pass with no release-blocking clipping, overlap, unreadable text or broken workflow.",
        "",
        f"- Commit: `{record.get('commit', 'unknown')}`",
        f"- App version: `{record.get('app_version', 'unknown')}`",
        f"- Desktop: `{record.get('screen', {}).get('actual', 'unknown') if isinstance(record.get('screen'), dict) else 'unknown'}`",
        f"- Requested UI scale: `{record.get('ui_scale', {}).get('requested', 'unknown') if isinstance(record.get('ui_scale'), dict) else 'unknown'}`",
        f"- Detected UI scale: `{record.get('ui_scale', {}).get('detected', 'unknown') if isinstance(record.get('ui_scale'), dict) else 'unknown'}`",
        f"- DPI mode: `{record.get('dpi_status', 'unknown')}`",
        "",
        "## Required visual review",
        "",
        "- [ ] AI inspector is fully readable; Remove button and diagnostics controls are visible.",
        "- [ ] Create inspector is fully readable; Restore/Erase, subject and style controls do not overlap.",
        "- [ ] Export inspector is fully readable; image and mask export actions are visible.",
        "- [ ] Compare/wipe view remains usable and does not overlap Studio controls.",
        "- [ ] Reduced-window capture remains usable with footer branding visible.",
        "- [ ] Permanent `by Swir` and `github.com/Swir` branding is visible and unclipped.",
        "- [ ] No screenshot shows critical clipping, overlap, blank panels or unreadably small text.",
        "",
        "## Captures",
        "",
    ]
    for item in screenshots if isinstance(screenshots, list) else []:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Reviewer result",
            "",
            "- Reviewer: ",
            "- Review date: ",
            "- Result: `PENDING`",
            "- Notes: ",
            "",
        ]
    )
    return "\n".join(lines)


def _capture_window(root, destination: Path) -> None:
    from PIL import ImageGrab

    root.update_idletasks()
    root.update()
    time.sleep(0.15)
    x = int(root.winfo_rootx())
    y = int(root.winfo_rooty())
    width = int(root.winfo_width())
    height = int(root.winfo_height())
    if width < 100 or height < 100:
        raise RuntimeError(f"Refusing invalid capture geometry {width}x{height}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    image = ImageGrab.grab(
        bbox=(x, y, x + width, y + height),
        all_screens=True,
    )
    image.save(destination, format="PNG")
    if not destination.is_file() or destination.stat().st_size < 1024:
        raise RuntimeError(f"UI evidence capture is missing or too small: {destination}")


def capture_acceptance(
    *,
    target_size: tuple[int, int],
    ui_scale: float,
    output_dir: Path,
    label: str,
) -> dict[str, object]:
    """Capture a deterministic Studio Pro visual-evidence set on Windows."""
    if sys.platform != "win32":
        raise RuntimeError("Windows UI acceptance capture must run on Windows")
    if not 1.0 <= ui_scale <= 2.0:
        raise ValueError("UI scale must be within the supported 1.0-2.0 acceptance range")

    # Match the production startup order: choose DPI awareness before Tk creates
    # the first native window, then let the Studio use its normal responsive logic.
    dpi_status = enable_windows_dpi_awareness()
    from backgroundpxr.studio_v050 import BackgroundPXRStudio050App
    from backgroundpxr.ui import create_root

    root = create_root()
    screenshots: list[str] = []
    try:
        root.tk.call("tk", "scaling", WINDOWS_TK_BASE_SCALING * ui_scale)
        root.withdraw()
        app = BackgroundPXRStudio050App(root)

        actual_screen = (int(root.winfo_screenwidth()), int(root.winfo_screenheight()))
        if actual_screen != target_size:
            raise RuntimeError(
                f"Acceptance desktop mismatch: actual={actual_screen}, expected={target_size}"
            )

        effective_width, effective_height, detected_scale = effective_ui_screen(root)
        if abs(detected_scale - ui_scale) > 0.03:
            raise RuntimeError(
                f"UI scale mismatch: detected={detected_scale:.3f}, requested={ui_scale:.3f}"
            )

        placement = plan_window(*target_size)
        root.deiconify()
        try:
            root.state("normal")
        except Exception:
            pass
        root.geometry(placement.geometry)
        root.update_idletasks()
        root.update()
        try:
            root.attributes("-topmost", True)
            root.lift()
            root.focus_force()
        except Exception:
            pass

        restored_size = (int(root.winfo_width()), int(root.winfo_height()))
        page_steps = (
            ("ai", "ai"),
            ("create", "create"),
            ("export", "export"),
        )
        for page, capture_name in page_steps:
            app._show_inspector(page)
            root.update_idletasks()
            path = output_dir / f"{safe_label(label)}-{capture_name}.png"
            _capture_window(root, path)
            screenshots.append(path.name)

        app._show_inspector("create")
        app._on_preview_mode(app._preview_label("compare"))
        root.update_idletasks()
        compare_path = output_dir / f"{safe_label(label)}-create-compare.png"
        _capture_window(root, compare_path)
        screenshots.append(compare_path.name)
        app._on_preview_mode(app._preview_label("result"))

        # Capture the supported minimum window as visual resize evidence. The
        # existing smoke gate still checks the broader reduced-desktop matrix.
        root.geometry(
            f"{placement.min_width}x{placement.min_height}+{placement.x}+{placement.y}"
        )
        root.update_idletasks()
        root.update()
        app._show_inspector("create")
        reduced_path = output_dir / f"{safe_label(label)}-reduced-create.png"
        _capture_window(root, reduced_path)
        screenshots.append(reduced_path.name)
        reduced_size = (int(root.winfo_width()), int(root.winfo_height()))

        branding_text = str(app.footer_github.cget("text"))
        record: dict[str, object] = {
            "schema": 1,
            "app": APP_NAME,
            "app_version": __version__,
            "commit": os.environ.get("GITHUB_SHA", "local"),
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "review_status": "pending-visual-review",
            "screen": {
                "requested": f"{target_size[0]}x{target_size[1]}",
                "actual": f"{actual_screen[0]}x{actual_screen[1]}",
                "effective": f"{effective_width}x{effective_height}",
            },
            "ui_scale": {
                "requested": round(ui_scale, 2),
                "detected": round(detected_scale, 3),
            },
            "dpi_status": dpi_status,
            "window": {
                "restored": f"{restored_size[0]}x{restored_size[1]}",
                "reduced": f"{reduced_size[0]}x{reduced_size[1]}",
                "minimum_policy": f"{placement.min_width}x{placement.min_height}",
                "compact_inspector": bool(app._compact_inspector),
            },
            "branding_probe": branding_text,
            "screenshots": screenshots,
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = output_dir / f"{safe_label(label)}-evidence.json"
        metadata_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        checklist_path = output_dir / f"{safe_label(label)}-review.md"
        checklist_path.write_text(build_review_checklist(record), encoding="utf-8")
        return record
    finally:
        try:
            root.destroy()
        except Exception:
            pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture BackgroundPXR Windows Studio Pro UI acceptance evidence"
    )
    parser.add_argument("--size", default="1600x900", help="Acceptance desktop WIDTHxHEIGHT")
    parser.add_argument("--ui-scale", type=float, default=1.0, help="Windows UI scale multiplier")
    parser.add_argument("--output-dir", type=Path, default=Path("ui_evidence"))
    parser.add_argument("--label", default="windows-ui")
    return parser


def main() -> int:
    args = _parser().parse_args()
    target_size = parse_size(args.size)
    record = capture_acceptance(
        target_size=target_size,
        ui_scale=args.ui_scale,
        output_dir=args.output_dir,
        label=args.label,
    )
    print(
        "BackgroundPXR UI evidence captured: "
        f"{len(record['screenshots'])} screenshots, "
        f"scale={record['ui_scale']}, screen={record['screen']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
