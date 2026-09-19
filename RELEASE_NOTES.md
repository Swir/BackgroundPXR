# BackgroundPXR 1.0.0rc1 — Release Candidate 1

> **Qualification candidate only.** This is not a published GitHub Release. Public downloads remain on v0.4.0 until every 1.0 acceptance gate is verified.

## English

BackgroundPXR 1.0.0rc1 is the first exact 1.0 release-candidate package for the Studio Pro workflow. It consolidates the local AI engine, manual mask refinement, creative composition tools, safer export path and the Windows UI/HiDPI work completed on the road to 1.0.

### Studio Pro workflow
- Local AI background removal with supported Fast, Quality, High Quality v2 and Portrait processing modes.
- Cutout, Replace, Blur and Studio composition modes.
- Manual Restore/Erase refinement with zoom, pan, brush controls, cleanup helpers and Undo/Redo.
- Subject scale and position controls without rerunning AI.
- Outline/sticker and adjustable shadow controls.
- Result, mask, black-matte and white-matte previews plus mask PNG export.

### Export and reliability
- PNG/JPG/WebP export with canvas presets and filename suffixes.
- Collision-safe output naming so existing exports and source files are not overwritten.
- Atomic export writes to reduce the risk of partial/corrupted output files.
- Localized single-export failure guidance with stable diagnostic IDs.
- Batch processing keeps progress/heartbeat diagnostics and reports partial failures without discarding successful results.

### Windows UI acceptance
- The fixed 1600×900 Windows smoke gate remains required.
- 125% and 150% Windows UI scaling are covered by the automated acceptance matrix.
- Dedicated visual evidence at 100%, 125% and 150% scaling was reviewed after fixing stale preview geometry on resize.
- The permanent `by Swir` and `github.com/Swir` branding remains part of the packaged documentation and application identity.

### Release-candidate qualification
The pull-request Windows pipeline must build the portable PyInstaller package from the exact candidate source head, verify bundled `rembg` / `pymatting` / `onnxruntime` metadata, run `BackgroundPXR.exe --self-test-runtime`, create the ZIP and SHA-256 sidecar, and pass `tools/verify_release_package.py` before this candidate can satisfy the roadmap package gate.

The final 1.0 GitHub Release is still blocked until the remaining functional/regression/manual-workflow gate is complete and the final package is published with post-release smoke verification.

---

## Polski

BackgroundPXR 1.0.0rc1 to pierwszy dokładny kandydat do wydania 1.0 dla workflow Studio Pro. Łączy lokalny silnik AI, ręczną korektę maski, narzędzia kompozycji, bezpieczniejszy eksport oraz poprawki Windows/HiDPI wykonane na drodze do 1.0.

### Workflow Studio Pro
- Lokalne usuwanie tła AI w trybach Fast, Quality, High Quality v2 i Portrait.
- Tryby Wytnij, Podmień, Rozmyj i Studio.
- Ręczna korekta Przywróć/Usuń z zoomem, przesuwaniem, ustawieniami pędzla, narzędziami czyszczenia i Cofnij/Ponów.
- Skala i pozycja obiektu bez ponownego uruchamiania AI.
- Kontur/naklejka i regulowany cień.
- Podgląd wyniku, maski, czarnego/białego tła oraz eksport maski PNG.

### Eksport i niezawodność
- Eksport PNG/JPG/WebP, presety płótna i własne suffixy nazw.
- Nazwy wyjściowe odporne na kolizje — bez nadpisywania istniejących eksportów ani plików źródłowych.
- Atomowy zapis eksportu ograniczający ryzyko częściowych/uszkodzonych plików.
- Lokalizowane komunikaty błędów eksportu z trwałymi identyfikatorami diagnostycznymi.
- Batch zachowuje telemetrię postępu/heartbeat i raportuje częściowe błędy bez utraty poprawnych wyników.

### Akceptacja Windows UI
- Obowiązkowy test Windows 1600×900.
- Automatyczna macierz skali 125% i 150%.
- Dedykowane screeny 100%, 125% i 150% zostały zweryfikowane po naprawie geometrii podglądu przy zmianie rozmiaru okna.
- Stały branding `by Swir` oraz `github.com/Swir` pozostaje w dokumentacji pakietu i identyfikacji aplikacji.

### Kwalifikacja kandydata
Pipeline Windows na Pull Request musi zbudować przenośny pakiet PyInstaller dokładnie z tego źródłowego head, zweryfikować metadane `rembg` / `pymatting` / `onnxruntime`, uruchomić `BackgroundPXR.exe --self-test-runtime`, utworzyć ZIP i plik SHA-256 oraz przejść `tools/verify_release_package.py`, zanim kandydat spełni bramkę pakietu w roadmapie.

Finalny GitHub Release 1.0 pozostaje zablokowany do ukończenia końcowej bramki funkcjonalnej/regresyjnej/manualnej i późniejszej weryfikacji paczki po publikacji.
