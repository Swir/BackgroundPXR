from __future__ import annotations

import argparse
import re
from pathlib import Path


class ReleasePolicyError(RuntimeError):
    """Raised when a version is not eligible for a public BackgroundPXR release."""


_FINAL_VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_ROADMAP_ITEM_RE = re.compile(r"^- \[(?P<state>[ xX])\]\s+", re.MULTILINE)


def validate_final_release_version(
    version: str, *, minimum_major: int = 1
) -> tuple[int, int, int]:
    """Return a parsed final release version or raise ReleasePolicyError.

    Public GitHub Releases must use a plain numeric X.Y.Z version. Pre-release
    identifiers such as rc/beta are deliberately rejected so qualification
    candidates can be built and tested without becoming public releases.
    """
    match = _FINAL_VERSION_RE.fullmatch(version)
    if not match:
        raise ReleasePolicyError(
            f"Refusing public release: {version!r} is not a final X.Y.Z version."
        )

    parsed = tuple(int(part) for part in match.groups())
    if parsed[0] < minimum_major:
        raise ReleasePolicyError(
            f"Refusing pre-{minimum_major}.0 public release for BackgroundPXR {version}."
        )
    return parsed


def _validate_1_0_roadmap(roadmap_text: str) -> None:
    states = [match.group("state").lower() == "x" for match in _ROADMAP_ITEM_RE.finditer(roadmap_text)]
    if len(states) != 10:
        raise ReleasePolicyError(
            "Refusing BackgroundPXR 1.0 release: ROADMAP_1_0.md must contain exactly "
            f"10 canonical acceptance items, found {len(states)}."
        )
    if not all(states[:9]):
        first_open = next(index for index, checked in enumerate(states[:9], start=1) if not checked)
        raise ReleasePolicyError(
            "Refusing BackgroundPXR 1.0 release: canonical acceptance item "
            f"{first_open} is still unchecked; items 1-9 must pass before publication."
        )
    if states[9]:
        raise ReleasePolicyError(
            "Refusing BackgroundPXR 1.0 release: acceptance item 10 includes publication "
            "and post-release smoke verification, so it must remain unchecked until after "
            "the GitHub Release succeeds."
        )


def _validate_release_notes(version: str, release_notes_text: str) -> None:
    heading = re.compile(
        rf"^# BackgroundPXR {re.escape(version)}(?:\s|$)",
        re.MULTILINE,
    )
    if not heading.search(release_notes_text):
        raise ReleasePolicyError(
            "Refusing public release: RELEASE_NOTES.md does not contain a top-level "
            f"BackgroundPXR {version} section."
        )


def validate_public_release_readiness(
    version: str,
    *,
    minimum_major: int = 1,
    roadmap_text: str | None = None,
    release_notes_text: str | None = None,
) -> tuple[int, int, int]:
    """Validate the final public-release gate for BackgroundPXR.

    Version syntax is always enforced. The first 1.0 publication additionally
    requires explicit repository evidence that canonical acceptance items 1-9
    are complete while item 10 (publish + post-release smoke) is still open, and
    release notes must already identify the exact final version.
    """
    parsed = validate_final_release_version(version, minimum_major=minimum_major)

    if parsed == (1, 0, 0):
        if roadmap_text is None:
            raise ReleasePolicyError(
                "Refusing BackgroundPXR 1.0 release: ROADMAP_1_0.md evidence is required."
            )
        if release_notes_text is None:
            raise ReleasePolicyError(
                "Refusing BackgroundPXR 1.0 release: RELEASE_NOTES.md evidence is required."
            )
        _validate_1_0_roadmap(roadmap_text)
        _validate_release_notes(version, release_notes_text)
    elif release_notes_text is not None:
        _validate_release_notes(version, release_notes_text)

    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate that a BackgroundPXR version may be published publicly"
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--minimum-major", type=int, default=1)
    parser.add_argument(
        "--roadmap",
        type=Path,
        help="Canonical ROADMAP_1_0.md used to prove the 1.0 pre-publication gate.",
    )
    parser.add_argument(
        "--release-notes",
        type=Path,
        help="Release notes that must identify the exact final version.",
    )
    return parser


def _read_text(path: Path | None, label: str) -> str | None:
    if path is None:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReleasePolicyError(f"Cannot read {label}: {path}: {exc}") from exc


def main() -> int:
    args = _parser().parse_args()
    try:
        validate_public_release_readiness(
            args.version,
            minimum_major=args.minimum_major,
            roadmap_text=_read_text(args.roadmap, "roadmap"),
            release_notes_text=_read_text(args.release_notes, "release notes"),
        )
    except ReleasePolicyError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"BackgroundPXR release policy: OK ({args.version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
