# EVAL-0159: Terminal Defaults And Quick Launch

- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `complete`
- Acceptance scope: this approved saved-default/quick-launch increment only;
  whole-feature coverage remains partial in Eval0158.
- Feature: [FEAT-0166](../feature/feat-0166-web-terminal-work-area.md)
- Spec: [SPEC-0166](../spec/spec-0166-web-terminal-work-area.md)
- Run: [RUN-243](../run/run-20261111-243-terminal-defaults-and-quick-launch.md)
- Parent PRD: [PRD-0028](../prd/prd-0028-web-terminal-work-area.md)
- Profile: `fullstack-product`; attempt1.

This evaluation covers the approved saved-default/quick-launch revision. It does
not replace Eval0158 or its partial whole-feature coverage. Physical macOS IME,
actual hidden-document and representative existing-corpus performance gaps remain
at that owner; Safari, long-soak and broad assistive-tool evidence remain unverified.

## Observed Results

| Evaluator | Result and boundary |
| --- | --- |
| Contract | PASS: private feature-owned TOML section shares the common lock/revision/atomic writer, preserves unrelated/unknown fields and rejects stale writes. Read/save/launch validation never constructs a manager. Invalid/deleted paths remain editable and cannot silently select another folder. Native/non-feature admission remains excluded. |
| Functional | PASS: immediate New uses a validated settings snapshot; next New uses changed defaults, existing PTY identity survives, and Split inherits its clicked pane. Lost successful New/Split replies retain explicit paths/key and recover the same PID after settings or source cwd changes. |
| Design | PASS: existing Settings form family, two inputs, folder picker and Save; same 720×560 desktop dialog. Actual320px emulation has304px dialog and270px form without horizontal overflow; fields and actions remain reachable. Running actions wrap within the narrow dialog. No new cards, token system or explanatory rail. |
| Interaction | PASS: settings loading/failure/reload/stale/invalid/save paths, blocked writes during a delayed common read, subsequent General save, immediate create/split, all-background recovery, and explicit background/open/end. Background/open retained IDs/PIDs; End removed only its selected tab and preserved another tab. |

## Verification

- Full Python suite: **1,633 tests, OK (22 skipped)**. The22 real-PTY methods
  require an explicitly prepared isolated engine. Three new relevant methods
  ran separately against real macOS PTYs: future-only defaults, invalid defaults
  without manager start, and retry after defaults change/original folder removal.
  All three pass. Prior19 methods retain their separate Eval0158 observations.
- New settings module:12 tests pass; common-settings focused31 and UI contracts45
  pass. After the final JS-only split fingerprint repair, UI contracts45 and JS
  syntax checks pass again; actual lost-reply split/browser witnesses were renewed.
- xterm asset rebuild/parser check, repository privacy and catalog checks pass.
  Final offline web wheel:18 relevant files byte-match source, including feature
  settings, shared Settings, templates, guides and xterm assets. Actual PyInstaller
  collection excludes Terminal while retaining shared Settings (125 data files,
  234 admitted modules); no native binary build was performed.
- All process/browser tests used isolated synthetic HOME/data/cache and public
  copied engine dependencies. User service, settings and running jobs were not
  installed, restarted, stopped or edited by this Run. The original synthetic
  PTY also survived the QA backend restart during repairs.

## Independent Challenge And Adjudication

Primary owns architecture, persistence, integration and acceptance. The named
`review_challenger` received no history for the fresh pass and raw full frozen
baseline/candidate bundles, constraints, callers/tests and unchanged governance.
Its role was read-only and non-executing; it performed no builds/tests/runtime
mutation or publication. Configured binding was the named review role; exact
internal model identity and separate OS isolation are unavailable. Runtime
witnesses below are primary-produced evidence, not independent executions.

| Claim | Status / action | Discriminating evidence |
| --- | --- | --- |
| Trimming can select a different existing cwd sibling | Supported / fixed | Browser reproduced the substitution, then exact selected/saved/launched trailing-space path matched after repair. Shell paths also remain exact. |
| Delayed common read can overwrite the newly saved revision | Supported / fixed | Held response reproduced next General save reverting. Terminal controls now block that write; full common values/revision are returned together. Renewed witness saved Terminal then UTC successfully. |
| Re-resolving defaults changes an accepted create retry | Supported / fixed | Identical key-only request initially produced409 after a defaults change. UI now captures validated explicit paths once; lost successful reply + settings change recovered identical key/body/PID and no duplicate; next New used changed defaults. Runtime/core remain pass-through. |
| Mutable source cwd replaces a pending split identity | Supported / fixed | Repair confirmation found this remaining branch. Stable pane ID/direction now identifies intent. A real source OSC7 cwd change after a dropped successful split reply retained original body/key and same split PID; terminal count included only the intended source and split. |

Baseline1840 manifest: `bf26acb46c450f8b5449421e58adb0bf2e473af29aa251e86d6baf57a3561254`.
Initial1844 candidate: `4962110d695794276aad63881d7ff138087db2b765ea5cfc9f6d0c42e0e7100e`.
Second candidate: `3eff2072455afe6852541842aca9591d89d399d08144a21ef8d174b7edc77869`.
Final code candidate: `ae9a7ebc4cdcf9d28a8f134340a76f64e209b7a9e80bb8b60d939d79a296d9e4`.
Complete path/content inventories validated; the last delta is one JS line.
One fresh pass and two repair confirmations ended with no remaining objection
within the changed paths. This scoped challenge is not whole-feature acceptance.
Private stage evidence retains immutable bundles, raw review return, witnesses,
logs and screenshot observations; durable behavior remains in the owning policies.
