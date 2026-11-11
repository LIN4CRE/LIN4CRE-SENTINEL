# Security hardening checklist (defensive)

## Before LAN/public exposure — blocking
- [ ] Bind loopback by default; make non-loopback an explicit, noisy opt-in.
- [ ] Add strong per-install API token/auth for mutations, export, audit, backup/restore; constant-time comparison; rotation/recovery.
- [ ] Add per-token rate limits and request/body caps; timeouts on outbound calls.
- [ ] Serve only behind HTTPS reverse proxy; correct trusted-proxy configuration; secure headers; HSTS on HTTPS only.
- [ ] `Cache-Control: no-store` on private API responses; ensure browser cache cannot retain exports.
- [ ] Protect or disable `/api/docs` in production mode.
- [ ] Verify CORS origins from exact deployment URLs; remember CORS is not authorization.
- [ ] Threat-model CSRF if cookie auth is introduced; token auth must not be exposed to third-party scripts.
- [ ] Test unauthenticated requests, invalid token, replay, expired approval, kill-switch, export, backup, restore.

## Supply chain / releases
- [ ] Pin base images by digest; automate update PRs.
- [ ] Dependabot/Renovate; review changelogs; test lockfile upgrades.
- [ ] Publish SBOM and build provenance; sign Windows assets; publish SHA-256 checksums.
- [ ] Least-privilege CI permissions, protected release environment, CODEOWNERS, required checks.
- [ ] Ensure secrets never enter logs, exports, backups, issue attachments, or crash reports.

## Runtime / data
- [ ] Restrictive permissions for data, token and replay files; test on Windows ACL and POSIX.
- [ ] Validate backup restore from corrupted, partial, old-schema and full-disk cases.
- [ ] Ensure logs redact personal/research data; retention and deletion documented.
- [ ] Explicitly test SQLite lock/full-disk failure and recovery.
- [ ] No automatic testing, scope expansion, or report submission.
