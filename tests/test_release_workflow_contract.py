from __future__ import annotations

from pathlib import Path


def _workflow_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    return (repo_root / ".github" / "workflows" / "windows.yml").read_text(
        encoding="utf-8"
    )


def test_release_workflow_verifies_freshly_published_assets() -> None:
    workflow = _workflow_text()

    publish = workflow.index("- name: Publish GitHub Release")
    fresh_download = workflow.index(
        "- name: Verify published 1.0 release from fresh download"
    )
    package_verify = workflow.index("python tools/verify_release_package.py", fresh_download)
    runtime_self_test = workflow.index("--self-test-runtime", fresh_download)
    evidence_upload = workflow.index("- name: Upload post-release smoke evidence")

    assert publish < fresh_download < package_verify < runtime_self_test < evidence_upload
    assert "gh release download $tag" in workflow[fresh_download:evidence_upload]
    assert "targetCommitish" in workflow[fresh_download:evidence_upload]
    assert "--source-sha \"$env:GITHUB_SHA\"" in workflow[fresh_download:evidence_upload]


def test_post_release_smoke_is_publication_only_and_records_evidence() -> None:
    workflow = _workflow_text()
    start = workflow.index("- name: Verify published 1.0 release from fresh download")
    tail = workflow[start:]

    publication_guard = "if: github.event_name == 'push' && github.ref == 'refs/heads/main'"
    assert tail.count(publication_guard) >= 2
    assert '"runtime_self_test=OK"' in tail
    assert '"published_asset_smoke=OK"' in tail
    assert "post_release_smoke.txt" in tail
    assert "retention-days: 30" in tail
