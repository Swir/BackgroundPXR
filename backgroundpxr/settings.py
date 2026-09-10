from __future__ import annotations
import json, os
from pathlib import Path
DEFAULTS={
"language":"English","model":"High Quality v2","background_mode":"transparent","background_color":"#FFFFFF","background_blur":18,
"export_format":"PNG","edge_refine":0,"edge_softness":0.4,"edge_contrast":8,"alpha_matting":True,"shadow":False,"trim":False,"padding":24,
"canvas_preset":"Original","output_suffix":"_pxr","auto_open_output":False,"output_dir":str(Path.home()/"Pictures"/"BackgroundPXR"),
"brush_size":48,"brush_hardness":75}
class SettingsStore:
    def __init__(self)->None:
        base=Path(os.environ.get("LOCALAPPDATA",Path.home()/".backgroundpxr")); self.directory=base/"BackgroundPXR"; self.path=self.directory/"settings.json"
    def load(self)->dict:
        data=dict(DEFAULTS)
        try:
            if self.path.exists():
                loaded=json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded,dict): data.update({k:loaded[k] for k in DEFAULTS if k in loaded})
        except (OSError,ValueError,TypeError): pass
        return data
    def save(self,data:dict)->None:
        payload=dict(DEFAULTS); payload.update({k:data[k] for k in DEFAULTS if k in data})
        try:
            self.directory.mkdir(parents=True,exist_ok=True); tmp=self.path.with_suffix(".tmp"); tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8"); tmp.replace(self.path)
        except OSError: pass
