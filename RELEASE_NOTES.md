# BackgroundPXR 0.3.4 — AI Background Studio Foundation

## English

BackgroundPXR 0.3.4 starts the transition from a simple background remover into **AI Background Studio** while keeping the proven 0.3.3 AI runtime and diagnostics.

### AI Background Studio modes
- New first-class Studio selector in the left project panel.
- Four workflow modes: **Cutout / Replace / Blur / Studio**.
- Cutout switches to transparent output.
- Replace reuses the existing custom color or replacement-image workflow.
- Blur reuses the original-image background blur workflow.
- Studio switches to a clean white studio base with soft shadow enabled.
- Alt+1 / Alt+2 / Alt+3 / Alt+4 switch Studio modes quickly.

### Bottom clipping fix
- The always-visible 82px thumbnail strip is now collapsed by default.
- A dedicated **Show thumbnails / Hide thumbnails** control expands it only when needed.
- F6 toggles the thumbnail strip.
- The top tool strip, footer and action-button chrome were compacted without reducing readable text sizes.
- Extra safety margin is reserved at the bottom for Windows taskbars and unusual DPI work areas.

### Readability improvements
- Left project panel widened to approximately 336px.
- Project file rows use readable 10pt text and longer visible file names.
- Studio mode controls use 9–10pt text.
- Important editing and export controls retain readable fonts and minimum button sizes.

### Existing professional tools retained
- High Quality v2 / Quality / Fast / Portrait AI modes.
- Alpha matting and edge refinement.
- Restore / Erase manual mask editor.
- Smart Cleanup, Remove Leftovers, Reset Mask.
- Zoom, pan, Undo / Redo.
- Replace background, custom color, Blur Original and white/transparent output.
- Batch processing and PNG/JPG/WEBP export.
- Live percentage, processing stages and full diagnostics LOG.
- Footer branding: **by Swir • github.com/Swir**.

### Release gate
- Windows smoke test launches the actual 0.3.4 Studio class.
- It verifies the real sidebar, Studio mode selector, collapsed/expanded thumbnail strip, readable fonts, button sizes, right-panel overlap and bottom safety at 1600×900.
- The frozen EXE runtime self-test for rembg/pymatting/onnxruntime/tqdm remains enabled.

---

## Polski

BackgroundPXR 0.3.4 rozpoczyna zmianę programu z prostego removera w pełne **AI Background Studio**, zachowując sprawdzony silnik AI i diagnostykę z wersji 0.3.3.

### Tryby AI Background Studio
- Nowy główny przełącznik Studio w lewym panelu projektu.
- Cztery tryby pracy: **Wytnij / Podmień / Rozmyj / Studio**.
- Wytnij ustawia przezroczyste tło.
- Podmień korzysta z istniejącej podmiany tła obrazem lub własnym kolorem.
- Rozmyj wykorzystuje rozmycie oryginalnego tła.
- Studio ustawia czyste białe tło i automatycznie włącza miękki cień.
- Alt+1 / Alt+2 / Alt+3 / Alt+4 szybko zmieniają tryb Studio.

### Naprawa uciętego dołu
- Pasek miniaturek o wysokości 82px nie jest już stale widoczny.
- Nowy przycisk **Pokaż miniatury / Ukryj miniatury** rozwija go tylko wtedy, gdy jest potrzebny.
- F6 przełącza pasek miniaturek.
- Pasek narzędzi, stopka i wysokości przycisków zostały zwarte bez zmniejszania czytelnych czcionek.
- Na dole zostawiamy dodatkowy zapas dla paska zadań Windows i nietypowego skalowania DPI.

### Lepsza czytelność
- Lewy panel projektu ma około 336px szerokości.
- Wiersze plików projektu korzystają z czytelnej czcionki 10pt i pokazują dłuższe nazwy plików.
- Przełącznik trybów Studio ma 9–10pt.
- Najważniejsze przyciski edycji i eksportu zachowują czytelne rozmiary i minimalne wymiary.

### Zachowane narzędzia profesjonalne
- Najwyższa jakość v2 / Jakość / Szybki / Portret.
- Alpha matting i dopracowanie krawędzi.
- Ręczny edytor maski Przywróć / Usuń.
- Smart Cleanup, Usuń resztki, Reset maski.
- Zoom, przesuwanie, Cofnij / Ponów.
- Podmiana tła, własny kolor, Rozmyj oryginał oraz tło białe/przezroczyste.
- Batch oraz eksport PNG/JPG/WEBP.
- Procent postępu, etapy pracy i pełny LOG diagnostyczny.
- Stopka: **by Swir • github.com/Swir**.

### Kontrola release
- Smoke test Windows uruchamia prawdziwą klasę Studio 0.3.4.
- Sprawdza rzeczywisty sidebar, przełącznik Studio, zwinięty/rozwinięty pasek miniaturek, czcionki, rozmiary przycisków, nakładanie paneli i zapas na dole przy 1600×900.
- Nadal działa self-test finalnego EXE sprawdzający rembg/pymatting/onnxruntime/tqdm.

**0.3.4 is the first release in the AI Background Studio line.**
