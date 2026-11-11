# Security & Privacy Audit

**Score: 76/100 for intended single-user local deployment.** If reachable beyond loopback without authentication, the posture falls sharply (estimated <40/100). This is a source/live-local audit, not a penetration test.

## Confirmed strengths
- Host companion binds `127.0.0.1:8765`, token-authenticated, HMAC signed short-lived envelopes, replay protection and allowlisted actions.
- Exact-plan hash approval; server-side role checks; human approval required for consequential actions.
- Pydantic validation, parameterised SQL, no React HTML sinks, no hard-coded secrets found.
- Append-only audit triggers, verified recovery points, hash manifests, rollback, approvals revoked on restore.
- Docker runs non-root, read-only, drops capabilities, no-new-privileges, loopback-only port mapping, no Docker socket/host mounts.
- Existing headers: nosniff, SAMEORIGIN, no-referrer, restrictive Permissions-Policy.

## Confirmed material risks
- Core API has **no authentication**: unauthenticated create programme, mutate settings, export data, read audit all succeeded in local test.
- `npm run server` and Dockerfile bind `0.0.0.0`; `compose.yaml` host publish is loopback-only, but direct server execution exposes LAN interfaces.
- No CSP, HSTS (not appropriate for loopback HTTP; needed for HTTPS), private API `Cache-Control: no-store`, or rate limiting.
- `/api/docs` is exposed on loopback; no explicit public production toggle.
- Data can include researcher handle/name, research notes, findings, audit history and export. No app auth means local host trust is the boundary.
- Image tags are floating (`node:20-alpine`, `python:3.12-slim`); no image digest pinning, release signature/SBOM not evidenced.

## Deployment boundary
**Do not expose the app to LAN or public internet** until token authentication, rate limits, HTTPS reverse proxy, secure headers, backup threat review, and deployment-specific authorization are implemented and tested. CORS is not authentication. HSTS must only be set on HTTPS origin; never add HSTS on local HTTP.

Detailed examples: `headers.md`; checklist: `hardening-checklist.md`.
