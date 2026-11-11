# Full Audit — LIN4CRE SENTINEL (Forensic)

**Target:** https://github.com/LIN4CRE/LIN4CRE-SENTINEL · **Date:** 11 Nov 2026 · **Depth:** Forensic / exhaustive  
**Reading guide:** Each category has **Observations** (measured, with evidence) and **Recommendations** (owner + effort). **Confirmed** = reproduced; **Suspected** = needs verification. Edge cases (empty, denied, 404, failed forms, offline) are called out per category.

**Scores:** Brand 68 · UX 74 · UI 71 · Content 83 · SEO 22 · Performance 68 · Accessibility 58 · Security 76 · Technical 81 · CRO 35 · AI 88 · Competitive 64 · Missing 55 · Priority Matrix 90 · Executive 82 · **Overall (public) 61 · Overall (product) 76**

---

## 1. Executive Summary — 82/100

### Observations
- **Confirmed:** Product is coherent and honest. Starts empty, never invents data, shows “No Data Available”, “partial”, “unverified” states explicitly (`src/pages/Dashboard.tsx`, `docs/VERIFICATION.md`).
- **Confirmed:** Engineering quality is high for v0.2.0: 21/21 tests pass, production build passes (JS 424.98 kB / gzip 123.45 kB, CSS 70.38 kB / gzip 14.80 kB, 1611 modules), CI runs on push/PR, community files complete.
- **Confirmed:** Public presence is minimal: GitHub repo + release `v0.2.0` only. No Pages (`has_pages:false`), `homepageUrl` = repo URL, 0 stars/forks, no custom OG image, 10 topics.
- **Confirmed:** Biggest risks are accessibility micro-type, unauthenticated core API (safe only on loopback), single-bundle performance, and unverified Windows/Docker paths.

### Recommendations
- **R1.1 (growth, S):** Decide public surface (keep local-only vs publish site). Do not expose the local app publicly without auth. See Roadmap Phase 0.
- **R1.2 (design+eng, S):** Fix a11y blockers + code-split + CSP/cache headers (Today). See `Accessibility/`, `Performance/`, `Security/`.
- **R1.3 (eng, M):** Windows verification sprint + signed releases before promoting downloads. See Tasks T-25/T-27.

---

## 2. Brand Review — 68/100

### Observations
- **Identity (confirmed):** Wordmark “LIN4CRE / SENTINEL” with shield-crosshair SVG mark (`src/components/UI.tsx:Logo`), lime accent `#b7ef72` on near-black `#0a0f0e`, Inter/system stack, Lucide icons. Consistent across SPA, Windows setup (`SentinelSetup.pyw` uses same `#b7ef72`/`#0d1511` palette), README banner (`docs/images/banner.png`, 1.5 MB), and release page.
- **Typography (confirmed):** `font-family: Inter, ui-sans-serif, -apple-system, …` (`src/styles.css:2`) but **Inter is never loaded** (no `<link>`, no `@font-face`, no `fontsource`). Falls back to system sans — acceptable, but brand type is not actually Inter. No type scale; sizes are ad-hoc (7–34 px).
- **Colour system (confirmed):** Well-defined CSS variables (`--bg`, `--panel`, `--accent`, `--green/amber/red/blue`, `--radius:13px`, `--mono`). Dark-only theme; no light mode, no high-contrast mode. Accent lime is distinctive and memorable.
- **Visual consistency (confirmed):** Strong within the app (panels, badges, buttons, cards share tokens). Weak across public surfaces: GitHub repo has no custom OG image (`usesCustomOpenGraphImage:false`), no social preview, no favicon in SPA, banner is AI-generated (disclosed in `THIRD_PARTY_NOTICES.md` — good honesty).
- **Trustworthiness (confirmed):** Copy is exceptionally trustworthy (“No payout is guaranteed”, “No simulated success”, “Sources checked 11 Nov 2026”). Visual trust is undermined by unsigned installer + SmartScreen warning + “Windows not verified” disclaimers (honest, but friction).
- **Positioning (confirmed):** “Local-first, evidence-backed, human-controlled” is clear and differentiated. No tagline, no value-prop hierarchy, no audience definition, no social proof (0 stars, no testimonials, no logos).
- **Edge cases:** Loading state (`app-loading` with animated line) is branded; connection-error state shows logo + clear message (good). No offline state, no favicon fallback, no print stylesheet.

### Recommendations
- **R2.1 (design, S):** Load Inter properly (self-host woff2 + `font-display:swap`) or change stack to system-only and document it. Add favicon set + OG image. See `Metadata/`, `Design/tokens.md`.
- **R2.2 (design+content, S):** Publish a one-page brand sheet: logo usage, colour tokens, type scale (12–34 px), icon rules, tone (“precise, evidence-led, no hype”). See `Design/tokens.md`.
- **R2.3 (growth, S):** Set custom OG image on GitHub + public site; add 3–5 social-proof assets once real users exist (stars, downloads, testimonials — never fake). See `Content/rewrites.md`.
- **R2.4 (design, M):** Add light/high-contrast theme toggle (respects `prefers-contrast`, `forced-colors`). Dark-only excludes some users.

---

## 3. User Experience — 74/100

### Observations
- **Navigation (confirmed):** Sidebar (242 px) with 11 routes grouped OPERATIONS/SYSTEM, active indicator, pending-approvals badge, mobile drawer with scrim (`src/components/Layout.tsx`). Topbar with global search (→ `/opportunities?q=`), approval bell, mode chip, kill-switch banner. Clear IA; no breadcrumbs needed for 11 routes.
- **User flows (confirmed):** Core loop is well-choreographed: Dashboard → Opportunities (record programme) → Approvals (exact scope) → Research (evidence) → Reports (Markdown) → Earnings (actual paid). Each step gates the next (e.g., finding requires active approval; report requires validated finding; payment requires accepted/resolved). Empty states guide next action with CTA (e.g., “Record first programme”).
- **Information architecture (confirmed):** 11 routes: `/`, `/assistant`, `/maintenance`, `/recovery`, `/opportunities`, `/approvals`, `/research`, `/reports`, `/earnings`, `/audit`, `/settings`. Settings uses anchor sections (`#safety`, `#pc-audit`, `#backups`, `#ai`, `#sources`) with smooth scroll. No sitemap page, no help/search beyond opportunities search.
- **Mobile vs desktop (confirmed):** Responsive breakpoints at 1500/1180/980/740/430 px. Sidebar collapses to drawer <740 px; grids stack; tables scroll. Browser QA claims 390 px fits for Dashboard/Assistant/Maintenance/Recovery (per `docs/VERIFICATION.md`). **Suspected:** Opportunities/Research modals with 3-section forms may be cramped at 390 px (needs manual check).
- **CTA placement (confirmed):** Primary CTAs are consistent (`Record programme`, `Ask SENTINEL`, `Check everything`). Destructive actions (kill-switch, revoke, restore) require modal confirmation with explicit checkbox (good friction). No onboarding tour, no first-run checklist beyond Dashboard “Workstation readiness” (4 steps).
- **Forms (confirmed):** `Field` component wraps inputs with `<label>` + hint + required asterisk. Validation is server-side (Pydantic) + HTML `required`/`type`/`min`/`max`. Error display is toast-only (no inline field errors, no `aria-describedby`/`aria-invalid`). Failed forms show toast with server message (good) but lose field-level context.
- **Readability (confirmed):** Body copy is clear and jargon-light, but font sizes 8–11 px dominate (see §4). Line-height 1.5–1.65 is good; line-length is constrained by max-width 1600 px + panels.
- **Friction points (confirmed):** (1) Cold start: empty DB + no demo data = blank dashboard for new users. (2) Windows setup requires extracting ZIP to permanent folder, SmartScreen bypass, Python bootstrap — high friction. (3) Ollama must be manually tested/selected before AI features unlock. (4) No search across findings/reports/audit (only opportunities + audit filter).
- **Edge cases (confirmed):** Loading (skeleton line), error (full-page “core unavailable” + retry), empty (per-route `EmptyState`), denied (403 role, 423 kill-switch, 409 state conflicts), 404 (SPA fallback masks — see §10), offline (no offline detection; `fetch` fails → generic error), failed forms (toast), expired approvals (shown as revoked), partial operations (honest `partial` status). Offline + 404 are the weakest.

### Recommendations
- **R3.1 (design+eng, M):** Add first-run onboarding: 4-step checklist (already on Dashboard) + optional **clearly-labelled demo dataset** toggle (never mixed with real ledger; banner “Demo data — not real earnings”). See Task T-18.
- **R3.2 (eng, S):** Inline form errors with `aria-invalid`/`aria-describedby`, focus first error, preserve input on failure. See `Accessibility/fixes.md`.
- **R3.3 (eng, S):** Global search across programmes/findings/reports/audit (or at least findings + reports). Currently opportunities-only.
- **R3.4 (design, S):** Add offline detection banner (“You’re offline — changes will fail”) + retry queue note. See `JavaScript/fixes.ts`.
- **R3.5 (content, S):** Add Help/FAQ + “What is SENTINEL?” explainer for first-time visitors (public site). See `Content/rewrites.md`.

---

## 4. User Interface — 71/100

### Observations
- **Visual hierarchy (confirmed):** Clear: `PageHeader` (eyebrow + H1 + description + actions) → hero/stats → panels → lists. H1 `clamp(25px,2.4vw,34px)`, H2 panel titles, H3 card titles. Score rings, stat cards, pipeline stages provide scannable hierarchy.
- **Spacing/alignment (confirmed):** 8-px-ish rhythm, 13 px radius, 1 px borders (`#24302b`), consistent padding (panel-head 18×21 px, main-content 34 px). Sidebar 242 px + topbar 64 px sticky with blur. Dense but consistent.
- **Contrast (confirmed, computed):** Body `#e8efeb` on `#0a0f0e` 16.53:1 (AAA). Muted `#728078` 4.67:1 (AA pass). **Fails:** footer `#536159` 2.96:1, nav-section `#5e6d64` 3.44:1, placeholder `#637168` 3.76:1, `core-status small #56635b` ~3.2:1. Badges pass (6.0–9.25:1). Accent `#b7ef72` on black 14.35:1 (excellent).
- **Component consistency (confirmed):** `Button` (primary/secondary/ghost/danger, sm/md), `Badge` (colour-inferred), `StatCard`, `ScoreRing`, `EmptyState`, `Modal`, `Field`, `Notice`, `OperationCard` — all token-driven. Icons uniformly Lucide with `stroke-width 1.65` in nav.
- **Icons/motion/density (confirmed):** Lucide throughout (no emoji in UI; release page uses emoji — inconsistent). Motion: hover lifts, toast slide, loading shimmer, orbit rings. No `prefers-reduced-motion` guard. Density is high: 7–10 px micro-labels everywhere (see histogram below).
- **Responsiveness (confirmed):** Breakpoints 1500/1180/980/740/430 px; grids collapse; sidebar drawer; tables → scroll. No container queries, no fluid type beyond H1 clamp.
- **Font-size histogram (confirmed, `src/styles.css` + `operations.css`):** 10 px ×32, 9 px ×32, 9.5 px ×21, 8.5 px ×21, 8 px ×16, 11 px ×15, 10.5 px ×11, 12 px ×5, 7.5 px ×5, 7 px ×1. **~140 declarations below 12 px.** This is the single biggest UI defect.
- **Edge cases:** Long programme names/assets truncate with ellipsis (good). Score `—` for unscored (good). Badge text uses `label()` Title Case (good). No skeleton loaders beyond initial app-loading; list updates flash without transition.

### Recommendations
- **R4.1 (design+eng, S):** Raise minimum to 12 px (micro-labels 12 px, body 14–16 px). See `CSS/fixes.css` + `Design/tokens.md` type scale.
- **R4.2 (design, S):** Fix contrast fails (footer, nav-section, placeholder, small mono). See `CSS/fixes.css` token overrides.
- **R4.3 (design+eng, S):** Add `prefers-reduced-motion` + `forced-colors` support. See `CSS/fixes.css`.
- **R4.4 (design, M):** Reduce density: increase panel padding, group micro-labels, add “comfortable density” toggle for accessibility.
- **R4.5 (eng, S):** Add skeleton loaders for dashboard/lists; preserve scroll on refresh.

---

## 5. Content / Copy — 83/100

### Observations
- **Clarity/grammar/tone (confirmed):** Exemplary. Precise, evidence-led, no hype. Examples: “Autonomous intelligence. Explicit authorisation. Evidence before claims.”, “Earnings are real, or they are zero.”, “No simulated success.”, “Nothing runs without authorisation.” British English (`authorisation`, `organisation`) consistent. No grammar errors found in sampled copy.
- **Structure (confirmed):** Every page has eyebrow + H1 + 1-sentence description. Modals have title + description + notices. Forms have section titles + hints. Docs are well-structured (README → WINDOWS_SETUP → OPERATIONS → VERIFICATION → SOURCES → RESTORE).
- **Trust signals (confirmed):** “Sources checked 11 Nov 2026”, “No payout is guaranteed”, “£0 spend ceiling”, “Append-only”, “Fail-closed”, verification tables, limitations sections. **Missing:** testimonials, logos, stats, press, community size, security audit report, uptime/SLA.
- **CTAs (confirmed):** Action-oriented and honest (“Record programme”, “Ask SENTINEL”, “Check everything”, “Review & approve”). No dark patterns, no fake urgency. No marketing CTAs (no “Start free”, “Book demo”) — correct for local app, gap for public site.
- **Thin/duplicate/missing (confirmed):** No About, Services, Pricing, Contact, Blog, FAQ, Help, Legal (Privacy/Terms), Accessibility statement, Status page. Docs are deep but no single “What is SENTINEL?” landing narrative. Release notes are excellent but GitHub-only.
- **README (confirmed):** 7 KB, strong: banner, tagline, Windows quick-start, architecture diagram, verification, costs (£0), licence. Missing: badges (CI, licence, version), table of contents, screenshots in README (only banner; screenshots are in release notes), demo GIF, FAQ.
- **Edge cases:** Empty states are copy-rich and instructive (not “No data”). Error copy is specific (“SENTINEL core is unavailable… Start the local API and retry”). Offline/404 copy is generic/missing.

### Recommendations
- **R5.1 (content, S):** Add README badges + TOC + screenshots + FAQ + “Who is this for / not for”. See `Content/rewrites.md`.
- **R5.2 (content, M):** Publish public-site copy: Homepage hero, Features, How it works, Security, Downloads, Docs, FAQ, Contact. See `Content/rewrites.md` for drafts.
- **R5.3 (content, S):** Add Accessibility statement, Privacy notice, Terms (for public site), Support/Contact page. See Task T-22/T-23/T-24.
- **R5.4 (content, S):** Keep the anti-hype voice — do not introduce “AI-powered revolutionary” marketing fluff. The honesty *is* the brand.

---

## 6. SEO Audit — 22/100

> **Scope note:** There is no public website to audit. This section audits (a) the GitHub repo as the de-facto website and (b) the SPA `index.html` as if it were public. Scores reflect “no public site” reality.

### Observations
- **Titles/meta (confirmed):** SPA `index.html` has `<title>LIN4CRE SENTINEL</title>` + single `<meta name="description" content="LIN4CRE SENTINEL — human-controlled vulnerability research and bounty intelligence.">` + `theme-color`. **Missing:** canonical, robots meta, OG (`og:title/description/image/url/type`), Twitter Card, keywords (not needed), author, `og:locale`, favicons, manifest, preconnect/preload. No per-route titles (SPA has one static title for all 11 routes).
- **Headings (confirmed):** SPA has one H1 per page (good) via `PageHeader`, but all routes share the same `<title>` (bad for SEO). No H1 on GitHub repo landing beyond README H1.
- **Canonicals/robots/sitemap/schema (confirmed):** No canonical tags. `/robots.txt` returns SPA HTML (200, `text/html`) — **confirmed broken**. `/sitemap.xml` returns SPA HTML — **confirmed broken**. No JSON-LD/schema in SPA or README. GitHub repo has no `sitemap.xml` (GitHub handles repo indexing, but no custom sitemap).
- **Internal linking/URL structure (confirmed):** SPA uses clean BrowserRouter paths (`/opportunities`, `/approvals`…). No breadcrumbs, no sitemap page, no footer links (footer is 2 spans, no nav). GitHub README links to docs (good) but no external backlinks strategy.
- **Image SEO/alt (confirmed):** SPA has **zero `<img>`** (all SVG icons + CSS). Docs images (`docs/images/*.png`, 2.3 MB total, banner 1.5 MB) have alt text in README/release (`![…](…)`) but no `width`/`height`, no WebP/AVIF, no lazy-loading. Banner 1.5 MB is oversized for social/OG.
- **Crawlability/indexability (confirmed):** SPA is client-rendered (`<div id="root">` + JS bundle). Without SSR/prerender, crawlers see empty shell. No `noindex` (correct for local app, wrong for public site). GitHub repo is indexable (public, MIT, topics) but `homepageUrl` points to itself (no external site to rank).
- **Keyword opportunities (confirmed gap):** No keyword map. Likely targets: “local-first bug bounty”, “human-controlled vulnerability research”, “cash-only bug bounty tracker”, “evidence-backed security research”, “Ollama bug bounty”, “Windows security research setup”. None are targeted in titles/meta/H1s.
- **GitHub SEO (confirmed):** Description is good (“Local-first, evidence-backed…”). Topics (10) are relevant. Missing: custom OG image, website link (none), social links, `fundingLinks`, discussions/wiki polish. 0 stars/forks = no social proof signals.
- **Edge cases:** SPA fallback returns 200 for unknown routes (soft-404 — SEO poison). No custom 404 page. No redirect strategy. No hreflang (en-GB only).

### Recommendations (prioritised by SEO impact)
- **R6.1 (growth+eng, Critical):** Publish public site (Pages/Vercel) with prerendered/SSR landing + docs. SPA-only cannot rank. See `SEO/SEO-Audit.md`.
- **R6.2 (eng, High):** Fix `/robots.txt` + `/sitemap.xml` (serve real files, not SPA fallback). See `Robots/`.
- **R6.3 (eng+content, High):** Add per-route `<title>` + meta description + canonical + OG/Twitter + JSON-LD. See `Metadata/`, `Schema/`, `HTML/snippets.md`.
- **R6.4 (eng, Medium):** Real 404 page (404 status, not 200 SPA). See `HTML/snippets.md`.
- **R6.5 (content+growth, Medium):** Keyword map + internal linking + backlink outreach (HackerOne/Intigriti communities, dev.to, etc. — without spam). See `SEO/keyword-map.md`.
- **R6.6 (eng, Low):** Optimise images (WebP, resize banner to 1200×630 OG, add dimensions, lazy-load). See `Performance/`.

---

## 7. Performance — 68/100

### Observations
- **Core Web Vitals signals (suspected, no public URL):** Local app on `127.0.0.1` will be fast (no network). On slow 4G, 425 KB JS + 70 KB CSS (no preload, no split) likely pushes LCP >2.5 s. INP likely good (small DOM, no heavy main-thread work). CLS likely good (fixed sidebar/topbar, no late layout shifts except images — none in SPA). **Needs Lighthouse once public site exists.**
- **Page weight (confirmed):** JS 424.98 kB raw / 123.45 kB gzip (single chunk `index-*.js`), CSS 70.38 kB raw / 14.80 kB gzip, HTML 0.58 kB. Total ~496 kB raw / ~139 kB gzip for initial load. Docs images 2.3 MB (banner 1.5 MB) affect GitHub/release page weight, not SPA.
- **JS/CSS bloat (confirmed):** All 11 routes + all pages + all Lucide icons in one bundle. `lucide-react` imports are named (tree-shakeable) but still large. No `React.lazy`, no `manualChunks`, no `vite-plugin-compression`. CSS is 938 lines (656 + 282) in 2 files, no minification beyond Vite default (which is on). No critical-CSS inlining.
- **Fonts (confirmed):** Inter referenced but not loaded → system fallback (actually *good* for performance: zero font download, no FOUT). No `font-display` issue because no webfont.
- **Lazy loading/compression/caching (confirmed):** No `loading="lazy"` (no `<img>` in SPA), no `decoding="async"`, no `fetchpriority`. No `Cache-Control`, `ETag` (except Vite dev?), `Expires`, `Vary: Accept-Encoding` observed on live server (only `vary: Origin`). No Brotli/Gzip headers observed (Uvicorn default may gzip? Not confirmed — headers show no `Content-Encoding`). Static `/assets/*` served via `StaticFiles` without explicit cache headers.
- **Request chains (confirmed):** `DataContext` fires **10 parallel `fetch`** on mount (`/health`, `/dashboard`, `/programmes`, `/approvals`, `/findings`, `/reports`, `/payments`, `/audit`, `/settings`, `/sources`). No batching, no `Promise.allSettled` (one failure fails all → full-page error). Polling: Assistant every 2.5 s, Maintenance every 3 s (no visibility-change pause, no backoff). `api.ts` has no timeout, no `AbortController`, no retry.
- **Backend (confirmed):** SQLite WAL + foreign keys, per-request `connect()` (correct lifecycle via `ClosingConnection`). No connection pooling needed (SQLite). No response compression middleware, no ETag, no pagination on `/api/audit` (limit 200, max 1000 — okay), no caching on `/api/sources`/`/api/scoring` (static data refetched every load).
- **Edge cases:** No offline handling, no request timeout (hangs indefinitely), no skeleton (blank until 10 fetches resolve), no stale-while-revalidate.

### Recommendations
- **R7.1 (eng, High):** Route-level code-splitting (`React.lazy` for 11 pages) + `manualChunks` (vendor/react/router/icons). Target initial JS <150 KB. See `Performance/optimizations.md`.
- **R7.2 (eng, High):** Add `Cache-Control: public, max-age=31536000, immutable` for `/assets/*`, `no-cache` for `index.html`, Gzip/Brotli. See `Performance/optimizations.md`.
- **R7.3 (eng, Medium):** Batch initial load (single `/api/bootstrap` or `Promise.allSettled` + partial render), add timeout + `AbortController`, pause polling on `hidden` + backoff. See `JavaScript/fixes.ts`.
- **R7.4 (eng, Medium):** Cache static `/api/sources`/`/api/scoring` (ETag/304), paginate audit, add `React.memo` for lists.
- **R7.5 (eng, Low):** Optimise docs images (WebP, resize, lazy). See `Performance/optimizations.md`.

---

## 8. Accessibility — 58/100 (WCAG 2.2)

### Observations
- **Landmarks/semantics (confirmed):** Good: `<aside>` sidebar, `<nav>` main-nav, `<header>` topbar + page-header, `<main>`, `<footer>`, `<section>` panels, `<article>` stat/operation cards, `<table>` for data. One H1 per page (good). Heading order mostly H1→H2→H3 (some H2 inside cards after H1 — okay). No skip-link (fail).
- **Keyboard/focus (confirmed):** `:focus-visible` outline 2 px accent (good). All interactive elements are native `<button>`/`<a>`/`<input>` (good). **Gaps:** `Modal` has no focus trap, no focus return, no `aria-labelledby` (uses `aria-label` only), background not inert. Mobile drawer has no focus management, no `aria-expanded`/`aria-controls`, scrim is clickable div (not button). Filter tabs are `<button>` without `role="tablist"`/`aria-selected` (acceptable as buttons, but no arrow-key nav). Conversation menu has no Escape handling.
- **ARIA (confirmed):** Sparse but correct where used: `aria-label` on search, sort, icon-buttons; `aria-hidden` on decorative SVG; `role="dialog" aria-modal="true"` on Modal. **Missing:** `aria-live` for toasts/status, `aria-invalid`/`aria-describedby` for form errors, `aria-expanded` for expanders, `aria-current="page"` for nav (uses `.active` class only), `aria-pressed` for toggles, `aria-busy` for loading, `aria-describedby` for hints.
- **Contrast (confirmed, computed):** Pass: body 16.53:1, text-soft 8.79:1, accent 14.35:1, badges 6.0–9.25:1, nav 6.97:1, eyebrow 5.89:1, page-p 6.01:1, muted 4.67:1. **Fail AA (4.5:1 normal, 3:1 large):** footer 2.96:1, nav-section 3.44:1, placeholder 3.76:1, `core-status small` ~3.2:1, `global-search kbd` ~3.0:1. Placeholder contrast is a known WCAG nuance (placeholders are not required to meet 4.5:1 if labels exist, but here placeholder *is* the label for search — fail).
- **Type size (confirmed):** 7–10 px micro-type fails WCAG 1.4.4 (Resize text) in practice and is unreadable for low-vision users. No rem units (all px), no user font-size respect, no zoom test (200% zoom likely breaks 242 px sidebar + 1600 px max-width layout).
- **Forms (confirmed):** `Field` uses wrapping `<label>` (good — implicit association). Required indicated by `*` + `required` attr (good). Hints are `<small>` inside label (okay, but no `id`/`aria-describedby` link). Errors are toast-only (fail 3.3.1/3.3.3). No `autocomplete` attrs, no `inputmode`, no `aria-required`.
- **Screen-reader friendliness (confirmed):** Icons are decorative (Lucide SVGs have no `aria-hidden` except brand mark — screen readers may announce them). Score rings convey score via text (good). Status dots + badges convey via text (good — not colour-only). Tables have `<th>` (good). Chat messages have no `role="log"`/`aria-live`. Toasts have no live region (fail 4.1.3).
- **Motion (confirmed):** No `prefers-reduced-motion` handling. Animations: loading shimmer, toast slide, hover lifts, orbit rings, progress bars. Vestibular risk for orbit/loading animations.
- **Target size (confirmed):** WCAG 2.2 AA requires 24×24 px minimum (2.5.8), AAA 44×44. Many targets fail: badge 22 px min-height, `approval-bell b` 16 px, `nav-item b` 19 px, `operation-expand` 25 px, `icon-button` (unstyled size), filter-tab buttons (small padding). Primary buttons (36 px) pass AA but fail AAA.
- **Error handling (confirmed):** Toasts announce visually only. No `role="alert"` for errors. No persistent error summary. No `aria-live="polite"` for operation status changes.
- **Edge cases:** Focus is lost on route change (no focus management to H1/main). Modal Escape works, but focus not restored. Drawer Escape not handled. Toast dismiss button has no `aria-label`. Loading state has no `aria-busy`/`role="status"`.

### Recommendations
- **R8.1 (design+eng, Critical):** Type scale ≥12 px, contrast fixes, skip-link, focus-trapped modal with return, toast `role="status"`/`role="alert"`, `aria-expanded`/`aria-current`, reduced-motion. See `Accessibility/fixes.md` + `CSS/fixes.css`.
- **R8.2 (eng, High):** Inline form errors + `aria-invalid`/`aria-describedby`, focus first error. See `Accessibility/fixes.md`.
- **R8.3 (eng, Medium):** Target-size pass: 24 px minimum (AA), 44 px for primary actions. See `CSS/fixes.css`.
- **R8.4 (design+eng, Medium):** Publish Accessibility statement + test with NVDA/VoiceOver + keyboard-only + 200% zoom. See Task T-22.

---

## 9. Security & Privacy — 76/100

### Observations
- **HTTPS (confirmed):** Local app is HTTP on loopback (correct — no TLS needed for `127.0.0.1`). No HSTS (correct for HTTP loopback; **required** if ever served over HTTPS). No mixed content (no external resources except GitHub/npm/Ollama APIs server-side).
- **Security headers (confirmed, live curl):** Present: `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: no-referrer`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`. **Missing:** `Content-Security-Policy` (no CSP at all), `Strict-Transport-Security` (N/A for loopback HTTP, required for HTTPS), `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`, `Cache-Control` (sensitive data cacheable), `X-Permitted-Cross-Domain-Policies`. `X-Frame-Options: SAMEORIGIN` is correct (not `DENY` — app may need same-origin framing? Actually no framing needed; `DENY` would be stricter, but `SAMEORIGIN` is acceptable).
- **Cookie flags (confirmed):** No cookies set (stateless API, no session cookie). `session_role` is server-side DB setting, not a cookie — good (no cookie flags to audit). No `Set-Cookie` observed.
- **Mixed content / exposed files (confirmed):** No external scripts/styles/fonts (all bundled). `public/downloads/*.ps1` are intentionally public (audit/backup scripts). `.env`, `host_data/`, `data/*.db` are gitignored + CI-checked (good). `/api/docs` (Swagger UI) is publicly reachable on loopback (info disclosure: full API schema). `/api/system/export` dumps all data unauthenticated (see below).
- **Clickjacking (confirmed):** `X-Frame-Options: SAMEORIGIN` mitigates. No CSP `frame-ancestors` (would be stronger). No `frame-ancestors 'none'` needed for local app.
- **Authentication/Authorization (confirmed, critical):** **Core research API has zero authentication.** `POST /api/programmes`, `PATCH /api/settings`, `GET /api/system/export`, `GET /api/audit` all succeed unauthenticated (verified). Operations routes use server-side `session_role` (default `owner`) with `require()` permission checks — but role is **not** tied to any credential; anyone who can reach the port is `owner`. Host companion *does* require `X-Sentinel-Token` + HMAC envelope + replay protection (excellent). **Threat model is “single trusted user on loopback”** (`SECURITY.md`) — safe *iff* loopback-only. `npm run server` binds `0.0.0.0` (all interfaces) — **dangerous default**.
- **Input validation (confirmed):** Strong: Pydantic models with `Field(min/max/ge/le)`, URL validators (http/https + netloc), asset single-line checks, currency upper-casing, duplicate-URL 409, reward_max≥min, approval scope-subset checks, expiry future checks, kill-switch 423, evidence completeness gates. No SQL injection (parameterised queries throughout). No XSS (React escapes; `content_md` rendered in `<pre>` as text, not HTML). No `dangerouslySetInnerHTML`/`eval`/`exec` found.
- **Host companion (confirmed):** Binds `127.0.0.1:8765` only (good). Token via env/file, `secrets.compare_digest` (good). Replay: `used-operations.json` (last 500), fail-closed on unreadable state (good). Allowlisted actions only (`validate_plan`, 1–12 actions), protected code paths, patch size ≤200 KB, 1–20 files. No arbitrary shell/path/command params. WinGet exact IDs, no hash bypass. Excellent.
- **Docker (confirmed):** Non-root (`sentinel:10001`), read-only FS, `cap_drop: ALL`, `no-new-privileges`, loopback-only publish, no socket/host mounts, healthcheck. Strong. Missing: image signing, SBOM, pinned digests (uses `node:20-alpine` + `python:3.12-slim` tags, not digests).
- **Secrets (confirmed):** No hardcoded secrets. `.env.example` has placeholders. Tokens excluded from backups/exports (good). `host-token` file permissions not explicitly set (relies on FS defaults — should be `0600`).
- **Privacy (confirmed):** Local-first: no analytics, no tracking, no external calls except Ollama (localhost), GitHub/npm release checks (server-side, user-initiated), and host companion (loopback). No PII collected beyond researcher name/handle (user-entered). No GDPR/UK GDPR statement (not needed for local app; needed for public site with analytics/forms).
- **Rate limiting / DoS (confirmed gap):** No rate-limiting on any route. `POST /api/programmes/import` caps at 100 (good). `GET /api/audit` caps at 1000 (good). No timeout on `fetch` (client) or `httpx` (except Ollama 4 s, host 20–3900 s). No request-size limits beyond Pydantic field maxes (notes 50 KB, evidence 200 KB — reasonable).
- **Edge cases:** Token missing → 503 (good). Replay → 409 (good). Tampered plan → 409 (good). Expired envelope → 403 (good). Corrupted backup → restore blocked (good). Unreadable replay state → fail-closed 503 (good). Kill-switch → 423 + revocation (good). **Missing:** brute-force protection on token (no rate-limit), audit-log tampering via DB file access (SQLite triggers only protect via SQL, not file overwrite — documented as local-trust).

### Recommendations (defensive only)
- **R9.1 (eng, Critical):** Bind core to `127.0.0.1` by default (`--host 127.0.0.1` in `npm run server`, Dockerfile `CMD`, docs). Require explicit `--host 0.0.0.0` opt-in with warning. See `Security/hardening-checklist.md`.
- **R9.2 (eng, High):** Add token gate for mutating core routes (reuse host-token pattern or new `SENTINEL_API_TOKEN`). Read-only health/dashboard may stay open on loopback. See `Security/headers.md` + Task T-10.
- **R9.3 (eng, High):** Add CSP (report-only → enforce), HSTS (when HTTPS), `Cache-Control: no-store` for `/api/*`, `COOP`/`CORP`. See `Security/headers.md`.
- **R9.4 (eng, Medium):** Rate-limit + request timeouts + `host-token` file `0600` + Docker digest pinning + SBOM/signing. See `Security/hardening-checklist.md`.
- **R9.5 (eng, Low):** Protect `/api/docs` (disable in prod or require token), add `X-Robots-Tag: noindex` for local app.

---

## 10. Technical / Bugs — 81/100

### Observations
- **Quality defects (confirmed):** No crashes in tests/build. Two `ResourceWarning` (SQLite) + Starlette/httpx `TestClient` deprecation warning noted in `docs/VERIFICATION.md` (reproduced Starlette warning in this audit). No TODO/FIXME found. No `console.log` in src (clean).
- **Broken links/paths/assets (confirmed):** All internal routes return 200 (SPA). `/robots.txt` + `/sitemap.xml` return SPA HTML (broken as files, but not 404). `HEAD` returns 405 (broken for health checks/monitors expecting HEAD). `/api/docs` returns 200 (Swagger UI — intentional? Should be noted). `public/downloads/*.ps1` exist and are copied by `prepare-downloads.mjs` (good). `dist/` is gitignored (good). No broken `<img>` (none in SPA). Docs images exist (6 files, 2.3 MB).
- **Platform/stack signals (confirmed):** React 19, Vite 6, TS 5.7, FastAPI 0.115+, Pydantic 2.9+, Uvicorn 0.34+, httpx 0.27+, psutil 6+. Python 3.12+ required (sandbox 3.11 still ran tests with `--break-system-packages` — version floor not enforced at runtime). Node 20+ required. SQLite WAL. No ORM (raw SQL — fine for this scale). No migrations (schema via `CREATE TABLE IF NOT EXISTS` — no upgrade path for breaking changes).
- **Maintainability (confirmed):** Clean separation: `backend/` (core), `host_companion/` (host), `src/` (UI), `windows/` (setup), `scripts/` (PS1), `tests/` (21 tests). `tsconfig` strict, `noUnusedLocals:false` (lenient). No ESLint/Prettier config found (no `.eslintrc`, no `prettier` in `package.json`) — style drift risk. No `pyproject.toml`/`ruff`/`mypy` config — Python lint/type gap.
- **Third-party deps (confirmed):** Frontend: `react`, `react-dom`, `react-router-dom`, `lucide-react`, `vite`, `@vitejs/plugin-react`, `typescript` (7 deps, 0 vulnerabilities per `npm audit`). Backend: `fastapi`, `uvicorn[standard]`, `pydantic`, `httpx`, `python-multipart`, `psutil` (6 deps). No Dependabot/Renovate (supply-chain gap). No lockfile drift (`package-lock.json` committed, `npm ci` in CI/Docker — good).
- **Bug list (confirmed):**
  - **B1 (Medium):** `HEAD /` + `HEAD /api/health` → 405. Healthchecks/monitors using HEAD will fail. Fix: add `include_in_schema=False` HEAD handlers or `methods=["GET","HEAD"]`.
  - **B2 (Medium):** SPA catch-all masks 404s (`GET /nonexistent-route` → 200). Breaks SEO, debugging, monitoring. Fix: real 404 for non-asset unknown paths + custom 404 page.
  - **B3 (Low):** `DataContext` all-or-nothing fetch (10 parallel, one failure → full-page error). Fix: `allSettled` + partial render.
  - **B4 (Low):** `frontend()` serves any file under `dist/` if `candidate.is_file()` — includes `downloads/*.ps1` (intentional) but also any future sensitive file. Fix: allowlist extensions.
  - **B5 (Low):** `download_report` writes to `BACKUP_DIR.parent/reports/` on every download (side-effect on GET — violates safe-method semantics). Fix: stream from memory, no disk write.
  - **B6 (Low):** `update_finding` builds SQL via f-string `f"UPDATE findings SET {assignments}…"` with keys from Pydantic model (safe today, but fragile). Fix: allowlist columns.
  - **B7 (Info):** `require_https_url` allows `http` (name says https). Intentional for local dev, but misleading. Fix: rename or enforce https in prod.
  - **B8 (Info):** `SENTINEL_DISABLE_MONITOR` env var is read where? (monitor loop checks it — verify). Tests set it; prod default enables monitoring (good).
- **Edge cases:** Empty DB (handled), corrupted backup (blocked), expired approval (revoked), kill-switch (423), duplicate programme URL (409), out-of-scope asset (422), missing evidence (422), unpaid bounty without date (422), replayed operation (409), tampered plan (409), host unavailable (503 with message), Ollama unavailable (graceful “not connected”). **Missing:** offline, 404, rate-limit, concurrent-write conflict, disk-full, DB-locked (SQLite `timeout=10` helps, but no retry UI).

### Recommendations
- **R10.1 (eng, High):** Fix B1+B2 (HEAD + real 404). See `HTML/snippets.md` + Task T-12.
- **R10.2 (eng, Medium):** Fix B3+B5 (partial render + no GET side-effects). See `JavaScript/fixes.ts`.
- **R10.3 (eng, Medium):** Add ESLint + Prettier + Ruff + mypy (CI). See Task T-13.
- **R10.4 (eng, Medium):** Add DB migrations (Alembic or versioned schema) + `pyproject.toml`. See Task T-14.
- **R10.5 (eng, Low):** Add Dependabot + CODEOWNERS + branch protection + SBOM. See Task T-15.

---

## 11. Conversion (CRO) — 35/100

> **Scope note:** SENTINEL is a local tool with no signup/checkout. CRO is scored as a *public website funnel* (GitHub repo → release → install → activation). Low score = “no funnel exists”, not “funnel is broken”.

### Observations
- **CTAs (confirmed):** In-app CTAs are clear and honest. Public CTAs: GitHub “Download ZIP” / “Code” / release assets (`Setup.exe`, `Windows-Setup.zip`). No landing page, no “Get started”, no email capture, no demo, no pricing page (correctly £0, but not stated as a funnel element).
- **Signup/checkout/contact flows (confirmed):** None. No accounts (single-user local). No contact form, no support email, no Discord/Slack, no newsletter. Support = GitHub issues + `SUPPORT.md` (good for OSS, weak for CRO).
- **Trust badges/social proof (confirmed):** None. 0 stars, 0 forks, no testimonials, no logos, no press, no security audit, no uptime, no “as seen on”. Release page has verification table (trust via transparency, not social proof). MIT licence + SECURITY.md help, but no badges.
- **Conversion friction (confirmed):** GitHub → Release → Download EXE/ZIP → Extract → SmartScreen bypass → Python bootstrap → Inspect → Approve → Pair → Test Ollama → Record programme. **~10 steps** before first value. No guided tour, no video, no GIF, no “5-minute quickstart”. Unsigned EXE triggers SmartScreen (major friction). No checksum/SHA published alongside release assets (trust gap).
- **Funnel gaps (confirmed):** No awareness (no site/SEO), no consideration (no docs site/features page), no evaluation (no demo/screenshots in README beyond banner), no conversion (no guided install), no retention (no analytics/feedback), no advocacy (no share/star prompt, no referral).
- **Edge cases:** Failed install → “partial” + retry (good, but no troubleshooting guide linked). Host not paired → warning + download link (good). Ollama not connected → “Test connection” (good). No onboarding email, no drip, no in-app tips.

### Recommendations
- **R11.1 (growth+content, High):** Public landing page with hero, screenshots/GIF, 3-step quickstart, downloads, security, FAQ, contact. See `Content/rewrites.md`.
- **R11.2 (eng+content, High):** Publish SHA-256 checksums + signed releases + SmartScreen instructions + video walkthrough. See Task T-27.
- **R11.3 (design+eng, Medium):** In-app onboarding checklist + demo mode + “Star on GitHub” + feedback prompt (opt-in, local-only). See Task T-18/T-19.
- **R11.4 (growth, Medium):** Add README badges, screenshots, GIF, FAQ, “Who is this for”. See `Content/rewrites.md`.
- **R11.5 (growth, Low):** Privacy-respecting analytics (Plausible/Fathom, no cookies) on public site only; never in local app without opt-in. See Task T-19.

---

## 12. AI Opportunities — 88/100

### Observations
- **In-product AI (confirmed, strong):** Conversational console (`/assistant`) with persisted conversations, deterministic registered intents (17 intents: health, backup, restore, check_updates, install_updates, install_missing, repair_docker/agent, emergency_stop, earnings, discover_programmes, start_research, reports, model_advice, code_change, explain, storage), optional local Ollama classification (temperature 0, JSON-only, confidence ≥0.65, allowlisted intents only), constrained code patches (approved roots, diff-only, protected paths, backup+verify+reverse). Models cannot issue shell commands, expand scope, or submit reports. **This is exemplary constrained-AI design.**
- **Automation (confirmed):** Periodic read-only monitoring (never installs), update checks (official sources only), dependency registry, installation reports, emergency stop. No auto-remediation (correct). No onboarding automation, no support bot beyond assistant, no content automation, no analytics automation.
- **Personalization/qualification (confirmed gap):** No lead qualification (no leads), no personalization (single-user), no recommendation engine beyond six-factor ranking (which *is* personalization via researcher estimates — good). No “next best action” beyond Dashboard checklist.
- **Business value estimates (confirmed gap — no metrics):** No baseline (no users, no funnel). Estimates below are directional, not guarantees.
- **Edge cases:** Ollama unavailable → deterministic fallback (good). Model returns invalid JSON → `None` → deterministic (good). Code patch invalid → 422 with reason (good). Unknown intent → honest “no safe action” (good). No hallucinated programmes/earnings (good). **Missing:** prompt-injection handling (user text is classified, not executed — safe by design, but no explicit injection tests), model-output logging/evals, cost tracking (local only, £0).

### Recommendations (with expected business value)
| # | Opportunity | Value | Effort | Owner |
|---|-------------|-------|--------|-------|
| A1 | **Terms-compliant programme connector** (authenticated APIs only, preserve URLs + timestamps; never scrape/invent). Unlocks discovery — the #1 user request (`discover_programmes` intent currently returns “not configured”). | **High** — removes manual programme entry (biggest activation blocker) | L (4–8 wks) | eng+growth |
| A2 | **RAG over user’s own docs** (programme policies, findings, reports) for grounded Q&A (“What does this policy say about AI use?”). Local embeddings only. | **Medium-High** — faster research, fewer policy mistakes | M (3–4 wks) | eng+AI |
| A3 | **Intent eval harness** (golden set of 200+ utterances, measure precision/recall per intent, CI gate). Prevents regression as intents grow. | **Medium** — quality/safety | S (1 wk) | eng+AI |
| A4 | **Onboarding copilot** (guided checklist + contextual tips + “what to do next” based on real state). | **Medium** — activation | S–M (1–2 wks) | design+eng |
| A5 | **Report-quality linter** (checks evidence completeness, AI disclosure, severity justification before validation). | **Medium** — acceptance rate | S (1 wk) | eng+content |
| A6 | **Support bot** (docs-grounded answers, no hallucinated steps; escalate to GitHub issues). | **Low-Medium** — support deflection | M (2–3 wks) | eng+content |
| A7 | **Analytics copilot** (weekly digest: eligible queue, expiring approvals, stale sources, earnings trend — from real data only). | **Low-Medium** — retention | S (1 wk) | eng |
| A8 | **Isolated research executor** (Phase 5 gates: EULA review, isolated network, egress proxy, rate-limit outside model, kill-switch wiring, lab-only testing). **Do not build until gates met.** | **High (strategic)** — but high risk | XL (3–6 mo) | eng+security |

**Guardrails for all AI work:** No autonomous testing/submission, no scope expansion, no invented data, human approval for consequential actions, local-first by default, disclose AI use per platform rules.

---

## 13. Competitive Positioning — 64/100

> **Method note:** No unverified competitor claims are made. Comparison is against *current best practices* for local-first security-research tools and public OSS sites, not named competitors’ features.

### Observations
- **Above average:** Radical honesty (empty states, partial status, unverified warnings) — most tools hide these. Exact-plan approval + HMAC + replay protection — more rigorous than typical “AI agent” tools. Cash-only + explainable ranking — more principled than opaque scoring. Recovery discipline (SHA-256, safety points, selective restore) — enterprise-grade. Constrained AI (deterministic intents, no shell) — safer than autonomous agents.
- **Average:** Dark UI polish, Lucide icons, Inter/system stack, responsive breakpoints, docs depth, CI, community files. Comparable to well-maintained OSS.
- **Behind:** No public site/docs site (most OSS have GitHub Pages/ReadTheDocs). No demo/screenshots in README (most have GIFs). No analytics/feedback loop. No programme connectors (manual entry only). No signed releases. No i18n. No PWA/offline. No light mode. No keyboard shortcuts beyond Ctrl+K (→ assistant).
- **Patterns worth adopting (best practice, not competitor claims):** (1) GitHub Pages docs site with search (MkDocs/Docusaurus). (2) README badges + GIF + FAQ. (3) Signed releases + checksums + SBOM (SLSA). (4) Demo mode with clearly-labelled sample data. (5) Privacy-respecting analytics on public site. (6) Accessibility statement + VPAT. (7) Changelog page + RSS. (8) “Star on GitHub” + community prompts. (9) Keyboard shortcuts + command palette (Ctrl+K already exists — extend). (10) PWA install prompt for public docs.

### Recommendations
- **R13.1 (growth, High):** Ship public docs site + landing page (see §6/§11). This alone closes the biggest positioning gap.
- **R13.2 (eng, Medium):** Signed releases + SBOM + checksums (see Task T-27).
- **R13.3 (design+eng, Medium):** Demo mode + onboarding (see Task T-18).
- **R13.4 (eng, Low):** Command palette + shortcuts + PWA for docs (see Tasks T-29/T-31).

---

## 14. Missing Features — 55/100

### Observations (prioritised by business value)
| # | Missing feature/page/policy | Value | Evidence of absence |
|---|-----------------------------|-------|---------------------|
| M1 | **Public website** (homepage, features, screenshots, downloads, docs, changelog, security, contact) | Critical — discoverability | No Pages, no domain, `homepageUrl`=repo |
| M2 | **Help / FAQ / troubleshooting** (Windows install failures, SmartScreen, Ollama setup, Docker, rollback) | High — support deflection | Docs exist but no FAQ/search; no troubleshooting matrix |
| M3 | **Accessibility statement + VPAT** | High — trust/compliance | No statement file/page |
| M4 | **Privacy policy / data-handling notice** (for public site + analytics) | High — legal/trust | No policy (local app needs none; public site will) |
| M5 | **Terms / licence page** (MIT summary + third-party terms) | Medium | `LICENSE` + `THIRD_PARTY_NOTICES.md` exist, but no public Terms page |
| M6 | **Onboarding / demo mode** (guided checklist + sample data) | High — activation | Empty start, no demo toggle |
| M7 | **Analytics (privacy-respecting, public site only)** | Medium — measurement | No analytics code |
| M8 | **Feedback / NPS / support funnel** | Medium — retention | No feedback widget, no NPS |
| M9 | **Search across all records** (findings/reports/audit) | Medium — UX | Only opportunities + audit filter |
| M10 | **Keyboard shortcuts + command palette** | Low-Medium — power users | Only Ctrl+K → assistant |
| M11 | **i18n (en-GB only today)** | Low — international | No i18n framework |
| M12 | **PWA / offline docs** | Low | No manifest, no SW |
| M13 | **Status / uptime page** | Low | No status (local app — N/A; public site — needed) |
| M14 | **Blog / changelog page / RSS** | Low-Medium — SEO/community | `CHANGELOG.md` exists, no public page/RSS |
| M15 | **Contact / support page** (email, issues link, SLA) | Medium | `SUPPORT.md` exists, no public page |

### Recommendations
- **R14.1 (growth+content, Critical):** Public site MVP (M1+M2+M5+M15). See Roadmap Phase 1.
- **R14.2 (design+eng, High):** Demo mode + onboarding (M6). See Task T-18.
- **R14.3 (content, High):** A11y statement + Privacy + Terms (M3+M4+M5). See Tasks T-22/T-23.
- **R14.4 (eng, Medium):** Global search (M9) + shortcuts (M10). See Tasks T-20/T-29.
- **R14.5 (growth, Low):** Analytics + feedback (M7+M8) + blog/RSS (M14). See Task T-19.

---

## 15. Priority Matrix — 90/100

> **Score rationale:** This package provides a fully categorised matrix (Critical/High/Medium/Low) with time, difficulty, and impact for every recommendation. Score 90 reflects completeness/actionability of the matrix itself; product prioritisation maturity is scored in §1–§14.

### Matrix (summary — full table in `Priority-Roadmap.md`)

| Priority | Count | Examples |
|----------|-------|----------|
| **Critical** | 6 | A11y blockers, loopback+token gate, public-site decision, real 404/HEAD, CSP, Windows verification |
| **High** | 14 | Code-split, cache headers, SEO assets, onboarding, demo mode, global search, form errors, signed releases, docs site |
| **Medium** | 18 | RAG, eval harness, report linter, analytics, i18n spike, PWA eval, SBOM, migrations, lint/type CI |
| **Low** | 12 | Light mode, blog/RSS, status page, shortcuts polish, image optimisation, OG polish |

Every item in `Developer-Tasks.md` maps to this matrix with **Title, Description, Acceptance criteria, Priority, Estimated effort, Owner discipline**.

---

## Appendix A: Evidence index

- Build: `npm run build` → JS 424.98 kB (gzip 123.45 kB), CSS 70.38 kB (gzip 14.80 kB), 1611 modules.
- Tests: `python -m unittest discover -s tests -v` → 21/21 OK.
- Live: `uvicorn backend.main:app --host 127.0.0.1 --port 18000` → headers, SPA fallback, robots/sitemap, unauthenticated API, CORS (see §9/§10).
- GitHub: `gh repo view` + `gh release view v0.2.0` + `gh api …/pages` (404, no Pages).
- Static: `grep` for semantics/ARIA/forms/polling/bind/secrets; contrast math (WCAG luminance); font-size histogram.

## Appendix B: What was *not* checked

- No Lighthouse/PageSpeed (no public URL). No NVDA/VoiceOver run. No Windows/Docker/Ollama live run. No pen-test. No competitor feature scraping. All labelled **Suspected** where relevant.

*Next: `Priority-Roadmap.md` (phased plan) → `Developer-Tasks.md` (implementable tasks) → subfolders (copy/code assets).*
