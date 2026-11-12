# LIN4CRE SENTINEL — Remediation Log

**Date:** 2026-11-12
**Branch:** `arena/e06cb42d-lin4cre-sentinel`
**Baseline:** `211640aa48ea629098b1cd20c6a7963f60d7033b` (v0.2.4)
**Companion report:** `docs/FORENSIC-AUDIT-2026-11-12.md`

This log records every code change made during the forensic audit, the defect it fixes, and the regression test that pins the fix. No security boundary was weakened to make any test pass.

---

## Change summary

| File | Change | Defect | Priority |
|------|--------|--------|----------|
| `windows/sentinel_runtime.py` | `extract_release` containment check | Zip-slip (arbitrary file write outside extraction root) | **P0** |
| `backend/main.py` | `frontend()` returns JSON 404 for `/api/*` | SPA shell masked API failures; false 200 for mobile routes | **P1** |
| `backend/host_client.py` | `companion_base()` honours `SENTINEL_HOST_COMPANION_URL` | Override ignored; host ops failed on Windows | **P1** |
| `tests/test_regressions.py` | 17 new regression tests | — | — |

---

## P0 — Zip-slip in Windows release extraction

**File:** `windows/sentinel_runtime.py`
**Function:** `extract_release(archive, destination)`

### Defect

Containment was checked with a string prefix:

```python
if not str(target).startswith(str(root)):
    raise RuntimeError('The download contains an unsafe path and was not extracted.')
```

A sibling directory such as `<root>-evil` also satisfies `startswith(root)`, so an archive entry like `LIN4CRE-SENTINEL/../app-evil/escape.txt` wrote a file outside the extraction root. **Reproduced** with a crafted archive: the file `escape.txt` was written to the sibling directory.

### Fix

Exact parent check:

```python
try:
    target.relative_to(root)
except ValueError as exc:
    raise RuntimeError('The download contains an unsafe path and was not extracted.') from exc
```

### Regression test

`ReleaseExtractionSafetyTests` (4 tests):
- `test_sibling_escape_is_refused` — the exact P0 reproduction; asserts `RuntimeError` and no file outside the root.
- `test_deep_traversal_is_refused` — `../..` entry.
- `test_legit_single_prefix_archive_is_extracted` — a normal single-top-folder archive still extracts (prefix stripped).
- `test_multi_top_archive_is_extracted` — a multi-top-folder archive extracts with structure preserved.

---

## P1 — Core app served the SPA shell for unknown `/api/*` paths

**File:** `backend/main.py`
**Function:** `frontend(full_path)`

### Defect

The catch-all route returned `dist/index.html` (HTTP 200, HTML) for every unmatched path, including `/api/*`. This:

- masked genuine API failures (a client received a "successful" HTML page instead of an error status), and
- falsely implied the core app served the mobile companion routes (`/api/mobile/v1/*`), which are a separate ASGI application (`backend.mobile_main`).

**Reproduced:** `GET /api/mobile/v1/overview` → 200 HTML.

### Fix

```python
if full_path == "api" or full_path.startswith("api/"):
    raise HTTPException(404, "API endpoint not found")
```

Placed before the SPA-shell return, so unmatched `/api/*` paths get a JSON 404 while all frontend routes still serve the SPA.

### Regression test

`ApiNotFoundHandlingTests` (5 tests):
- `test_unknown_api_path_returns_json_404`
- `test_unknown_api_subpath_returns_json_404`
- `test_mobile_companion_routes_are_not_served_by_the_core_app` — the exact reproduction; asserts JSON 404, not HTML.
- `test_known_api_paths_are_unaffected` — `/api/health` still 200 JSON.
- `test_frontend_routes_still_serve_the_spa` — non-API routes still return the SPA shell.

---

## P1 — `SENTINEL_HOST_COMPANION_URL` override ignored

**File:** `backend/host_client.py`
**Functions:** `host_request`, `host_status` (new helper `companion_base`)

### Defect

`windows/SentinelSetup.pyw` and `scripts/Deploy-Sentinel.ps1` export `SENTINEL_HOST_COMPANION_URL=http://127.0.0.1:8765`, but `host_client.py` read only the stored `host_companion_url` setting (default `http://host.docker.internal:8765`). On Windows, `host.docker.internal` does not resolve, so host inspection and operations failed by default.

**Reproduced:** stored setting and env override disagreed; the backend dialed the non-resolvable default.

### Fix

New `companion_base(current)` helper:

- Honours the env override **only** when the stored setting still holds the untouched default.
- The override must satisfy the same loopback-only policy the settings API enforces: scheme `http`, host in `(localhost, 127.0.0.1, host.docker.internal)`, port in `(None, 8765)`.
- An operator-set stored value always wins over the environment (operator intent is authoritative).
- A malformed override (bad URL, wrong port, non-loopback host, https) falls back to the stored value.

Both `host_request` and `host_status` now call `companion_base(current)` instead of reading the setting directly.

### Regression test

`CompanionUrlOverrideTests` (8 tests):
- `test_loopback_override_is_honoured`, `test_localhost_override_is_honoured`, `test_host_docker_internal_override_is_honoured`
- `test_non_loopback_override_is_rejected`, `test_non_default_port_is_rejected`, `test_https_override_is_rejected`
- `test_operator_setting_beats_environment_override`, `test_no_override_uses_stored_value`

---

## P2 — CI billing lock (operational, no code change)

All 20 recent GitHub Actions runs fail with a **billing lock** annotation; the job never starts. This is an account condition, not a code defect. All CI steps were verified to pass locally (compileall, 46 unittests, npm ci, npm run build, archive validation, secret grep). No code change is warranted. Resolution requires restoring the GitHub account billing.

---

## P3 — Environmental blockers (no code change)

| Item | Blocker | Classification |
|------|---------|----------------|
| Docker image build | Docker not installed | BLOCKED |
| Android APK build | Gradle/JDK 17 not installed | BLOCKED |
| Playwright browser QA | Chromium binary unavailable; download host not in network allowlist | BLOCKED |
| Windows `.exe` (PyInstaller) build | PyInstaller not installed | BLOCKED |

These are environmental limitations of the audit sandbox, not defects in the repository.

---

## Verification after changes

- `python -m unittest discover -s tests` → **46/46 pass** (29 pre-existing + 17 new).
- `tests/test_regressions.py` alone → **17/17 pass**.
- Recovery round-trip → **16/16 pass**.
- Frontend static verification → **19/19 pass**.
- End-to-end API → **51/51 pass**.

---

## How to run the regression tests

```bash
python -m unittest tests.test_regressions -v
# or the whole suite:
python -m unittest discover -s tests -v
```

The new tests are self-contained and use isolated temporary directories; they do not touch real data.
