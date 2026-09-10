# BackgroundPXR 0.3.0 — Studio Editor

## English

BackgroundPXR 0.3.0 turns the app from a simple background remover into a local background-removal studio for Windows.

### New professional studio interface
- New three-column layout inspired by a modern creative editor.
- Left project panel with drag & drop, thumbnails and quick presets.
- Large Before / After workspace with a dedicated editor toolbar.
- Fixed right-side cards for AI Removal, Refine Edges, Manual Cleanup and Export.
- Graphic PXR tool icons throughout the interface.
- No full-interface scrolling; only the project file list scrolls when many files are added.
- Permanent `by Swir` footer with a clickable `github.com/Swir` link.

### Better AI background removal
- New **High Quality v2** mode based on the local BiRefNet general model.
- Fine hair / alpha matting option for difficult edges.
- Post-processed masks for cleaner cutouts.
- Edge refinement controls: expand/shrink mask, feather and mask contrast.
- Existing Quality, Fast and Portrait modes remain available.

### Manual Cleanup editor
- **Restore brush** — bring back parts removed by AI.
- **Erase brush** — remove background leftovers manually.
- Adjustable brush size and hardness.
- Mouse-wheel zoom from 25% to 800%.
- Pan and Fit tools.
- Undo / Redo history.
- Smart Cleanup for small semi-transparent mask noise.
- Remove Leftovers for small disconnected foreground islands.
- Reset Mask returns to the original AI cutout.
- Manual edits are non-destructive and do not rerun the AI model.

### Background and export tools
- Transparent, white, custom-color, custom-image and blurred-original backgrounds.
- Product, Portrait, Object and Transparent quick presets.
- PNG, JPG and WEBP export.
- Original, 1:1, 4:5, 9:16, 16:9 and Product 2000×2000 canvases.
- Custom filename suffix and output folder.
- Optional automatic opening of the output folder.
- Batch processing remains available.

### Reliability
- Expanded engine and manual-mask unit tests.
- A real Windows GUI startup smoke test now constructs the full interface before a release is allowed to build.
- The smoke test uses the same CustomTkinter major version as the release build.

The first use of an AI model may download its model file. Image processing then runs locally on the computer.

---

## Polski

BackgroundPXR 0.3.0 zmienia program z prostego narzędzia do usuwania tła w lokalne studio edycji tła dla Windows.

### Nowy profesjonalny interfejs
- Nowy trzykolumnowy układ w stylu nowoczesnego programu graficznego.
- Lewy panel projektu z drag & drop, miniaturami i szybkimi presetami.
- Duży obszar Przed / Po z osobnym paskiem narzędzi edytora.
- Stałe panele po prawej: Usuwanie AI, Dopracuj krawędzie, Ręczne poprawki i Eksport.
- Graficzne ikony narzędzi PXR.
- Brak przewijania całego interfejsu; przewija się wyłącznie lista plików, gdy jest ich dużo.
- Stała stopka `by Swir` z klikalnym `github.com/Swir`.

### Dokładniejsze usuwanie tła AI
- Nowy tryb **Najwyższa jakość v2** oparty na lokalnym modelu BiRefNet general.
- Opcja alpha matting do włosów i trudnych krawędzi.
- Dodatkowe czyszczenie maski po AI.
- Regulacja maski: rozszerzanie/zwężanie, miękkość i kontrast.
- Nadal dostępne tryby Jakość, Szybki i Portret.

### Ręczny edytor poprawek
- **Przywróć** — odzyskuje fragmenty, które AI usunęło za mocno.
- **Usuń** — ręcznie usuwa resztki tła.
- Regulowany rozmiar i twardość pędzla.
- Zoom kółkiem myszy od 25% do 800%.
- Przesuwanie obrazu i Dopasuj.
- Cofnij / Ponów.
- Smart Cleanup do półprzezroczystych zabrudzeń maski.
- Usuń resztki do małych odłączonych fragmentów tła.
- Reset maski przywraca wynik AI.
- Ręczne poprawki są niedestrukcyjne i nie uruchamiają ponownie modelu AI.

### Tła i eksport
- Tło przezroczyste, białe, własny kolor, własny obraz i rozmyty oryginał.
- Presety Produkt, Portret, Obiekt i Przezroczyste.
- Eksport PNG, JPG i WEBP.
- Płótna: oryginał, 1:1, 4:5, 9:16, 16:9 i Produkt 2000×2000.
- Własny dopisek do nazwy i folder zapisu.
- Opcjonalne automatyczne otwieranie folderu po eksporcie.
- Nadal dostępne przetwarzanie wielu zdjęć.

### Stabilność
- Rozszerzone testy silnika i ręcznego edytora maski.
- Przed każdym wydaniem Windows uruchamiany jest prawdziwy smoke test, który buduje cały interfejs GUI.
- Test GUI korzysta z tej samej głównej wersji CustomTkinter co finalny build.

Przy pierwszym użyciu danego modelu AI jego plik może zostać pobrany. Późniejsze przetwarzanie obrazu odbywa się lokalnie na komputerze.
