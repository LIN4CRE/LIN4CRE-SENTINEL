# Changelog

## 0.2.2 — 2026-11-12

### Added

- A single-file `LIN4CRE-SENTINEL-Setup.exe` that sets SENTINEL up with one double-click. It finds an existing installation, otherwise downloads and installs the official release archive, locates a real Python interpreter and opens the graphical setup manager.
- Automatic interpreter discovery through the Windows registry and the standard per-user and machine-wide install folders, ignoring the Microsoft Store alias stub.
- The setup manager now shows an inspection summary instead of the placeholder text, and opens the operations console when it starts the private local services.
- A reproducible build script for the standalone setup executable.

### Fixed

- The setup launcher no longer treats an already installed Python as missing, and no longer offers to install a second interpreter.
- The setup manager resolves the application folder from the launcher instead of assuming it sits next to the script.
- The Windows setup archive no longer embeds the setup executable.

### Verification

24/24 isolated tests pass. The production frontend build, the Windows setup archive and the standalone setup executable were rebuilt. The one-click executable was launched repeatedly on Windows 11: it located the installation, started the core and host-companion services, completed a read-only inspection and opened the console with no manual step.

## 0.2.1 — 2026-11-12

### Fixed

- Windows setup now runs a read-only inspection automatically once the local services are up, instead of waiting for a manual re-scan.
- The setup manager can reveal and edit the paired companion token without tripping over a hidden widget state.
- Host inspection accepts `OLLAMA_HOST` values without a URL scheme and reports Ollama as healthy.
- The Windows setup archive now ships the `scripts/` directory, so the packaged tooling is present after extraction.
- Full restore releases the SQLite handle on Windows, so corruption detection and restore complete without a locked database.

### Verification

All 24 isolated tests pass on Windows 11 with Python 3.12.10. Python compilation, the production frontend build and the rebuilt Windows setup ZIP also passed. Core and host-companion services, Ollama inspection and recovery-point creation were exercised end to end. Docker/WSL2 enablement remains an administrative target-hardware task.

## 0.2.0 — 2026-11-11

### Added

- Conversational AI operations console with persisted conversations and registered intents.
- Real host-companion inspection, authenticated backup, official update discovery and allowlisted execution.
- Dependency registry, periodic read-only monitoring and maintenance interfaces.
- Exact-plan owner approvals, server-side role enforcement, HMAC envelopes and replay protection.
- Verified recovery points, corruption detection, selective exact restore and automatic safety points.
- Repeatable graphical Windows setup manager and native missing-Python bootstrap.
- Constrained, human-approved local-model code patches with source backup and reverse verification.
- Installation-report export, emergency stop and complete GitHub community/CI documentation.

### Security and reliability

- Prevented role elevation through request headers.
- Added fail-closed replay state and lock-protected nonce recording.
- Fixed SQLite connection lifecycle and pre/post-restore WAL handling.
- Preserved later audit/operation history during restoration and revoked restored approvals.
- Added exact file-set restoration and file rollback rather than merge-only recovery.
- Separated core and host backup/emergency outcomes with honest `partial` status.

### Verification

21 isolated automated tests passed; Python compilation and production frontend build passed. Chromium QA passed 11 routes, real assistant interactions and 390 px mobile layouts without console/page errors. Windows administration and Docker execution remain target-platform validation tasks.

## 0.1.0 — 2026-11-11

Initial local research-operations milestone: cash-only eligibility, explainable ranking, exact-scope approvals, evidence records, human validation, reports, actual payment ledger, audit controls and verified SQLite backup.
