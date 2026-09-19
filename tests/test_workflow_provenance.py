from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXACT_HEAD = "${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha }}"


def test_windows_qualification_uses_exact_pull_request_head() -> None:
    workflow = (ROOT / ".github" / "workflows" / "windows.yml").read_text(encoding="utf-8")

    assert workflow.count(f"ref: {EXACT_HEAD}") >= 2
    assert "Verify exact source checkout" in workflow
    assert "Verify exact qualification source" in workflow
    assert "git rev-parse HEAD" in workflow
    assert f"name: BackgroundPXR-qualification-{EXACT_HEAD}" in workflow


def test_release_publication_stays_separate_from_candidate_qualification() -> None:
    workflow = (ROOT / ".github" / "workflows" / "windows.yml").read_text(encoding="utf-8")

    assert "Publish GitHub Release" in workflow
    assert "if: github.event_name == 'push'" in workflow
    assert "Refusing pre-1.0 GitHub release" in workflow
