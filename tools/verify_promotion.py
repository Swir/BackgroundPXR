from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


class PromotionVerificationError(RuntimeError):
    """Raised when a manually qualified RC cannot safely be promoted to 1.0."""


_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
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


def validate_witness_record(evidence: dict[str, object]) -> str:
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
        raise PromotionVerificationError("Final witness source_sha must be a 40-character Git SHA.")

    archive = str(candidate.get("archive") or "").strip()
    sha256 = str(candidate.get("sha256") or "").strip().lower()
    if archive != "BackgroundPXR-1.0.0rc1-Windows.zip":
        raise PromotionVerificationError("Final witness is not bound to the expected RC1 archive.")
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise PromotionVerificationError("Final witness ZIP SHA-256 is missing or invalid.")

    environment = evidence.get("environment")
    if not isinstance(environment, dict):
        raise PromotionVerificationError("Final witness Windows environment is missing.")
    windows_version = str(environment.get("windows_version") or "").strip()
    scaling = environment.get("display_scaling_percent")
    if not windows_version:
        raise PromotionVerificationError("Final witness Windows version is missing.")
    if not isinstance(scaling, int) or scaling <= 0:
        raise PromotionVerificationError("Final witness display scaling is missing or invalid.")

    model = str(evidence.get("ai_model") or "").strip()
    if not model:
        raise PromotionVerificationError("Final witness AI model is missing.")

    steps = evidence.get("steps")
    if not isinstance(steps, list) or len(steps) != 8:
        raise PromotionVerificationError("Final witness must contain exactly eight manual steps.")

    seen: set[int] = set()
    for item in steps:
        if not isinstance(item, dict):
            raise PromotionVerificationError("Final witness step entry must be an object.")
        step_id = item.get("id")
        if not isinstance(step_id, int) or not 1 <= step_id <= 8 or step_id in seen:
            raise PromotionVerificationError("Final witness contains an invalid or duplicate step id.")
        seen.add(step_id)
        if item.get("status") != "pass":
            raise PromotionVerificationError(
                f"Final witness step {step_id} is not explicitly pass."
            )

    return source_sha


def validate_promotion_changes(changed_files: list[str]) -> None:
    normalized = {item.replace("\\", "/").strip() for item in changed_files if item.strip()}
    blocked = sorted(normalized - _ALLOWED_PROMOTION_FILES)
    if blocked:
        raise PromotionVerificationError(
            "Runtime/source changes were made after the manually qualified RC: "
            + ", ".join(blocked)
        )


def git_changed_files(base_sha: str, release_sha: str, *, repo_root: Path) -> list[str]:
    if not _SHA_RE.fullmatch(base_sha) or not _SHA_RE.fullmatch(release_sha):
        raise PromotionVerificationError("Promotion comparison requires full 40-character Git SHAs.")
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
    changed_files = git_changed_files(rc_sha, release_sha, repo_root=repo_root)
    validate_promotion_changes(changed_files)
    return rc_sha, changed_files


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify that BackgroundPXR 1.0 is a metadata-only promotion of the manually qualified RC."
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
        raise SystemExit(f"BackgroundPXR 1.0 promotion verification failed: {exc}") from exc

    changed = ", ".join(changed_files) if changed_files else "(none)"
    print(
        "BackgroundPXR 1.0 promotion verification: OK "
        f"(manual RC {rc_sha} -> release {args.release_sha}; changed: {changed})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
