from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "readme"
PROJECT = "BackgroundPXR"
SCOPE = "Product readiness"
REASON = "No canonical roadmap denominator"

CARD = '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="190" viewBox="0 0 1200 190" role="img" aria-labelledby="title desc"><title id="title">BackgroundPXR progress</title><desc id="desc">BackgroundPXR product readiness progress is N/A because no canonical roadmap with a reproducible completion denominator exists.</desc><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#02050A"/><stop offset="1" stop-color="#07111C"/></linearGradient><pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#62E5FF" stroke-opacity=".055"/></pattern></defs><rect x="1" y="1" width="1198" height="188" rx="24" fill="url(#bg)" stroke="#62E5FF" stroke-opacity=".22"/><rect x="1" y="1" width="1198" height="188" rx="24" fill="url(#grid)"/><text x="50" y="42" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="16" font-weight="700" letter-spacing="3">SWIR PROGRESS</text><text x="50" y="78" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="30" font-weight="800">BackgroundPXR</text><text x="50" y="106" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="15">Product readiness</text><text x="1110" y="78" text-anchor="end" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="34" font-weight="800">N/A</text><text x="1110" y="106" text-anchor="end" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="14" font-weight="700">MAINTAINED</text><rect x="50" y="132" width="1100" height="24" rx="12" fill="#08131F" stroke="#62E5FF" stroke-opacity=".16"/><text x="50" y="178" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="13">Verified scope: N/A</text><text x="1150" y="178" text-anchor="end" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="13">No canonical roadmap denominator</text></svg>\n'''
MINI = '''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="82" viewBox="0 0 900 82" role="img" aria-labelledby="title desc"><title id="title">BackgroundPXR compact progress</title><desc id="desc">Product readiness is N/A because no canonical roadmap denominator exists.</desc><rect x="1" y="1" width="898" height="80" rx="18" fill="#02050A" stroke="#62E5FF" stroke-opacity=".22"/><text x="24" y="27" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="12" font-weight="700" letter-spacing="2">SWIR ROADMAP</text><text x="24" y="54" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="19" font-weight="800">N/A</text><rect x="170" y="25" width="700" height="20" rx="10" fill="#08131F"/><text x="870" y="67" text-anchor="end" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="11">Product readiness · no reproducible denominator</text></svg>\n'''
TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="180" viewBox="0 0 1200 180" role="img" aria-labelledby="title desc"><title id="title">SWIR Progress template</title><desc id="desc">Reusable template only. Not project data.</desc><rect x="1" y="1" width="1198" height="178" rx="24" fill="#02050A" stroke="#62E5FF" stroke-opacity=".22"/><text x="50" y="48" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="18" font-weight="700">SWIR PROGRESS TEMPLATE</text><text x="50" y="90" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="30" font-weight="800">TEMPLATE — NOT PROJECT DATA</text><rect x="50" y="120" width="1100" height="24" rx="12" fill="#08131F"/><text x="50" y="164" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="13">Populate only from an authoritative verified source.</text></svg>\n'''


def outputs() -> dict[str, str]:
    if list(ROOT.glob("ROADMAP*.md")):
        raise SystemExit("Roadmap detected: configure an authoritative calculation before regenerating SVG progress.")
    return {"progress-card.svg": CARD, "progress-mini.svg": MINI, "progress-template.svg": TEMPLATE}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = outputs()
    for text in data.values():
        ET.fromstring(text)
        if "XXX" in text:
            raise SystemExit("Invalid SVG placeholder")
    if args.check:
        stale = [name for name, text in data.items() if not (OUT / name).exists() or (OUT / name).read_text(encoding="utf-8") != text]
        if stale:
            raise SystemExit("stale progress assets: " + ", ".join(stale))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in ("progress-card.svg", "progress-mini.svg"):
            if f"assets/readme/{name}" not in readme:
                raise SystemExit(f"README is missing {name}")
        print("progress assets are current")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in data.items():
        (OUT / name).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
