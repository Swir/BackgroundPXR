from __future__ import annotations

import re
from pathlib import Path


_JOB_HEADER_RE = re.compile(r"^  [A-Za-z0-9_-]+:\s*$", re.MULTILINE)


def _workflow_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    return (repo_root / ".github" / "workflows" / "windows.yml").read_text(
        encoding="utf-8"
    )


def _job_block(workflow: str, job_name: str) -> str:
    marker = f"  {job_name}:"
    start = workflow.index(marker)
    next_job = _JOB_HEADER_RE.search(workflow, start + len(marker))
    end = next_job.start() if next_job else len(workflow)
    return workflow[start:end]


def test_publication_requires_explicit_publish_release_prefix() -> None:
    workflow = _workflow_text()
    frozen_job = _job_block(workflow, "frozen-runtime")
    release_job = _job_block(workflow, "build-release")

    assert (
        "!startsWith(github.event.head_commit.message, 'publish-release:')"
        in frozen_job
    )
    assert (
        "startsWith(github.event.head_commit.message, 'publish-release:')"
        in release_job
    )
    assert "startsWith(github.event.head_commit.message, 'release:')" not in workflow
    assert "github.event_name == 'workflow_dispatch'" in release_job


def test_release_prep_commits_remain_qualification_runs() -> None:
    release_job = _job_block(_workflow_text(), "build-release")

    # A normal release-preparation title such as "release: add witness kit"
    # must not be interpreted as authorization to create/publish a GitHub Release.
    assert "'publish-release:'" in release_job
    assert "'release:'" not in release_job


def test_publication_waits_for_test_and_real_ai_smoke() -> None:
    release_job = _job_block(_workflow_text(), "build-release")

    # The release trigger contract must remain compatible with the release-grade
    # real-AI smoke gate instead of assuming the older scalar `needs: test` form.
    assert "needs: [test, real-ai-smoke]" in release_job
