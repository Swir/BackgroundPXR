from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


class PromotionVerificationError(RuntimeError):
    """Raised when a manually qualified RC cannot safely be promoted to 1.0."""


_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_RC_ARCHIVE_RE = re.compile(
    r"^BackgroundPXR-1\.0\.0rc1(?:-[A-Za-z0-9_.-]+)?-Windows\.zip$"
)

# Files that may change after the manual runtime test while release qualification
# tooling is still being hardened. Runtime/app inputs remain intentionally absent.
_ALLOWED_HARDENING_FILES = {
    ".github/workflows/windows.yml",
    ".github/workflows/witness-kit.yml",
    "docs/acceptance/final-functional-workflow.md",
    "tests/test_alpha_matting_memory.py",
    "tests/test_release_trigger_contract.py",
    "tests/test_release_workflow_contract.py",
    "tests/test_verify_promotion.py",
    "tests/test_windows_witness.py",
    "tools/verify_promotion.py",
    "tools/windows_witness.py",
}

# After the policy head is frozen, the final 1.0 promotion is metadata-only.
_ALLOWED_PROMOTION_FILES = {
    "backgroundpxr/__init__.py",
    "README.md",
    "RELEASE_NOTES.md",
    "ROADMAP_1_0.md",
    "assets/readme/progress-card.svg",
    "assets/readme/progress-mini.svg",
    "docs/acceptance/final-functional-witness.json",
}


def load_witness(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PromotionVerificationError(f"Final Windows witness is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PromotionVerificationError(f"Final Windows witness is invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise PromotionVerificationError("Final Windows witness root must be a JSON object.")
    return data


def _validate_candidate(evidence: dict[str, object]) -> str:
    candidate = evidence.get("candidate")
    if not isinstance(candidate, dict):
        raise PromotionVerificationError("Final witness candidate metadata is missing.")

    version = str(candidate.get("version") or "").strip()
    if version != "1.0.0rc1":
        raise PromotionVerificationError(
            f"Final witness must qualify 1.0.0rc1, found {version!r}."
        )

    source_sha = str(candidate.get("source_sha") or "").strip().lower()
    if not _SHA_RE.fullmatch(source_sha):
        raise PromotionVerificationError(
            "Final witness source_sha must be a 40-character Git SHA."
        )

    archive = str(candidate.get("archive") or "").strip()
    sha256 = str(candidate.get("sha256") or "").strip().lower()
    if not _RC_ARCHIVE_RE.fullmatch(archive):
        raise PromotionVerificationError(
            "Final witness is not bound to a BackgroundPXR 1.0.0rc1 Windows archive."
        )
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise PromotionVerificationError("Final witness ZIP SHA-256 is missing or invalid.")

    return source_sha


def _validate_legacy_eight_step_witness(evidence: dict[str, object]) -> None:
    environment = evidence.get("environment")
    if not isinstance(environment, dict):
        raise PromotionVerificationError("Final witness Windows environment is missing.")
    windows_version = str(environment.get("windows_version") or "").strip()
    scaling = environment.get("display_scaling_percent")
    if not windows_version:
        raise PromotionVerificationError("Final witness Windows version is missing.")
    if not isinstance(scaling, int) or scaling <= 0:
        raise PromotionVerificationError(
            "Final witness display scaling is missing or invalid."
        )

    model = str(evidence.get("ai_model") or "").strip()
    if not model:
        raise PromotionVerificationError("Final witness AI model is missing.")

    steps = evidence.get("steps")
    if not isinstance(steps, list) or len(steps) != 8:
        raise PromotionVerificationError(
            "Final witness must contain exactly eight manual steps."
        )

    seen: set[int] = set()
    for item in steps:
        if not isinstance(item, dict):
            raise PromotionVerificationError("Final witness step entry must be an object.")
        step_id = item.get("id")
        if (
            not isinstance(step_id, int)
            or not 1 <= step_id <= 8
            or step_id in seen
        ):
            raise PromotionVerificationError(
                "Final witness contains an invalid or duplicate step id."
            )
        seen.add(step_id)
        if item.get("status") != "pass":
            raise PromotionVerificationError(
                f"Final witness step {step_id} is not explicitly pass."
            )


def _validate_hybrid_attestation(evidence: dict[str, object]) -> None:
    attestation = evidence.get("manual_attestation")
    if not isinstance(attestation, dict):
        raise PromotionVerificationError("Hybrid witness manual_attestation is missing.")
    if attestation.get("status") != "pass":
        raise PromotionVerificationError(
            "Hybrid witness manual_attestation must be explicitly pass."
        )

    platform = str(attestation.get("platform") or "").strip()
    observed_path = str(attestation.get("observed_path") or "").strip()
    statement = str(attestation.get("statement") or "").strip()
    observed_date = str(attestation.get("date") or "").strip()

    if not platform.lower().startswith("windows"):
        raise PromotionVerificationError(
            "Hybrid witness must record a real Windows manual observation."
        )
    if observed_path != "High Quality v2 + alpha matting":
        raise PromotionVerificationError(
            "Hybrid witness must cover the release-blocking High Quality v2 + alpha matting path."
        )
    if len(statement) < 12:
        raise PromotionVerificationError(
            "Hybrid witness manual statement is missing or too short."
        )
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", observed_date):
        raise PromotionVerificationError(
            "Hybrid witness manual observation date must be YYYY-MM-DD."
        )

    policy_head_sha = str(evidence.get("policy_head_sha") or "").strip().lower()
    if not _SHA_RE.fullmatch(policy_head_sha):
        raise PromotionVerificationError(
            "Hybrid witness policy_head_sha must be a 40-character Git SHA."
        )


def validate_witness_record(evidence: dict[str, object]) -> str:
    source_sha = _validate_candidate(evidence)
    schema = evidence.get("schema_version")

    if schema == 1:
        _validate_legacy_eight_step_witness(evidence)
    elif schema == 2:
        _validate_hybrid_attestation(evidence)
    else:
        raise PromotionVerificationError(
            f"Unsupported final witness schema_version: {schema!r}."
        )

    return source_sha


def witness_policy_head(evidence: dict[str, object]) -> str:
    source_sha = validate_witness_record(evidence)
    if evidence.get("schema_version") == 1:
        return source_sha
    return str(evidence["policy_head_sha"]).strip().lower()


def _validate_changed_files(
    changed_files: list[str],
    *,
    allowed: set[str],
    label: str,
) -> None:
    normalized = {
        item.replace("\\", "/").strip()
        for item in changed_files
        if item.strip()
    }
    blocked = sorted(normalized - allowed)
    if blocked:
        raise PromotionVerificationError(
            f"{label}: disallowed changes after manual qualification: "
            + ", ".join(blocked)
        )


def validate_hardening_changes(changed_files: list[str]) -> None:
    _validate_changed_files(
        changed_files,
        allowed=_ALLOWED_HARDENING_FILES | _ALLOWED_PROMOTION_FILES,
        label="Release-gate hardening",
    )


def validate_promotion_changes(changed_files: list[str]) -> None:
    _validate_changed_files(
        changed_files,
        allowed=_ALLOWED_PROMOTION_FILES,
        label="Final metadata promotion",
    )


def _commit_is_available(sha: str, *, repo_root: Path) -> bool:
    proc = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def _ensure_commit_available(sha: str, *, repo_root: Path) -> None:
    """Fetch an exact witness commit when checkout refs no longer advertise it.

    GitHub Actions checks out all current branches/tags for the release job, but an
    earlier pull-request merge commit used to build the manually tested RC may no
    longer be reachable from those refs after a squash merge. The object still
    exists in GitHub and can be fetched by its exact SHA. Fetch only that immutable
    object; never substitute another commit or weaken the provenance comparison.
    """
    if _commit_is_available(sha, repo_root=repo_root):
        return

    proc = subprocess.run(
        [
            "git",
            "fetch",
            "--no-tags",
            "--no-recurse-submodules",
            "--depth=1",
            "origin",
            sha,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not _commit_is_available(sha, repo_root=repo_root):
        detail = (proc.stderr or proc.stdout).strip()
        raise PromotionVerificationError(
            "Cannot fetch exact witness commit required for provenance verification: "
            f"{sha}: {detail}"
        )


def git_changed_files(base_sha: str, release_sha: str, *, repo_root: Path) -> list[str]:
    if not _SHA_RE.fullmatch(base_sha) or not _SHA_RE.fullmatch(release_sha):
        raise PromotionVerificationError(
            "Promotion comparison requires full 40-character Git SHAs."
        )

    _ensure_commit_available(base_sha, repo_root=repo_root)
    _ensure_commit_available(release_sha, repo_root=repo_root)

    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base_sha}..{release_sha}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise PromotionVerificationError(
            f"Cannot compare manually qualified RC with release head: {detail}"
        )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def verify_promotion(
    witness: Path,
    release_sha: str,
    *,
    repo_root: Path,
) -> tuple[str, list[str]]:
    evidence = load_witness(witness)
    rc_sha = validate_witness_record(evidence)
    policy_sha = witness_policy_head(evidence)

    if evidence.get("schema_version") == 2:
        hardening_files = git_changed_files(rc_sha, policy_sha, repo_root=repo_root)
        validate_hardening_changes(hardening_files)
    else:
        hardening_files = []

    changed_files = git_changed_files(policy_sha, release_sha, repo_root=repo_root)
    validate_promotion_changes(changed_files)

    return rc_sha, hardening_files + changed_files


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that BackgroundPXR 1.0 is a metadata-only promotion of a "
            "manually qualified runtime with release-gate hardening tracked explicitly."
        )
    )
    parser.add_argument("--witness", required=True, type=Path)
    parser.add_argument("--release-sha", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        rc_sha, changed_files = verify_promotion(
            args.witness,
            args.release_sha,
            repo_root=args.repo_root,
        )
    except PromotionVerificationError as exc:
        raise SystemExit(
            f"BackgroundPXR 1.0 promotion verification failed: {exc}"
        ) from exc

    changed = ", ".join(changed_files) if changed_files else "(none)"
    print(
        "BackgroundPXR 1.0 promotion verification: OK "
        f"(manual RC {rc_sha} -> release {args.release_sha}; changed: {changed})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
