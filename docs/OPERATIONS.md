# Operations guide

## Ask SENTINEL

Open **Ask SENTINEL** or press Ctrl/Cmd+K. Useful requests include:

- “Check whether everything is working.”
- “Install anything I’m missing.”
- “Check for updates.”
- “Review compatible updates.”
- “Fix the Docker connection.”
- “Start Ollama.”
- “How much space is SENTINEL using?”
- “Back up everything.”
- “Restore a verified recovery point.”
- “Show actual earnings.”
- “Explain what you are doing.”
- “Stop all running research.”

SENTINEL maps ordinary language to registered operations. If deterministic matching is unavailable, a selected local Ollama model may classify intent only into the registered set. It cannot supply shell commands or choose testing targets. Unsupported requests return an explicit unavailable response.

## Operation states

- `pending_approval`: plan recorded; nothing consequential has run.
- `queued`: exact plan approved; waiting to start.
- `running`: signed operation is executing.
- `succeeded`: registered actions and available verification passed.
- `partial`: a separately reported core/host portion failed or remains unavailable.
- `failed`: the operation or verification failed; inspect error and rollback evidence.
- `cancelled`: pending/queued operation cancelled before execution.

A running indicator is driven by persisted operation state, not simulated progress.

## Permissions

| Role | Permissions |
| --- | --- |
| Viewer | Read |
| Researcher | Read, research, backup |
| Operator | Researcher permissions plus repair |
| Owner | All operations, including install, update, restore, security and model permissions |

The server-side `session_role` setting controls the active local session. Request headers do not elevate it. Host mutations independently require an owner-signed envelope.

## Update discovery

Official release providers are registered per component. Results may include installed/latest compatible versions, upstream version, release URL/notes, published time, matching asset size, category and cost-review signals.

“Latest upstream” is not automatically “compatible.” Major-version changes and newly detected costs require separate review. Absence of data is not proof that no update exists.

## Code changes

With a verified local Ollama model selected, ask for a specific source change. SENTINEL retrieves only relevant allowed source context and asks the model for a unified diff.

Before execution you must review the complete patch. Protected files include dependency manifests and the approval/security/audit/recovery/companion execution controls. The host rejects arbitrary commands and paths. Source backups are hashed, the patch is preflighted, and applicable syntax/build checks run. A failed patch operation can use its registered reverse plan.

Model-generated code is not automatically correct or secure. Human technical review remains required. Without a verified model, code-change planning is unavailable.

## Emergency stop

Emergency stop activates the core kill switch, revokes pending/approved testing approvals and asks the host to stop only SENTINEL-registered research processes whose process identity matches. It does not kill arbitrary PIDs, uninstall software or delete data.

If host termination cannot be verified, the operation is `partial` even though core revocation succeeded.

## Research and submissions

SENTINEL’s programme ranking is only as good as the recorded source and researcher estimates. Exact-scope testing approval does not execute a live test in this release. External testing and every external submission remain human-controlled. Read current programme/platform rules, disclose AI assistance as required, and never claim a finding without reproducible evidence.

## Recovery routine

- Create and verify a recovery point before consequential changes.
- Periodically use **Verify**, not merely the presence of a folder.
- Keep a separate copy off the same failure domain where practical.
- Do not delete the last known-good point.
- After restoration, review actual record counts, security state, audit history and host pairing.
