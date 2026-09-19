from __future__ import annotations

from pathlib import Path

from backgroundpxr import __version__


ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_documented_coherently() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    notes = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")

    assert __version__ in readme
    assert f"BackgroundPXR {__version__}" in notes

    if "rc" in __version__.lower():
        combined = f"{readme}\n{notes}".lower()
        assert "not a github release" in combined
        assert "qualification" in combined
