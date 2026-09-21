from __future__ import annotations

from pathlib import Path


def _workflow_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    return (repo_root / ".github" / "workflows" / "windows.yml").read_text(
        encoding="utf-8"
    )


def _witness_workflow_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    return (repo_root / ".github" / "workflows" / "witness-kit.yml").read_text(
        encoding="utf-8"
    )


def test_release_workflow_qualifies_remote_draft_before_publication() -> None:
    workflow = _workflow_text()

    create_draft = workflow.index("- name: Create draft GitHub Release")
    verify_draft = workflow.index("- name: Verify draft release assets before publication")
    publish = workflow.index("- name: Publish verified GitHub Release")
    fresh_download = workflow.index(
        "- name: Verify published 1.0 release from fresh download"
    )

    assert create_draft < verify_draft < publish < fresh_download

    draft_slice = workflow[create_draft:publish]
    assert "--draft --target $env:GITHUB_SHA" in draft_slice
    assert "gh release download $tag" in draft_slice
    assert "targetCommitish" in draft_slice
    assert "--source-sha \"$env:GITHUB_SHA\"" in draft_slice
    assert "$draftState -ne 'true'" in draft_slice

    publish_slice = workflow[publish:fresh_download]
    assert "gh release edit $tag --draft=false" in publish_slice
    assert "$draftState -ne 'false'" in publish_slice


def test_release_workflow_verifies_freshly_published_assets() -> None:
    workflow = _workflow_text()

    fresh_download = workflow.index(
        "- name: Verify published 1.0 release from fresh download"
    )
    package_verify = workflow.index("python tools/verify_release_package.py", fresh_download)
    runtime_self_test = workflow.index("--self-test-runtime", fresh_download)
    evidence_upload = workflow.index("- name: Upload post-release smoke evidence")

    assert fresh_download < package_verify < runtime_self_test < evidence_upload
    published_slice = workflow[fresh_download:evidence_upload]
    assert "gh release download $tag" in published_slice
    assert "targetCommitish" in published_slice
    assert "--source-sha \"$env:GITHUB_SHA\"" in published_slice
    assert "$draftState -ne 'false'" in published_slice


def test_post_release_smoke_is_publication_only_and_records_evidence() -> None:
    workflow = _workflow_text()
    start = workflow.index("- name: Create draft GitHub Release")
    tail = workflow[start:]

    publication_guard = "if: github.event_name == 'push' && github.ref == 'refs/heads/main'"
    assert tail.count(publication_guard) >= 5
    assert '"runtime_self_test=OK"' in tail
    assert '"published_asset_smoke=OK"' in tail
    assert "post_release_smoke.txt" in tail
    assert "retention-days: 30" in tail


def test_final_release_requires_manual_rc_promotion_integrity() -> None:
    workflow = _workflow_text()
    build_release = workflow.index("  build-release:")
    create_draft = workflow.index("- name: Create draft GitHub Release")
    gate_slice = workflow[build_release:create_draft]

    assert "fetch-depth: 0" in gate_slice
    assert "uses: actions/setup-python@v5" in gate_slice
    assert gate_slice.index("uses: actions/setup-python@v5") < gate_slice.index(
        "python tools/release_policy.py"
    )
    assert "python tools/verify_promotion.py" in gate_slice
    assert "--witness docs/acceptance/final-functional-witness.json" in gate_slice
    assert '--release-sha "$env:GITHUB_SHA"' in gate_slice
    assert "python tools/release_policy.py" in gate_slice
    assert gate_slice.index("python tools/release_policy.py") < gate_slice.index(
        "python tools/verify_promotion.py"
    )


def test_witness_kit_is_bound_to_successful_exact_main_qualification() -> None:
    workflow = _witness_workflow_text()

    assert "pull_request:" in workflow
    assert "workflow_run:" in workflow
    assert "- Windows build & release" in workflow
    assert "github.event_name == 'workflow_run'" in workflow
    assert (
        "run.conclusion === 'success' && run.head_branch === 'main' && run.event === 'push'"
        in workflow
    )
    assert "listWorkflowRunArtifacts" in workflow
    assert "BackgroundPXR-qualification-${run.head_sha}" in workflow
    assert "core.setOutput('found', artifact ? 'true' : 'false')" in workflow
    assert "ref: ${{ github.event.workflow_run.head_sha }}" in workflow
    assert "run-id: ${{ github.event.workflow_run.id }}" in workflow


def test_witness_kit_skips_ineligible_or_unqualified_runs() -> None:
    workflow = _witness_workflow_text()
    kit_job = workflow.index("  build-witness-kit:")
    kit_workflow = workflow[kit_job:]

    assert "if (!eligible)" in kit_workflow
    assert "core.setOutput('found', 'false')" in kit_workflow
    assert "core.setOutput('found', artifact ? 'true' : 'false')" in kit_workflow
    assert kit_workflow.count("if: steps.qualification.outputs.found == 'true'") >= 7


def test_witness_recorder_gets_frozen_pr_smoke_before_main_kit() -> None:
    workflow = _witness_workflow_text()

    smoke_job = workflow.index("  recorder-smoke:")
    kit_job = workflow.index("  build-witness-kit:")
    assert smoke_job < kit_job
    pr_slice = workflow[smoke_job:kit_job]
    assert "github.event_name == 'pull_request'" in pr_slice
    assert "--hidden-import tools.verify_release_package" in pr_slice
    assert "BackgroundPXR-Witness.exe --help" in pr_slice


def test_witness_kit_builds_and_smokes_standalone_recorder() -> None:
    workflow = _witness_workflow_text()

    kit_job = workflow.index("  build-witness-kit:")
    kit_workflow = workflow[kit_job:]
    build = kit_workflow.index("- name: Build standalone witness recorder")
    smoke = kit_workflow.index("- name: Verify standalone recorder against exact RC")
    assemble = kit_workflow.index("- name: Assemble one-click witness kit")
    upload = kit_workflow.index("- name: Upload witness kit")

    assert build < smoke < assemble < upload
    assert "--hidden-import tools.verify_release_package" in kit_workflow[build:smoke]
    assert "--name BackgroundPXR-Witness tools/windows_witness.py" in kit_workflow[build:smoke]
    assert "BackgroundPXR-Witness.exe init" in kit_workflow[smoke:assemble]
    assert "candidate.source_sha" in kit_workflow[smoke:assemble]
    assert "BackgroundPXR-Witness.exe guided" in kit_workflow[assemble:upload]
    assert "START-WITNESS.cmd" in kit_workflow[assemble:upload]
    assert "WITNESS-KIT-INFO.txt" in kit_workflow[assemble:upload]
    assert "retention-days: 7" in kit_workflow[upload:]
