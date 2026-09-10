from __future__ import annotations

import json
import os
from pathlib import Path


DEFAULTS = {
    "language": "English",
    "model": "Quality",
    "background_mode": "transparent",
    "background_color": "#FFFFFF",
    "background_blur": 18,
    "export_format": "PNG",
    "edge_softness": 0.8,
    "shadow": False,
    "trim": False,
    "padding": 24,
    "canvas_preset": "Original",
    "output_suffix": "_pxr",
    "auto_open_output": False,
}


class SettingsStore:
    def __init__(self) -> None:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".backgroundpxr"))
        self.directory = base / "BackgroundPXR"
        self.path = self.directory / "settings.json"

    def load(self) -> dict:
        data = dict(DEFAULTS)
        try:
            if self.path.exists():
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data.update({k: loaded[k] for k in DEFAULTS if k in loaded})
        except (OSError, ValueError, TypeError):
            pass
        return data

    def save(self, data: dict) -> None:
        payload = dict(DEFAULTS)
        payload.update({k: data[k] for k in DEFAULTS if k in data})
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(".tmp")
            temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            temp.replace(self.path)
        except OSError:
            pass
