# BackgroundPXR 0.3.3 — Model Download & Readable UI Fix

## English

BackgroundPXR 0.3.3 fixes the first-run AI model download crash in the Windows portable build and improves readability on 1600×900 / high-DPI displays.

### First-run AI model download fix
- Fixed `AttributeError: 'NoneType' object has no attribute 'write'` raised by `tqdm` while `rembg`/`pooch` downloads an AI model.
- The cause was PyInstaller `--windowed`: Windows GUI executables can start with `sys.stdout` and `sys.stderr` set to `None`.
- BackgroundPXR now creates safe writable fallback streams before `rembg`, `pooch` or `tqdm` can be reached.
- Running from source is unchanged: normal console streams remain untouched.
- The frozen EXE self-test now creates a real `tqdm` progress probe on `stderr`, reproducing the writer path used during model downloads.
- The existing frozen runtime checks for `pymatting`, `rembg`, `onnxruntime` and package metadata remain enabled.
- A release is blocked automatically if the final EXE fails any runtime check.

### Readable 1600×900 Studio UI
- Removed the 0.88 global widget scaling that made the 0.3.2 interface too small.
- Important UI text is now 9 pt or larger, with larger project/sidebar controls and clearer status text.
- The left project panel is wider and the Clear button has reserved width so Polish labels are not clipped.
- The right studio panel is also wider for Polish text and longer model/background names.
- The four studio cards use explicit compact label heights rather than shrinking the fonts.
- AI Removal, Refine Edges, Manual Cleanup and Export remain visible together without a whole-panel scrollbar.
- Footer text and the GitHub/by Swir area are more readable.

### Verified layout
- Automated GUI testing verifies the final Studio shell rather than the older intermediate UI class.
- At the Windows CI test workspace the right panel measured 682 px high; the complete card stack ended at 609 px, leaving roughly 73 px of safety margin.
- The test verifies the left sidebar width, Clear button bounds, card overlap, Export visibility, minimum button sizes and minimum readable font sizes.
- Unit tests also reproduce the no-console `stdout/stderr` condition used by a PyInstaller windowed executable.

All existing functions remain available: local AI background removal, High Quality v2 / Quality / Fast / Portrait modes, alpha matting, manual Restore/Erase editing, Smart Cleanup, Remove Leftovers, replacement backgrounds, zoom/pan, Undo/Redo, batch processing, PNG/JPG/WebP export, live percentage and diagnostics LOG.

---

## Polski

BackgroundPXR 0.3.3 naprawia błąd pobierania modelu AI przy pierwszym uruchomieniu wersji portable Windows oraz poprawia czytelność interfejsu na 1600×900 i ekranach z wyższym DPI.

### Naprawa pobierania modelu AI
- Naprawiono błąd `AttributeError: 'NoneType' object has no attribute 'write'`, który pojawiał się w `tqdm` podczas pobierania modelu przez `rembg`/`pooch`.
- Przyczyną był tryb PyInstaller `--windowed`: aplikacja GUI Windows może uruchomić się z `sys.stdout` i `sys.stderr` ustawionymi na `None`.
- BackgroundPXR tworzy teraz bezpieczne zapisywalne strumienie zanim kod dotrze do `rembg`, `pooch` albo `tqdm`.
- Uruchamianie programu ze źródeł pozostaje bez zmian — normalna konsola nie jest podmieniana.
- Self-test gotowego EXE uruchamia teraz prawdziwy testowy pasek `tqdm` zapisujący do `stderr`, czyli dokładnie ścieżkę używaną przy pobieraniu modelu.
- Nadal sprawdzane są `pymatting`, `rembg`, `onnxruntime` i ich metadane wewnątrz gotowego EXE.
- Jeżeli finalny EXE nie przejdzie testów runtime, release zostaje automatycznie zablokowany.

### Czytelny Studio UI 1600×900
- Usunięto globalne skalowanie 0.88 z wersji 0.3.2, które zbyt mocno pomniejszało cały interfejs.
- Ważne teksty interfejsu mają teraz co najmniej 9 pt, powiększone są również główne kontrolki projektu i status.
- Lewy panel projektu jest szerszy, a przycisk Wyczyść ma zarezerwowaną szerokość, więc polskie napisy nie powinny być ucinane.
- Prawy panel Studio jest również szerszy, żeby pomieścić dłuższe polskie nazwy.
- Cztery karty po prawej oszczędzają miejsce przez mniejsze wysokości pustych wierszy etykiet, a nie przez zmniejszanie czcionek.
- Usuwanie AI, Dopracuj krawędzie, Ręczne poprawki i Eksport pozostają widoczne jednocześnie bez przewijania całego panelu.
- Stopka `by Swir` i link GitHub są bardziej czytelne.

### Zweryfikowany układ
- Test GUI sprawdza teraz finalną klasę Studio, a nie wcześniejszą pośrednią wersję interfejsu.
- W środowisku testowym Windows prawy panel miał 682 px wysokości, a komplet kart kończył się na 609 px — około 73 px zapasu.
- Test sprawdza szerokość lewego panelu, granice przycisku Wyczyść, brak nakładania kart, widoczność Eksportu, minimalne rozmiary przycisków i minimalny rozmiar ważnych czcionek.
- Test jednostkowy odtwarza również sytuację bez konsoli, czyli `stdout/stderr=None`, występującą w aplikacji PyInstaller `--windowed`.

Pozostają wszystkie dotychczasowe funkcje: lokalne usuwanie tła AI, tryby Najwyższa jakość v2 / Jakość / Szybki / Portret, alpha matting, ręczne Przywróć/Usuń, Smart Cleanup, Usuń resztki, podmiana tła, zoom/przesuwanie, Cofnij/Ponów, batch, eksport PNG/JPG/WebP, procent postępu oraz LOG diagnostyczny.
