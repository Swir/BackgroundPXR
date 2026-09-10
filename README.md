# BackgroundPXR — Power eXtreme Remover

**by Swir** · https://github.com/Swir

BackgroundPXR is a Windows desktop background-removal and creative cutout studio designed for fast local work with product photos, portraits and social media images.

## Current feature set

- Professional three-column Studio Editor interface with PXR cyan/violet branding.
- English first, full Polish interface second.
- High Quality v2, Quality, Fast and Portrait AI modes.
- Fine hair / alpha matting and post-processed masks for difficult edges.
- Backgrounds: Transparent, White, Custom Color, Custom Image and Blur Original.
- Edge refinement: expand/shrink, feather and contrast.
- Manual Cleanup editor with Restore and Erase brushes.
- Adjustable brush size and hardness, zoom up to 800%, pan, fit, Undo and Redo.
- Smart Cleanup, Remove Leftovers and Reset Mask.
- Product, Portrait, Object and Transparent presets.
- PNG/JPG/WebP export and batch processing.
- Canvas presets: Original, 1:1, 4:5, 9:16, 16:9 and Product 2000×2000.
- Custom output suffix, output folder and optional automatic folder opening.
- Persistent local settings.
- Permanent **by Swir** footer with a clickable **github.com/Swir** link.

## Live diagnostics

BackgroundPXR shows a numeric percentage and the current processing stage while it works. During the AI/model step, an elapsed-seconds heartbeat updates every second so a long model load or inference does not look like a frozen application.

A built-in **LOG** button opens the diagnostics window. Processing, composition and export failures receive a `PXR-...` error ID and are saved with their full technical traceback in a rotating local log. The report can be copied to the clipboard or its folder opened directly from the app.

The percentage is based on real processing checkpoints and completed queue items. Neural inference does not expose a trustworthy internal percentage, so the app shows the active AI stage and live elapsed time rather than inventing fake progress inside that operation.

The selected rembg model may download automatically on first use. Later image processing runs locally.

## Run from source

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Windows releases

The GitHub workflow tests every update. It performs syntax checks, unit tests and a real Windows GUI startup smoke test. A commit whose message starts with `release:` additionally installs the full application dependencies, generates the PXR Windows icon, builds the portable application with PyInstaller, creates a ZIP and SHA-256 checksum, uploads the artifact and publishes a GitHub Release.

## Project identity

**BackgroundPXR — Power eXtreme Remover**  
Created **by Swir**  
GitHub: https://github.com/Swir

> Background segmentation is probabilistic. Always review difficult hair, fur, transparent objects and fine edges before publishing. Use the Manual Cleanup editor for final corrections when necessary.
