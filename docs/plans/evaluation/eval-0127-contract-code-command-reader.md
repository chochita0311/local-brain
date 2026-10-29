# EVAL-0127: Code Command Reader Contract

## Metadata

- ID: `eval-0127-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-165](../run/run-20261017-165-code-command-reader.md)
- Attempt: 1
- Feature: [FEAT-0127](../feature/feat-0127-code-command-reader.md)
- Spec: [SPEC-0127](../spec/spec-0127-code-command-reader.md)
- Execution Profile: `fullstack-product`
- Surface Lane: backend/data, docs
- Evidence Coverage: `partial`
- Created: `2026-10-17`

## Scope And Inspected Contract

Source inspection of the current working tree against the approved scene policy:

- The reviewed CLI remains the producer. Version 1 keeps its normalized fields
  and hash calculation. Version 2 adds literal scenes, fixed refs, independent
  content hashes, manual authorship, selection reason and concept/depth/rubric.
  Worktree/index scenes require at least one matching content fingerprint. The
  importer generates the display diff from complete before/after file snapshots.
- Existing immutable packet_json, revision identity, attempts, transactions and
  visibility remain the persistence owners; no SQL migration is added here.
  Strict fields, sizes, dates, source membership and focused-line ranges precede
  writes. Structural admission does not prove author claims or official ownership.
- Home chooses one current visible scene from pre-day history. Earlier pending
  work is reconstructed as of the start of today, so finalizing it does not refill
  today's feed. Pending resume selects the oldest unresolved answer. Due reviews
  prioritize help-needed history; new material uses declared signal/date/ID.
- Depth uses two distinct earlier response dates at each available level, with
  completed self-assessment before today. Hinted/read/weaker assessments reset
  that level's sequence. Same-day feedback availability is derived conservatively
  for the same concept; it never rewrites stored help reports or proves mastery.
- Explicit question practice and saved-attempt URLs preserve their own identity.
  Browser drafts are tab-local and revision/question-specific. Native forms,
  bounded same-origin POSTs and user-entered recovery remain the write boundary.
  Rendering does not execute commands, fetch documents or invoke a model.

## Observed Actions

- Actual reviewed import inserted two private work scenes with six questions.
  Existing lessons and revisions remain. No artificial learner answer or
  self-assessment was created. The command scene preserves a work-note execution
  report with unknown historical platform version; the diff preserves fixed
  files and matched declared dependency/API version, without a deployment claim.
- Python AST parsing, four Jinja template parses and JavaScript syntax parsing
  completed. These establish syntax only.
- Value dictionaries and schema presentation were regenerated successfully.
  The schema build first identified a stale baseline digest left from the
  preceding learning schema change; the digest was reconciled to the actual DDL.
  No DDL or personal row was changed to repair that derived owner.
- The local app restarted successfully against the existing private database.

## Stale-Assumption Reconciliation

Producer/consumer inspection covered learning.py, CLI/routes, home/library/reader,
scoped assets, the label registry and derived dictionaries. Product, common
learning, scene/data-model policies, README and design owners now distinguish v1
compatibility, v2 scenes, one daily selection and current manual authoring from
later automatic discovery/generation. The previous one-new-plus-two-review policy
is historical. Planning navigation points to this active successor without
erasing FEAT-0125's missing functional evidence.

## Evidence Gaps And Route

This PASS covers contract inspection. No behavior tests were added or run.
SPEC-0127 requirements 1–7 still need runtime evidence for invalid/atomic intake,
v1 replay identity, timezone rollover, pending transitions, depth/reset/help
boundaries, explicit practice, duplicate/conflict recovery, drafts, visibility,
historical revisions and no-script behavior. Syntax and successful real intake
do not establish those paths. These gaps are **blocking for Feature/Run pass**.
Functional evaluation remains unexecuted; the Run stays active. Model correctness,
automatic freshness and delayed learning benefit are not established.

## Article Extension: Bounded Source Review — 2026-10-17

The optional v2 article lives in the existing immutable packet. Validation admits
only its declared fields, 2–5 unique section IDs, bounded text, resolving unique
references and a contiguous 1-based scene range of at most 24 lines. Range values
must have type int, excluding bool. Overall references include the scene's work
source and an official source; every section includes an official source and its
references are a subset of the article's. The common packet cap still applies.
Absent articles leave existing normalized payloads unchanged. These are inspected
predicates, not tested invalid-input or replay guarantees.

Shared safe Markdown derives article HTML; literal scene code supplies the preview.
Home and individual article routes use one component. Library routing and fixed
home/article read-return destinations were inspected. Existing explicit POST,
assisted-practice and no-GET-record semantics remain. New content revisions retain
older evidence and attempts while receiving their own revision-specific schedule.

Actual reviewed intake accepted two reconstructed private articles. Work evidence,
primary documentation and versioned source were reconciled before importing them;
historical uncertainty and invented scenarios remain labeled. Java/Go highlighting
uses the installed Pygments version through explicit aliases. Python/Jinja syntax,
generated dictionary build and initial render observations provide bounded evidence.
No tests or learner mutations were performed. Invalid intake, legacy replay,
save/retry/no-script and schedule behavior remain functional acceptance gaps; the
earlier contract PASS does not close them or establish user acceptance of this revision.

