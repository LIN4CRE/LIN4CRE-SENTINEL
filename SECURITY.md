# Security policy

## Supported version

Security fixes are applied to the current `main` branch. SENTINEL 0.2.1 is an early local-operations release; core Windows behaviour is validated on Windows 11, while optional Docker/WSL2 administration still depends on the target PC's firmware and administrator access.

## Report a vulnerability

Do not open a public issue containing exploit details, credentials, private programme data, evidence or user content. Use GitHub **Private vulnerability reporting** when enabled by the repository owner, or contact the owner through the private channel listed in their GitHub profile.

Include the affected version/commit, impact, reproduction conditions, and whether host approval or local access is required. Do not test against third-party systems or real bug-bounty assets to demonstrate a SENTINEL issue.

## Trust boundaries

### Core application

- The intended deployment is a single trusted user on loopback. It is **not a multi-tenant Internet service**.
- The active role is server-side session state; request headers cannot elevate a viewer/researcher to owner.
- External testing and report submission require separate human workflow controls.
- SQLite audit rows reject updates and deletion through triggers.
- The global kill switch revokes pending and active test approvals.

### Host companion

- Binds only to `127.0.0.1`; do not change this to a LAN/public address.
- Requires a locally stored bearer token for inspection and execution.
- Mutations additionally require a short-lived owner envelope containing the operation ID, expiry, exact canonical-plan SHA-256 and HMAC signature.
- Used operation IDs are rejected; unreadable replay state fails closed.
- Only registered actions are accepted. There is no arbitrary shell, PowerShell, Python, command or path parameter.

### Android companion (preview)

- The Android app is a read-only client; it cannot execute testing, change settings, approve scope, operate the host companion, restore data or submit reports.
- It connects to a separate ASGI app (`backend.mobile_main`) that exposes only authenticated read-only endpoints. Do not expose `backend.main:app` to a phone or network.
- The mobile API binds to loopback by default in the documented command. Remote access must use a private VPN or a properly configured HTTPS ingress with firewall restrictions; do not send bearer tokens over plain HTTP.
- Pairing stores only a SHA-256 token digest on the server; the client encrypts the bearer token using Android Keystore. Revoke by running `python -m backend.mobile_pairing --rotate` and replacing the token in the app.
- Mobile API responses include private programme names, scope approvals and paid totals. Treat the bearer token as sensitive and grant access only to trusted devices.
- The GitHub preview APK is debug-signed, not production-signed. Do not rely on it for a stable authenticated production distribution.

### Install, update and code changes

- Installation/update plans originate from actual inspection and registered component metadata.
- WinGet uses exact package IDs and does not bypass installer hashes.
- Major updates, newly paid items and unsupported installers are excluded from automatic plans.
- A recovery point is created before consequential operations. Presence of a rollback is reported separately; universal rollback is not claimed.
- AI code output must be a unified diff under allowed source/test/documentation roots. Dependency files, secrets and protected security/approval/audit/recovery/executor files are rejected.
- Every affected source file is backed up and hash-verified before patch preflight/application. Python syntax or frontend build checks run as applicable; reverse patches are registered.

### Backup and restore

- Every manifest file is measured and SHA-256 hashed; SQLite integrity and foreign keys are checked.
- Absolute/parent-traversal manifest paths and symbolic-link recovery content are rejected.
- Restore is blocked after corruption. A new safety point is created first.
- Selected folders are restored exactly, not merged. File failures attempt rollback to the safety state.
- Later audit, operation and recovery history is retained during database restoration. Restored test approvals are revoked and an active kill switch remains active.
- API credentials, host tokens and model weights are deliberately excluded from ordinary recovery points.

## Secrets

Never commit `.env`, `host_data`, `data`, tokens, API keys, evidence, private scope rules, reports, earnings or model weights. If a token is exposed, stop the companion, replace the token, review audit/operation history and rotate any related credentials.

## Security-testing rules

Only test assets you own or for which you have current explicit written permission. Record exact programme scope, methods, automation/AI restrictions and rate limits. Re-read current programme rules before every engagement. No approval in SENTINEL expands scope, authorises destructive behaviour or guarantees programme/platform permission.
