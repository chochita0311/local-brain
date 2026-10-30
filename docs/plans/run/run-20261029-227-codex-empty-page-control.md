# RUN-227: Codex Empty Page Control

## Metadata

- ID: `run-20261029-227`
- Status: `passed`
- Feature: [FEAT-0015](../feature/feat-0015-session-subsession-source-contract.md)
- Parent PRD: [PRD-0002](../prd/prd-0002-session-browsing-and-subsession-organization.md)
- Active Spec: [SPEC-0015 R2](../spec/spec-0015-r2-codex-empty-page-control.md)
- Attempt: `1` source-only complete; `2` live application complete; `3` compatibility audit complete; `4` closeout reviews and verification passed; `5` older app stopped and web restoration verified
- Execution Profile: `fullstack-product`
- Surface Lanes: data normalization → existing Session presentation verification → docs
- Required Evaluators: contract, functional, design, interaction
- Created: `2026-10-29`

## Initial Goal And Authorization

Correct the confirmed leading empty-page control being treated as an authored
question and Session title. The owner's initial request authorized this bounded
correction under the existing generated-context contract. Recognition is limited
to the observed null-page envelope; unknown payloads and literal examples remain
visible. That initial correction required no new feature or publication; later
runtime and publication authority is recorded in attempts 2 and 4.

## Execution Contract

Implement SPEC-0015 R2 in the Codex parser, version its Session projection and
verify ordinary Sync repair for unchanged files. Existing presentation consumers
must show the real first question and normalized counts without template hiding.
Preserve original native files, Usage snapshots and curated Session identity.

## Evidence Plan

- Reproduce the exact control with synthetic legacy, response and mixed logs.
- Test rejection/literal boundaries and preservation of adjacent authored input.
- Import with the previous parser contract, upgrade unchanged files in both
  Codex sources, then verify stable identity, pins, Usage and idempotence.
- Run parser/Sync/detail checks, the repository regression suite, owner/generated
  checks, privacy and whitespace validation.
- Inspect synthetic Sessions inventory/detail and back navigation in a browser.
- In attempt 1, real source verification is read-only and live synchronization
  is excluded. Attempt 2 adds authorized normal web Sync; native distribution
  remains outside the Run's evidence and authority.

## Diagnosis And Producer Evidence

Shared screenshots and a subsequently inspected native desktop sample show the
same standalone empty-page envelope before the real prompt. This is generated
context leaking into the title/conversation, not demonstrated encoding damage.
The sample identifies its originator as Codex Desktop while its internal source
field is `vscode`; that source field does not establish which visible app was
used. The observed Desktop version, `0.165.0-alpha.1.2`, can produce this form,
but neither the reason for its internal source classification, its exclusive
producer/version range nor the exact UI trigger was established.

Earlier inspected personal/company logs and fixtures lacked this standalone
shape. Their passing results therefore did not exercise it; they do not prove
the owner used only a CLI. Initial connector authentication and attachment-pixel
access gaps were resolved by login and owner-provided local images/native input.
Private original locators, identities and screenshot content stay outside Git.
The separate management-navigation report was not investigated or resolved by
this parser correction; its cause remains unestablished here.

## Outcome

The following records the completed source-only first attempt.

- [Fix](../fix/fix-0015-codex-empty-page-control.md): complete; the recognized
  null-page control no longer becomes an authored message or title.
- [Evaluation](../evaluation/eval-0015-r2-codex-empty-page-control.md): contract
  and functional PASS; design/interaction PASS WITH SUGGESTIONS for a pre-existing
  narrow-screen long-literal-title limitation, recorded in the Sessions backlog.
- Verification: 40 parser tests, 25 Sync tests and 1,425 repository tests pass;
  owner/generated/privacy/catalog/whitespace checks are current. Synthetic
  inventory/detail/parent/back navigation was inspected at 1440, 920 and 320px.
- Actual native input was reparsed read-only and returned one authored question.
  Live user data, installed app and native sources were not changed.
- The source-only correction takes effect after running this code and completing
  ordinary Session Sync. No additional full-force scan or Usage repricing is needed.
- No common harness/design rule promotion is proposed by this product defect.
- Human review: review the completed correction and its explicit evidence limits;
  native distribution and live synchronization remain separate operations.

## Attempt 2: Apply To The Existing Local Web Server

- Status: `passed`.
- Authorization: the owner reported that the existing local Session detail still
  displayed the control and requested the visible correction. This follow-up
  includes ordinary Session Sync against that existing web runtime; a restart
  is needed only if its process still holds the old parser.
- Preflight: the page still displays the control and its source-file projection
  is v11. The current web process starts after the source correction, so request
  ordinary Sync first rather than restarting an already refreshed process.
- Verify the retained Session ID, v12 projection, one-question count, real title
  and first displayed input. Compare native source and existing Usage/curation
  before and after where the source remains unchanged.
- No native app replacement, unrelated source registration, new parser behavior,
  commit or publication is included. Keep private runtime IDs and content out of Git.

### Observed Result

- The existing web process already held the corrected code; no additional
  restart was necessary. Its persisted Session projection still used v11.
- Detail GET reads the stored normalized projection; it does not reparse JSONL
  on every visit. The version change is acted on by Sync, so saving source code
  alone did not refresh the visible title. Automatic Sync depends on its enabled
  state and configured interval; the follow-up explicitly ran normal Sync.
- Normal Session Sync completed across the registered sources without failed
  files. The selected Session retained its ID and now records v12, one authored
  question and the real title/first input.
- The actual detail HTTP response is 200 and matches the repaired database title
  and question count. The leading control is absent from both title and first input.
- Before/after fingerprints match for that unchanged native file and its
  existing Usage rows. Actual pin/link snapshots are empty before and after;
  preservation of populated curation is established by the synthetic upgrade
  fixture, not this live sample. Private locators and fingerprints stay outside Git.
- The earlier synthetic browser and regression evidence remains applicable;
  this follow-up adds actual web/database application, not native-app delivery
  or a claim about every historical source/client form.

## Attempt 3: Provider Dispatch And Parsing Compatibility

- Status: `passed`; owner-requested explanation and regression audit.
- Verify provider kind, stable source identity and user-editable labels; cover
  arbitrary roots, names and multiple Codex profiles with current schema v2.
- Compare pre-change and corrected parser outputs on immutable local snapshots
  without modifying native sources or the running database. Keep raw snapshots
  and private corpus inventory outside Git; remove task scratch at exit.
- Require complete equality for unaffected inputs; separately classify intended
  empty-page removals/title changes and any unexpected differences.
- Report exact recognition boundaries and uncertainty. A passing suite or
  bounded corpus comparison does not prove every possible future input.

### Compatibility Result

- Production adapter selection uses `registration.provider_kind`; fixture-folder
  keys and user labels are not parser types. A current-schema integration test
  covers three arbitrary named/rooted Codex profiles and a Claude source labeled
  Codex, then renames every profile. Identities, events and Usage remain stable.
- The full suite now passes **1,426 tests**, including 26 Session Sync tests.
- A read-only old/new parser comparison uses immutable byte snapshots and the
  same current dependencies/original-home tier for both implementations. Outputs
  match for unaffected inputs; the only observed difference is the intended
  control-message removal/title repair. No Usage or retained-event changes and
  no parser errors or unexpected differences were found. Private corpus counts
  and source fingerprints remain in ignored evidence.
- Recognition remains content based: an intentionally authored, standalone
  user block exactly equal to the recognized null-page envelope is also filtered.
  Framed/fenced/embedded or assistant examples and unknown payloads remain literal.
- The initial visible-application delay came from retaining the old normalized
  database projection until Sync. Source-only checks were reported before actual
  runtime application was completed; attempt 2 supplied that missing evidence.

### Existing Text-Heuristic Boundary

The owner's final parsing question covers existing rules as well as the new
envelope. Structural record/role metadata selects parsing routes, including
Claude's `isMeta` exclusion. Existing Codex generated-context recognition,
question-reply decoding, counterpart matching and reference extraction also use
message text, with different effects. Their current boundaries belong to the
[Session normalization owner](../../policies/project/data-model/workspace-and-session-activity.md#conversation-normalization-and-empty-sources).

A fresh synthetic check confirms that an authored standalone
`environment_context` block is filtered in Codex but retained in Claude, while
an explanatory prefix preserves it in both. Another check confirms that a valid
maintenance header at the start of a user message classifies both providers as
maintenance/metadata-only even when followed by a request to explain that format.
The classifier examines any normalized user message, not only the first overall
message. An unknown Run ID loses its FK link but keeps that Session policy, as
documented by the [header owner](../../policies/project/data-model/maintenance-execution.md#maintenance_runs).

These are pre-existing content-versus-intent limitations, not additional fixes
in this Run. Equal old/new outputs establish absence of observed introduced
differences in the compared corpus; they cannot establish that shared existing
heuristics correctly classify every authored input. Broader provenance-based
recognition and the separate CRLF variants remain deferred in the Sessions backlog.

## Attempt 4: Session Closeout

- Status: reviews and verification `passed`; repository publication is authorized
  after these checks, with the concrete commit/push outcome reported in the
  execution receipt.
- Authorization: the owner requests consolidation of this session in existing
  owners, independent docs-structuring/docs-shaping reviews, relevant code review
  and verification, owned temporary-artifact cleanup, and then commit/push of
  this session's repository changes. This supersedes the earlier attempts'
  publication exclusions without authorizing native distribution or external
  disclosure of private source evidence.
- Scope: preserve the bounded parser correction, completed live-web application,
  provider-routing evidence and compatibility limits. Reconcile the final
  text-heuristic discussion with current owners and distinguish completed work
  from deferred parsing/presentation/native-distribution follow-ups.
- Closeout verification and review results are recorded in the existing
  [evaluation](../evaluation/eval-0015-r2-codex-empty-page-control.md); no separate
  session log or repository-wide document restructuring is required.
- Remaining work: broader content/provenance safeguards, CRLF variants and narrow
  literal-title containment stay in the Sessions backlog; non-null page states
  need native evidence. The separate navigation report and installed-native-app
  delivery were not resolved by this correction.

## Attempt 5: Recurrent Projection With An Older App

- Status: runtime recovery `passed`; the older build must stay closed until it
  is rebuilt/restarted with compatible parser code.
- The owner reports the same visible control again after closeout. Read-only
  inspection confirms the selected projection has returned to v11, with the
  control title and two questions. Current source/editable imports remain v12;
  direct web requests expose the stored old projection.
- A running packaged native backend and development web backend open the same
  database. Read-only extraction of the packaged parser's embedded code confirms
  v11; the frozen app predates the source correction and lacks the new recognizer.
  The exact process responsible for the historical overwrite was not logged.
- An isolated synthetic round trip reproduces the mechanism: v12 produces the
  authored title/one question, a sequential v11 writer restores the control/two
  questions, and v12 repairs it again. Native bytes, Session identity and Usage
  stay unchanged. This does not require concurrent writes; the existing local
  writer lock is not a parser-version compatibility gate.
- The earlier web/source/test evidence was valid for its observed runtime, but
  closeout did not verify continued correctness with an older packaged app also
  collecting into that store. Native delivery was excluded, so source/web
  completion did not establish consistent parser versions for every writer
  sharing the store.
- The owner explicitly approves quitting the older native app while retaining
  the web service. Normal app quit and backend exit are confirmed; no native
  rebuild/replacement or broader parser change is performed.
- The selected Session is repaired through ordinary web Sync: v12, authored
  title/first input, one question and HTTP 200. Native source and existing
  Usage/pin/link snapshots match before/after. One full Sync attempt fails while
  the web process is replaced; the retry on the current web backend completes
  across all registered sources with zero failed files. Selected HTML/DB title,
  first authored input and count agree, and tracked Codex files no longer retain
  a v11 projection. No developer-triggered web restart was needed.
- Current mixed-version operating guidance belongs to the
  [Developer Guide](../../policies/project/developer-guide.md#setup-and-run).
  Keep the old build closed, or rebuild/restart it before resuming collection
  alongside the updated web backend. Earlier standalone-literal/CRLF/non-null/
  narrow-title limits remain separate.

Subsequent numeric revision admission, ingestion-layer separation and app rebuild
were completed under [REFACTOR-0002](../refactoring/refactor-0002-ingestion-layers-and-session-revisions.md).
Its [merge check](../refactoring/logs/2026-10-30_refactor-0002_final-merge-check.md)
owns the later DDL correction and source/package/runtime proof. Earlier exclusions
and recovery observations above retain their original attempt scope.
