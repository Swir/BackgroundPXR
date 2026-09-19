# Windows HiDPI / resize acceptance — 2026-09-19

Acceptance item: dedicated Windows HiDPI/resize/manual UX pass for BackgroundPXR 1.0.

## Evidence

- Production branch under review: `quality/ui-visual-evidence`.
- Pre-fix evidence head: `ae55c094a4ee7ee71535af32e16e9e5551a0b948`.
- Pre-fix visual-evidence run: `35471186601`.
- Replacement evidence head: `ac33d4a1d26d5aba64ad16b347f95339ce210899`.
- Replacement visual-evidence run: `35471597540`.
- Replacement artifact digest: `sha256:0c25f3f309e0e03b944a717457347820c8be04bec0463cdd64cd9e82b208f556`.
- Windows build/test run for the replacement head: `35471597537`.

The visual-evidence workflow provisions a real 1600×900 Windows runner and captures the production Studio at 100%, 125% and 150% UI scaling. Each scale records AI, Create, Export, Create/Compare and reduced-window Create views. The regular Windows smoke matrix independently covers 1600×900, 125%/150% scaling, reduced desktops, readable controls, permanent `by Swir` + `github.com/Swir` branding and the manual Restore/Erase/Undo/Redo workflow.

## Regression found and resolved

The first evidence artifact exposed a genuine reduced-window defect: preview placeholder content retained coordinates from the larger geometry and was clipped after the window shrank. `BackgroundPXRStudio051App` now coalesces preview `<Configure>` events and redraws after geometry settles. Focused unit coverage verifies the resize debounce and final refresh behavior.

## Replacement visual review

All 15 replacement captures were inspected after the fix:

- 100%, 125% and 150% AI/Create/Export layouts are readable and unclipped.
- Create/Compare remains usable at all three scales.
- Reduced-window Create views keep both preview placeholders centered and fully visible.
- Inspector controls remain visible without overlap or unreadable text.
- Permanent `by Swir` and `github.com/Swir` branding remains visible and unclipped.
- No release-blocking blank panel, clipping or overlap was observed.

Result: **PASS** for the dedicated HiDPI/resize/manual UX acceptance item. This evidence does not satisfy the separate 1.0 release-candidate package or final release gates.
