# BackgroundPXR 0.3.1 — Live Diagnostics

## English

BackgroundPXR 0.3.1 focuses on visibility, reliability and easier troubleshooting during AI processing.

### Live processing status
- A permanent numeric percentage is shown next to the progress bar.
- The status line shows the current stage, current file and batch position.
- Stages include opening the image, AI/model processing, edge refinement, composing the result and saving.
- During long AI inference or first-time model loading, a live elapsed-seconds heartbeat updates every second so the app no longer looks frozen.
- Batch percentage is calculated across the whole queue, not only the current file.

### Error diagnostics
- New **LOG** button beside the progress/status area.
- The LOG button turns red and displays the number of errors when something fails.
- Single-image processing errors automatically open the diagnostics window.
- Every technical error receives a report ID such as `PXR-20260910-...`.
- Full exception type, message and traceback are saved locally instead of being hidden or printed only to the console.
- Processing, composition and export failures are now surfaced to the user.

### Diagnostics window
- Live session history in a dedicated dark PXR diagnostics window.
- Copy the full report to clipboard with one click.
- Open the local log folder directly from the app.
- Clear the current log from the interface.
- The persistent log is stored under the local BackgroundPXR application data folder.
- Logs rotate automatically so the main log does not grow forever.

### Reliability
- Added automated tests for progress calculation, persistent logging and error report IDs.
- The Windows GUI smoke test now starts the diagnostics-enabled application and verifies the percentage and LOG controls exist.
- Existing 0.3.0 Studio Editor features remain available: High Quality v2, alpha matting, Restore/Erase brushes, zoom, pan, Undo/Redo and manual mask cleanup.

The percentage represents deterministic processing checkpoints and completed batch work. Neural-network inference itself does not expose a trustworthy frame-by-frame percentage, so BackgroundPXR shows the AI stage plus a live elapsed timer while that step is running rather than inventing fake progress.

---

## Polski

BackgroundPXR 0.3.1 koncentruje się na pełnej informacji o pracy programu, stabilności i łatwiejszym naprawianiu problemów.

### Status pracy na żywo
- Obok paska postępu jest stale widoczny procent wykonania.
- Linia statusu pokazuje aktualny etap, nazwę pliku i pozycję w kolejce.
- Etapy obejmują: otwieranie zdjęcia, pracę AI/modelu, dopracowanie krawędzi, składanie wyniku i zapis.
- Podczas długiego liczenia AI albo pierwszego pobierania/ładowania modelu co sekundę aktualizuje się licznik czasu, więc program nie wygląda jak zawieszony.
- W trybie batch procent liczony jest dla całej kolejki, a nie tylko jednego zdjęcia.

### Diagnostyka błędów
- Nowy przycisk **LOG** obok paska postępu i statusu.
- Gdy pojawi się problem, LOG zmienia kolor na czerwony i pokazuje liczbę błędów.
- Przy błędzie jednego przetwarzanego zdjęcia okno diagnostyczne otwiera się automatycznie.
- Każdy błąd techniczny dostaje własny identyfikator, np. `PXR-20260910-...`.
- Pełny typ wyjątku, komunikat i traceback są zapisywane lokalnie zamiast znikać albo trafiać wyłącznie do konsoli.
- Błędy przetwarzania, składania obrazu i eksportu są teraz widoczne dla użytkownika.

### Okno diagnostyczne
- Historia bieżącej sesji w osobnym ciemnym oknie PXR.
- Jednym kliknięciem można skopiować cały raport do schowka.
- Z programu można bezpośrednio otworzyć folder z logami.
- Można wyczyścić bieżący dziennik.
- Log jest przechowywany lokalnie w danych aplikacji BackgroundPXR.
- Log automatycznie się rotuje, żeby plik nie rósł bez końca.

### Stabilność
- Dodane testy obliczania procentów, zapisywania logów i identyfikatorów błędów.
- Smoke test Windows uruchamia teraz wersję z diagnostyką i sprawdza, czy procent oraz przycisk LOG naprawdę powstały w GUI.
- Wszystkie funkcje Studio Editor 0.3.0 pozostają: High Quality v2, alpha matting, pędzle Przywróć/Usuń, zoom, przesuwanie, Cofnij/Ponów i ręczne poprawki maski.

Procent oznacza rzeczywiste, kontrolowane etapy przetwarzania oraz postęp kolejki. Samo liczenie sieci neuronowej nie udostępnia wiarygodnego procentu „w środku” operacji, dlatego podczas tego etapu BackgroundPXR pokazuje nazwę etapu i działający licznik sekund zamiast udawać fałszywy postęp.
