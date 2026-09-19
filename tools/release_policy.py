from __future__ import annotations

import argparse
import re


class ReleasePolicyError(RuntimeError):
    """Raised when a version is not eligible for a public BackgroundPXR release."""


_FINAL_VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def validate_final_release_version(version: str, *, minimum_major: int = 1) -> tuple[int, int, int]:
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate that a BackgroundPXR version may be published publicly"
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--minimum-major", type=int, default=1)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        validate_final_release_version(args.version, minimum_major=args.minimum_major)
    except ReleasePolicyError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"BackgroundPXR release policy: OK ({args.version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
