# Verification record — updated 12 November 2026

## Latest Windows 11 verification — 12 November 2026 (release 0.2.4)

- Host: Windows 11, Python 3.12.10, Node.js 26.7.0, npm 11.19.0, Git for Windows 2.48.1, Ollama 0.40.16, OpenCode 2.2.5.
- `python -m unittest discover -s tests`: **29/29 passed**, including five new OpenCode detection tests.
- `python -m compileall -q backend host_companion windows`: **passed**.
- `npm run build`: **passed**; the production frontend was built and the Windows setup archive rebuilt.
- `scripts/build-setup-exe.py`: **passed**; the standalone setup executable and the command launcher were rebuilt.
- **OpenCode detection fixed and re-verified.** The inspection previously searched only `PATH` and reported the OpenCode desktop application as "not installed / not configured". It now finds the desktop application folder, the command-line build inside the user-data folder, the npm global command and `PATH`. A live inspection of this PC reports OpenCode as `healthy` at version `2.2.5`, installed as the desktop application, with the user configuration folder recorded. The desktop application is never launched to read its version; the version is read from its metadata.
- **Command launcher verified on a clean profile.** `LIN4CRE-SENTINEL-Setup.cmd` was run with an isolated user profile and local-app-data folder: it downloaded the published release, extracted it, located the interpreter and started both services, which reported `operational`. It was also run against the existing installation, where it opened the setup assistant without downloading anything.
- **Smart App Control observed.** Smart App Control is enabled on this PC (`VerifiedAndReputablePolicyState: 1`) and refuses to run a newly built unsigned executable until it has accumulated a reputation. A rebuilt setup executable was blocked with "An Application Control policy has blocked this file" while an earlier build of the same launcher still ran. The command launcher is not subject to executable reputation and is therefore the recommended download.
- **Deployment script verified.** `scripts/Deploy-Sentinel.ps1` copied and hash-verified 66 files into a clean folder and over the live installation, and both services reported `operational` afterwards. The existing verified recovery point and the settings were preserved.
- The existing verified recovery point `20261112-7b6b0814fcf4` survived the upgrade and remained `verified`.
- Chromium QA was **not rerun** as an automated run: there is no local Chromium/Playwright harness. The console was opened and inspected manually in Chrome at `127.0.0.1:8000`.
- The Android APK is still **not built**: no JDK or Android SDK is available. GitHub CI for `main` still fails before any job step because the account is locked for billing, which is unrelated to this code.

## Prior Windows 11 verification — 12 November 2026 (release 0.2.2)

- Host: Windows 11, Python 3.12.10, Node.js 26.7.0, npm 11.19.0, Git for Windows 2.48.1, Ollama 0.40.16.
- `python -m unittest discover -s tests`: **24/24 passed**.
- `python -m compileall -q backend host_companion windows`: **passed**.
- `npm run build`: **passed**; the production frontend was built and the Windows setup archive rebuilt (2,634,997 bytes, 65 entries, no database, no nested executable).
- `scripts/build-setup-exe.py`: **passed**; the standalone one-click setup executable was rebuilt (11,882,384 bytes).
- **One-click setup verified repeatedly.** `LIN4CRE-SENTINEL-Setup.exe` located the existing installation, located the interpreter through the registry, started the core service (`127.0.0.1:8000`) and the host companion (`127.0.0.1:8765`), completed a read-only inspection, rendered the inspection summary and opened the console. No manual step and no error dialog was produced across repeated runs.
- **Fresh-machine path verified.** The published `v0.2.2` archive was downloaded from the release URL, extracted into an empty folder, and the setup manager started both services from it; `/api/health` and `/v1/status` both reported version `0.2.2` and `operational`.
- **Published assets verified by re-download.** The SHA-256 of both release assets matched the values recorded in the release notes exactly.
- Inspection on this PC reported SENTINEL core, Python, Ollama, Node.js, npm and Git as `healthy`; Docker Desktop/Engine/Compose as `missing` and WSL2 as `unhealthy` because hardware virtualization is not enabled in the BIOS. Setup offered Docker Desktop for review and installed nothing.
- The existing verified recovery point `20261112-7b6b0814fcf4` survived the upgrade and remained `verified`.
- Chromium QA was **not rerun** as an automated run: there is no local Chromium/Playwright harness. The console was opened and inspected manually in Chrome at `127.0.0.1:8000`.
- The Android APK is still **not built**: no JDK or Android SDK is available. GitHub CI for `main` still fails before any job step because the account is locked for billing, which is unrelated to this code.

## Prior sandbox verification — 12 November 2026

- `.venv/bin/python -m unittest discover -s tests -v`: **24/24 passed** (3 mobile companion, 16 upgrade/security/recovery, 5 workflow/scoring).
- `.venv/bin/python -m compileall -q backend host_companion windows`: **passed**.
- `npm ci`: **passed**, 0 vulnerabilities reported by npm during install.
- `npm run build`: **passed**; TypeScript and Vite production build completed. The build now packages the Windows setup archive after the frontend is built and copies the final archive into both `public/downloads/` and `dist/downloads/`.
- Generated archive inspection: **54 entries**; includes the built frontend and setup entry point, and contains no SQLite database.
- `npm audit --omit=dev`: **0 vulnerabilities**.
- Python checks ran on Python 3.11.2 (the documented minimum is Python 3.12); the JavaScript build ran on Node 22.22.3 (the documented target is Node 20).
- Chromium browser QA was **not rerun**: this sandbox has no Chromium executable or Playwright installation. The 11-route/390 px browser results below are from the prior recorded run, not this verification.
- Android APK build was **not possible locally**: no JDK or Android SDK is installed. GitHub Android CI and CI runs for `main` are failed before any job steps because the account is locked due to a billing issue. The Android release workflow dispatch was attempted, but GitHub returned HTTP 403 `Resource not accessible by integration`. There is **no Android APK release asset**; the only published `v0.2.0` assets are Windows installers.
- No Vercel project is configured for SENTINEL, and no Supabase project is used by the app. SENTINEL is designed as a local-first SQLite application; connecting an unrelated account/project would introduce an unnecessary remote data dependency.

## Prior verification record — 11 November 2026

## Automated results

- `python -m unittest discover -s tests -v`: **21/21 passed** in isolated temporary storage.
- `python -m compileall -q backend host_companion windows`: **passed**.
- `npm run build`: **passed**; TypeScript and Vite production bundle completed.
- Chromium browser QA: **11 application routes returned HTTP 200**; assistant explanation and actual empty-ledger response completed; dashboard, Assistant, Maintenance and Recovery fit 390 px mobile viewports; **zero console/page errors**.

### Acceptance paths covered

- Cash-only rejection, policy review and deterministic ranking.
- Exact-scope approvals, evidence validation, human submission and paid-ledger gates.
- Audit modification/deletion rejection.
- Signed-envelope acceptance, tamper/expiry/role rejection and invalid action/model rejection.
- Authenticated host execution and replay blocking.
- Server-side role enforcement despite an owner spoofing header.
- Changed-plan approval rejection.
- Missing/selected dependency planning without execution.
- Failed-install recovery-point creation and honest failure.
- Successful update only with host verification.
- Failed-update registered rollback.
- Backup integrity, corruption detection, exact full database/file/config restoration and history preservation.
- Emergency-stop permission revocation.
- Natural-language real ledger and unsupported-capability responses.
- Installation report with unavailable—not inferred—host state.
- Real isolated code-patch backup/application/syntax verification/reversal and protected-path rejection.
- Code changes correctly unavailable without a verified local model.

External host installers and official update services were not executed by isolated tests; mocks are used only at the host boundary to test core planning/failure behaviour. The code-patch test applies a real patch to a temporary fixture with Git.

## Live application checks

- Controlled restart loaded application version `0.2.0`; SQLite integrity returned `ok`.
- Pre-upgrade live backup: `sentinel-20261111T193129Z-144dba.db`, SHA-256 `252958dab2abf557bc58060f17b8310e65266d464899107afb1d72a57a3c2796`, 135,168 bytes.
- Production business data remained empty: no programmes, findings, reports or payments.
- Windows companion was correctly `not connected`/unpaired in the sandbox; no Windows health was inferred.

## Actual build-environment dependency versions

These are observed sandbox versions, not claimed Windows versions:

| Component | Observed version |
| --- | --- |
| Python | 3.13.16 |
| FastAPI | 0.162.4 |
| Uvicorn | 0.54.0 |
| Pydantic | 2.14.2 |
| HTTPX | 0.28.1 |
| python-multipart | 0.0.33 |
| psutil | 7.2.2 |
| Starlette | 1.10.0 |
| AnyIO | 4.16.0 |
| Node.js | 20.20.2 |
| npm | 10.8.2 |
| Git | 2.47.3 |

`package.json`/`package-lock.json` and `requirements.txt` are the manifests to use for installation; the table is evidence of the tested environment.

## Warnings and unverified targets

- The test harness retains two non-blocking SQLite `ResourceWarning` messages in some runs and the upstream Starlette/httpx TestClient deprecation warning. Tests pass, but these warnings remain cleanup work.
- The sandbox cannot administer the user’s Windows PC. Clean Windows installation, UAC/elevation, restart, Docker Desktop/Engine/Compose, Ollama/models, OpenCode, successful vendor installation/update, failed-update vendor rollback and Windows full restoration remain unverified on that machine.
- Docker is unavailable in the build sandbox; Compose was not executed.
- No real bounty-platform connection, external AI call, Ollama inference, live testing or report submission was made.
- Model updates remain review-only until separate verified model-weight backup/recovery exists.
- WinGet has no universal safe downgrade; only registered rollback paths are claimed.

## Ongoing cost

No required paid API or subscription was introduced. The £0 statement covers SENTINEL’s software charge only, not electricity, hardware, internet or separately approved third-party costs.
