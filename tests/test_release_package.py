from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest

from tools.verify_release_package import PackageVerificationError, verify_release_package


def _package(
    tmp_path: Path,
    *,
    version: str = "0.4.0",
    readme: str | None = None,
    notes: str | None = None,
    extra_members: dict[str, bytes] | None = None,
) -> tuple[Path, Path]:
    archive = tmp_path / f"BackgroundPXR-{version}-Windows.zip"
    checksum = tmp_path / f"{archive.name}.sha256"
    readme = readme or f"BackgroundPXR {version}\nby Swir\nhttps://github.com/Swir\n"
    notes = notes or f"# BackgroundPXR {version} — Studio Pro\n"

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("BackgroundPXR/BackgroundPXR.exe", b"MZ\x00test")
        bundle.writestr("BackgroundPXR/README.md", readme.encode("utf-8"))
        bundle.writestr("BackgroundPXR/RELEASE_NOTES.md", notes.encode("utf-8"))
        for name, payload in (extra_members or {}).items():
            bundle.writestr(name, payload)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive, checksum


def test_valid_release_package_passes(tmp_path: Path) -> None:
    archive, checksum = _package(tmp_path)
    verify_release_package(archive, checksum, "0.4.0")


def test_checksum_mismatch_is_rejected(tmp_path: Path) -> None:
    archive, checksum = _package(tmp_path)
    checksum.write_text(f"{'0' * 64}  {archive.name}\n", encoding="utf-8")

    with pytest.raises(PackageVerificationError, match="SHA-256 mismatch"):
        verify_release_package(archive, checksum, "0.4.0")


def test_path_traversal_member_is_rejected(tmp_path: Path) -> None:
    archive, checksum = _package(tmp_path, extra_members={"../outside.txt": b"bad"})

    with pytest.raises(PackageVerificationError, match="Unsafe ZIP member path"):
        verify_release_package(archive, checksum, "0.4.0")


def test_missing_permanent_branding_is_rejected(tmp_path: Path) -> None:
    archive, checksum = _package(tmp_path, readme="BackgroundPXR 0.4.0\n")

    with pytest.raises(PackageVerificationError, match="branding is missing"):
        verify_release_package(archive, checksum, "0.4.0")


def test_release_notes_must_match_version(tmp_path: Path) -> None:
    archive, checksum = _package(tmp_path, notes="# BackgroundPXR 0.3.3\n")

    with pytest.raises(PackageVerificationError, match="does not identify BackgroundPXR 0.4.0"):
        verify_release_package(archive, checksum, "0.4.0")
