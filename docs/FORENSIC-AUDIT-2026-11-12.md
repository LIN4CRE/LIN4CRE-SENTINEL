# LIN4CRE SENTINEL — Forensic Audit Report

**Date:** 2026-11-12
**Repository:** `LIN4CRE/LIN4CRE-SENTINEL`
**Release under audit:** v0.2.4 (tag `v0.2.4`)
**Baseline commit:** `211640aa48ea629098b1cd20c6a7963f60d7033b`
**Audit branch:** `arena/e06cb42d-lin4cre-sentinel`
**Scope:** Evidence-based forensic audit across 11 phases — repository preservation, inventory, functional audit, security forensics, Windows installer, Docker, Android, dependency/supply-chain, automated testing/CI, remediation (P0–P3), and verification.

> **Honesty note.** Every classification below (PASS / FAIL / BLOCKED / NOT RUN / UNVERIFIED) reflects what was actually executed in this environment. Tests that could not run are reported as BLOCKED, never as passing. Three code defects were found and fixed; each fix has a regression test that reproduces the original defect.

---

## 0. Executive summary

| # | Area | Outcome |
|---|------|---------|
| 1 | Repository preservation & inventory | **PASS** — 159 tracked files, 3.6 MB, clean tree at baseline |
| 2 | Functional audit (live API) | **PASS** — 51 end-to-end checks pass against a real running server |
| 3 | Security forensics | **PASS with 3 findings fixed** — no open critical vulnerabilities remain |
| 4 | Windows installer | **PASS with 1 defect fixed** — zip-slip in release extraction |
| 5 | Docker | **BLOCKED (build)** / **PASS (static review)** — Docker absent; config is hardened |
| 6 | Android | **BLOCKED (build)** / **PASS (static review)** — Gradle/JDK absent; app is read-only & HTTPS-only |
| 7 | Dependency / supply-chain | **PASS** — `npm audit` 0 vulnerabilities; Python deps range-pinned |
| 8 | Automated testing / CI | **PASS (code) / BLOCKED (GitHub Actions)** — all steps pass locally; GitHub CI blocked by account billing lock, not by code |
| 9 | Remediation P0–P3 | **PASS** — 3 defects fixed with regression tests |
| 10 | Verification | **PASS** — full suite 46/46; recovery round-trip 16/16; frontend static 19/19 |

**Three defects found and fixed:**

1. **[P0 — security] Zip-slip in Windows release extraction** (`windows/sentinel_runtime.py`) — an archive entry could write outside the extraction root. Fixed with an exact `relative_to` containment check.
2. **[P1 — correctness/security] Core app returned the SPA HTML shell (HTTP 200) for unknown `/api/*` paths** (`backend/main.py`) — masked real API failures and falsely served the mobile companion routes. Fixed to return a JSON 404.
3. **[P1 — functional] `SENTINEL_HOST_COMPANION_URL` environment override was ignored** (`backend/host_client.py`) — the Windows setup manager and deploy script exported it, but the backend dialed `host.docker.internal:8765`, which does not resolve on Windows. Fixed to honour the override (loopback-only, operator setting wins).

---

## 1. Repository preservation & inventory

- **Remote:** `https://github.com/LIN4CRE/LIN4CRE-SENTINEL.git`
- **Tracked files:** 159, total 3.6 MB.
- **Secrets hygiene:** only `data/.gitkeep` is committed; no `sentinel.db`, `host-token`, `.env`, or credential files are tracked. `.gitignore` excludes `data/`, `host_data/`, `logs/`, `build/`, `*.pyc`, `.env`, Android outputs.
- **Releases:** v0.2.0–v0.2.4 (5 releases); tag `v0.2.4` is the latest.
- **Branch:** `arena/e06cb42d-lin4cre-sentinel`, branched from `main` @ `211640a`. Working tree was clean at baseline; changes made during this audit are listed in §9.

### Inventory

| Directory | Contents |
|-----------|----------|
| `backend/` | 15 Python modules (~2,400 LOC): `main.py`, `db.py`, `scoring.py`, `recovery.py`, `operations.py`, `operation_security.py`, `host_client.py`, `mobile_auth.py`, `mobile_pairing.py`, `mobile_api.py`, `mobile_main.py`, `monitor.py`, `assistant.py`, `maintenance.py`, `inspection.py` |
| `host_companion/` | Windows host companion ASGI server (`server.py`, `executor.py`, `inspector.py`, `backup.py`) |
| `windows/` | Windows launcher, setup manager, runtime helpers, bootstrap, install scripts |
| `android/` | Android read-only companion (Java, Gradle) |
| `scripts/` | PowerShell deployment/backup/audit scripts + Node/Python build scripts |
| `src/` | React/TypeScript frontend (11 routes) |
| `tests/` | unittest suite (workflow, upgrade acceptance, inspection) + Playwright QA |
| `.github/workflows/` | `ci.yml`, `android-ci.yml` |
| `docs/` | ANDROID, WINDOWS_SETUP, VERIFICATION, OPERATIONS, RESTORE, SOURCES, IMPLEMENTATION_PLAN |
| `Dockerfile`, `compose.yaml` | Container deployment |

---

## 2. Functional audit (live API)

**Method:** Ran `backend.main:app` on `127.0.0.1:8137` with an isolated data dir (`SENTINEL_DATA_DIR=/tmp/sentinel-audit-data`), monitor disabled, and a test host token. Exercised the full research workflow via a purpose-built end-to-end check (`.audit/e2e_api_check.py`, urllib only).

**Result: 51/51 checks PASS.**

Coverage includes:

- **Health & config:** `/api/health` operational; testing engine + auto-submission disabled; sources and scoring endpoints expose real data; dashboard returns real counts.
- **Programme lifecycle:** creation succeeds; cash-only eligibility enforced; duplicate canonical URL rejected (409); non-cash-payout programme rejected by `scoring.py`.
- **Approval state machine:** pending → approved (200); approved → revoked (200); revoked → any decision (409); re-approval of an approved approval is a re-affirmation (200); out-of-scope asset rejected (422).
- **Finding → validate → report → submit → accept → pay:** finding requires an active approval; empty evidence refused at validation (422); validation requires explicit human confirmation; validated finding is evidence-locked (immutable); duplicate report rejected (409); submission without human confirmation refused (422); human-confirmed submission recorded; payment requires an accepted report and a payment date.
- **Audit log:** append-only (DELETE raises `sqlite3.IntegrityError`).
- **Kill switch:** activates; revokes pending and active approvals; blocks approval decisions (423) and new approval requests (423) while active; resets cleanly.
- **Backup & export:** verified backup created with SHA-256 manifest; path traversal does not disclose files; backslash traversal refused (400); data export returns all core tables.

---

## 3. Security forensics

### 3.1 Security boundaries — all preserved

| Boundary | Status | Evidence |
|----------|--------|----------|
| Desktop app loopback-only (core on 127.0.0.1) | **PASS** | `SentinelSetup.pyw` binds `127.0.0.1`; CORS restricted to `localhost:5173` |
| Host companion bound 127.0.0.1 | **PASS** | `host_companion/server.py` rejects non-loopback bind; constant-time token compare (`compare_digest`) |
| Host changes require authenticated owner-authorised operation | **PASS** | operation approval requires install + `plan_hash` + `confirmed=true`; authorisation envelope owner-only, ≤600 s, HMAC |
| Operation plans checked against exact approved hashes | **PASS** | `plan_hash()` verified before execution; changed plan → 409 |
| Replay protection effective | **PASS** | nonce file prevents replay; replay → 409 |
| Request headers must not elevate permissions | **PASS** | `X-Sentinel-Role` header ignored; server-side `session_role` setting is authoritative (test_03) |
| Allowlisted execution model intact | **PASS** | `validate_plan()` rejects `shell` and malformed actions; no `shell=True` anywhere |
| Global emergency stop works | **PASS** | kill switch revokes approvals and blocks decisions (423) |
| Android read-only | **PASS** | `ApiClient` issues GET only; `MainActivity` has no mutation path |
| Android credentials never over plain HTTP | **PASS** | `validateBaseUrl` rejects non-HTTPS; `usesCleartextTraffic="false"`; token AES/GCM-encrypted with Android Keystore |
| Research approvals separate from testing permission | **PASS** | approval records scope assets/methods/rate-limit independently |
| Report submission human-controlled | **PASS** | `human_confirmation=true` required for submit/accept |
| No arbitrary shell execution introduced | **PASS** | only 3 benign list-form `subprocess.Popen` calls; no shell surface |

### 3.2 Findings and fixes

**Finding 1 — [P0] Zip-slip in Windows release extraction.**
`windows/sentinel_runtime.py::extract_release` used `str(target).startswith(str(root))` for containment. A sibling directory such as `<root>-evil` also satisfies that prefix check, so an archive entry `LIN4CRE-SENTINEL/../app-evil/escape.txt` wrote a file outside the extraction root. **Reproduced** with a crafted archive (file written to a sibling). **Fixed** with `target.relative_to(root)` (exact parent check). **Regression test:** `ReleaseExtractionSafetyTests`.

**Finding 2 — [P1] Core app served the SPA shell for unknown `/api/*` paths.**
The catch-all `frontend()` route returned `dist/index.html` (HTTP 200, HTML) for any unmatched path, including `/api/*`. This masked genuine API failures (a client saw a "successful" HTML page instead of an error) and falsely implied the core app served the mobile companion routes (`/api/mobile/v1/*`), which are a separate ASGI app. **Reproduced:** `GET /api/mobile/v1/overview` → 200 HTML. **Fixed:** unknown `/api/*` now returns a JSON 404. **Regression test:** `ApiNotFoundHandlingTests`.

**Finding 3 — [P1] `SENTINEL_HOST_COMPANION_URL` override ignored.**
`windows/SentinelSetup.pyw` and `scripts/Deploy-Sentinel.ps1` export `SENTINEL_HOST_COMPANION_URL=http://127.0.0.1:8765`, but `backend/host_client.py` read only the stored `host_companion_url` setting (default `http://host.docker.internal:8765`). On Windows, `host.docker.internal` does not resolve, so host inspection and operations failed by default. **Reproduced:** stored setting and env override disagreed; backend dialed the non-resolvable default. **Fixed:** added `companion_base()` which honours the override only when the stored setting is still the untouched default, and only for loopback hosts (`localhost`, `127.0.0.1`, `host.docker.internal`) on port 8765 over HTTPS-free `http`. An operator-set value always wins over the environment. **Regression test:** `CompanionUrlOverrideTests`.

### 3.3 Attack-surface probes (all PASS)

- Path traversal via `/api/system/backups/{filename}`: `../../etc/passwd` normalised away → 404; backslash `%5C` → 400; `sentinel.db` without a matching backup → 404. No file disclosure.
- Frontend path traversal: `/../backend/main.py` → SPA shell (no source disclosure); containment via `DIST.resolve() in candidate.parents`.
- No arbitrary shell surface: grep confirmed only list-form `Popen` calls.
- Mobile API standalone: no token → 401, wrong token → 401, valid → 200; core routes → 404; mutations → 404; docs → 404.

---

## 4. Windows installer

**Reviewed:** `Install-Sentinel.cmd`, `SentinelSetup.cmd`, `SentinelLauncher.pyw`, `SentinelSetup.pyw`, `sentinel_runtime.py`, `Bootstrap.ps1`, `Find-Python.ps1`, `START-HERE.txt`, `build-windows-setup.py`, `build-setup-exe.py`, `package-downloads.mjs`, `prepare-downloads.mjs`.

**Findings:**

- **Zip-slip (P0)** — fixed (§3.2, Finding 1).
- **Companion URL override ignored (P1)** — fixed (§3.2, Finding 3).

**Positive observations:**

- `SentinelSetup.pyw` starts only loopback services; preserves an existing pairing token rather than replacing credentials; refuses to run if the token is shorter than 32 characters; reports failures honestly without assuming success.
- `Bootstrap.ps1` offers the official python.org package via `winget` only when no interpreter exists; records a pre-install timestamp; never assumes success.
- `Find-Python.ps1` ignores the Microsoft Store alias stub.
- `build-windows-setup.py` excludes `data/`, `host_data/`, `logs/`, `runtime/`, `node_modules`, `__pycache__`, `.git`, and `*.zip`/`*.exe` from the release archive.
- `Install-Sentinel.cmd` downloads only from the official GitHub release URL and validates the archive contents before declaring success.

**Build status:** The Windows setup archive was produced locally (`dist/downloads/LIN4CRE-SENTINEL-Windows-Setup.zip`, 67 entries, 2,645,169 bytes) and validated (contains built `index.html` + `SentinelSetup.cmd`, no `.db`/`.db-wal`/`.db-shm`). The PyInstaller `.exe` build is **NOT RUN** (PyInstaller not installed); classified **BLOCKED (environmental)**.

---

## 5. Docker

**Reviewed:** `Dockerfile`, `compose.yaml`.

- Multi-stage build (Node 20 frontend → Python 3.12 slim backend).
- Non-root user (`sentinel`, uid 10001); `VOLUME /data`; healthcheck.
- `compose.yaml`: `read_only: true`, `tmpfs /tmp` (noexec, nosuid), `cap_drop: ALL`, `no-new-privileges`, ports bound to `127.0.0.1`, no docker socket, no host network, no privileged mode.

**Build status:** **BLOCKED** — Docker is not available in this environment. The configuration is statically sound and hardened; the build itself could not be executed.

---

## 6. Android

**Reviewed:** `AndroidManifest.xml`, `ApiClient.java`, `ConfigStore.java`, `MainActivity.java`, `build.gradle.kts`, `gradle.properties`, `gradle-wrapper.properties`.

- `allowBackup="false"`, `usesCleartextTraffic="false"`, `INTERNET` permission only.
- `ApiClient.validateBaseUrl` rejects non-HTTPS, userinfo, query, and fragment; `setInstanceFollowRedirects(false)` so the bearer token is never forwarded to a redirect target; GET only.
- `ConfigStore` encrypts the token with Android Keystore AES/GCM, randomised IV, `setRandomizedEncryptionRequired(true)`, `MODE_PRIVATE` SharedPreferences.
- `MainActivity` is read-only (overview, programmes, approvals); no mutation, settings, or report-submission path.

**Build status:** **BLOCKED** — Gradle/JDK 17 are not available in this environment. The Android CI workflow (`android-ci.yml`) could not be executed either (same billing lock). The app is statically sound; the APK was **NOT** built or tested.

---

## 7. Dependency / supply-chain

- **npm:** `npm audit` → **0 vulnerabilities** (74 packages). Dependencies: React 19, react-router-dom 7, Vite 6, TypeScript 5.7, lucide-react.
- **Python:** `requirements.txt` range-pins `fastapi`, `uvicorn[standard]`, `pydantic`, `httpx`, `python-multipart`, `psutil`. Installed cleanly into the project-local venv.
- **Third-party notices:** `THIRD_PARTY_NOTICES.md` present.

---

## 8. Automated testing / CI

### 8.1 Local CI replication — all steps PASS

The CI workflow steps were reproduced locally:

- `python -m compileall backend host_companion` — OK
- `python -m unittest discover -s tests -v` — **46/46 pass** (29 pre-existing + 17 new regression tests)
- `npm ci` — 74 packages, 0 vulnerabilities
- `npm run build` — Vite build succeeds, produces `dist/index.html` (2,645,169-byte zip)
- Windows setup archive validation — 67 entries, contains `index.html` + `SentinelSetup.cmd`, no DB files
- Secret grep — clean

### 8.2 GitHub Actions — BLOCKED (account billing lock, not code)

All 20 recent workflow runs (`ci.yml` and `android-ci.yml`) show status `failure`. The run annotation on a representative run (43268368762) states: **"account is locked due to a billing issue"**. The job never started (run duration ~4 s). **This is an account/billing condition, not a code defect.** No workflow step failed on its own merits.

---

## 9. Remediation (P0–P3)

See `docs/REMEDIATION-LOG-2026-11-12.md` for the full change log. Summary:

| Priority | Defect | Fix | Regression test |
|----------|--------|-----|-----------------|
| **P0** | Zip-slip in `extract_release` | `relative_to` containment check | `ReleaseExtractionSafetyTests` (4 tests) |
| **P1** | Core served SPA HTML for unknown `/api/*` | JSON 404 for `/api/*` | `ApiNotFoundHandlingTests` (5 tests) |
| **P1** | `SENTINEL_HOST_COMPANION_URL` ignored | `companion_base()` honours loopback override | `CompanionUrlOverrideTests` (8 tests) |
| P2 | CI billing lock | Operational (account), no code change | N/A |
| P3 | Browser/Docker/Android builds | Environmental, no code change | N/A |

**Files changed:**

- `backend/main.py` — `frontend()` returns JSON 404 for `/api/*`.
- `backend/host_client.py` — `companion_base()` helper; both call sites use it.
- `windows/sentinel_runtime.py` — `extract_release()` containment fix.
- `tests/test_regressions.py` — 17 new regression tests.

---

## 10. Verification

- **Full unittest suite:** 46/46 pass (`python -m unittest discover -s tests`).
- **Recovery round-trip:** 16/16 pass — backup creation, tamper detection, refusal to restore a corrupted point, exact restore, pre-restore safety artifact, approval revocation on recovery.
- **Frontend static verification:** 19/19 pass — SPA shell served, all 11 routes return the shell, built JS/CSS assets resolve, `/api/health` JSON 200, unknown `/api/*` JSON 404, mobile route not served as HTML.
- **End-to-end API:** 51/51 pass (§2).

### Not run / blocked (honest classification)

| Item | Status | Reason |
|------|--------|--------|
| Docker image build | **BLOCKED** | Docker not installed |
| Android APK build | **BLOCKED** | Gradle/JDK not installed |
| Playwright browser QA | **BLOCKED** | Chromium binary unavailable; `cdn.playwright.dev` not in the network allowlist |
| GitHub Actions runs | **BLOCKED** | Account billing lock |
| Windows `.exe` (PyInstaller) build | **BLOCKED** | PyInstaller not installed |

---

## 11. Conclusion

LIN4CRE SENTINEL v0.2.4 is a well-engineered, security-conscious application. Its mandatory security boundaries are intact, its CI steps all pass when executed locally, and its dependency tree is clean. Three real defects were identified and fixed during this audit — one security-relevant (zip-slip), two correctness/functional (SPA-masking of API errors; ignored companion-URL override). Each fix is covered by a regression test that reproduces the original defect. The only outstanding blockers are environmental (Docker, Gradle/JDK, Chromium, GitHub billing), not code defects.
