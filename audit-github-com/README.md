# LIN4CRE SENTINEL — Master Website Audit & Growth Package

**Target:** https://github.com/LIN4CRE/LIN4CRE-SENTINEL  
**Product (corrected):** LIN4CRE SENTINEL — local-first, human-controlled vulnerability-research operations (React + TypeScript SPA + FastAPI + SQLite + Windows host companion)  
**Audit date:** 11 November 2026 (UTC)  
**Audit depth:** Forensic / exhaustive  
**Auditor role:** Multi-disciplinary team (UX, UI, Brand, SEO, Performance, Accessibility, Security, Full-stack, CRO, Marketing, PM, Copy, AI)

> **Critical framing correction:** The brief auto-derived the product name as “Github” and market as “[object Object]”. Both are wrong. This is **not** github.com and **not** a public marketing website. It is a **local-first desktop/web app** whose only public surface today is the **GitHub repository + release page**. There is **no GitHub Pages site, no custom domain, no public marketing homepage**. All SEO/CRO scores below are therefore scored against *both* surfaces and clearly labelled. See `Assumptions-and-Gaps.md` for full correction.

---

## Start here (first 5 implementation steps)

1. **Decide the public surface.** Either (a) keep SENTINEL private/local-only and treat the GitHub repo as the website, or (b) publish a public site (GitHub Pages / Vercel) for docs + downloads. Do not deploy the local app to the public internet without auth. See `Priority-Roadmap.md` Phase 0.
2. **Fix the 3 accessibility blockers:** raise micro-type from 7–10 px to ≥12 px, fix footer/nav-section contrast, add skip-link + focus-trapped modal + toast live-region. Snippets in `Accessibility/` + `CSS/fixes.css`.
3. **Harden the core API before any LAN/public exposure:** add loopback bind by default, CSP + HSTS (when HTTPS), rate-limit, and an auth/token gate for mutating routes. See `Security/`.
4. **Split the 425 KB JS bundle** with route-level `React.lazy()` + manual chunks; add cache headers for `/assets/*`. See `Performance/`.
5. **Publish the missing public assets:** `robots.txt`, `sitemap.xml`, OG/Twitter meta, JSON-LD, `manifest.webmanifest`, favicons, and a real 404 page. Templates in `Robots/`, `Schema/`, `Metadata/`, `HTML/`.

Full phased plan: `Priority-Roadmap.md`. GitHub-ready tasks: `Developer-Tasks.md`.

---

## Scores (out of 100)

| # | Category | Score | One-line verdict |
|---|----------|-------|------------------|
| 1 | Executive Summary | **82** | Honest, evidence-led product; public presence is the gap |
| 2 | Brand Review | **68** | Coherent dark “sentinel” identity; no public brand system |
| 3 | User Experience | **74** | Excellent empty/loading/error honesty; steep first-run curve |
| 4 | User Interface | **71** | Polished dark UI; micro-type and density hurt usability |
| 5 | Content / Copy | **83** | Best-in-class anti-hype copy; no marketing narrative |
| 6 | SEO Audit | **22** | No public site, no meta/OG/schema/robots/sitemap |
| 7 | Performance | **68** | Local app is snappy; 425 KB single bundle, polling, no caching |
| 8 | Accessibility | **58** | Good landmarks/focus; tiny type, contrast fails, no skip/focus-trap |
| 9 | Security & Privacy | **76** | Strong local-first threat model; no core auth, no CSP/HSTS |
| 10 | Technical / Bugs | **81** | 21/21 tests pass, clean build; HEAD 405 + SPA 404 masking |
| 11 | Conversion (CRO) | **35** | No funnel by design; GitHub release page is the only funnel |
| 12 | AI Opportunities | **88** | Deterministic intents + constrained patches; no RAG/evals/connectors |
| 13 | Competitive Positioning | **64** | Differentiated honesty; behind on discovery/automation |
| 14 | Missing Features | **55** | Missing public site, help, analytics, a11y statement, demo |
| 15 | Priority Matrix | **90** | Roadmap in this package is fully prioritised with effort/impact |
| — | **OVERALL (public website)** | **61** | Repo-as-website + local app blended |
| — | **OVERALL (local product only)** | **76** | Excluding SEO/CRO public-site penalties |

**How to read scores:** 90–100 exemplary, 75–89 strong, 60–74 adequate with notable gaps, 40–59 weak, <40 critical. SEO/CRO are scored as a *public website*; the local app intentionally has no funnel, so low scores there do **not** mean the product is broken — they mean “if you want public growth, this work is required.”

---

## Package contents

```
audit-github-com/
├── README.md                  ← you are here
├── Executive-Summary.md       ← decision-ready summary, strengths/weaknesses, effort vs impact
├── Full-Audit.md              ← forensic findings for all 15 categories (observations vs recommendations)
├── Priority-Roadmap.md        ← Today → Long-term phased plan + priority matrix
├── Developer-Tasks.md         ← GitHub Issues-ready tasks (title, description, acceptance criteria, priority, effort, owner)
├── Assumptions-and-Gaps.md    ← input corrections, confirmed vs suspected, unverified items
├── SEO/
│   ├── SEO-Audit.md
│   ├── meta-templates.md
│   └── keyword-map.md
├── Accessibility/
│   ├── Accessibility-Audit.md
│   └── fixes.md               ← drop-in TSX/CSS snippets
├── Performance/
│   ├── Performance-Audit.md
│   └── optimizations.md       ← Vite/code-split/cache snippets
├── Security/
│   ├── Security-Audit.md
│   ├── headers.md             ← CSP/HSTS/frame/referrer examples
│   └── hardening-checklist.md
├── Content/
│   ├── Content-Audit.md
│   └── rewrites.md            ← rewritten hero, README, release, empty states
├── Design/
│   ├── Design-Audit.md
│   └── tokens.md              ← design tokens + type scale
├── HTML/
│   ├── HTML-Audit.md
│   └── snippets.md            ← index.html, 404, semantic fixes
├── CSS/
│   ├── CSS-Audit.md
│   └── fixes.css              ← contrast/type/motion fixes
├── JavaScript/
│   ├── JavaScript-Audit.md
│   └── fixes.ts               ← lazy routes, abort, polling, a11y helpers
├── Schema/
│   ├── schema.jsonld          ← SoftwareApplication + FAQ + Breadcrumb
│   └── README.md
├── Robots/
│   ├── robots.txt             ← public-site variant (copy to site root)
│   ├── robots-local.txt       ← local-app variant (Disallow: /)
│   └── README.md
└── Metadata/
    ├── metadata.md
    ├── open-graph.md
    └── manifest.webmanifest
```

**Conventions used throughout:**
- **Observation** = what was measured (with file/URL/curl evidence). **Recommendation** = what to do (with owner + effort).
- **Confirmed** = reproduced in this audit (build, tests, curl, grep, contrast math). **Suspected** = likely but not reproduced (needs target-PC/Docker verification).
- Every recommendation has an **owner discipline**: `design / eng / content / growth`.

---

## Evidence snapshot (reproduced 11 Nov 2026)

- `npm run build` → `dist/assets/index-*.js 424.98 kB (gzip 123.45 kB)`, `index-*.css 70.38 kB (gzip 14.80 kB)`, 1611 modules, built in 2.76 s.
- `python -m unittest discover -s tests -v` → **21/21 passed** (16 upgrade + 5 workflow).
- Live `uvicorn backend.main:app` → `GET /api/health 200`, `GET / 200 (SPA)`, `GET /robots.txt 200 (SPA HTML, not robots)`, `GET /sitemap.xml 200 (SPA HTML)`, `HEAD / 405`, `GET /api/docs 200`, `GET /nonexistent-route 200 (SPA fallback)`.
- Headers on `/api/health`: `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: no-referrer`, `Permissions-Policy: camera=(), microphone=(), geolocation=()` — **no CSP, no HSTS, no Cache-Control, no COOP/COEP**.
- Core API is **unauthenticated**: `POST /api/programmes`, `PATCH /api/settings {kill_switch:true}`, `GET /api/system/export` all succeed with no credentials (verified). Safe only because deployment is loopback-only by intent.
- GitHub: public, MIT, 0 stars/forks, 1 release `v0.2.0` (11 Nov 2026), 10 topics, no Pages (`has_pages:false`), `homepageUrl` = repo URL itself, custom OG image **not** set.

---

## What this package is / is not

- **Is:** a complete, implementable audit + roadmap + copy/config/code assets for turning SENTINEL into a trustworthy, fast, accessible, production-ready product *and* (if desired) a public website.
- **Is not:** a penetration test, a legal opinion, or a guarantee of bounty outcomes. No live testing, scraping, or third-party probing was performed. Defensive recommendations only.
