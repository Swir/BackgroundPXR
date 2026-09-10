<div align="center">

# BackgroundPXR

### AI Background Studio for Windows

**Remove backgrounds • Replace backgrounds • Blur backgrounds • Refine edges • Export transparent PNGs**

A privacy-first **AI background remover for Windows** with local processing, batch workflow, manual mask cleanup and professional background editing tools.

**Power eXtreme Remover — by Swir**

[Download latest release](https://github.com/Swir/BackgroundPXR/releases/latest) · [All releases](https://github.com/Swir/BackgroundPXR/releases) · [GitHub profile](https://github.com/Swir)

![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-1678C2?style=for-the-badge&logo=windows11&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Local AI](https://img.shields.io/badge/AI-Local%20Processing-16C784?style=for-the-badge)
![Release](https://img.shields.io/github/v/release/Swir/BackgroundPXR?style=for-the-badge)

</div>

---

## What is BackgroundPXR?

**BackgroundPXR — AI Background Studio** is a desktop photo tool for Windows 10/11 built for people who want to **remove a background from an image without uploading the photo to a cloud service**.

It combines automatic AI cutout tools with a manual mask editor, background replacement, blur effects, batch processing and export presets. It is designed for product photos, portraits, marketplace listings, social media graphics and transparent PNG creation.

BackgroundPXR can be used as an **offline background remover**, **AI cutout editor**, **transparent PNG maker**, **product photo background remover**, **portrait background remover** and **batch background removal tool for Windows**.

> AI models may download automatically the first time they are used. After the required model is available locally, image processing is performed on your computer.

---

## Download for Windows

### Latest version: **0.3.4 — AI Background Studio Foundation**

Download the newest portable Windows build from:

### [Download BackgroundPXR for Windows](https://github.com/Swir/BackgroundPXR/releases/latest)

1. Download `BackgroundPXR-0.3.4-Windows.zip` from **Releases**.
2. Extract the ZIP to a normal folder.
3. Run `BackgroundPXR.exe`.
4. Add an image and choose an AI mode.
5. Review the cutout, fix difficult edges if needed, then export.

No separate Python installation is required for the packaged Windows release.

---

## AI Background Studio

BackgroundPXR is evolving from a simple background remover into a complete **AI Background Studio**.

| Studio mode | What it does |
| --- | --- |
| **Cutout** | Removes the image background and creates a transparent subject |
| **Replace** | Replaces the original background with a custom image or solid color |
| **Blur** | Keeps the subject sharp while blurring the original background |
| **Studio** | Creates a clean studio-style result with a white background and optional soft shadow |

The same AI subject mask can be refined and reused, so you can experiment with different backgrounds without repeatedly cutting out the subject manually.

---

## Main features

### AI background removal

- **High Quality v2**, Quality, Fast and Portrait processing modes
- Fine hair and difficult-edge handling with **alpha matting**
- Expand / shrink subject mask
- Feather control
- Mask contrast control
- Transparent, white, custom-color, image and blurred backgrounds
- Local AI processing after the required model is available

### Manual Cleanup Editor

AI segmentation is not perfect on every photo. BackgroundPXR includes tools for fixing difficult areas instead of forcing you to start again.

- **Restore brush** — bring back parts of the subject removed by AI
- **Erase brush** — remove leftover background manually
- Brush size and hardness controls
- Zoom up to **800%**
- Pan / Fit view
- Undo / Redo
- Smart Cleanup
- Remove Leftovers
- Reset Mask

This makes BackgroundPXR useful for hair, clothing edges, product contours and other areas where an automatic background remover may need a final manual correction.

### Background creation and replacement

- Transparent background
- White background
- Custom solid color
- Custom replacement image
- Blur original background
- Soft shadow
- Auto crop
- Padding controls
- Product and portrait presets

### Export and batch processing

- PNG export with transparency
- JPG export
- WebP export
- Process one image or multiple images
- Batch background removal
- Output filename suffix
- Custom output folder
- Optional automatic opening of the output folder
- Canvas presets:
  - Original size
  - Square 1:1
  - Portrait 4:5
  - Story 9:16
  - Landscape 16:9
  - Product 2000×2000

---

## Built for real workflows

BackgroundPXR is useful when you need a fast **background remover for product photos**, marketplace listings, portraits or social media graphics.

Typical use cases include:

- removing backgrounds from product photos for e-commerce
- preparing transparent PNG files for websites and graphic design
- replacing photo backgrounds without Photoshop
- creating clean white-background marketplace images
- blurring portrait backgrounds
- cutting out people and objects from photos
- processing multiple images in one batch
- manually repairing imperfect AI masks
- creating social-media-ready images in common aspect ratios
- working with private photos locally instead of uploading them to an online background remover

---

## Privacy-first local processing

BackgroundPXR is designed around local desktop processing.

- No account is required by the application
- Photos are processed locally after the required AI model is available
- The editor does not require uploading your images to a BackgroundPXR server
- Settings and diagnostics are stored locally

This makes it suitable for users searching for a **local AI background remover**, **offline image background remover** or a **background removal tool without photo uploads**.

---

## Live progress and diagnostics

You should always know whether the application is working.

BackgroundPXR displays:

- live processing percentage
- current image name
- current processing stage
- elapsed time during long AI operations
- batch progress
- success / error state

The built-in **LOG** window records technical errors with a unique `PXR-...` error ID and full traceback. The report can be copied directly for troubleshooting.

This diagnostic system is also used during development to catch packaging and AI-runtime problems before a Windows release is published.

---

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl + Z` | Undo |
| `Ctrl + Y` | Redo |
| `Ctrl + +` | Zoom in |
| `Ctrl + -` | Zoom out |
| `F6` | Show / hide thumbnail strip |
| `Alt + 1` | Cutout mode |
| `Alt + 2` | Replace mode |
| `Alt + 3` | Blur mode |
| `Alt + 4` | Studio mode |

---

## Run from source

### Requirements

- Windows 10 or Windows 11 recommended
- Python 3.12
- Internet connection may be required for the first download of an AI model

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

---

## Release quality checks

Windows releases are automatically checked before publication.

The CI pipeline performs:

- Python syntax validation
- unit tests
- real GUI startup smoke test
- 1600×900 layout validation
- Windows portable build with PyInstaller
- bundled `rembg`, `pymatting` and `onnxruntime` checks
- frozen EXE runtime self-test
- `tqdm` / no-console runtime test
- ZIP packaging
- SHA-256 checksum generation

A release build is blocked when one of these required checks fails.

---

## Roadmap

BackgroundPXR is actively evolving into a larger photo background studio.

Planned directions include:

- richer Studio background presets
- gradient backgrounds
- stronger portrait blur / bokeh controls
- outline and sticker effects
- improved configurable shadows
- export of the AI mask itself
- more marketplace and social presets
- stronger manual edge-editing workflow
- mask overlay views
- additional keyboard shortcuts
- future professional UI migration to **PySide6 + QML**

---

## Search-friendly project description

If you found this repository while looking for a **free AI background remover for Windows**, **offline background remover**, **remove background from image app**, **transparent PNG background remover**, **batch background remover**, **AI background replacement tool**, **product photo background remover**, **portrait cutout tool**, **local AI photo editor**, **remove background without uploading**, or a **Windows alternative to online background removal tools**, BackgroundPXR is built around exactly those workflows.

The project focuses on local AI cutouts, manual correction and practical desktop workflow rather than requiring a web account for every edit.

---

# Polski

## BackgroundPXR — AI Background Studio

**BackgroundPXR** to aplikacja dla Windows 10/11 do lokalnego **usuwania tła ze zdjęć przy pomocy AI**, podmiany tła, rozmywania tła, tworzenia przezroczystych PNG i ręcznego poprawiania niedoskonałych masek.

Program jest rozwijany jako pełne **AI Background Studio**, a nie tylko prosty background remover.

### Najważniejsze możliwości

- automatyczne usuwanie tła AI
- tryby Najwyższa jakość v2 / Jakość / Szybki / Portret
- przezroczyste PNG
- białe i kolorowe tło
- podmiana tła własnym zdjęciem
- rozmywanie oryginalnego tła
- alpha matting do włosów i trudnych krawędzi
- ręczne narzędzia **Przywróć / Usuń**
- zoom do 800%
- Cofnij / Ponów
- Smart Cleanup i Usuń resztki
- przetwarzanie wielu zdjęć
- eksport PNG / JPG / WebP
- presety 1:1, 4:5, 9:16, 16:9 i Produkt 2000×2000
- procent postępu i pełny LOG diagnostyczny
- lokalne przetwarzanie zdjęć po pobraniu potrzebnego modelu AI

### Dla kogo?

BackgroundPXR może przydać się do:

- zdjęć produktów do sklepów internetowych
- ofert marketplace
- portretów
- grafik na social media
- wycinania osób i przedmiotów
- tworzenia przezroczystych plików PNG
- masowego usuwania tła
- lokalnej pracy ze zdjęciami bez wysyłania ich do serwera BackgroundPXR

### Pobierz

### [Pobierz najnowszą wersję BackgroundPXR](https://github.com/Swir/BackgroundPXR/releases/latest)

---

## Notes

AI background segmentation is probabilistic. Hair, fur, glass, smoke, semi-transparent materials and very low-contrast edges may require manual correction. Always review important images before publishing them.

---

<div align="center">

### BackgroundPXR — Power eXtreme Remover

**Remove. Replace. Create.**

Created and developed **by Swir**

[github.com/Swir](https://github.com/Swir)

</div>
