# EVAL-0147: gcloud Drive Settings Connection

## Metadata

- ID: `eval-0147-gcloud`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`
- Feature: [FEAT-0147](../feature/feat-0147-drive-settings-connection.md)
- Active Spec: [SPEC-0147](../spec/spec-0147-drive-settings-connection.md)
- Run: [Run216](../run/run-20261028-216-drive-settings-connection.md)
- Attempt: 2
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Created: `2026-10-28`

## Contract And Evaluation

The owner explicitly approved `gcloud auth login --enable-gdrive-access --force` and full `https://www.googleapis.com/auth/drive` scope. This supersedes the app-owned Desktop Client/readonly+drive.file/Keychain prerequisite. Credentials and refresh stay with Google Cloud CLI; LocalBrain stores the selected account identity and keeps access tokens briefly in memory. Operations remain bounded to configured root/selection. Existing-login reuse and explicit browser login are separate actions. All background tokens pin the selected account; global SDK account/ADC are unchanged. No schedule silently starts login, no credential revocation or automatic legacy-vault migration is added.

Primary agent performs Orchestrator, Spec, Builder and evaluator roles sequentially. Same-author logical role checks are not independent certification. Contract PASS covers the revised producer/consumer boundary; functional PASS has partial coverage because real-provider/recipient evidence is separate. For Settings/guides, design and UX-heuristic checks PASS for the observed Settings/Docs surfaces in extend mode, under the existing constitution. Foundation producer checks pass before dependent consumer acceptance.

## Evidence

- `.venv/bin/python -m unittest discover -s tests -p 'test_google_drive*.py' -v`: 52 tests PASS, including 14 SDK auth tests. Synthetic executables/transport only; no real login or user-token retrieval.
- Full suite: 1310 tests, 1305 pass, 5 fail. These are unchanged pre-existing Learning/schema owner-table/audit inventory, schema-presentation count and value-registry count failures. Corresponding input fingerprints match the work-start baseline. No green full-suite claim.
- Browser: production GcloudAuth subprocess path with a synthetic SDK and synthetic Drive API. Cached tab opening issued no CLI commands. Existing-login reuse issued account listing and a pinned token command, no login. An explicit Google-login click issued the approved flags plus `--no-activate`, `--quiet`, `--user-output-enabled`; pending controls disabled and recovered. A different account produced an inline actionable warning without changing the binding. Five root publishers, whole-folder selection, upload (2 files including hidden), receive (1 file), independent default intervals and OFF state observed. No actual Google interaction.
- Chrome1440×1000 and actual320×800 viewports: existing Settings family retained; scope explanation, account field and auth buttons wrap within the dialog, no root horizontal overflow; last publisher/footer reachable. The actual guide link navigates to `/help/settings#heading-google-drive`; command and official SDK installation link are present. No new design/interaction rule candidate.
- Wheel: eleven required Drive modules/assets/guide match source; no keyring dependency, Client JSON or runtime/credential artifacts. Frozen macOS backend builds and serves authenticated Settings/status/guide/current JS; anonymous status returns401; shutdown exits0. With minimal GUI PATH it discovers the installed SDK. A second frozen launch invokes a synthetic SDK, checks pinned-account argv and clean child runtime, sanitizes a reauth failure and avoids Google calls.
- Installed SDK575.0.1 safely executes `version --format=json` through the source adapter. This is executable/runtime evidence, not Google login or Drive permission evidence.

## Limits And Route

Real Google login, consent, actual two-account My Drive/Shared Drive create/update/move/Trash/download and installed-recipient/full Tauri UI-host behavior remain unverified. Full scope does not grant folder sharing permissions. Client/project preparation is no longer a blocker for the approved SDK flow. This PASS covers the bounded authentication revision and its local/package consumers, not live provider/release or final human acceptance. No user content, account, publisher name or real destination was used in evidence.

Preserve prior evaluations as historical evidence of the superseded authentication design. Current state belongs to the [Drive contract](../../policies/project/google-drive-sync.md) and this revision. Final privacy/catalog/diff checks are recorded in the closing Run.
