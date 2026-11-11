# Windows setup, verification and recovery

## Audience

This path is for users who do not want to write PowerShell, Python, JavaScript, Docker commands or configuration files. Technical work happens inside the graphical setup manager and conversational console.

## Clean setup

1. Obtain the complete `LIN4CRE-SENTINEL-Windows-Setup.zip` from the project release or **Maintenance → Download Windows setup**.
2. Back up any existing SENTINEL installation before extracting over it. Prefer a new folder for a first installation.
3. Extract the archive fully into a permanent folder.
4. Double-click `windows/SentinelSetup.cmd`.
5. Review any Windows SmartScreen/UAC prompt. This source release is unsigned; UAC should appear only when a selected vendor installer requires elevation.
6. If Python is absent, the native bootstrap explains the official `Python.Python.3.12` WinGet package. Nothing installs until you select **Install Python & continue**. Close and reopen setup afterwards so detection is fresh.
7. If local runtime packages are absent, the graphical manager displays the missing packages and asks before using `requirements.txt`.
8. Wait for the private local services, then select **Inspect this PC**.

The setup manager starts the host companion and core using the same local pairing token. An existing valid pairing is preserved rather than silently replaced.

## What inspection checks

Depending on actual OS support and permissions, the companion probes:

- CPU architecture/core counts, RAM and available GPU data;
- Windows/WSL status, filesystems, used/free storage and expected ports;
- Python, Node.js/npm, Git and SENTINEL core/database;
- Docker Desktop presence/version, Engine functionality and Compose;
- Ollama executable/version, real API response and installed models;
- registered OpenCode/security-tool configuration;
- official component release sources and Ollama registry digests only when requested.

An executable’s presence is not treated as functional health. Missing, unavailable, unconfigured and verification-failed states remain distinct. Historical audits are not fresh host verification.

## Approve an installation or repair

1. After inspection, select only missing/unhealthy components you want.
2. Choose **Plan selected installations** or **Plan health repair**.
3. Read the registered actions, parameters, plan hash and rollback statement.
4. Approve only that exact plan. Approval starts execution; there is no hidden second plan.
5. Follow any vendor/UAC prompt. SENTINEL does not bypass installer security hashes or request a reboot automatically.
6. Review the terminal state and verification evidence. `partial` means part of the operation could not be verified or completed.

The backend rechecks current host state when planning. Unsupported components fail closed. Existing applications are not silently uninstalled or reset.

## Retry, failed installation and update rollback

- A failed operation creates a pre-change recovery-point reference when the core was available.
- **Retry** creates a new operation requiring fresh approval; signed host envelopes cannot be replayed.
- npm update plans can include a reverse update to the recorded previous version.
- WinGet does not provide a universal safe downgrade. If no registered rollback exists, the UI says so; failure is not relabelled as recovery.
- Model digest changes are review-only because model weights are not included in ordinary backups.

## Backup

Select **Create verified backup** in setup, **Back up everything** in Recovery, or ask SENTINEL in ordinary language.

A core recovery point includes the SQLite database, settings, audit history, evidence/reports/research folders and non-secret application/agent configuration. Host configuration backup is attempted separately. If the host portion is unavailable, the operation is `partial`; the core recovery result is not hidden.

Every file is SHA-256 recorded. SQLite online backup, integrity and foreign-key checks run before a point is marked verified.

## Restore

1. Open **Recovery**.
2. Select **Verify** on the desired point and review any errors.
3. Choose **Restore**, then database, files and/or configuration.
4. Review and approve the exact restore plan.
5. SENTINEL verifies the point again, creates a fresh safety point, stages the database, restores selected state and verifies hashes/integrity.
6. On failure, database/file rollback to the pre-restore state is attempted and reported.

Restoring selected folders replaces their contents to match the recovery point; it does not merge extra post-backup files into the restored state. The safety point is created before replacement. Restored test approvals are revoked, and an active kill switch remains active.

Credentials and model weights must be re-authorised/rebuilt separately. Never delete the last known-good recovery point.

## Installation report

Select **Save installation report**. The JSON report contains the generation time, application version, fresh inspection result, install/repair/update operations, latest verified recovery point, setup state and limitations. It includes unavailable results rather than filling gaps with assumptions.

## Startup and recovery after failure

The graphical setup manager is repeatable. Open it again to inspect current state, review logs under the local SENTINEL application-data folder, create a new plan or enter Recovery. A service that does not become ready is reported as failed; setup does not infer success from process creation.

## Target-platform validation still required

The build sandbox cannot administer the user’s Windows PC. Before relying on this release operationally, validate on that PC: clean setup, missing/outdated detection, Docker/Ollama/model/OpenCode inspection, UAC behaviour, successful vendor installation/update, failed-update rollback where supported, restart behaviour and full recovery. Record actual outcomes in a new installation report.
