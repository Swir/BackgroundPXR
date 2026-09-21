from __future__ import annotations

import argparse
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "readme"
ROADMAP = ROOT / "ROADMAP_1_0.md"
README = ROOT / "README.md"
CHECKBOX_RE = re.compile(r"^\s*-\s+\[([ xX])\]\s+", re.MULTILINE)
LEGACY_UNICODE_BAR_RE = re.compile(r"[█▓▒░▰▱■□]{5,}")
LEGACY_ASCII_BAR_RE = re.compile(r"\[[#=\-]{8,}\]")


def measure() -> tuple[int, int, float]:
    text = ROADMAP.read_text(encoding="utf-8")
    states = CHECKBOX_RE.findall(text)
    if not states:
        raise SystemExit("ROADMAP_1_0.md has no measurable acceptance checklist")
    completed = sum(1 for state in states if state.lower() == "x")
    total = len(states)
    return completed, total, completed / total


def fmt_percent(fraction: float) -> str:
    return f"{fraction * 100.0:.1f}%"


def card_svg(completed: int, total: int, fraction: float) -> str:
    pct = fmt_percent(fraction)
    width = 1100.0 * fraction
    status = "COMPLETE" if completed == total else "IN PROGRESS"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="190" viewBox="0 0 1200 190" role="img" aria-labelledby="title desc">
  <title id="title">BackgroundPXR 1.0 acceptance progress — {pct}</title>
  <desc id="desc">BackgroundPXR 1.0 acceptance scope: {completed} of {total} verified items, {pct}. Release readiness is tracked separately.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#02050A"/><stop offset="1" stop-color="#07111C"/></linearGradient>
    <linearGradient id="fill" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#0088FF"/><stop offset="1" stop-color="#62E5FF"/></linearGradient>
    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#62E5FF" stroke-opacity=".055"/></pattern>
    <filter id="glow" x="-40%" y="-100%" width="180%" height="300%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <clipPath id="clip"><rect x="50" y="132" width="1100" height="24" rx="12"/></clipPath>
  </defs>
  <rect x="1" y="1" width="1198" height="188" rx="24" fill="url(#bg)" stroke="#62E5FF" stroke-opacity=".22"/>
  <rect x="1" y="1" width="1198" height="188" rx="24" fill="url(#grid)"/>
  <text x="50" y="42" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="16" font-weight="700" letter-spacing="3">SWIR PROGRESS</text>
  <text x="50" y="78" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="30" font-weight="800">BackgroundPXR</text>
  <text x="50" y="106" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="15">1.0 acceptance roadmap</text>
  <text x="1110" y="78" text-anchor="end" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="34" font-weight="800">{pct}</text>
  <text x="1110" y="106" text-anchor="end" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="14" font-weight="700">{status}</text>
  <rect x="50" y="132" width="1100" height="24" rx="12" fill="#08131F" stroke="#62E5FF" stroke-opacity=".16"/>
  <rect id="progress-fill" x="50" y="132" width="{width:.3f}" height="24" rx="12" fill="url(#fill)" filter="url(#glow)" clip-path="url(#clip)"/>
  <text x="50" y="178" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="13">Verified: {completed} / {total}</text>
  <text x="1150" y="178" text-anchor="end" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="13">Release readiness tracked separately</text>
</svg>
'''


def mini_svg(completed: int, total: int, fraction: float) -> str:
    pct = fmt_percent(fraction)
    width = 700.0 * fraction
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="82" viewBox="0 0 900 82" role="img" aria-labelledby="title desc">
  <title id="title">BackgroundPXR 1.0 compact progress — {pct}</title>
  <desc id="desc">{completed} of {total} BackgroundPXR 1.0 acceptance items are verified.</desc>
  <defs><linearGradient id="fill" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#0088FF"/><stop offset="1" stop-color="#62E5FF"/></linearGradient></defs>
  <rect x="1" y="1" width="898" height="80" rx="18" fill="#02050A" stroke="#62E5FF" stroke-opacity=".22"/>
  <text x="24" y="27" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="12" font-weight="700" letter-spacing="2">SWIR ROADMAP</text>
  <text x="24" y="54" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="19" font-weight="800">{pct}</text>
  <rect x="170" y="25" width="700" height="20" rx="10" fill="#08131F"/>
  <rect id="progress-fill" x="170" y="25" width="{width:.3f}" height="20" rx="10" fill="url(#fill)"/>
  <text x="870" y="67" text-anchor="end" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="11">{completed}/{total} verified · 1.0 acceptance scope</text>
</svg>
'''


def template_svg() -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="180" viewBox="0 0 1200 180" role="img" aria-labelledby="title desc">
  <title id="title">SWIR Progress template</title>
  <desc id="desc">Reusable template only. TEMPLATE — NOT PROJECT DATA.</desc>
  <rect x="1" y="1" width="1198" height="178" rx="24" fill="#02050A" stroke="#62E5FF" stroke-opacity=".22"/>
  <text x="50" y="48" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="18" font-weight="700">SWIR PROGRESS TEMPLATE</text>
  <text x="50" y="90" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="30" font-weight="800">TEMPLATE — NOT PROJECT DATA</text>
  <rect x="50" y="120" width="1100" height="24" rx="12" fill="#08131F"/>
  <text x="50" y="164" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="13">Populate only from an authoritative verified source.</text>
</svg>
'''


def outputs() -> dict[str, str]:
    completed, total, fraction = measure()
    return {
        "progress-card.svg": card_svg(completed, total, fraction),
        "progress-mini.svg": mini_svg(completed, total, fraction),
        "progress-template.svg": template_svg(),
    }


def validate_presentation(data: dict[str, str]) -> None:
    readme = README.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    if readme.count("assets/readme/progress-card.svg") != 1:
        raise SystemExit("README must embed exactly one progress-card.svg")
    if "progress-mini.svg" in readme:
        raise SystemExit("README must not embed progress-mini.svg")
    if roadmap.count("assets/readme/progress-mini.svg") != 1:
        raise SystemExit("ROADMAP_1_0.md must embed exactly one progress-mini.svg")
    for name, text in data.items():
        ET.fromstring(text)
        if "XXX" in text:
            raise SystemExit(f"invalid SVG placeholder in {name}")
    for path, text in ((README, readme), (ROADMAP, roadmap)):
        for line in text.splitlines():
            if LEGACY_UNICODE_BAR_RE.search(line) or LEGACY_ASCII_BAR_RE.search(line):
                raise SystemExit(f"legacy text progress meter found in {path.name}: {line.strip()[:120]}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = outputs()
    validate_presentation(data)
    if args.check:
        stale = [
            name for name, text in data.items()
            if not (OUT / name).exists() or (OUT / name).read_text(encoding="utf-8") != text
        ]
        if stale:
            raise SystemExit("stale progress assets: " + ", ".join(stale))
        completed, total, fraction = measure()
        print(f"BackgroundPXR 1.0 progress: {completed}/{total} = {fmt_percent(fraction)}")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in data.items():
        (OUT / name).write_text(text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
