from __future__ import annotations

from pathlib import Path


def _workflow_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    return (repo_root / ".github" / "workflows" / "windows.yml").read_text(
        encoding="utf-8"
    )


def test_publication_requires_explicit_publish_release_prefix() -> None:
    workflow = _workflow_text()
    frozen_runtime = workflow.index("  frozen-runtime:")
    build_release = workflow.index("  build-release:")
    needs_test = workflow.index("    needs: test", build_release)

    frozen_slice = workflow[frozen_runtime:build_release]
    release_guard = workflow[build_release:needs_test]

    assert (
        "!startsWith(github.event.head_commit.message, 'publish-release:')"
        in frozen_slice
    )
    assert (
        "startsWith(github.event.head_commit.message, 'publish-release:')"
        in release_guard
    )
    assert "startsWith(github.event.head_commit.message, 'release:')" not in workflow
    assert "github.event_name == 'workflow_dispatch'" in release_guard


def test_release_prep_commits_remain_qualification_runs() -> None:
    workflow = _workflow_text()
    build_release = workflow.index("  build-release:")
    release_guard = workflow[build_release : workflow.index("    needs: test", build_release)]

    # A normal release-preparation title such as "release: add witness kit"
    # must not be interpreted as authorization to create/publish a GitHub Release.
    assert "'publish-release:'" in release_guard
    assert "'release:'" not in release_guard
