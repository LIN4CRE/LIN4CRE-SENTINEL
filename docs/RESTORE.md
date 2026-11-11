# Recovery checklist

## Windows configuration backup

1. Locate the timestamped backup folder and `manifest.json`.
2. Review every warning. If model weights were excluded, do not claim they are recoverable from this backup.
3. Re-run SHA-256 verification against each backed-up file. `Initialize-Sentinel.ps1` performs this check before folder setup.
4. Stop applications that own the configuration being restored.
5. Restore to a **separate recovery directory** first and compare paths/files.
6. Only after checking the recovered copy, merge deliberately. Never overwrite the sole current installation.

## SENTINEL SQLite backup

1. Stop SENTINEL and its Docker container.
2. Preserve the current database in a separate location.
3. Verify the `.db` against its `.sha256` sidecar.
4. Restore as `sentinel.db` in the configured data directory or a temporary recovery directory.
5. Start a temporary SENTINEL instance against the recovered database.
6. Check programme, approval, finding, report, payment and audit counts; export JSON for a second recovery format.
7. Only then make it the active database.

## Docker named volume

Use a temporary volume for the first restore test. Do not run experimental restore commands against the active `sentinel-data` volume. Record the exact image/version and volume mount used for the recovery test.

A backup is not considered verified merely because a file exists: its hash must match and a recovery inspection must succeed.
