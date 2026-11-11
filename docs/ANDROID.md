# SENTINEL Android Companion (Preview)

The Android app is a **read-only companion**, not a standalone port of SENTINEL. Your existing desktop/server installation retains the SQLite database and performs all approved operations. The phone can view a dashboard summary, programme list, and scope approvals; it cannot create approvals, run tests, change settings, execute maintenance, restore data, or submit reports.

## Requirements

- SENTINEL desktop/server with this release's `backend.mobile_main` read-only API.
- Android 8.0 (API 26) or later.
- A trusted private connection to the server. The Android app accepts **HTTPS only** and uses the system TLS trust store.
- Do not port-forward the server or expose it on public Wi-Fi. Prefer a private VPN with HTTPS, a managed private network, or a carefully firewalled HTTPS reverse proxy.

## 1. Create a companion credential

Run from the repository root, using the same `SENTINEL_DATA_DIR` as the main app:

```bash
python -m backend.mobile_pairing
```

The command prints a high-entropy token once and stores only its SHA-256 digest at `data/mobile-token.sha256` (or `$SENTINEL_DATA_DIR/mobile-token.sha256`). Copy the token into the Android app. Do not put it in a URL, chat, shell history, issue, or log. Rotating it invalidates the old token:

```bash
python -m backend.mobile_pairing --rotate
```

The digest file is best-effort restricted to the current user on POSIX. On Windows, protect the containing data directory with the account's ACLs.

## 2. Start only the read-only mobile API

Keep the primary SENTINEL API and host companion on loopback. The separate mobile ASGI app contains only three authenticated, read-only data routes and does not expose `/api/docs`, the frontend, mutations, assistant, host operations, or recovery.

```bash
# Same data directory as the desktop app. Local-only listener; do not bind 0.0.0.0 directly.
SENTINEL_DATA_DIR=/path/to/sentinel-data python -m uvicorn backend.mobile_main:app --host 127.0.0.1 --port 8765
```

Configure a trusted HTTPS/VPN ingress to forward only to `127.0.0.1:8765`. Example Caddy site (requires a real DNS name and valid HTTPS certificate):

```caddyfile
sentinel.example.net {
    reverse_proxy 127.0.0.1:8765
}
```

Use the same data directory for pairing and for the mobile API process. Limit ingress at the VPN/firewall to your own devices. The read-only endpoints still reveal private programme names, scope approvals and actual paid totals; the bearer token is a secret.

> **Do not use plain HTTP.** The app rejects it. A bearer token sent over unencrypted Wi-Fi can be intercepted. Do not expose the existing `backend.main:app` on a network: that core API is not a remote-access API.

## 3. Install and pair the APK

1. Download **`SENTINEL-Android-Companion-preview.apk`** from the Android preview GitHub Release.
2. Verify its SHA-256 using the adjacent `.sha256` file (for example, `sha256sum -c SENTINEL-Android-Companion-preview.apk.sha256`).
3. Install the APK; Android may ask you to allow installation from the selected source.
4. Enter your HTTPS origin (for example `https://sentinel.example.net`) and the one-time pairing token.
5. Tap **Save securely and connect**. The token is encrypted using an Android Keystore AES-GCM key and is not displayed again.

The current GitHub APK is a **preview build signed with the ephemeral Android debug key from CI**, not a production signing identity. It is suitable for evaluation, but future preview builds may require uninstalling the previous build before installing the new one. Do not treat this APK as a verified production release. Production signing requires a stable private signing key managed outside source control (for example in protected GitHub Actions secrets) and a documented rotation/recovery plan.

## API surface

All routes require `Authorization: Bearer <token>` and return `Cache-Control: no-store`:

- `GET /api/mobile/v1/health`
- `GET /api/mobile/v1/overview`
- `GET /api/mobile/v1/programmes?limit=50` (maximum 100)
- `GET /api/mobile/v1/approvals?limit=50` (maximum 100)

Unknown paths return 404; the mobile app has no generic proxy to the core API. The API is intentionally read-only. This is a preview integration: token rotation is currently performed on the server command line, not in the Android UI.

## Build locally

Requirements: JDK 17 and Android SDK platform 35.

```bash
cd android
./gradlew --no-daemon assembleDebug
```

APK output: `android/app/build/outputs/apk/debug/app-debug.apk`.

## Limitations / next steps

- No background sync, notifications, offline cache, biometrics, write operations, or direct Android host automation.
- No public backend is provided; users operate their own private mobile API ingress.
- Preview APK is debug-signed. Stable production updates require a maintained release signing key.
- This companion is not an authorization to test targets. Follow each programme's current scope and policy.
