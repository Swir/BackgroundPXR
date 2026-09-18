# BackgroundPXR 0.4.0 — Studio Pro

## English

BackgroundPXR 0.4.0 is the first **Studio Pro** release. It keeps the proven local AI removal engine from 0.3.x, but redesigns the right-side workflow and adds creative controls that work on an already generated subject mask.

### New Studio Pro inspector
- The old long right-side stack is replaced with three pages: **AI / CREATE / EXPORT**.
- Controls stay larger and more readable instead of being compressed vertically.
- The inspector is validated automatically at **1600×900**.
- Existing live percentage, LOG diagnostics and model runtime self-tests remain enabled.

### Subject transform
- New **Scale** control.
- New **Position X / Position Y** controls.
- Transform changes are instant after the AI mask exists and do not rerun the neural model.
- Default values preserve the 0.3.x output when the user does not change Studio Pro controls.

### Outline / Sticker
- New optional subject outline.
- Adjustable outline width.
- Custom outline color.
- New **Sticker** preset for transparent cutouts with a white outline.

### Improved shadow
- Shadow remains optional.
- New shadow opacity control.
- New shadow blur control.
- Shadow is rendered on the final canvas instead of forcing the subject into a larger intermediate image.

### Better previews
- Result preview.
- Black/white matte preview for checking halos and edge contamination.
- Grayscale mask preview.
- Manual Restore/Erase mode still shows the editable subject mask directly.

### Mask export
- New **Export Mask PNG** action.
- Saves the current alpha mask as a grayscale PNG.
- Uses the current manually refined mask when Manual Cleanup edits exist.

### Style presets
- Sticker preset.
- Product preset with clean white background, softer shadow and product-friendly scale.
- Portrait preset using the blurred original background.

### Engine and persistence
- Studio Pro settings are saved locally:
  - subject scale and position,
  - outline state/width/color,
  - shadow opacity/blur/offsets,
  - preview mode.
- Added engine tests for transform, outline, shadow, mask extraction and mask export.
- Added Studio Pro GUI smoke tests for all inspector pages.

---

## Polski

BackgroundPXR 0.4.0 to pierwsza wersja **Studio Pro**. Zachowuje sprawdzony lokalny silnik AI z linii 0.3.x, ale przebudowuje prawy panel i dodaje kreatywne narzędzia działające na już wyliczonej masce obiektu.

### Nowy panel Studio Pro
- Zamiast jednej długiej kolumny są trzy strony: **AI / TWÓRZ / EKSPORT**.
- Kontrolki mogą być większe i czytelniejsze, bo nie muszą być ściskane pionowo.
- Układ jest automatycznie sprawdzany przy **1600×900**.
- Nadal działają procent postępu, LOG diagnostyczny i self-test finalnego EXE.

### Skala i pozycja obiektu
- Nowy suwak **Skala**.
- Nowe suwaki **Pozycja X / Pozycja Y**.
- Zmiany są natychmiastowe po utworzeniu maski i nie uruchamiają AI ponownie.
- Domyślne wartości zachowują wygląd wyników z 0.3.x.

### Kontur / Naklejka
- Opcjonalny kontur wokół obiektu.
- Regulowana grubość.
- Własny kolor konturu.
- Preset **Naklejka** z białym obrysem i przezroczystym tłem.

### Lepszy cień
- Cień nadal można włączać/wyłączać.
- Regulacja krycia.
- Regulacja rozmycia.
- Cień jest renderowany na finalnym płótnie, bez sztucznego powiększania obiektu.

### Lepszy podgląd
- Podgląd wyniku.
- Podgląd na czarnym i białym tle do wykrywania halo.
- Podgląd maski w skali szarości.
- W trybie ręcznej korekty Przywróć/Usuń nadal widać bezpośrednio edytowaną maskę.

### Eksport maski
- Nowy przycisk **Eksportuj maskę PNG**.
- Zapisuje bieżącą maskę alfa jako obraz PNG w skali szarości.
- Jeśli maska była poprawiana ręcznie, eksportuje aktualną poprawioną wersję.

### Presety stylu
- Naklejka.
- Produkt — białe tło, delikatniejszy cień i skala dobrana pod zdjęcia produktowe.
- Portret — rozmyte oryginalne tło.

### Silnik i ustawienia
- Nowe ustawienia Studio Pro są zapisywane lokalnie:
  - skala i pozycja obiektu,
  - kontur / grubość / kolor,
  - krycie i rozmycie cienia,
  - tryb podglądu.
- Dodane testy silnika dla transformacji, konturu, cienia, maski i eksportu maski.
- Dodane testy GUI wszystkich stron Studio Pro.

**BackgroundPXR 0.4.0 moves the project from background removal toward a real creative AI Background Studio.**
