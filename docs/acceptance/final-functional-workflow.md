# BackgroundPXR 1.0 final functional workflow gate

This document is the witness protocol for roadmap acceptance item 9. The item stays unchecked until release-grade Windows automation is green **and** a real human observation exists for the release-blocking Windows runtime path. No runtime/source change may be introduced after that observation without invalidating it.

## Automated prerequisites

The release policy head and the final publication head must be green for the maintained Windows checks, including:

- Python syntax and unit/regression tests;
- the fixed 1600×900 GUI gate plus supported HiDPI/resize coverage;
- UI evidence checks;
- the frozen `BackgroundPXR.exe --self-test-runtime` gate;
- qualification ZIP, `BUILD_INFO.txt`, SHA-256 and package verification;
- the **real High Quality v2 + alpha-matting Windows smoke**, which downloads/loads the production `birefnet-general` model, performs a real inference and requires the alpha-matting path to complete.

`--self-test-runtime` also contains the deterministic integrated Studio workflow probe. Without downloading a model it verifies image decode, synthetic cutout hand-off, manual Restore/Erase with Undo/Redo, Studio composition with transform/outline/shadow/background, PNG/JPG/WebP export, and mask export from inside the frozen executable.

The real-AI smoke complements this deterministic workflow by proving that the external AI model/runtime path actually works on a clean Windows runner.

## Manual Windows evidence

Two evidence formats are accepted.

### A. Full eight-step witness

The original one-click witness kit remains valid. A human may run `START-WITNESS.cmd` and explicitly pass all eight steps recorded by `BackgroundPXR-Witness.exe`. This produces schema-version 1 evidence and is the most detailed manual route.

### B. Runtime-equivalent owner attestation

For a release-blocking defect that was reproduced and then re-tested by the project owner on a real Windows package, schema-version 2 evidence may record that observation when all of the following are true:

1. the tested package is a verifiable `1.0.0rc1` Windows ZIP with source SHA and SHA-256 provenance;
2. the human explicitly confirms the corrected **High Quality v2 + alpha matting** path works on Windows;
3. the later policy head differs from that tested source only in explicitly allowed release-gate hardening, tests, witness tooling or release metadata;
4. no application runtime file, dependency manifest or packaging input changes after the human observation;
5. the final publication head differs from the frozen policy head only by the metadata-only 1.0 promotion set;
6. all automated Windows, UI, real-AI, frozen-runtime and package gates are green on the release path.

`tools/verify_promotion.py` enforces items 3–5. This route does **not** convert a casual statement into broad UI evidence: the human observation covers the actual Windows runtime/AI regression, while the maintained automated suites cover the deterministic Studio workflow, 1600×900/HiDPI UI behavior, export and frozen-runtime/package integrity.

Any later runtime/source change invalidates the attestation and requires a new Windows observation.

## Evidence record

Schema-version 2 records:

- tested candidate version, archive name, source SHA and ZIP SHA-256;
- the frozen release-policy head SHA;
- explicit `pass` status;
- Windows platform;
- observed path: `High Quality v2 + alpha matting`;
- a concise human-observation statement and date.

Do not invent missing observations. A failed, pending or non-Windows attestation is release-blocking.

## One-click witness kit

After a successful `main` qualification run, the `Windows witness kit` workflow still creates a short-lived artifact named `BackgroundPXR-witness-kit-<source_sha>`. It contains the exact qualification ZIP/checksum, standalone witness recorder, `START-WITNESS.cmd`, this protocol and provenance metadata.

The kit remains the preferred route when a new manual pass is required. The hybrid attestation route exists only so a **real, already-observed Windows regression retest** can remain valid while release-only CI/evidence tooling is strengthened without changing application runtime bits.

## Completion rule

Roadmap item 9 may move to complete only when:

- the human evidence is valid;
- no known critical release-blocking defect remains;
- the exact policy/release path is green for all required Windows automation;
- promotion verification proves there was no unobserved runtime change.

This gate authorizes only the 1.0 promotion. Publication, checksum/provenance verification and post-release smoke remain roadmap item 10.
