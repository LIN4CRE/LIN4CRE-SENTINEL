# Assumptions, Input Corrections & Gaps

## 1. Input resolution — what was auto-filled and what is correct

The brief contained two auto-resolved inputs that are **incorrect** and have been corrected throughout this package:

| Brief field | Auto-resolved value | Correct value (used in this audit) | Source |
|-------------|---------------------|-------------------------------------|--------|
| Product / brand name | “Github” | **LIN4CRE SENTINEL** | `README.md` title, `index.html` `<title>LIN4CRE SENTINEL</title>`, `backend/main.py` `FastAPI(title="LIN4CRE SENTINEL")`, GitHub repo `LIN4CRE/LIN4CRE-SENTINEL` |
| Market / niche | “[object Object]” | **Local-first vulnerability-research operations for solo/ small-team bug-bounty researchers (cash-only programmes, human-controlled)** | `README.md`, `docs/IMPLEMENTATION_PLAN.md` §1, `backend/scoring.py` cash-only gate |
| Target type | Website / Web app | **Local-first web app (React SPA + FastAPI) + GitHub repo as public surface. No public marketing website exists.** | `package.json`, `Dockerfile`, `compose.yaml`, `gh repo view` (`has_pages:false`, `homepageUrl` = repo URL) |
| Version / focus | production | **v0.2.0 (11 Nov 2026), early local-operations release; Windows/Docker target validation pending** | `CHANGELOG.md`, `docs/VERIFICATION.md`, `SECURITY.md` |
| Audit depth / output | Forensic / maximum agent-executable | **As requested** | — |

**If you intended a different product or market, correct it here and re-run the affected sections (SEO keyword map, competitive positioning, CRO funnel).** All other findings are product-agnostic and remain valid.

---

## 2. Scope actually audited

### In scope (publicly accessible + local checkout)
- GitHub repo `https://github.com/LIN4CRE/LIN4CRE-SENTINEL` (README, docs, releases, topics, community files, CI, file tree).
- Local web app source: `index.html`, `src/` (11 routes), `backend/` (FastAPI), `host_companion/`, `windows/`, `scripts/`, `Dockerfile`, `compose.yaml`, `vite.config.ts`, `package.json`, `requirements.txt`.
- Live local server smoke test (`uvicorn` on `127.0.0.1:18000/18001`): headers, SPA fallback, robots/sitemap behaviour, unauthenticated API behaviour, CORS.
- Build + tests: `npm run build` (bundle sizes), `python -m unittest` (21/21).
- Static analysis: grep for semantics, ARIA, forms, polling, bind addresses, secrets, TODOs; contrast-ratio math for design tokens.

### Out of scope / not performed
- No penetration testing, no vulnerability exploitation, no scraping of third-party bounty platforms, no live testing against real assets. Defensive recommendations only.
- No Windows target-PC administration (sandbox cannot administer the user’s PC — explicitly stated in `docs/VERIFICATION.md`).
- No Docker/Compose execution (unavailable in build sandbox — stated in `docs/VERIFICATION.md`).
- No real Ollama inference, external AI calls, bounty-platform connections, or report submissions.
- No Lighthouse/PageSpeed run against a public URL (no public URL exists). Performance is assessed from bundle analysis + code review + local smoke test. **Suspected** CWV values are labelled as such.
- No screen-reader run (NVDA/VoiceOver) or keyboard-only walkthrough beyond code inspection. A11y findings are code-based + contrast math; manual AT testing is listed as a task.

---

## 3. Confirmed vs suspected

### Confirmed (reproduced in this audit)
- Bundle: JS 424.98 kB raw / 123.45 kB gzip; CSS 70.38 kB raw / 14.80 kB gzip; 1611 modules.
- Tests: 21/21 pass. Build: passes.
- Headers: only `nosniff`, `SAMEORIGIN`, `no-referrer`, `Permissions-Policy(camera,microphone,geolocation)`. No CSP/HSTS/Cache-Control.
- `/robots.txt` and `/sitemap.xml` return SPA `index.html` (200, `text/html`), not robots/sitemap.
- `HEAD /` and `HEAD /api/health` return **405 Method Not Allowed** (FastAPI GET-only routes without HEAD handler in this setup).
- `GET /nonexistent-route` returns **200 SPA HTML** (catch-all `/{full_path:path}`), masking 404s.
- Core API unauthenticated: `POST /api/programmes`, `PATCH /api/settings`, `GET /api/system/export` succeed with no credentials.
- CORS: `allow_origins` = `localhost:5173` + `127.0.0.1:5173` only; evil-origin preflight correctly rejected (`Disallowed CORS origin`), but simple GET from evil origin still returns 200 (no `Access-Control-Allow-Origin` header, so browser blocks JS read — correct behaviour, noted for clarity).
- `npm run server` / `vite --host 0.0.0.0` / Dockerfile `CMD --host 0.0.0.0` bind all interfaces; `compose.yaml` correctly publishes loopback-only (`127.0.0.1:8787:8000`).
- Micro-type: `font-size` histogram dominated by 7–10 px (see `Full-Audit.md` §4/§8). Contrast fails: footer 2.96:1, nav-section 3.44:1, placeholder 3.76:1 (computed).
- No skip-link, no focus trap in `Modal`, toasts have no `role="status"`/`aria-live`, no `prefers-reduced-motion` handling.
- No `robots.txt`, `sitemap.xml`, `manifest.webmanifest`, favicons, OG/Twitter meta, JSON-LD, canonical in repo or `index.html`.
- GitHub: public, MIT, 0 stars/forks, 1 release `v0.2.0` with 2 assets (`Setup.exe`, `Windows-Setup.zip`), 10 topics, no Pages, no custom OG image, branch protection API returns 403 (cannot confirm protection exists).
- No secrets tracked in Git (`.gitignore` + CI check; grep found no hardcoded keys/tokens beyond test fixtures).

### Suspected (likely, needs verification)
- **LCP/INP/CLS:** Likely LCP >2.5 s on slow 4G due to 425 KB JS + render-blocking CSS + no preload; INP likely okay (small DOM) but polling + large lists may jank. Needs Lighthouse on public site once published.
- **Windows first-run failure rate:** Suspected high due to unsigned installer + SmartScreen + Python bootstrap + UAC + Docker Desktop variance. Needs target-PC testing.
- **Ollama model quality for intent classification / code patches:** Unknown without local evals. Deterministic fallback mitigates, but model-dependent paths may be brittle.
- **SQLite WAL + concurrent writes under load:** Likely fine for single-user, but `connect()` per request + `transaction()` patterns should be load-tested.
- **Search-engine indexing of GitHub repo:** Repo is indexable via GitHub, but without custom OG image, description polish, and external backlinks, rich results will be minimal.

---

## 4. Gaps & unknowns (explicit)

| # | Gap | Why it matters | How to close |
|---|-----|----------------|--------------|
| G1 | No public URL / domain / hosting decision | Blocks SEO, CRO, analytics, OG, sitemap | Decide Pages vs Vercel vs custom domain (Roadmap Phase 0) |
| G2 | No target-PC Windows verification | Top adoption risk | Verification sprint (Task T-25) |
| G3 | No Docker execution verification | Container path unproven | CI Docker build + smoke test (Task T-26) |
| G4 | No real user data (starts empty) | Cannot measure activation, funnel, retention | Opt-in analytics + demo mode (Tasks T-18, T-19) |
| G5 | No accessibility statement / VPAT | Trust + compliance gap | Publish statement (Task T-22) |
| G6 | No privacy policy / data-handling page for public site | Required if analytics/forms added | Publish (Task T-23) |
| G7 | No support SLA / contact channel beyond GitHub issues | CRO/trust gap | Add Support page + `SUPPORT.md` link (Task T-24) |
| G8 | No release signing / SBOM / provenance | Supply-chain trust gap | Sign + SBOM (Task T-27) |
| G9 | No i18n (en-GB only) | Limits international researchers | i18n spike (Task T-30) |
| G10 | No offline/PWA story | Local-first could benefit | PWA evaluation (Task T-31) |

---

## 5. Standards used

- **Accessibility:** WCAG 2.2 (AA target; AAA noted where relevant), WAI-ARIA Authoring Practices (dialog, live regions, focus management).
- **Performance:** Core Web Vitals (LCP ≤2.5 s, INP ≤200 ms, CLS ≤0.1), web.dev performance guidance, Vite/Rollup code-splitting best practice.
- **SEO:** Google Search Central (titles, meta, canonicals, robots, sitemap, structured data), Open Graph / Twitter Cards, schema.org `SoftwareApplication`.
- **Security:** OWASP ASVS (local-app subset), OWASP Top 10, Mozilla Observatory / securityheaders.com expectations, Docker hardening (non-root, read-only, cap-drop — already present).
- **Design:** Responsive (320 px → 1600 px), modern dark UI, Lucide icons, Inter/system font stack.

---

## 6. Reproducibility

All measurements in this package can be reproduced from the repo root:

```bash
npm ci && npm run build          # bundle sizes in dist/assets/
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v   # 21 tests
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
curl -i http://127.0.0.1:8000/api/health
curl -i http://127.0.0.1:8000/robots.txt   # returns SPA HTML (finding)
gh repo view LIN4CRE/LIN4CRE-SENTINEL --json name,description,url,homepageUrl,licenseInfo,stargazerCount,repositoryTopics
```

Contrast ratios were computed with the WCAG relative-luminance formula (see `Full-Audit.md` §8 for pairs).
