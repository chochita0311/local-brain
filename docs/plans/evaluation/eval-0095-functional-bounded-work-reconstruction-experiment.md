# EVAL-0095 Functional: Bounded Work Reconstruction Experiment

## Metadata

- ID: `eval-0095-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run: [RUN-20260915-101](../run/run-20260915-101-bounded-work-reconstruction-experiment.md)
- Attempt: `2`
- Feature: [FEAT-0095](../feature/feat-0095-bounded-work-reconstruction-experiment.md)
- Spec: [SPEC-0095](../spec/spec-0095-bounded-work-reconstruction-experiment.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: extraction/scoring → local experiment
- Evidence Coverage: `partial`
- Created: `2026-09-15`
- Updated: `2026-09-16`

## Scope And Environment

Evaluated the standalone comparison after Contract review in the existing
macOS Python 3.9 virtual environment. Automated test inputs were synthetic and
task-owned. Attempt 2 additionally checked bounded read-only execution on the
owner-selected current database without exposing its contents or labels.
No UI changed, so server/browser/Design/Interaction evaluation is
not applicable. This report does not accept the whole Feature.

## Acceptance Evidence

| Feature point | Executed behavior |
| --- | --- |
| 1: matched arms | PASS on synthetic snapshots: metadata/text and no-organization variants share eligibility, source binding, and coverage; metadata entry rejects a text-bearing snapshot |
| 2: scoped extraction | PASS for authored explicit Korean/English goal clauses, contributing investigation/implementation/verification, mixed Sessions, conflicting actions/criteria, and unrecognized/negated abstention |
| 3: source attribution | PASS: exact offsets survive Markdown/newlines/decimal punctuation; roles, source kinds, observed wording/evidence, and inferred fields stay distinct; completion claims never close work |
| 4: honest comparison | PASS: full unfiltered output, missing goals, fragmentation, wrong/duplicate assignments, incompatible merges, unknown labels, zero denominators, changed snapshot hashes, and partial input are exercised |
| 5: replay | PASS: shuffled/unchanged input, unrelated append, multiple source/workspace identities, changed references, late evidence, removed sources, and exact correction reuse/inactivation |
| 6: bounded local operation | PASS on synthetic real schema and CLI: selected text/hash/time limits, ineligible/disabled body gates, read-only enforcement, database byte equality, no default database creation, private output, limits, failure cleanup, and cancellation/reaping |
| 7: no inflated viability | PASS: even a successful synthetic or undersized database-mode report leaves viability unverified; missing real evidence remains a Feature/Run block |

## Synthetic Measurements

- Two Sessions sharing ten artifacts: the unchanged metadata comparator emits
  `45` qualifying pairs; one explicitly shared outcome produces `1` text flow.
- A preauthored `48`-Session history contains `10` expected efforts, including
  one `30`-Session effort with three subordinate activity phases. The text arm
  recovers `10/10` goals with `10/10` assessed correction-free groups for that
  fixture. This is not a private accuracy estimate.
- Changing that history to three synthetic sources, four workspace identities,
  and nonrepeating document references preserves all text flows while the pair
  baseline has no shared pairs.
- Unrelated append retains `10/10` prior flow identities and `48/48` prior
  assignments with zero label changes. Thirty genuinely different explicit
  goals remain thirty flows rather than being forced into a display budget.
- A new statement cannot acquire an earlier exact correction. Removing its
  evidence or replacing it with equal-length different wording deactivates
  the target without changing the correction or labeling new work.

## Commands And Regression

Using `.venv/bin/python -B` without installation or network access:

```text
python -B -m unittest discover -s tests -p 'test_work_reconstruction*.py' -q
python -B -m unittest discover -s tests -q
```

Results: `61/61` focused and `645/645` total tests passed. Existing Session
inventory/ingestion/reference, Focus/assertion/correction, Workstream/Thread,
Local Context, Atlassian, Search, Schema, and Task Runner behavior remains green.
The known Starlette `TemplateResponse` deprecation warning is unchanged.

Build-time checks exposed a stale generated SQL-use audit and restricted `ps`
monitoring. Regenerated the audit and used task-worker self peak-RSS monitoring
without changing the approved cap or inspecting unrelated processes. A synthetic
URL fixture matched the email privacy rule; it now uses a localhost authority
and the scanner passes without an exception. No private content was involved.

## Gaps And Findings

- No remaining reproducible implementation defect in the executed synthetic
  scope. Test-owned directories, databases, reports, and processes were cleaned
  up; no task recovery artifact remains.
- An unassessed private execution check passed, but no independently prepared
  private answer key or blinded held-out quality assessment exists. Authored phrasings do not establish general
  language understanding; narrow exact-goal grouping can miss or fragment real
  paraphrases. No reported synthetic number may be used as a local quality claim.
- No model-free adequacy, real correction burden, full-corpus stability, production
  latency, Linux runtime, or legacy-cutover outcome is claimed.

## Route

Retain technical PASS with partial Feature evidence. RUN-20260915-101 and
FEAT-0095 stay `blocked` on independent assessment, not DB/path/time selection.
Prepare assessment without whole-sample manual organization. Once available,
run the bounded local comparison and reconcile all quality/safety requirements;
failure or insufficiency cannot be compensated by an approval inbox.

## Attempt 2 Current-Data Check

The owner selected current stored LocalBrain information through now. The
explicit preparer sampled its existing time range under the original caps;
no source rescan, keyword-driven selection, predictive answer key, or model
was used. Runtime returned `EXPERIMENT_RECORDED`, and local checks confirmed
`assessment=unassessed`, `private_quality=insufficient`, `viability=unverified`.
The temporary private manifest/report was then removed and cleanup confirmed.
No corpus contents, actual sample counts, private labels, or source timestamps
were emitted. This establishes that the bounded command runs against current
storage, not that it reconstructs the owner's work accurately.
