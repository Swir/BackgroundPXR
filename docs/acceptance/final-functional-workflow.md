# BackgroundPXR 1.0 final functional workflow gate

This document is the witness protocol for roadmap acceptance item 9. The item must remain unchecked until the exact release-candidate package passes the automated prerequisites below **and** a human completes the manual Windows workflow without a critical release-blocking defect.

## Automated prerequisites

The exact candidate head must be green for all maintained Windows checks, including:

- Python syntax and unit/regression tests;
- the fixed 1600×900 GUI gate and supported HiDPI/resize matrix;
- UI evidence capture/review checks;
- the frozen `BackgroundPXR.exe --self-test-runtime` gate;
- qualification ZIP, `BUILD_INFO.txt`, SHA-256 and package verification.

`--self-test-runtime` now includes a deterministic integrated workflow probe. Without downloading a model it verifies image decode, synthetic cutout hand-off, manual Restore/Erase with Undo/Redo, Studio composition with transform/outline/shadow/background, PNG/JPG/WebP export, and mask export from inside the frozen executable.

## Manual Windows witness

Run these steps from the exact qualification ZIP that will be promoted to 1.0:

1. Extract the ZIP to a clean folder and launch `BackgroundPXR.exe`; confirm startup has no crash or console dependency and the permanent **by Swir** plus **github.com/Swir** branding is visible.
2. Import at least one JPG and one PNG, run the normal AI removal flow with a supported model, and confirm the subject preview updates correctly.
3. In manual refinement, use **Erase** and **Restore**, change brush size/hardness, zoom/pan/Fit, then verify **Undo** and **Redo** restore the expected mask states.
4. In Studio Pro, exercise Cutout plus at least two composed modes among Replace/Blur/Studio; change subject scale/position and enable outline and shadow. Verify the preview remains responsive and visually coherent.
5. Export PNG, JPG and WebP plus a mask. Confirm outputs open successfully, use the selected canvas/suffix, preserve intended transparency where supported, and never overwrite the source or an existing export silently.
6. Run one small batch with at least two images. Confirm progress/diagnostics remain usable and a single-file failure is reported without crashing or losing successful outputs.
7. Switch between English and Polish and confirm the main import/process/manual/export workflow remains understandable and controls are not clipped at the tested Windows scaling.
8. Open diagnostics/log access and confirm a failure can be identified without exposing unrelated private paths or breaking the session.

## Evidence record

Record the following with the pass:

- candidate version and exact `source_sha` from `BUILD_INFO.txt`;
- ZIP SHA-256;
- Windows version and display scaling used;
- AI model used for the manual pass;
- pass/fail for steps 1–8 and any defect IDs/notes.

Only after all steps pass with no known critical release-blocking defect may roadmap item 9 be checked and progress move from 8/10 to 9/10. This protocol does not authorize a GitHub Release; publication and post-release smoke verification remain roadmap item 10.
