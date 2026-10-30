# EVAL-0015 R2: Codex Empty Page Control

## Metadata

- ID: `eval-0015-r2-codex-empty-page-control`
- Status: `complete`
- Result: `PASS WITH SUGGESTIONS`
- Evidence Coverage: `complete` for the bounded source/parser and existing-browser checks below
- Run: [RUN-227](../run/run-20261029-227-codex-empty-page-control.md)
- Attempts: `1` initial source evaluation; `2` actual web application; `3` compatibility audit; `4` closeout reviews and verification passed; `5` older app stopped and web restoration verified
- Feature: [FEAT-0015](../feature/feat-0015-session-subsession-source-contract.md)
- Spec: [SPEC-0015 R2](../spec/spec-0015-r2-codex-empty-page-control.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: data normalization, existing Session presentation verification, docs
- Evaluators: contract, functional, design, interaction; sequential primary-agent checks
- Created: `2026-10-29`

## Contract And Functional Result: PASS

Three parser regressions cover the observed leading/repeated control across
legacy, response and combined representations, mixed authored content blocks,
JSON whitespace, control-only input, duplicate keys and unknown/malformed shapes.
They preserve quoted/fenced/embedded text, assistant examples and an authored
question-reply answer containing the same envelope. Before the fix, four positive
subcases failed on control-derived titles; all 40 parser tests pass afterward.

An unchanged-source upgrade fixture seeds the old v11 projection for both Codex
profiles. Ordinary Sync repairs title, one-question count, normalized events and
search, preserves Session/source identities, pins, Workstream links and exact
Usage rows, and leaves Claude data untouched. A control-only normalized stub is
retired under existing rules without changing native bytes or stat metadata.
Repeated Sync imports nothing and preserves the repaired events and Usage.
All 25 Session Sync tests pass, including the strengthened link-preservation
assertions added after the full-suite run.

The full repository suite passes **1,425 tests**, with no failures, errors or
skips. The first sandboxed attempt could not bind the loopback HTTP fixture;
the rerun with that restriction removed completed successfully. This was an
environment limitation, not a suppressed product failure.

A separate read-only native-sample parse returns a real title, one authored
question, no retained empty-page control and zero skipped lines. It does not
mutate the running app or establish live database repair.

## Design And Interaction Result: PASS WITH SUGGESTIONS

An isolated local server and task-owned headless Chrome used synthetic data.
At 1440, 920 and 320 CSS pixels, inventory entry leads to the real prompt title,
the detail begins with that prompt, the question count is one, and the completed
reply retains its existing role frame. Inventory return and valid child-to-parent
links remain usable. General corrected details have no outer-document overflow.
Wide and narrow screenshots were inspected; no template, CSS or client code changed.

Fenced XML examples remain visible. At 320px, a long literal XML title can still
overflow the document. Replacing only that heading with the pre-fix projected
control title in the same DOM also overflows. This is an author-performed DOM
comparison using the unchanged renderer, not an independent frozen-baseline app
test. The existing title-containment limitation is non-blocking for this parser
correction and is recorded in the [Sessions backlog](../project/backlog.md#p1---sessions-and-retrieval).

## Ownership, Generated Outputs And Limits

- The canonical Session normalization owner defines the exact recognition and
  preservation boundaries. Schema presentation and cleanup-audit changes are
  source/digest refreshes only; no schema, object decision or table shape changes.
- Source-of-truth, schema presentation, cleanup-audit, privacy, plan catalog and
  whitespace checks pass. Existing question-reply duplicate-key behavior remains
  covered after the shared strict JSON decoder is extracted.
- Initial evaluation is performed by the implementing primary agent; no independent
  reviewer, native app rebuild or installed-app replacement is claimed. Live Sync
  was excluded from attempt 1 and separately authorized and observed below.
- Non-null page states and the separately observed CRLF filtering issue are not
  included. They require their own evidence and bounded follow-up.
- Browser fixtures, logs, profiles and captures were task-owned temporary
  evidence; only this synthetic, self-contained receipt is retained in Git.

## Attempt 2: Actual Local Web Application — PASS

The owner's follow-up reported that the current web detail still displayed the
control. Read-only preflight found a v11 persisted projection while the running
web process had started after the source correction. An ordinary Session Sync
was therefore sufficient; the existing process did not need another restart.

The Sync completed without failed files. The selected Session now records the
v12 parser contract, a real prompt title and one authored question. Its actual
HTTP detail response returns 200, matches the database title/count and begins
with the authored input. Native-file size, mtime and content fingerprint and
existing Usage-row fingerprints match before/after. Actual pin/link snapshots
are empty before and after; preservation of populated curation is verified by
the synthetic upgrade fixture. These checks concern the selected unchanged
source and completed normal Sync, not all possible concurrent or historical
source changes.

No product code changed in this follow-up, so the prior regression evidence is
retained without replaying the entire suite. This is direct HTTP/database
evidence added to the earlier synthetic browser checks; no new actual-user
browser capture or native app rebuild is claimed. Private identities, process
details, content and fingerprints remain outside Git.

## Attempt 3: Provider Routing And Compatibility Audit — PASS

Production routes through `SESSION_SCAN_ADAPTERS.get(registration.provider_kind)`.
The earlier test's lowercase keys select its legacy fixture folders; its labels
are separate configuration fields. A new current-schema test registers three
Codex profiles with arbitrary IDs, roots and labels, including a Codex provider
labeled Claude, plus a Claude provider labeled Codex. All use their declared
adapter, and subsequent label changes neither merge identities nor alter Session,
Event or Usage rows. All 26 Sync tests and **1,426 full-suite tests** pass.

The committed pre-change parser and working-tree parser were run on the same
immutable local byte snapshots. Both use current shared dependencies and the
original home's resolved current service tier; this isolates the parser delta
and is not a replay of historical configuration or the entire historical app.
The inspected registered Codex JSONL corpus has no unexpected output difference.
Unchanged inputs produce equal complete ParsedSession values; the changed input
only loses the recognized control event and gains the real title. Retained Event
fields, Usage, metadata, skills and reference evidence remain equal. Both parsers
complete without errors. Compressed/archive/unavailable/future inputs are not
established by this comparison, and no live sources/settings/database were written.

The narrow content-based rule also filters a deliberately authored user message
if its whole text is indistinguishable from the recognized null-page envelope.
It does not distinguish intent for that exact standalone shape. Fences, quotation
framing, explanatory text, assistant examples and validated question-reply answers
remain preserved by the tested routes. A control-only source may become eligible
for existing empty-stub reconciliation; meaningful Usage/skill/event retention
and shared-owner safeguards remain the existing owner contract, not a new deletion
rule. These boundaries limit any claim of universal parsing compatibility.

## Existing Heuristics And Closeout Scope

The final discussion and synthetic checks also establish shared pre-existing
text-recognition limits, recorded in [RUN-227](../run/run-20261029-227-codex-empty-page-control.md#existing-text-heuristic-boundary).
Codex can filter an authored standalone environment wrapper; the shared
maintenance-header classifier can change the whole Session's classification and
indexing even when later text asks about that header. These are distinct from
evidence extraction, which does not itself remove conversation, and from
structural record/role filtering. Their current behavior is documented by the
normalization/header owners; broader safeguards and CRLF variants remain
follow-ups. No corresponding production rule was changed by this discussion.

The old/new comparison establishes observed compatibility for the parser delta,
not correctness of heuristics shared by both versions. It does not compare an
actual Claude corpus; Claude production code is unchanged and covered by the
repository suite. Native packaging, installed-app delivery and future producer
formats remain outside the verified scope. The owner subsequently authorized
independent document reviews, final verification and repository publication in
RUN-227 attempt 4.

## Attempt 4: Final Review And Verification — PASS

Two independent, read-only document reviewers applied docs-structuring and
docs-shaping to the consolidated Run/spec/evaluation/fix and relevant owners,
original authority, implementation and tests. Both found the existing layered
structure suitable; no document-wide rewrite or new session log was needed.

- Structuring findings corrected: preserve the original foundation trace while
  routing FEAT-0015 to the R2 spec/Run/evaluation/fix, and replace the Task Runner
  guide's narrower header predicate with a link to the canonical header owner.
- Shaping findings corrected: distinguish empty actual pin/link snapshots from
  synthetic populated-curation preservation, retain the observed Desktop version
  beside its producer uncertainty, and explicitly leave the separate navigation
  report uninvestigated/unresolved by this correction.
- The primary agent checked these findings against the session evidence and
  decisive code/tests. Existing parsed-empty owner/sibling/Usage safeguards were
  preserved; an optional cleanup of their pre-existing adjacent repetition was
  left alone. Stable entrances and unrelated documents were not restructured.

Final primary-agent code review covered the production delta, strict JSON
decoder reuse, per-block legacy/response call paths, Session-versus-Usage
freshness, provider dispatch and new parser/Sync assertions. It found no blocking
code issue within this bounded change; the two independent document reviews do
not make the original code/browser evaluations independent.

The complete suite was rerun using the configured `.venv` interpreter:
**1,426 tests passed, zero failures/errors/skips**. This is the environment
installed by uv; direct invocation avoids the sandbox's unavailable shared uv
cache. Loopback HTTP fixtures ran with the required local binding permission.
Parser/test content fingerprints still matched the checked inputs afterward.
Fresh synthetic checks also confirmed the existing environment-wrapper and
later-user-message maintenance-header behavior for both providers; no new
production rule or tracked fixture was introduced for that documentation check.

Data-model owner, schema-presentation, cleanup-audit, plan-catalog, relative-link,
privacy and whitespace checks passed. The generated schema/audit delta contains
only owner-source digests, with all 732 object decisions unchanged. These checks
do not replay original screenshots, native sources or the earlier live Sync;
their evidence and stated limits remain the prior attempts' observations.

Publication is limited to this session's reviewed repository changes. Private
source evidence and existing ignored receipts remain local; task-owned review
and test scratch is removed after its processes and publication checks finish.
Native build/replacement, WKWebView behavior and future producer forms remain
unverified. The final execution receipt supplies the concrete commit and verified
push result rather than implying distribution from source/test success.

## Attempt 5: Mixed-Runtime Recurrence — Recovery PASS

The reported recurrence is a persisted v11 projection while source code and
editable imports remain v12. A running native build sharing the database embeds
the old v11 parser. An isolated synthetic v12 → v11 → v12 scan sequence reproduces
the title/count reversal and repair while preserving source bytes, Session ID
and Usage. Archive inspection establishes the old build's capability; the exact
historical overwrite process is not independently logged.

The owner authorizes quitting that native app. Both app and backend exit while
the web remains available. The selected actual detail is repaired and responds
200 with the authored title, first user input and one question; its source and
Usage/pin/link snapshots remain equal. The first full Sync fails while the web
process is replaced; the retry completes across all registered sources with
zero failed files. Final actual HTML/DB title and first input agree, the count
is one, and tracked Codex files no longer retain a v11 projection. No production
code changes or new claim of native-build delivery is involved, so the existing
1,426-test source evidence is retained rather than represented as a new rerun.
At this attempt, the old build had to stay closed until updated; a compatibility
gate preventing backward replacement had not yet been added. The subsequent
[REFACTOR-0002 delivery](../refactoring/refactor-0002-ingestion-layers-and-session-revisions.md)
adds admission in updated runtimes and verifies a rebuilt app. Its execution
records own that later delivery; unmodified older copies still require replacement.
