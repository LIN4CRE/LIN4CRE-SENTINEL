# GitHub-ready Developer / Product Tasks

Copy each block into a GitHub issue. `Priority` uses Critical / High / Medium / Low. Estimated efforts are person-effort, not calendar promises. Product safety constraints apply to all engineering work.

---

## T-01 — Fix accessibility type scale, contrast, motion, and target sizes

- **Description:** Raise all app text below 12 px to 12 px minimum (body 14–16 px); fix measured contrast failures for footer, nav section labels, placeholders, keyboard shortcut labels; respect `prefers-reduced-motion` and `forced-colors`; provide 24×24 px minimum interactive targets (44×44 primary where practical). Keep the existing dark palette.
- **Acceptance criteria:**
  - No rendered text below 12 CSS px except decorative/non-essential metadata, verified by CSS audit.
  - All normal text contrast ≥4.5:1 and large/bold text ≥3:1; automated axe scan has no contrast violations for touched screens.
  - Reduced-motion disables non-essential animations; forced-colors leaves controls visible.
  - Interactive target-size audit documents any WCAG 2.2 2.5.8 exceptions.
  - Screenshot review at 390 px, 768 px, 1440 px confirms no clipping/regression.
- **Priority:** Critical · **Effort:** 1–2 days · **Owner discipline:** design + engineering

## T-02 — Add keyboard skip link and robust modal focus management

- **Description:** Add a visible-on-focus “Skip to main content” link targeting `main#main-content`. Upgrade shared `Modal` with initial focus, Tab/Shift+Tab trap, Escape close, focus return, title association, and background inertness.
- **Acceptance criteria:**
  - Tab from page load reaches skip link first; Enter moves focus to main.
  - Opening modal moves focus inside; Tab cannot escape; Escape closes; focus returns to trigger.
  - Dialog accessible name comes from `aria-labelledby`; background cannot receive keyboard focus while open.
  - Manual keyboard test passes on Windows Chrome + Firefox; axe has no dialog violations.
- **Priority:** Critical · **Effort:** 1 day · **Owner discipline:** engineering

## T-03 — Make toasts, chat, loading, and operation status screen-reader accessible

- **Description:** Add `role="status"`/`aria-live="polite"` for success/info, `role="alert"` for errors; add `role="log"`/polite live updates for chat; label dismiss controls; expose loading via `aria-busy`; announce operation status transitions.
- **Acceptance criteria:**
  - NVDA/VoiceOver announce each toast once without stealing focus.
  - Error toasts are assertive; success toasts polite; close button has accessible name.
  - Chat message updates and operation state changes are announced without re-reading history.
  - Automated accessibility tests cover live-region roles.
- **Priority:** Critical · **Effort:** 1 day · **Owner discipline:** engineering

## T-04 — Add semantic navigation state and mobile drawer focus behavior

- **Description:** Add `aria-current="page"` to active route; mobile menu trigger gets `aria-expanded`/`aria-controls`; implement Escape close, focus management, and a keyboard-operable scrim/close mechanism.
- **Acceptance criteria:**
  - Active route is announced as current by screen readers.
  - Drawer opens with focus in the navigation, traps focus while open, closes with Escape and returns focus to trigger.
  - Scrim is not a clickable non-semantic `div`; controls meet 24×24 px minimum.
- **Priority:** High · **Effort:** 1 day · **Owner discipline:** engineering

## T-05 — Add accessible inline form validation and error recovery

- **Description:** Replace toast-only validation with field-level errors. Connect hints/errors via `aria-describedby`, set `aria-invalid`, preserve user input, focus first invalid field, and provide a form-level summary for server errors.
- **Acceptance criteria:**
  - Invalid required fields show text adjacent to the field and are announced.
  - Submitting invalid forms focuses the first invalid field and does not clear valid inputs.
  - Server 4xx errors map to a useful form-level message; 5xx/network errors preserve the form and offer retry.
  - Test empty, malformed URL, duplicate programme, expired approval, offline and server-error cases.
- **Priority:** High · **Effort:** 1–2 days · **Owner discipline:** engineering

## T-06 — Bind core server to loopback by default

- **Description:** Change default `npm run server` and Docker command to `127.0.0.1`. Require explicit documented opt-in to bind `0.0.0.0`; print a conspicuous warning when non-loopback binding is selected. Keep Compose host mapping loopback-only.
- **Acceptance criteria:**
  - Default server listens only on loopback and is unreachable from another LAN host.
  - Explicit environment/CLI opt-in supports container/network use with a warning.
  - Compose remains `127.0.0.1:8787:8000` and no privileged/socket mounts are added.
  - README and SECURITY threat model explain network boundary.
- **Priority:** Critical · **Effort:** 0.5 day · **Owner discipline:** engineering

## T-07 — Add authentication for core API mutations and data export

- **Description:** Add a per-install random API token (generated with secure randomness, stored with restrictive permissions) for mutating routes and sensitive export/audit endpoints. Use constant-time comparison, token rotation, and redacted logs. Health endpoint may remain minimal/read-only. Do not treat CORS as authentication.
- **Acceptance criteria:**
  - Unauthenticated programme create/update, settings changes, exports, audit access fail closed (401/403).
  - Token is never returned in UI/API, never logged, and has documented rotation/recovery flow.
  - Invalid tokens are rate-limited; tests cover missing, invalid, rotated, and valid token cases.
  - Host companion HMAC/replay protections remain unchanged.
- **Priority:** Critical before LAN exposure · **Effort:** 2–4 days · **Owner discipline:** engineering + security

## T-08 — Add security headers and private API cache controls

- **Description:** Implement CSP in report-only first, then enforce; add `Cache-Control: no-store` on `/api/*`; add COOP/CORP where compatible; add HSTS only on a genuine HTTPS public origin (not loopback HTTP). Keep existing nosniff/frame/referrer/permissions headers.
- **Acceptance criteria:**
  - CSP report-only produces zero unexplained violations in smoke tests, then enforced.
  - No API response containing user data is cacheable by shared caches.
  - HSTS is enabled only on HTTPS deployment with `includeSubDomains` decision documented; no HSTS on local HTTP.
  - Header tests cover index, API, errors, and static assets.
- **Priority:** High · **Effort:** 1–2 days · **Owner discipline:** engineering + security

## T-09 — Add rate limits, request timeouts, and safer host token file permissions

- **Description:** Apply per-route rate limits to auth and expensive operations, cap request bodies, add bounded outbound timeouts, and create host-token files with owner-only permissions where supported. Document local-app single-user scope.
- **Acceptance criteria:**
  - Repeated invalid auth and expensive requests return 429 with `Retry-After`.
  - External calls use bounded connect/read timeouts; the UI can cancel waiting calls.
  - Token file permission is 0600 (POSIX) or protected ACL on Windows; tests verify best-effort behavior.
  - Limits do not block normal polling or verified update checks.
- **Priority:** Medium · **Effort:** 3–5 days · **Owner discipline:** engineering + security

## T-10 — Fix HEAD handling and real 404 responses

- **Description:** Support `HEAD` for GET endpoints where monitoring/clients expect it. Replace SPA catch-all 200 on unknown paths with a real 404 response and accessible branded not-found UI; preserve valid React routes and static asset handling.
- **Acceptance criteria:**
  - `HEAD /` and `HEAD /api/health` return appropriate status/headers and no body.
  - Unknown page route returns 404 (not 200) and a useful page with Home/Help actions.
  - Unknown `/assets/*` and API paths return 404, never `index.html`.
  - Automated tests cover known route, unknown route, missing asset, API 404, HEAD.
- **Priority:** Critical · **Effort:** 1 day · **Owner discipline:** engineering

## T-11 — Split SPA into route-level chunks and set initial bundle budget

- **Description:** Lazy-load all 11 route components; configure Rollup manual chunks for React/router/vendor/icons. Add CI bundle-size budget and document exceptions.
- **Acceptance criteria:**
  - Initial JS compressed payload ≤150 KB (or documented decision if not achievable); each route loaded on demand.
  - No route renders blank while chunk loads; accessible loading fallback and chunk-load retry are present.
  - CI fails when initial JS exceeds budget by >10%.
  - Build output reports chunk sizes; smoke tests cover direct navigation to every route.
- **Priority:** High · **Effort:** 1–2 days · **Owner discipline:** engineering

## T-12 — Add static asset caching and compression

- **Description:** Serve fingerprinted `/assets/*` with immutable one-year caching; serve HTML `no-cache`; enable gzip/Brotli at reverse proxy (or middleware if appropriate). Avoid caching `/api/*` private data.
- **Acceptance criteria:**
  - Fingerprinted assets return `Cache-Control: public, max-age=31536000, immutable`.
  - `index.html` is revalidated; API data is `no-store`.
  - Browser cache test demonstrates re-use across reload; compression negotiated for JS/CSS/JSON where host supports it.
- **Priority:** High · **Effort:** 1 day · **Owner discipline:** engineering

## T-13 — Add public website and decide canonical hosting

- **Description:** Build a static/prerendered public site (GitHub Pages, Vercel, or custom domain) separated from the local app/API. Pages: Home, Features, How it works, Downloads, Docs, FAQ, Security, Accessibility, Support/Contact, Changelog. Do not host the unauthenticated local API publicly.
- **Acceptance criteria:**
  - Product owner records the hosting/domain decision, canonical origin, and local-app/public-site separation.
  - Landing content is crawlable without client JS; HTTPS enabled; mobile 320/390 px works.
  - Every navigation/footer link resolves; no public endpoint exposes local user data.
  - Page has analytics only if privacy notice + opt-in/consent basis are resolved.
- **Priority:** High (if growth goal) · **Effort:** 3–5 days · **Owner discipline:** growth + content + engineering

## T-14 — Add SEO metadata, robots, sitemap, schema, manifest, and favicons

- **Description:** Add route-appropriate title/description/canonical/OG/Twitter tags for the public site; sitemap and robots served as correct MIME/types; JSON-LD SoftwareApplication/FAQ/Breadcrumb; manifest/favicons. Do not use the local SPA routes as indexed SEO landing pages.
- **Acceptance criteria:**
  - `robots.txt` is `text/plain`, sitemap is `application/xml`, both return 200 on public origin.
  - Sitemap contains only canonical, indexable, public URLs; no local/private app routes.
  - OG image 1200×630 with correct public-origin URL; JSON-LD validates without fabricated ratings/reviews.
  - Each public page has unique title/description/canonical and `lang="en-GB"`.
- **Priority:** High · **Effort:** 2–3 days · **Owner discipline:** growth + content + engineering

## T-15 — Improve public repository conversion assets

- **Description:** Improve README with CI/licence/release badges, table of contents, screenshots/GIF, who it is for/not for, 5-minute quickstart, FAQ, support/security links, checksum instructions, and custom Open Graph image. Maintain anti-hype copy.
- **Acceptance criteria:**
  - README first screen explains product, user, safety boundary, and primary download/source action.
  - All badges and internal links resolve; screenshots have descriptive alt text and reasonable file size.
  - No fake testimonials, unsupported claims, or fabricated metrics.
  - Release includes SHA-256 checksums for each downloadable artifact.
- **Priority:** High · **Effort:** 1–2 days · **Owner discipline:** content + growth

## T-16 — Onboarding checklist and safe demo mode

- **Description:** Make first-run setup stepwise and contextual. Add optional demo mode with synthetic records in a separate disposable database; never mix demo earnings/findings with real user records.
- **Acceptance criteria:**
  - User can start empty, or explicitly launch demo data; demo state is persistently labelled.
  - No demo record can be submitted, exported as real earnings, or mistaken for real findings.
  - “Reset demo” deletes only demo DB; switching to real profile is explicit.
  - First-run checklist has progress, skip, and resume states; keyboard/SR accessible.
- **Priority:** High · **Effort:** 3–5 days · **Owner discipline:** product + design + engineering

## T-17 — Graceful partial data loading, offline state, and polling backoff

- **Description:** Replace all-or-nothing `DataContext` fetch with `Promise.allSettled`/partial state, add request timeout/AbortController, show offline banner, pause polling in hidden tabs, backoff after failures.
- **Acceptance criteria:**
  - Failure of one non-critical endpoint does not blank the entire app; affected panel shows retry.
  - Requests abort on route/unmount and time out with actionable UI.
  - Offline/online transitions are communicated; no claim that unsaved actions completed.
  - 2.5–3 second polling pauses when `document.hidden`, resumes with bounded refresh.
- **Priority:** High · **Effort:** 2–3 days · **Owner discipline:** engineering

## T-18 — Add privacy-respecting public-site analytics and feedback

- **Description:** If a public site is approved, add privacy-preserving aggregate analytics (no tracking in local product without explicit opt-in) and a feedback route. Define data retention and privacy notice before launch.
- **Acceptance criteria:**
  - No analytics calls from local app by default.
  - Public site analytics choice, cookies, retention, region, and consent/legal basis documented.
  - Feedback submission is optional, minimal data, and has clear support destination.
  - Metrics cover page view → docs → download, not cross-device fingerprinting.
- **Priority:** Medium · **Effort:** 3–5 days · **Owner discipline:** growth + engineering

## T-19 — Add searchable help centre and troubleshooting matrix

- **Description:** Publish a docs site/FAQ covering install, SmartScreen, Python bootstrap, host pairing, Ollama, Docker, backups, recovery, updates, error states, and safe uninstall. Include a compatibility matrix and links to logs/issues.
- **Acceptance criteria:**
  - Searchable, keyboard accessible, mobile responsive, versioned docs.
  - Each error message has a troubleshooting page/anchor.
  - Windows/Docker requirements clearly distinguish verified vs pending platform support.
  - Docs link back to security policy, accessibility statement, release checksums, support.
- **Priority:** High · **Effort:** 1–2 weeks · **Owner discipline:** content + engineering

## T-20 — Add accessibility statement and test protocol

- **Description:** Publish an accessibility statement (known gaps, WCAG target, contact route, update date) and add automated axe + keyboard + screen-reader + zoom test protocol to release checklist.
- **Acceptance criteria:**
  - Statement does not claim conformance until independently supported.
  - CI includes axe on core routes; manual checklist covers NVDA/VoiceOver and 200% zoom.
  - Accessibility regressions have severity labels and owner.
- **Priority:** High · **Effort:** 3–5 days · **Owner discipline:** design + engineering + content

## T-21 — Add privacy/legal/support pages for the public surface

- **Description:** Publish a plain-language privacy notice, Terms/acceptable-use note (clearly distinguish MIT licence), and Support/Contact page. Seek qualified legal review before making legal representations.
- **Acceptance criteria:**
  - Explain local data storage, external network calls, telemetry policy, data deletion/export, third-party dependencies.
  - Contact/support route is monitored and response expectations are stated honestly.
  - Terms do not imply bounty-program permission or guarantee outcomes.
  - Legal review is recorded before public launch.
- **Priority:** High before public analytics/site forms · **Effort:** 2–4 days + review · **Owner discipline:** content + product

## T-22 — Sign releases, publish checksums/SBOM, pin container digests

- **Description:** Add reproducible release workflow, signed Windows artifacts, SHA-256 checksums, SBOM (CycloneDX/SPDX), provenance attestation; pin base images by digest and update via automation.
- **Acceptance criteria:**
  - Each release asset has published checksum and verifiable signature/provenance instructions.
  - SBOM attached to release; CI verifies no known critical/high dependency issues or documents accepted exception.
  - Docker base image digest is pinned and updated by PR automation.
  - Windows signing certificate plan and SmartScreen impact are documented; do not claim “trusted” without validation.
- **Priority:** High · **Effort:** 1–2 weeks · **Owner discipline:** engineering + security

## T-23 — Add lint, formatting, type checks, schema migrations, and CI gates

- **Description:** Add ESLint/Prettier for TS, Ruff/mypy for Python, versioned DB schema migrations, dependency update bot, CODEOWNERS, branch protection, and CI checks.
- **Acceptance criteria:**
  - CI checks lint/type/tests/build on pull requests.
  - Existing DB upgrades from previous release are tested with backup/rollback.
  - Dependabot/Renovate updates are grouped and reviewed.
  - CODEOWNERS and branch rules require CI before merge, where repo permissions allow.
- **Priority:** Medium · **Effort:** 1–2 weeks · **Owner discipline:** engineering

## T-24 — Add AI intent evaluation and safe regression tests

- **Description:** Establish a golden evaluation set for deterministic intents and optional Ollama classifier. Include ambiguous, adversarial, injection-like, malformed, and unsupported requests. Safety actions remain deterministic; model cannot authorize execution.
- **Acceptance criteria:**
  - At least 200 versioned utterances with expected intent/abstain outcome.
  - CI reports precision/recall and blocks safety-critical regressions.
  - Injection-like requests cannot alter permissions, target scope, or invoke arbitrary actions.
  - Model/version/prompt/result metadata is stored without exposing sensitive data.
- **Priority:** Medium · **Effort:** 1–2 weeks · **Owner discipline:** engineering + AI

## T-25 — Run real Windows verification sprint

- **Description:** Test clean Windows 10/11 install, unsigned/signed installer behavior, UAC, Python bootstrap, host companion pairing, Docker Desktop, Ollama, upgrades, rollback, backup/restore, uninstall. Capture actual results only.
- **Acceptance criteria:**
  - Test matrix records OS build, hardware, exact installer hash, steps, expected/actual, logs, result.
  - Every failure has issue, severity, workaround, and re-test evidence.
  - Docs/README/release claims updated to observed scope; no “verified” claim without evidence.
  - Recovery point and uninstall/data-retention behavior verified.
- **Priority:** Critical before Windows promotion · **Effort:** 1 week · **Owner discipline:** engineering + QA

## T-26 — Build and smoke-test Docker image in CI

- **Description:** Add Docker build + container health/API smoke test to CI; verify non-root, read-only filesystem, dropped caps, loopback-only Compose, persistence and backup/restore.
- **Acceptance criteria:**
  - CI builds image for supported architectures and tests `/api/health` + static route.
  - Container UID is non-root; read-only, cap-drop, no-new-privileges remain.
  - Compose volume persists DB across restart; backup/restore test succeeds.
  - Docker support claims are updated based on actual CI evidence.
- **Priority:** Medium · **Effort:** 2–3 days · **Owner discipline:** engineering

## T-27 — Add terms-compliant programme data connector discovery spike

- **Description:** Evaluate official APIs/partner data sources only. Do not scrape, bypass auth, or invent programme data. Preserve source URL, policy URL, checked timestamp, policy changes, and user approval.
- **Acceptance criteria:**
  - Written source/license/terms review for each candidate.
  - No connector enabled without explicit user configuration and API credentials stored safely.
  - Imported records pass current validation and remain “needs review” until human confirms scope/policies.
  - Decision record includes go/no-go, cost, rate limits, privacy, maintenance owner.
- **Priority:** High (strategic) · **Effort:** 2-week spike; implementation 4–8 weeks · **Owner discipline:** product + engineering + security

## T-28 — Add report-quality linting before validation

- **Description:** Add deterministic checklist for evidence completeness, reproduction clarity, impact rationale, scope confirmation, and required AI-use disclosure. Do not generate fabricated evidence or auto-submit.
- **Acceptance criteria:**
  - Findings show missing/weak items with precise field links.
  - Linter never changes user text or severity silently.
  - Validation remains human-controlled and includes test cases for incomplete reports.
  - Platform-specific disclosure rules remain user-verifiable and sourced.
- **Priority:** Medium · **Effort:** 1 week · **Owner discipline:** product + engineering + content

## T-29 — Publish rewritten product copy and public landing page

- **Description:** Implement copy blocks in `Content/rewrites.md`; emphasize local-first, human authority, exact-scope approvals, zero paid software, no live testing or auto-submission. Include “for / not for” and clear install CTA.
- **Acceptance criteria:**
  - First viewport answers who it is for, what it does, how it is safe, and how to try it.
  - No guarantee, accepted-report claim, autonomous testing claim, fabricated metrics, or ambiguous “AI does security research” promise.
  - CTA labels distinguish source, Windows download, Docker, and docs.
  - Copy reviewed by product/security owner.
- **Priority:** High if public site · **Effort:** 2–3 days · **Owner discipline:** content + growth

## T-30 — Evaluate internationalisation and public docs PWA

- **Description:** Separate locale formatting/content from logic; assess additional locales and PWA/offline only for public docs. Do not cache private app API data in a service worker.
- **Acceptance criteria:**
  - Decision record includes demand, translation owner, content maintenance, bundle cost.
  - If PWA built, service worker caches only versioned public docs/static assets and excludes `/api/*` and personal data.
  - Date/currency formats are locale-aware without silent FX conversion.
- **Priority:** Low · **Effort:** 2–4 weeks spike/build · **Owner discipline:** product + engineering + content
