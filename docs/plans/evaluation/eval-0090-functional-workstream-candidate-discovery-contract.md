# EVAL-0090 Functional: Workstream Candidate Discovery Contract

## Metadata

- ID: `eval-0090-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run: [RUN-20260915-100](../run/run-20260915-100-workstream-candidate-discovery-contract.md)
- Attempt: `1`
- Feature: [FEAT-0090](../feature/feat-0090-workstream-candidate-discovery-contract.md)
- Spec: [SPEC-0090](../spec/spec-0090-workstream-candidate-discovery-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: none; synthetic normalization fixtures
- Evidence Coverage: `complete`
- Created: `2026-09-15`

## Scope

The uncommitted pure-contract implementation and
`tests/test_workstream_candidate_contract.py`, using only synthetic metadata
and source-reference facts in the existing Python 3.9 virtual environment.

## Checks And Evidence

- `python -B -m unittest discover -s tests -v` through the existing virtual
  environment passed `584/584`, including all 33 new candidate tests.
- A 26-Session fixture spans three source keys and separate workspaces without
  a selected Session, existing organization, or the Focus 24-Episode bound.
  The same native Session ID under two sources remains two distinct members.
- Two independent evidence pairs can share one Session with separate reasons.
  A shared anchor does not merge candidates, admit unsupported members, or
  enumerate an unsupplied pair. Every retained member supports both anchors.
- Negative controls cover one duplicated Session, one repeated/aliased anchor,
  disjoint single-anchor references, weak metadata/organization signals,
  failed or unconfirmed reads, containers, disabled/unresolved/ambiguous
  artifacts, ineligible Sessions, and malformed facts.
- Determinism checks cover duplicate/reversed pairs, twelve shuffled input
  permutations, source-scoped keys, source loss/restoration, conflicting facts,
  renamed labels/local IDs, added members, and unrelated Session metadata.
- Time checks cover equivalent offsets, known latest observations, invalid or
  overflowing timestamps, unknown times, ignored import/Session-end times,
  bounded latest ties, and full bounds/counts beyond evidence samples.
- Bound and privacy checks cover capped input consumption, explicit output
  membership overflow, bounded overlap, unknown/partial coverage, attributed
  labels/fallback, fixed diagnostics, serialization, unchanged caller inputs,
  and guarded new-module import/normalization with no application I/O.
- Existing Session inventory/detail/pin/sync/reference, workflow
  Focus/assertion/correction, Workstream/Thread, Local Context, Atlassian,
  Search, Schema, and Task Runner tests remained green.

## Execution Notes

- `uv run --offline` could not initialize the sandbox-restricted shared uv
  cache. Verification used the already installed `.venv/bin/python` without
  dependency installation or network access.
- The first full run exposed only the stale semantic-owner digest in the
  schema cleanup audit. After refreshing derived artifacts, the repeated
  suite passed. The existing Starlette `TemplateResponse` deprecation warning
  is unrelated and was not changed.

## Evidence Gaps

- None for SPEC-0090's pure normalization behavior.
- No real-source scan, database candidate producer, live server, browser,
  promotion, or usefulness result is claimed. Those are outside this Feature,
  not missing evidence for a user-visible change.

## Findings

- None remaining.

## Route

- Technical result: `pass` for the recorded synthetic normalization checks.
- Subsequent owner review returned RUN-20260915-100 to PRD-0017 planning and
  superseded FEAT-0091–0094. No automatic-reconstruction product acceptance or
  new execution follows from the retained test results.
