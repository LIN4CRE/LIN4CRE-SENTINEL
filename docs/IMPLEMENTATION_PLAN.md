# SENTINEL implementation plan v0.1

**Research and upstream checks:** 11 November 2026  
**Selected policy:** hybrid AI · cash-paying programmes only · human approval  
**Initial software spend:** £0

## 1. Delivery position

Milestone one implements the smallest useful operation: a source-of-truth programme register, policy gates, opportunity ranking, human test approvals, evidence-backed reporting, payment accounting, backup/export and a complete audit history. It deliberately does not begin with an autonomous testing stack.

No income or technical finding is implied by the software. No programme connector claims live data it has not fetched and verified.

## 2. Verified technology decisions

| Technology | Decision | Reason / constraint |
|---|---|---|
| OpenCode | Retain and audit existing installation | Active upstream is `anomalyco/opencode`; do not use archived `opencode-ai/opencode` instructions. |
| Ollama | Default inference provider | Explicit localhost-only connection test and installed-model discovery. Capability must be measured, not assumed. |
| PentAGI | Defer; isolation and EULA review required | Upstream provides multi-agent testing and broad tooling. It is unnecessary for milestone one and expands the host/network attack surface. |
| CyberGym | Defer; local benchmark subset only | Upstream documents ~240GB benchmark data and ~10TB full server data. Do not download either during initial setup. Keep services private. |
| Docker | Local core deployment only | Non-root, loopback binding, read-only root FS, dropped capabilities and no Docker socket. |
| SQLite | Local source of truth | WAL, foreign keys, online backups and immutable audit triggers. |
| Burp Suite Community | Optional later manual investigation tool | Install only after audit; no licence or version assumption is embedded. |
| External models | Disabled | No fixed free-quota assumption; recheck model IDs, privacy terms, limits and cost before any connector is enabled. |

## 3. Phases

### Phase 0 — Read-only audit (supplied, requires user execution)

- Windows, PowerShell, CPU/RAM/GPU and C:/D:/E: capacity.
- Docker, Compose, containers, images, volumes and storage.
- WSL distributions.
- Ollama version, installed/running models.
- OpenCode location/version and config-path existence (not secret contents).
- Python, Git, Node and npm versions.
- Existing Git worktrees and uncommitted-change state.

The script writes only the requested JSON report. It does not pull images, download models, restart Docker or edit repositories.

### Phase 1 — Backup and local core (implemented)

- Verified backup script with per-file SHA-256 verification.
- Backup-guarded D:/E: folder initialiser that rechecks hashes and refuses to proceed without a valid manifest.
- SQLite schema, settings and audit trail.
- Dashboard with truthful zero/empty states.
- Local backup and full JSON export.

### Phase 2 — Opportunity intelligence (implemented foundation)

- Real manual/JSON programme records.
- Cash, scope, policy, AI-use and payout-process gates.
- Source URLs and researcher source-check date required.
- Conservative ranking using six weighted factors.
- Expected-return-per-hour heuristic shown only with all researcher estimates.
- Rejected/review-required programmes cannot rise into the eligible queue.

Next: authenticated, terms-compliant platform connectors only after their current APIs and programme policies are reviewed. All fetched records must retain canonical URLs and retrieval timestamps.

### Phase 3 — Controlled research records (implemented foundation)

- Approval must exactly match recorded eligible assets.
- Methods, request ceiling and expiry are part of the approval envelope.
- Findings require an active approval covering the exact asset.
- Summary, reproduction, impact and evidence are required before validation.
- Human validation locks evidence fields.

Next: AI agents may summarise user-provided policy/evidence locally, but cannot create scope, probabilities or validation claims. Ollama output must be labelled and reviewed.

### Phase 4 — Reporting and earnings (implemented)

- Reports can be generated only from validated findings.
- Markdown contains actual finding fields and AI-use disclosure.
- No autonomous submission capability.
- Submitted status requires user confirmation.
- Award/payment records require accepted/resolved external status.
- Paid records require an actual payment date.
- Multi-currency totals remain separate.

### Phase 5 — Testing engine (not enabled)

Before PentAGI or any HTTP research executor:

1. Review EULA, source revision, dependencies and image provenance.
2. Threat-model Docker access. Do not mount the host Docker socket into an agent.
3. Use a dedicated isolated network and an egress proxy with exact scope allowlists.
4. Enforce rate limits outside the model/agent, not by prompt alone.
5. Require a valid approval scope hash at execution time.
6. Block destructive actions, credential access, data extraction, pivoting and automatic submission.
7. Wire the global kill switch to actual task/container termination.
8. Test against user-owned lab assets before any live programme.
9. Obtain programme-specific permission for the proposed method.

### Phase 6 — CyberGym evaluation (not downloaded)

- Start only with the official 10-task subset after explicit storage approval.
- Bind the server privately per current upstream instructions.
- Keep the benchmark server and agent network off the public internet.
- Record model, prompt, dataset revision, cost and verified result.
- Never translate benchmark success into a claim of live-target competence.

## 4. Scoring model

| Factor | Weight |
|---|---:|
| Realistic bounty | 25% |
| Researcher-estimated probability of a valid bug | 25% |
| Number of eligible assets | 15% |
| Testing permission / automation allowance | 15% |
| Competition and duplicate risk | 10% |
| Estimated investigation time | 10% |

Estimated return/hour = realistic reward × valid-bug probability × (1 − competition risk) ÷ estimated hours.

This is a ranking heuristic, not a statistical forecast. It does not include every programme-specific variable and is never added to earnings.

## 5. Next implementation gate

The next code change should be driven by the imported real PC audit. Produce a machine-specific dependency/version/conflict plan and a verified restore test before adding PentAGI, CyberGym, external AI or platform API credentials.
