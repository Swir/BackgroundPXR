from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from pathlib import Path, PurePosixPath


class PackageVerificationError(RuntimeError):
    """Raised when a Windows release package fails a release-safety check."""


_REQUIRED_FILES = {
    "backgroundpxr/backgroundpxr.exe",
    "backgroundpxr/build_info.txt",
    "backgroundpxr/readme.md",
    "backgroundpxr/release_notes.md",
}
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_SOURCE_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_ALLOWED_BUILD_CHANNELS = {"qualification", "release"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_member(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise PackageVerificationError(f"Unsafe ZIP member path: {name!r}")
    if path.parts and ":" in path.parts[0]:
        raise PackageVerificationError(f"Unsafe ZIP member path: {name!r}")
    return "/".join(path.parts)


def _read_checksum(sidecar: Path, archive_name: str) -> str:
    if not sidecar.is_file():
        raise PackageVerificationError(f"Missing checksum sidecar: {sidecar}")
    parts = sidecar.read_text(encoding="utf-8-sig").strip().split()
    if len(parts) != 2:
        raise PackageVerificationError("SHA-256 sidecar must contain exactly a digest and filename")
    digest, filename = parts
    filename = filename.lstrip("*")
    if not _SHA256_RE.fullmatch(digest):
        raise PackageVerificationError("SHA-256 sidecar contains an invalid digest")
    if filename != archive_name:
        raise PackageVerificationError(
            f"SHA-256 sidecar names {filename!r}, expected {archive_name!r}"
        )
    return digest.lower()


def _read_build_info(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        key, separator, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not separator or not key or not value:
            raise PackageVerificationError(f"Invalid BUILD_INFO line: {raw_line!r}")
        if key in fields:
            raise PackageVerificationError(f"Duplicate BUILD_INFO field: {key}")
        fields[key] = value

    missing = sorted({"version", "source_sha", "channel"} - fields.keys())
    if missing:
        raise PackageVerificationError(
            "BUILD_INFO is missing required fields: " + ", ".join(missing)
        )
    if not _SOURCE_SHA_RE.fullmatch(fields["source_sha"]):
        raise PackageVerificationError("BUILD_INFO source_sha must be a 40-character Git SHA")
    if fields["channel"] not in _ALLOWED_BUILD_CHANNELS:
        raise PackageVerificationError(
            "BUILD_INFO channel must be qualification or release"
        )
    return fields


def verify_release_package(
    archive: Path,
    checksum: Path,
    version: str,
    *,
    source_sha: str | None = None,
) -> None:
    """Validate a portable Windows package before it can become release evidence.

    The verifier is intentionally independent of PyInstaller. It checks the final
    ZIP that users receive: deterministic naming, checksum integrity, safe member
    paths, required executable/documentation files, exact build provenance,
    version coherence and the permanent SWIR author branding.
    """
    archive = Path(archive)
    checksum = Path(checksum)
    expected_archive_name = f"BackgroundPXR-{version}-Windows.zip"
    expected_checksum_name = f"{expected_archive_name}.sha256"

    if archive.name != expected_archive_name:
        raise PackageVerificationError(
            f"Unexpected archive name {archive.name!r}; expected {expected_archive_name!r}"
        )
    if checksum.name != expected_checksum_name:
        raise PackageVerificationError(
            f"Unexpected checksum name {checksum.name!r}; expected {expected_checksum_name!r}"
        )
    if not archive.is_file() or archive.stat().st_size == 0:
        raise PackageVerificationError(f"Release archive is missing or empty: {archive}")

    if source_sha is not None and not _SOURCE_SHA_RE.fullmatch(source_sha):
        raise PackageVerificationError("Expected source SHA must be a 40-character Git SHA")

    expected_digest = _read_checksum(checksum, archive.name)
    actual_digest = _sha256(archive)
    if actual_digest != expected_digest:
        raise PackageVerificationError(
            f"SHA-256 mismatch for {archive.name}: expected {expected_digest}, got {actual_digest}"
        )

    try:
        with zipfile.ZipFile(archive) as bundle:
            infos = [info for info in bundle.infolist() if not info.is_dir()]
            normalized: dict[str, zipfile.ZipInfo] = {}
            for info in infos:
                member = _normalize_member(info.filename)
                key = member.lower()
                if key in normalized:
                    raise PackageVerificationError(
                        f"Duplicate or case-colliding ZIP member: {info.filename!r}"
                    )
                normalized[key] = info

            missing = sorted(_REQUIRED_FILES - normalized.keys())
            if missing:
                raise PackageVerificationError(
                    "Release package is missing required files: " + ", ".join(missing)
                )

            exe = normalized["backgroundpxr/backgroundpxr.exe"]
            if exe.file_size <= 0:
                raise PackageVerificationError("BackgroundPXR.exe is empty")

            readme = bundle.read(normalized["backgroundpxr/readme.md"]).decode("utf-8-sig")
            notes = bundle.read(normalized["backgroundpxr/release_notes.md"]).decode(
                "utf-8-sig"
            )
            build_info_text = bundle.read(normalized["backgroundpxr/build_info.txt"]).decode(
                "utf-8-sig"
            )
    except zipfile.BadZipFile as exc:
        raise PackageVerificationError(f"Invalid ZIP archive: {archive}") from exc
    except UnicodeDecodeError as exc:
        raise PackageVerificationError("Packaged documentation must be valid UTF-8") from exc

    build_info = _read_build_info(build_info_text)
    if build_info["version"] != version:
        raise PackageVerificationError(
            f"BUILD_INFO version {build_info['version']!r} does not match package version {version!r}"
        )
    if source_sha is not None and build_info["source_sha"].lower() != source_sha.lower():
        raise PackageVerificationError(
            "BUILD_INFO source_sha does not match the exact source commit used for qualification"
        )
    if f"BackgroundPXR {version}" not in notes:
        raise PackageVerificationError(
            f"RELEASE_NOTES.md does not identify BackgroundPXR {version}"
        )
    if "by Swir" not in readme or "github.com/Swir" not in readme:
        raise PackageVerificationError(
            "Permanent 'by Swir' / github.com/Swir branding is missing from packaged README"
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify a BackgroundPXR Windows release ZIP")
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--checksum", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--source-sha",
        help="Expected exact Git commit SHA recorded inside BUILD_INFO.txt",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        verify_release_package(
            args.archive,
            args.checksum,
            args.version,
            source_sha=args.source_sha,
        )
    except PackageVerificationError as exc:
        raise SystemExit(f"BackgroundPXR release package verification failed: {exc}") from exc
    print(
        "BackgroundPXR release package verification: OK "
        f"({args.archive.name}, SHA-256 {_sha256(args.archive)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
