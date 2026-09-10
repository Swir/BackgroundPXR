# BackgroundPXR 0.3.2 — Runtime & Professional UI Hotfix

## English

BackgroundPXR 0.3.2 fixes the frozen Windows AI runtime and rebuilds the studio controls for 1600×900 / high-DPI displays.

### Critical AI runtime fix
- Fixed `importlib.metadata.PackageNotFoundError: No package metadata was found for pymatting` in the Windows portable release.
- `pymatting` is now an explicit application dependency.
- The PyInstaller build uses a dedicated spec file and explicitly bundles distribution metadata required by `pymatting`, `rembg` and `onnxruntime`.
- Every future Windows build now launches the finished `BackgroundPXR.exe --self-test-runtime` before packaging or publishing.
- The frozen self-test imports the real AI stack and verifies package metadata from inside the EXE bundle.
- If the runtime self-test fails, GitHub Actions prints its traceback and blocks the release.
- AI import errors now describe the actual runtime dependency failure instead of incorrectly saying only that `requirements.txt` is missing.

### Professional 1600×900 layout fix
- New `Professional UI` shell keeps the existing AI engine, manual mask editor and diagnostics while rebuilding the right-side studio controls.
- Right panel is wider and uses compact professional spacing rather than vertically oversized cards.
- AI Removal, Refine Edges, Manual Cleanup and Export are all visible together without overlapping.
- Primary buttons retain minimum usable dimensions and no longer collapse into each other.
- Brush Size and Brush Hardness are arranged side-by-side to save vertical space.
- Export controls, progress percentage, LOG button and action buttons remain visible at the bottom.
- Windows launches maximized by default.
- Widget scaling is normalized on 900p/1080p high-DPI displays to prevent CustomTkinter from making the control stack taller than the available workspace.

### New release gate
- The Windows GUI smoke test now forces a 1600×900 window and verifies that all four right-side cards fit inside the panel without overlap.
- The smoke test also verifies minimum sizes for Remove, Restore, Erase, Export and Process All buttons.

All Studio Editor features remain available: High Quality v2, Fast/Quality/Portrait models, alpha matting, Restore/Erase brushes, Smart Cleanup, Remove Leftovers, zoom, pan, Undo/Redo, live percentage and diagnostics LOG.

---

## Polski

BackgroundPXR 0.3.2 naprawia silnik AI w gotowej paczce Windows oraz przebudowuje panel programu pod 1600×900 i skalowanie DPI Windows.

### Krytyczna naprawa silnika AI
- Naprawiono błąd `importlib.metadata.PackageNotFoundError: No package metadata was found for pymatting` z wersji portable Windows.
- `pymatting` jest teraz jawną zależnością programu.
- PyInstaller korzysta z osobnego pliku spec i pakuje metadane wymagane przez `pymatting`, `rembg` oraz `onnxruntime`.
- Każdy kolejny build Windows przed utworzeniem ZIP-a uruchamia gotowy `BackgroundPXR.exe --self-test-runtime`.
- Self-test sprawdza prawdziwy stos AI i metadane pakietów już wewnątrz gotowego EXE.
- Jeśli test runtime nie przejdzie, GitHub Actions pokazuje traceback i blokuje publikację release.
- Błędy importu AI pokazują teraz rzeczywistą przyczynę problemu zamiast mylącego komunikatu o `requirements.txt`.

### Naprawa Professional UI 1600×900
- Nowa warstwa `Professional UI` zachowuje działający silnik, edytor maski i diagnostykę, ale przebudowuje prawy panel programu.
- Panel po prawej jest szerszy i ma zwarte, profesjonalne odstępy zamiast zbyt wysokich kart.
- Usuwanie AI, Dopracuj krawędzie, Ręczne poprawki i Eksport są widoczne jednocześnie i nie nachodzą na siebie.
- Najważniejsze przyciski zachowują minimalny użyteczny rozmiar i nie są zgniatane.
- Rozmiar i twardość pędzla są ustawione obok siebie, dzięki czemu odzyskaliśmy miejsce w pionie.
- Eksport, procent postępu, LOG i przyciski akcji pozostają widoczne na dole.
- Na Windows program uruchamia się domyślnie zmaksymalizowany.
- Na ekranach 900p/1080p normalizujemy skalowanie widgetów, żeby DPI Windows nie rozciągało panelu poza obszar programu.

### Nowa blokada wadliwych wydań
- Smoke test Windows wymusza teraz rozdzielczość 1600×900 i sprawdza, czy wszystkie cztery prawe karty mieszczą się bez nakładania.
- Sprawdzana jest również minimalna wielkość przycisków Usuń tło, Przywróć, Usuń, Eksportuj i Przetwórz wszystkie.

Pozostają wszystkie funkcje Studio Editor: High Quality v2, tryby Szybki/Jakość/Portret, alpha matting, pędzle Przywróć/Usuń, Smart Cleanup, Usuń resztki, zoom, przesuwanie, Cofnij/Ponów, procent postępu i pełny LOG diagnostyczny.
