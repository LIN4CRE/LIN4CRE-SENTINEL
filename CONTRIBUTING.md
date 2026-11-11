# Contributing

Thank you for improving SENTINEL without weakening its evidence and permission boundaries.

## Development setup

Use Python 3.12+ and Node.js 20+. Install `requirements.txt` and `npm ci`, then run the checks below. Do not commit runtime databases, tokens, evidence, reports, earnings, recovery points or model weights.

```bash
python -m unittest discover -s tests -v
python -m compileall -q backend host_companion windows
npm run build
```

For UI changes, also run `tests/browser_qa.py` against a local server using Playwright Chromium. Test desktop and 390 px mobile layouts and check browser console errors.

## Required invariants

- No fabricated programmes, versions, findings, health, updates, submissions, installations, restoration or earnings.
- No cash-free programme in the ranked research queue.
- No external testing or report submission without explicit human approval and exact scope.
- No arbitrary model-provided shell command, path, target or argument.
- No caller-header role elevation, unsigned host mutation or replayed signed operation.
- No automatic major/destructive update, unexpected paid dependency or silent uninstall.
- Backup and verify before consequential modification. Report partial/failed states accurately.
- Never automatically delete the last known-good recovery point.
- Preserve append-only audit history and fail-closed restored approvals.
- Keep monitoring read-only.

## Tests

Use temporary directories and explicit fixtures. Do not insert demonstration business records into the real database. Failure-path tests are required for new mutation paths: denied permission, altered plan, execution failure, verification failure and rollback where supported.

Windows-specific claims require actual target-OS evidence. Compilation on Linux is not proof that Windows installation, elevation, Docker, Ollama or rollback works.

## Pull requests

Describe user impact, exact security boundary changes, tests and unverified target-platform behaviour. Include before/after screenshots for UI changes. Small, focused changes are preferred. Reviewers should treat new dependencies, network calls, host permissions and recovery-format changes as security-sensitive.
