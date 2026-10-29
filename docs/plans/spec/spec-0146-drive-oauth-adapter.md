# SPEC-0146: Drive OAuth Adapter

## Metadata

- ID: `spec-0146`
- Status: `approved`
- Run: [run-20261028-215](../run/run-20261028-215-drive-oauth-adapter.md)
- Attempt: 2
- Parent Feature: [feat-0146](../feature/feat-0146-drive-oauth-adapter.md)
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Surface: `backend`
- Execution Profile: `foundation-contract`
- Required Evaluators: contract, functional
- Created: `2026-10-28`
- Updated: `2026-10-28`

## Approved Revised Contract

The owner-approved gcloud change replaces the prior app-owned Desktop OAuth implementation. Google CLI supplies the full `drive` scope, credentials and refresh. LocalBrain discovers an installed executable from an explicit process override, PATH or known desktop installation locations; it never sources a shell profile. Status reads only cached/local readiness. An explicit existing-login connection or login action binds one account to a root; all token requests use that account, independent of gcloud's current active account. Full Google read/write scope is disclosed in Settings/Docs; app operations stay within selected roots.

Use structured subprocess arguments, no shell, bounded timeouts, sanitized errors, disabled credential logging and owned-process cancellation. Existing-login connection never opens a browser. The separate Google-login action runs `gcloud auth login --enable-gdrive-access --force`, with a pinned account when known, `--no-activate` and no ADC update; browser consent remains Google's. Never read/copy the credential DB or refresh tokens into app storage. Token cache is memory-only and invalidation never revokes SDK credentials. Validate Drive account identity before committing a connection. Existing source authority, checkpoints, copies, selections and schedules remain intact on failure or account mismatch.

Dependent frontend/guide acceptance, owned by [SPEC0147](spec-0147-drive-settings-connection.md) and [SPEC0150](spec-0150-drive-operation-guides.md), not additional producer surface: same Settings family and tab, optional account field (blank uses the existing bound/current/unambiguous gcloud account), existing-login connection and explicit Google-login actions, cached readiness and inline errors. No extra sharing consent or write probes. Fullstack profile contract→backend→frontend→docs, with contract/functional and rendered design/interaction checks. Installer guide must describe gcloud installation, exact approved login command and root permissions; provider-project creation is no longer required. Frozen GUI environment discovery must be verified independently of browser source execution.

## Acceptance Mapping

The auth producer owns the SDK/API tests below; browser and guide/package consumer checks are dependency evidence owned by SPEC0147/0150. Tests cover argv/environment isolation, token redaction and memory-only caching, explicit account pinning, SDK absence/reauth/network errors, timeout/shutdown, existing-login reuse and browser login completion, API account mismatch, cached status/no CLI calls, unchanged sync/scheduler behavior and native request boundary. Browser checks cover real controls at desktop/320px and error/retry transitions. Package checks prove removal of embedded Client/Keychain dependency and SDK availability in a frozen backend. Live user Google/Drive operations remain unverified until performed through an authorized real connection; no new project creation is required for the documented SDK path.

## Evidence Limits

Earlier Run210/211/214 and their Desktop Client evidence remain historical. Revised implementation uses new Runs215/216/217. Real Google account/root access and write permissions remain separate from synthetic/frozen checks. No product choice remains open for this revision.
