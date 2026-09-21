from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.verify_release_package import PackageVerificationError, verify_release_package


class WitnessError(RuntimeError):
    """Raised when final Windows witness evidence is incomplete or inconsistent."""


STEP_TITLES = {
    1: "Startup and permanent Swir branding",
    2: "JPG/PNG import and real AI removal",
    3: "Manual Restore/Erase, zoom/pan/Fit, Undo/Redo",
    4: "Studio Pro composed modes and transform effects",
    5: "PNG/JPG/WebP plus mask export safety",
    6: "Two-image batch and partial-failure diagnostics",
    7: "English/Polish usability and unclipped controls",
    8: "Diagnostics usability and privacy sanity",
}

STEP_INSTRUCTIONS = {
    1: (
        "Launch BackgroundPXR.exe from the extracted qualification package. Confirm startup "
        "has no crash or console dependency and that 'by Swir' plus github.com/Swir branding "
        "is visible."
    ),
    2: (
        "Import at least one JPG and one PNG, run normal AI removal with the model recorded "
        "for this witness, and confirm the subject preview updates correctly."
    ),
    3: (
        "Use Erase and Restore, change brush size and hardness, zoom/pan/Fit, then verify "
        "Undo and Redo restore the expected mask states."
    ),
    4: (
        "Exercise Cutout plus at least two of Replace/Blur/Studio, move/scale the subject, "
        "enable outline and shadow, and confirm the preview stays responsive and coherent."
    ),
    5: (
        "Export PNG, JPG and WebP plus a mask. Open the outputs, verify canvas/suffix and "
        "transparency behavior, and confirm no source or existing export is overwritten silently."
    ),
    6: (
        "Run a small batch with at least two images. Confirm progress/diagnostics stay usable "
        "and one file failure is reported without crashing or losing successful outputs."
    ),
    7: (
        "Switch between English and Polish. Confirm the main import/process/manual/export flow "
        "remains understandable and controls are not clipped at the recorded Windows scaling."
    ),
    8: (
        "Open diagnostics/log access and confirm a failure can be identified without exposing "
        "unrelated private paths or breaking the session."
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_build_info(archive: Path) -> dict[str, str]:
    try:
        with zipfile.ZipFile(archive) as bundle:
            member = next(
                (
                    info
                    for info in bundle.infolist()
                    if not info.is_dir()
                    and info.filename.replace("\\", "/").lower()
                    == "backgroundpxr/build_info.txt"
                ),
                None,
            )
            if member is None:
                raise WitnessError("Qualification ZIP does not contain BackgroundPXR/BUILD_INFO.txt.")
            raw = bundle.read(member).decode("utf-8-sig")
    except zipfile.BadZipFile as exc:
        raise WitnessError(f"Invalid qualification ZIP: {archive}") from exc
    except UnicodeDecodeError as exc:
        raise WitnessError("BUILD_INFO.txt is not valid UTF-8.") from exc

    fields: dict[str, str] = {}
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        key, separator, value = line.partition("=")
        if not separator or not key.strip() or not value.strip():
            raise WitnessError(f"Invalid BUILD_INFO line: {raw_line!r}")
        fields[key.strip()] = value.strip()

    required = {"version", "source_sha", "channel"}
    missing = sorted(required - fields.keys())
    if missing:
        raise WitnessError("BUILD_INFO.txt is missing: " + ", ".join(missing))
    return fields


def _detect_display_scaling_percent() -> int | None:
    if os.name != "nt":
        return None
    try:
        import ctypes

        user32 = ctypes.windll.user32
        get_dpi = getattr(user32, "GetDpiForSystem", None)
        if get_dpi is not None:
            dpi = int(get_dpi())
            if dpi > 0:
                return round(dpi * 100 / 96)
    except (AttributeError, OSError, TypeError, ValueError):
        pass
    return None


def _candidate_metadata(archive: Path, checksum: Path) -> dict[str, str]:
    build_info = _read_build_info(archive)
    try:
        verify_release_package(
            archive,
            checksum,
            build_info["version"],
            source_sha=build_info["source_sha"],
        )
    except PackageVerificationError as exc:
        raise WitnessError(str(exc)) from exc

    return {
        "version": build_info["version"],
        "source_sha": build_info["source_sha"].lower(),
        "channel": build_info["channel"],
        "archive": archive.name,
        "sha256": _sha256(archive),
    }


def new_evidence(archive: Path, checksum: Path) -> dict[str, object]:
    candidate = _candidate_metadata(archive, checksum)
    return {
        "schema_version": 1,
        "candidate": candidate,
        "environment": {
            "windows_version": platform.platform(),
            "display_scaling_percent": _detect_display_scaling_percent(),
        },
        "ai_model": "",
        "steps": [
            {
                "id": step_id,
                "title": STEP_TITLES[step_id],
                "status": "pending",
                "notes": "",
            }
            for step_id in sorted(STEP_TITLES)
        ],
    }


def write_evidence(path: Path, evidence: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_evidence(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WitnessError(f"Witness evidence file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WitnessError(f"Witness evidence is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise WitnessError("Witness evidence root must be a JSON object.")
    return data


def record_result(
    evidence: dict[str, object],
    *,
    step_id: int | None = None,
    status: str | None = None,
    notes: str | None = None,
    model: str | None = None,
    scaling_percent: int | None = None,
) -> None:
    if model is not None:
        evidence["ai_model"] = model.strip()

    environment = evidence.get("environment")
    if not isinstance(environment, dict):
        raise WitnessError("Witness evidence environment section is missing.")
    if scaling_percent is not None:
        if scaling_percent <= 0:
            raise WitnessError("Display scaling must be a positive percentage.")
        environment["display_scaling_percent"] = scaling_percent

    if step_id is None:
        if status is not None or notes is not None:
            raise WitnessError("--status/--notes require --step.")
        return

    if step_id not in STEP_TITLES:
        raise WitnessError("Step must be between 1 and 8.")
    if status is None:
        raise WitnessError("--step requires --status.")
    if status not in {"pass", "fail", "pending"}:
        raise WitnessError("Status must be pass, fail or pending.")

    steps = evidence.get("steps")
    if not isinstance(steps, list):
        raise WitnessError("Witness evidence steps section is missing.")
    selected = next(
        (
            item
            for item in steps
            if isinstance(item, dict) and item.get("id") == step_id
        ),
        None,
    )
    if selected is None:
        raise WitnessError(f"Witness evidence does not contain step {step_id}.")
    selected["status"] = status
    if notes is not None:
        selected["notes"] = notes.strip()


def verify_evidence(
    evidence: dict[str, object],
    archive: Path,
    checksum: Path,
) -> None:
    expected = _candidate_metadata(archive, checksum)
    candidate = evidence.get("candidate")
    if not isinstance(candidate, dict):
        raise WitnessError("Witness evidence candidate section is missing.")

    for key in ("version", "source_sha", "archive", "sha256"):
        if candidate.get(key) != expected[key]:
            raise WitnessError(
                f"Witness candidate {key} does not match the exact qualification package."
            )

    environment = evidence.get("environment")
    if not isinstance(environment, dict):
        raise WitnessError("Witness environment section is missing.")
    windows_version = str(environment.get("windows_version") or "").strip()
    if not windows_version:
        raise WitnessError("Windows version evidence is missing.")
    scaling = environment.get("display_scaling_percent")
    if not isinstance(scaling, int) or scaling <= 0:
        raise WitnessError(
            "Display scaling evidence is missing; record it with --scaling-percent."
        )

    model = str(evidence.get("ai_model") or "").strip()
    if not model:
        raise WitnessError("AI model evidence is missing; record it with --model.")

    steps = evidence.get("steps")
    if not isinstance(steps, list) or len(steps) != len(STEP_TITLES):
        raise WitnessError("Witness evidence must contain exactly eight manual steps.")

    seen: set[int] = set()
    for item in steps:
        if not isinstance(item, dict):
            raise WitnessError("Witness step entry must be an object.")
        step_id = item.get("id")
        if not isinstance(step_id, int) or step_id not in STEP_TITLES or step_id in seen:
            raise WitnessError("Witness steps contain a missing, duplicate or invalid id.")
        seen.add(step_id)
        status = item.get("status")
        if status != "pass":
            raise WitnessError(
                f"Manual witness step {step_id} is {status!r}; all eight steps must pass."
            )


def extract_candidate(archive: Path, destination: Path) -> Path:
    """Safely extract the exact candidate and return its executable path."""

    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target = (destination / member.filename).resolve()
                try:
                    target.relative_to(destination)
                except ValueError as exc:
                    raise WitnessError(
                        f"Qualification ZIP contains an unsafe path: {member.filename}"
                    ) from exc
            bundle.extractall(destination)
    except zipfile.BadZipFile as exc:
        raise WitnessError(f"Invalid qualification ZIP: {archive}") from exc

    executable = destination / "BackgroundPXR" / "BackgroundPXR.exe"
    if not executable.is_file():
        raise WitnessError("Extracted qualification package does not contain BackgroundPXR.exe.")
    return executable


def _prompt_positive_int(label: str, input_fn: Callable[[str], str]) -> int:
    while True:
        value = input_fn(label).strip()
        try:
            number = int(value)
        except ValueError:
            print("Enter a positive integer, for example 125.")
            continue
        if number > 0:
            return number
        print("Enter a positive integer, for example 125.")


def run_guided_witness(
    archive: Path,
    checksum: Path,
    evidence_path: Path,
    *,
    model: str | None = None,
    scaling_percent: int | None = None,
    extract_dir: Path | None = None,
    launch_app: bool = True,
    input_fn: Callable[[str], str] = input,
) -> dict[str, object]:
    """Guide a human through all eight item-9 observations without auto-passing any step."""

    if evidence_path.exists():
        evidence = load_evidence(evidence_path)
        verify_candidate = evidence.get("candidate")
        if not isinstance(verify_candidate, dict):
            raise WitnessError("Existing witness evidence candidate section is missing.")
        expected = _candidate_metadata(archive, checksum)
        for key in ("version", "source_sha", "archive", "sha256"):
            if verify_candidate.get(key) != expected[key]:
                raise WitnessError(
                    "Existing witness evidence belongs to a different qualification package."
                )
    else:
        evidence = new_evidence(archive, checksum)
        write_evidence(evidence_path, evidence)

    if model is None:
        current_model = str(evidence.get("ai_model") or "").strip()
        if not current_model:
            current_model = input_fn("AI model used for this manual pass: ").strip()
            if not current_model:
                raise WitnessError("AI model is required before guided witness can continue.")
        model = current_model
    record_result(evidence, model=model)

    environment = evidence.get("environment")
    if not isinstance(environment, dict):
        raise WitnessError("Witness evidence environment section is missing.")
    if scaling_percent is None:
        existing_scaling = environment.get("display_scaling_percent")
        if isinstance(existing_scaling, int) and existing_scaling > 0:
            scaling_percent = existing_scaling
        else:
            detected = _detect_display_scaling_percent()
            scaling_percent = detected or _prompt_positive_int(
                "Windows display scaling percent (for example 125): ", input_fn
            )
    record_result(evidence, scaling_percent=scaling_percent)
    write_evidence(evidence_path, evidence)

    if launch_app:
        destination = extract_dir or evidence_path.parent / "BackgroundPXR-Witness-Run"
        executable = destination.resolve() / "BackgroundPXR" / "BackgroundPXR.exe"
        if not executable.is_file():
            executable = extract_candidate(archive, destination)
        try:
            subprocess.Popen([str(executable)], cwd=executable.parent)
        except OSError as exc:
            raise WitnessError(f"Could not launch qualification executable: {exc}") from exc
        print(f"Launched exact qualification executable: {executable}")

    steps = evidence.get("steps")
    if not isinstance(steps, list):
        raise WitnessError("Witness evidence steps section is missing.")

    print("\nBackgroundPXR 1.0 guided Windows witness")
    print("No step is auto-passed. Record only what you physically observed on this PC.\n")

    for step_id in sorted(STEP_TITLES):
        selected = next(
            (
                item
                for item in steps
                if isinstance(item, dict) and item.get("id") == step_id
            ),
            None,
        )
        if selected is None:
            raise WitnessError(f"Witness evidence does not contain step {step_id}.")
        if selected.get("status") == "pass":
            print(f"Step {step_id}/8 already passed: {STEP_TITLES[step_id]}")
            continue

        print(f"\nStep {step_id}/8 — {STEP_TITLES[step_id]}")
        print(STEP_INSTRUCTIONS[step_id])
        while True:
            answer = input_fn("Observed result [p]ass / [f]ail / [q]uit: ").strip().lower()
            if answer in {"p", "pass", "f", "fail", "q", "quit"}:
                break
            print("Enter p, f or q.")

        if answer in {"q", "quit"}:
            write_evidence(evidence_path, evidence)
            raise WitnessError(
                f"Guided witness paused at step {step_id}; evidence was saved to {evidence_path}."
            )

        notes = input_fn("Notes (optional, recommended for failures): ").strip()
        status = "pass" if answer in {"p", "pass"} else "fail"
        record_result(
            evidence,
            step_id=step_id,
            status=status,
            notes=notes,
        )
        write_evidence(evidence_path, evidence)

        if status == "fail":
            raise WitnessError(
                f"Manual witness step {step_id} failed; evidence was saved for diagnosis."
            )

    verify_evidence(evidence, archive, checksum)
    write_evidence(evidence_path, evidence)
    print(f"\nBackgroundPXR final Windows manual witness: OK — {evidence_path}")
    return evidence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and verify BackgroundPXR 1.0 Windows manual witness evidence."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create evidence bound to an exact qualification ZIP.")
    init.add_argument("--archive", required=True, type=Path)
    init.add_argument("--checksum", required=True, type=Path)
    init.add_argument("--output", required=True, type=Path)

    record = sub.add_parser("record", help="Record a manual witness result.")
    record.add_argument("--evidence", required=True, type=Path)
    record.add_argument("--step", type=int)
    record.add_argument("--status", choices=("pass", "fail", "pending"))
    record.add_argument("--notes")
    record.add_argument("--model")
    record.add_argument("--scaling-percent", type=int)

    verify = sub.add_parser("verify", help="Verify complete evidence against the exact ZIP.")
    verify.add_argument("--evidence", required=True, type=Path)
    verify.add_argument("--archive", required=True, type=Path)
    verify.add_argument("--checksum", required=True, type=Path)

    guided = sub.add_parser(
        "guided",
        help="Launch the exact RC and guide a human through all eight manual observations.",
    )
    guided.add_argument("--archive", required=True, type=Path)
    guided.add_argument("--checksum", required=True, type=Path)
    guided.add_argument(
        "--evidence",
        type=Path,
        default=Path("backgroundpxr-1.0-witness.json"),
    )
    guided.add_argument("--model")
    guided.add_argument("--scaling-percent", type=int)
    guided.add_argument("--extract-dir", type=Path)
    guided.add_argument(
        "--no-launch",
        action="store_true",
        help="Do not extract/launch BackgroundPXR.exe; useful only when it is already running.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "init":
            evidence = new_evidence(args.archive, args.checksum)
            write_evidence(args.output, evidence)
            print(f"BackgroundPXR Windows witness initialized: {args.output}")
            return 0

        if args.command == "record":
            evidence = load_evidence(args.evidence)
            record_result(
                evidence,
                step_id=args.step,
                status=args.status,
                notes=args.notes,
                model=args.model,
                scaling_percent=args.scaling_percent,
            )
            write_evidence(args.evidence, evidence)
            print(f"BackgroundPXR Windows witness updated: {args.evidence}")
            return 0

        if args.command == "guided":
            run_guided_witness(
                args.archive,
                args.checksum,
                args.evidence,
                model=args.model,
                scaling_percent=args.scaling_percent,
                extract_dir=args.extract_dir,
                launch_app=not args.no_launch,
            )
            return 0

        evidence = load_evidence(args.evidence)
        verify_evidence(evidence, args.archive, args.checksum)
        print("BackgroundPXR final Windows manual witness: OK")
        return 0
    except WitnessError as exc:
        raise SystemExit(f"BackgroundPXR Windows witness failed: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
