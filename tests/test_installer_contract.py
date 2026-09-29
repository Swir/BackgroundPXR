from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ISS = ROOT / "installer" / "BackgroundPXR.iss"
WORKFLOW = ROOT / ".github" / "workflows" / "installer.yml"


def test_installer_preserves_branding_and_safe_per_user_defaults() -> None:
    text = ISS.read_text(encoding="utf-8")

    assert "AppPublisher=Swir" in text
    assert "https://github.com/Swir" in text
    assert "https://github.com/Swir/BackgroundPXR/issues" in text
    assert "DefaultDirName={localappdata}\\Programs\\{#MyAppName}" in text
    assert "PrivilegesRequired=lowest" in text
    assert "UninstallDisplayIcon={app}\\BackgroundPXR.exe" in text
    assert 'Name: "{group}\\BackgroundPXR"' in text
    assert 'Name: "{autodesktop}\\BackgroundPXR"' in text
    assert "Tasks: desktopicon" in text
    assert "recursesubdirs createallsubdirs" in text


def test_installer_is_built_from_exact_published_stable_zip() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert 'gh release download $tag' in text
    assert 'BackgroundPXR-$env:VERSION-Windows.zip' in text
    assert "python tools/verify_release_package.py" in text
    assert "--source-sha \"$releaseTarget\"" in text
    assert "Expand-Archive -Path $archive -DestinationPath stable-package -Force" in text
    assert "pyinstaller" not in text.lower()


def test_installer_must_pass_install_runtime_and_uninstall_smoke() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "Silent install, frozen runtime self-test and uninstall" in text
    assert "'/VERYSILENT'" in text
    assert "--self-test-runtime" in text
    assert "backgroundpxr_runtime_selftest.txt" in text
    assert "unins000.exe" in text
    assert "BackgroundPXR.exe still exists after silent uninstall." in text


def test_stable_upload_requires_explicit_installer_release_merge_commit() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    guard = (
        "github.event_name == 'push' && github.ref == 'refs/heads/main' && "
        "startsWith(github.event.head_commit.message, 'installer-release:')"
    )
    assert guard in text
    assert "gh release upload $tag $installer $checksum --clobber" in text
    assert "gh release edit $tag --notes-file RELEASE_NOTES.md" in text
    assert "BackgroundPXR-1.0.0-Setup.exe" in text
    assert "BackgroundPXR-1.0.0-Setup.exe.sha256" in text
