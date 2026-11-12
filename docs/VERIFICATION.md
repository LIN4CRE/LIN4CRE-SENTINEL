# Verification record — updated 12 November 2026

## Latest sandbox verification — 12 November 2026

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
