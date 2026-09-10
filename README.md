# BackgroundPXR — Power eXtreme Remover

**BackgroundPXR** is a local Windows desktop app for AI background removal and background replacement. English is the default interface; Polish is available from the header.

## 0.1.0 preview

- Batch import from files, folders, and drag & drop.
- Side-by-side Before / After preview.
- Three local AI modes: **Quality** (`isnet-general-use`), **Fast** (`u2netp`), and **Portrait** (`birefnet-portrait`).
- Output backgrounds: transparent, white, custom color, or another image.
- Edge softness control.
- Optional soft product-style shadow.
- Auto-crop subject with configurable padding.
- PNG, JPG, and WEBP export.
- English / Polish UI.
- No account and no cloud upload. Models download automatically on first use and are then reused locally.

> BackgroundPXR does not use the `bria-rmbg` model by default. AI model weights can have licenses independent of rembg, so model licensing should be reviewed before commercial redistribution.

## Windows quick start

Recommended: **Python 3.11 or 3.12 (64-bit)**.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

The first removal can take longer because the selected local model is downloaded. Later runs reuse the model from the local rembg model cache.

## Build a Windows executable

```powershell
pip install -r requirements-dev.txt
pyinstaller --noconfirm --windowed --name BackgroundPXR --collect-all customtkinter --collect-all tkinterdnd2 app.py
```

For release builds, test the generated folder on a clean Windows machine before publishing. Rembg/ONNX model files are intentionally not bundled in 0.1.0; the selected model downloads on first use.

## Privacy

Images are processed on the user's computer by the local `rembg`/ONNX pipeline. BackgroundPXR itself does not upload images or require an account.

## Project direction

Planned next steps include a brush for mask correction, object-centered canvas presets for marketplaces, background blur, batch naming templates, model manager, and signed portable Windows builds.
