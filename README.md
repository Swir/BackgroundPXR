# BackgroundPXR — Power eXtreme Remover

**by Swir** · https://github.com/Swir

BackgroundPXR is a Windows desktop background-removal and creative cutout tool designed for fast local work with product photos, portraits and social media images.

## 0.2.0 — Premium redesign

- Premium compact dark interface with cyan/violet PXR branding.
- English first, full Polish interface second.
- Custom **BackgroundPXR / PXR icon** generated locally and used by the Windows build.
- AI modes: Quality, Fast and Portrait.
- Backgrounds: Transparent, White, Custom Color, Custom Image and **Blur Original**.
- Edge refinement, adjustable blur, soft shadow, auto-crop and padding.
- Canvas presets: Original, 1:1, 4:5, 9:16, 16:9 and Product 2000×2000.
- One-click presets for Product, Portrait and Social.
- Batch processing, custom filename suffix, PNG/JPG/WebP export.
- Persistent local settings and optional output-folder opening after export.
- Large Before / After workspace with checkerboard transparency preview.
- Clickable **github.com/Swir** link and **by Swir** branding in the application footer.
- Right-side controls use a fixed compact layout instead of a scrolling settings panel.

The selected rembg model downloads automatically on first use. Later processing is local.

## Run from source

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Windows releases

The GitHub workflow tests every update. A commit whose message starts with `release:` additionally installs the full application dependencies, generates the PXR Windows icon, builds a portable application with PyInstaller, creates a ZIP and SHA-256 checksum, uploads the build artifact and publishes a GitHub Release.

## Project identity

**BackgroundPXR — Power eXtreme Remover**  
Created **by Swir**  
GitHub: https://github.com/Swir

> Background segmentation is probabilistic. Always review difficult hair, fur, transparent objects and fine edges before publishing.
