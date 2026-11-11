# Priority Roadmap — Today → Long-term

**Product:** LIN4CRE SENTINEL v0.2.0 · **Date:** 11 Nov 2026  
**Rule:** Do not enable live testing, auto-submission, or public deployment until Phase-5 safety gates + auth/HTTPS are met.

---

## Phase 0 — Immediate (Today) — quick wins, safe to ship

| # | Task | Priority | Effort | Difficulty | Impact | Owner |
|---|------|----------|--------|------------|--------|-------|
| 0.1 | **Decide public surface** (local-only vs publish site). Document decision in `README.md` + `Assumptions-and-Gaps.md`. | Critical | 2 h | Easy | Unblocks SEO/CRO | growth + PM |
| 0.2 | **A11y type/contrast:** raise min to 12 px, fix footer/nav/placeholder contrast. | Critical | 4 h | Easy | WCAG AA path | design + eng |
| 0.3 | **Skip-link + modal focus trap + toast live-region + `aria-expanded`/`aria-current`.** | Critical | 4 h | Medium | Keyboard/SR access | eng |
| 0.4 | **Real 404 + HEAD handlers** (stop SPA 200 masking, fix 405). | Critical | 3 h | Easy | Correctness/SEO | eng |
| 0.5 | **Loopback by default:** change `npm run server` + Dockerfile CMD to `127.0.0.1`; warn on `0.0.0.0`. | Critical | 1 h | Easy | Prevents exposure | eng |
| 0.6 | **Cache headers for `/assets/*`** + `no-cache` for `index.html`. | High | 2 h | Easy | Perf | eng |
| 0.7 | **Dependabot + CODEOWNERS + custom OG image + README badges.** | High | 2 h | Easy | Supply-chain/trust | eng + growth |
| 0.8 | **Publish `robots-local.txt` note** (local app must `Disallow: /` if ever indexed). | High | 30 min | Easy | Prevents indexing | eng |

**Exit criteria:** A11y blockers merged, 404/HEAD fixed, loopback default, cache headers live, Dependabot active.

---

## Phase 1 — Short term (1–2 weeks) — high-value improvements

| # | Task | Priority | Effort | Difficulty | Impact | Owner |
|---|------|----------|--------|------------|--------|-------|
| 1.1 | **Route code-splitting** (`React.lazy` ×11 + `manualChunks`). Target initial JS <150 KB. | High | 1–2 d | Medium | LCP/INP | eng |
| 1.2 | **CSP (report-only → enforce) + HSTS (HTTPS) + `no-store` for `/api/*`.** | High | 1 d | Medium | Security | eng |
| 1.3 | **Token gate for mutating core routes** (reuse host-token pattern). | Critical | 2–4 d | Medium | Security | eng |
| 1.4 | **Public site MVP** (Pages/Vercel): landing, features, screenshots, downloads, docs, FAQ, contact, changelog. | High | 3–5 d | Medium | Discoverability | growth + eng + content |
| 1.5 | **SEO assets:** `robots.txt`, `sitemap.xml`, per-route title/meta/canonical/OG, JSON-LD, manifest, favicons. | High | 2–3 d | Easy | SEO | eng + growth |
| 1.6 | **Onboarding checklist + demo-mode spike** (clearly-labelled sample data, never in real ledger). | High | 3–5 d | Medium | Activation | design + eng + content |
| 1.7 | **Inline form errors** (`aria-invalid`/`aria-describedby`, focus first error). | High | 1–2 d | Easy | A11y/UX | eng |
| 1.8 | **Global search** (findings/reports/audit) + `allSettled` partial render + fetch timeout/Abort. | High | 2–3 d | Medium | UX/perf | eng |
| 1.9 | **GitHub hygiene:** branch protection, release checksums, `SUPPORT.md` link, topics/description polish. | Medium | 1 d | Easy | Trust | eng + growth |
| 1.10 | **Help/FAQ + troubleshooting matrix** (SmartScreen, Python, Docker, Ollama, rollback). | High | 2–3 d | Easy | Support deflection | content |

**Exit criteria:** Initial JS <150 KB, CSP live, token gate live, public site MVP live with SEO assets, onboarding usable.

---

## Phase 2 — Medium term (1–3 months) — larger enhancements

| # | Task | Priority | Effort | Difficulty | Impact | Owner |
|---|------|----------|--------|------------|--------|-------|
| 2.1 | **Windows verification sprint** (clean install, UAC, Docker, Ollama, rollback, restore) + publish report. | Critical | 1 wk | Medium | Trust/adoption | eng + QA |
| 2.2 | **Signed releases + SBOM + provenance** (SLSA). | High | 1 wk | Medium | Supply-chain | eng |
| 2.3 | **Docs site with search** (MkDocs/Docusaurus) + versioned docs. | High | 1–2 wks | Medium | SEO/support | content + eng |
| 2.4 | **A11y statement + VPAT + NVDA/VoiceOver + 200% zoom testing.** | High | 3–5 d | Medium | Compliance | design + eng |
| 2.5 | **Privacy policy + Terms** (public site). | High | 2 d | Easy | Legal/trust | content |
| 2.6 | **Privacy-respecting analytics** (public site only) + feedback/NPS. | Medium | 3–5 d | Easy | Measurement | growth + eng |
| 2.7 | **RAG over user docs** (local embeddings, grounded Q&A). | Medium | 3–4 wks | Hard | Research speed | eng + AI |
| 2.8 | **Intent eval harness** (200+ golden utterances, CI gate). | Medium | 1 wk | Medium | AI quality | eng + AI |
| 2.9 | **Report-quality linter** (evidence/AI-disclosure checks). | Medium | 1 wk | Easy | Acceptance rate | eng + content |
| 2.10 | **DB migrations + `pyproject.toml` + ESLint/Prettier/Ruff/mypy CI.** | Medium | 1 wk | Medium | Maintainability | eng |
| 2.11 | **Programme connector spike** (authenticated API only, terms review, preserve URLs/timestamps). | High | 4–8 wks | Hard | Discovery | eng + growth |
| 2.12 | **Docker CI build + smoke test** (fix “Docker not verified”). | Medium | 2–3 d | Easy | Reliability | eng |

**Exit criteria:** Windows verified, releases signed, docs searchable, a11y statement published, connector spike evaluated (go/no-go).

---

## Phase 3 — Long term — strategic roadmap

| # | Task | Priority | Effort | Difficulty | Impact | Owner |
|---|------|----------|--------|------------|--------|-------|
| 3.1 | **Isolated research executor** (Phase-5 gates: EULA, isolated net, egress proxy, external rate-limit, kill-switch wiring, lab-only). | High (strategic) | 3–6 mo | Very hard | Moat | eng + security |
| 3.2 | **CyberGym subset evals** (10-task subset, private bind, record model/prompt/cost/result; never claim live competence). | Medium | 4–6 wks | Hard | Eval credibility | eng + AI |
| 3.3 | **i18n** (en-GB → en-US/de/fr/es). | Low | 2–3 mo | Hard | International | eng + content |
| 3.4 | **PWA / offline docs** (manifest + SW for public docs; local app offline queue). | Low | 1–2 mo | Medium | UX | eng |
| 3.5 | **Multi-currency FX** (explicit, dated rates; never silent conversion). | Low | 2 wks | Medium | Earnings accuracy | eng |
| 3.6 | **Light / high-contrast themes** (`prefers-contrast`, `forced-colors`). | Low | 2–3 wks | Medium | Inclusion | design + eng |
| 3.7 | **Blog / changelog page / RSS** (SEO + community). | Low | 1 wk | Easy | SEO | content + growth |
| 3.8 | **Status page** (public site uptime). | Low | 3–5 d | Easy | Trust | eng |

---

## Priority matrix (all recommendations)

| ID | Recommendation | Priority | Time | Difficulty | Impact | Owner |
|----|----------------|----------|------|------------|--------|-------|
| R2.1 | Load Inter / favicons / OG image | Medium | 4 h | Easy | Brand/SEO | design |
| R2.2 | Brand sheet (tokens/type/tone) | Medium | 1 d | Easy | Consistency | design |
| R2.3 | Social-proof assets (real only) | Low | ongoing | Easy | CRO | growth |
| R2.4 | Light/high-contrast themes | Low | 2–3 wks | Medium | Inclusion | design |
| R3.1 | Onboarding + demo mode | High | 3–5 d | Medium | Activation | design+eng |
| R3.2 | Inline form errors | High | 1–2 d | Easy | A11y/UX | eng |
| R3.3 | Global search | High | 2–3 d | Medium | UX | eng |
| R3.4 | Offline banner | Medium | 1 d | Easy | UX | eng |
| R3.5 | Help/FAQ explainer | High | 2–3 d | Easy | Support | content |
| R4.1 | Type scale ≥12 px | Critical | 4 h | Easy | A11y | design+eng |
| R4.2 | Contrast fixes | Critical | 2 h | Easy | A11y | design |
| R4.3 | Reduced-motion/forced-colors | High | 4 h | Easy | A11y | eng |
| R4.4 | Density/comfortable toggle | Medium | 2–3 d | Medium | UX | design |
| R4.5 | Skeleton loaders | Medium | 2 d | Easy | Perf/UX | eng |
| R5.1 | README badges/TOC/screenshots/FAQ | High | 4 h | Easy | CRO/SEO | content |
| R5.2 | Public-site copy | High | 3–5 d | Easy | CRO | content |
| R5.3 | A11y/Privacy/Terms/Support pages | High | 3 d | Easy | Trust | content |
| R5.4 | Keep anti-hype voice | — | — | — | Brand | content |
| R6.1 | Public site (prerender/SSR) | Critical | 3–5 d | Medium | SEO | growth+eng |
| R6.2 | Fix robots/sitemap | High | 2 h | Easy | SEO | eng |
| R6.3 | Per-route meta/OG/JSON-LD | High | 2–3 d | Easy | SEO | eng+content |
| R6.4 | Real 404 | High | 3 h | Easy | SEO | eng |
| R6.5 | Keyword map + linking | Medium | 2 d | Easy | SEO | content+growth |
| R6.6 | Image optimisation | Low | 4 h | Easy | Perf/SEO | eng |
| R7.1 | Code-split | High | 1–2 d | Medium | Perf | eng |
| R7.2 | Cache/compression headers | High | 2 h | Easy | Perf | eng |
| R7.3 | Batch/timeout/polling pause | Medium | 2 d | Medium | Perf | eng |
| R7.4 | Cache static APIs/paginate | Medium | 2 d | Easy | Perf | eng |
| R7.5 | Docs image optimisation | Low | 4 h | Easy | Perf | eng |
| R8.1 | A11y blockers bundle | Critical | 1–2 d | Medium | A11y | design+eng |
| R8.2 | Form errors a11y | High | 1–2 d | Easy | A11y | eng |
| R8.3 | Target-size pass | Medium | 1 d | Easy | A11y | design |
| R8.4 | A11y statement + AT testing | High | 3–5 d | Medium | Compliance | design+eng |
| R9.1 | Loopback default | Critical | 1 h | Easy | Security | eng |
| R9.2 | Token gate for mutations | Critical | 2–4 d | Medium | Security | eng |
| R9.3 | CSP/HSTS/no-store | High | 1 d | Medium | Security | eng |
| R9.4 | Rate-limit/timeout/0600/digests/SBOM | Medium | 3–5 d | Medium | Security | eng |
| R9.5 | Protect /api/docs + noindex | Medium | 2 h | Easy | Security | eng |
| R10.1 | HEAD + 404 fix | Critical | 3 h | Easy | Correctness | eng |
| R10.2 | Partial render + no GET writes | Medium | 2 d | Medium | Correctness | eng |
| R10.3 | Lint/type CI | Medium | 1 d | Easy | Quality | eng |
| R10.4 | Migrations/pyproject | Medium | 1 wk | Medium | Maintainability | eng |
| R10.5 | Dependabot/CODEOWNERS/protection | Medium | 1 d | Easy | Supply-chain | eng |
| R11.1 | Landing page | High | 3–5 d | Medium | CRO | growth+content |
| R11.2 | Checksums/signing/video | High | 1 wk | Medium | CRO/trust | eng+content |
| R11.3 | Onboarding/demo/star/feedback | Medium | 3–5 d | Medium | CRO | design+eng |
| R11.4 | README polish | High | 4 h | Easy | CRO | content |
| R11.5 | Analytics (public only) | Medium | 3–5 d | Easy | Measurement | growth+eng |
| A1 | Programme connector | High | 4–8 wks | Hard | Discovery | eng+growth |
| A2 | RAG over user docs | Medium | 3–4 wks | Hard | Research | eng+AI |
| A3 | Intent evals | Medium | 1 wk | Medium | AI quality | eng+AI |
| A4 | Onboarding copilot | Medium | 1–2 wks | Medium | Activation | design+eng |
| A5 | Report linter | Medium | 1 wk | Easy | Acceptance | eng+content |
| A6 | Support bot | Low | 2–3 wks | Medium | Support | eng+content |
| A7 | Analytics copilot | Low | 1 wk | Easy | Retention | eng |
| A8 | Research executor | High (strategic) | 3–6 mo | Very hard | Moat | eng+security |
| R13.1 | Docs site | High | 1–2 wks | Medium | Positioning | content+eng |
| R13.2 | Signed releases/SBOM | High | 1 wk | Medium | Trust | eng |
| R13.3 | Demo mode | High | 3–5 d | Medium | Positioning | design+eng |
| R13.4 | Palette/PWA | Low | 2–4 wks | Medium | Positioning | eng |

---

## Start-here checklist (first 5 steps)

- [ ] 1. Decide public surface (Phase 0.1) — record decision.
- [ ] 2. Ship a11y blockers (Phase 0.2 + 0.3) — type, contrast, skip-link, modal trap, toast live.
- [ ] 3. Ship loopback default + 404/HEAD + cache headers (Phase 0.4 + 0.5 + 0.6).
- [ ] 4. Ship code-split + CSP (Phase 1.1 + 1.2).
- [ ] 5. Ship public-site MVP + SEO assets (Phase 1.4 + 1.5) *or* explicitly document “local-only, repo is the website” and ship `robots-local.txt` + GitHub polish instead.

*Tasks with acceptance criteria: `Developer-Tasks.md`. Copy/code assets: subfolders.*
