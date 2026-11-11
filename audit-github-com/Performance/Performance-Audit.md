# Performance Audit

**Score: 68/100.** No public URL exists, so real-world CWV/Lighthouse is unverified. Bundle measurements and request behavior were reproduced locally.

## Confirmed measurement

| Asset | Raw | gzip | Notes |
|------|-----:|-----:|------|
| Initial JS | 424.98 kB | 123.45 kB | One chunk, 1611 modules transformed |
| CSS | 70.38 kB | 14.80 kB | 938 source lines total |
| HTML | 0.58 kB | 0.35 kB | SPA shell |
| **Total** | **~496 kB** | **~139 kB** | Before API payloads |

## Confirmed issues
- No `React.lazy` / route-level split; all 11 page modules load on first visit.
- 10 parallel initial API reads; one rejection causes a global connection error (no partial rendering).
- Assistant polls every 2.5s and Maintenance every 3s; no hidden-tab pause/backoff.
- No explicit static cache headers, compression headers, request timeout or cancellation in client.
- Inter is named in font stack but not downloaded (fast, but visual inconsistency).
- Docs banner is 1.5 MB; six images total ~2.3 MB; only README/release surfaces use them.

## Suspected CWV risks
- On slow mobile network, JS payload and client-rendered startup may push LCP over 2.5 s. No field data/Lighthouse run was possible.
- INP/CLS are likely acceptable but require measurement. Do not publish guessed CWV values.

## Targets
- Initial JS ≤150 KB compressed (budget; revise with measurement), route chunks loaded on demand.
- Public site critical content renders without JS; app has a meaningful loading state.
- LCP ≤2.5 s, INP ≤200 ms, CLS ≤0.1 at 75th percentile after deployment.
- API data `no-store`; fingerprinted static assets immutable; avoid repeated polling in hidden tab.
