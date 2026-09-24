# EVAL-0100: Source Claim Extraction And Binding Trial — Contract

## Metadata

- ID: `eval-0100-contract`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-112](../run/run-20260923-112-source-claim-extraction-and-binding-trial.md)
- Attempt: `1`
- Feature: [FEAT-0100](../feature/feat-0100-source-claim-extraction-and-binding-trial.md)
- Spec: [SPEC-0100](../spec/spec-0100-source-claim-extraction-and-binding-trial.md)
- Execution Profile: `foundation-contract`
- Surface Lanes: `data`, `infra`
- Created: `2026-09-23`

## Scope And Evidence

Primary-agent review of the extended `work_state.py`, `work_claims.py`,
`work_claim_assessment.py`, `work_claim_trial.py`, synthetic fixtures/tests and
`evaluate-source-claims.py`, against the approved Spec and
[implemented contract](../../policies/project/source-claims-and-work-state.md).
The candidate is the frozen uncommitted worktree identified in RUN-112, not a
claimed commit or production consumer. All source inputs are synthetic.

| Contract surface | Evidence and result |
| --- | --- |
| Existing v1 behavior | PASS: original tests retained; prior source hash verified before in-memory comparison of eighteen scenarios and ninety permutations, all exactly equal |
| Model-aware provenance | PASS: separate v2 producer-bound claims/edges, stable source-native anchors, literal source authority distinct from inferred effects; forged lineage/support rejected |
| Atomic extraction | PASS: exact Unicode quotes and explicit occurrence indices, bounded fields, no fuzzy repair, uncovered text unresolved, contradictory no-work rejected |
| Target and lifecycle scope | PASS: supported same-step/occurrence premises required; contribution is not identity, child fulfillment cannot close an effort, derived support participates in cutoff checks |
| Separate evaluation paths | PASS: extraction and end-to-end receive no reference answers; conditioned claims/roster are explicitly fixture-supplied, never extraction or discovery evidence; cache modes/dependencies differ |
| Frozen experiment | PASS: source/reference/prompts/implementation/runtime fingerprints, all-denominator gates, all-unresolved baseline, original compatibility and conditional holdout preserved |
| Persistence and replay | PASS: owned local store, atomic checkpoint and call reservation, retained raw failures/skips, cumulative limits, clean missing-only resume, unclean/config/tamper/expiry refusal; actual 84-observation zero-generation replay |
| Admission | PASS: completed trial plus all gates and a report-bound primary review required before holdout; this failed candidate is withheld; no automatic private or product consumer |

Forty-two new model-free tests pass in both application and installed model
runtimes. All 28 supplied-reference controls pass; sixteen original legacy
compatibility checks remain unchanged. These controls establish scoring/projector
consistency given authored premises, not model extraction. Full application
regression runs 942 tests with zero failures and one existing optional graph skip.

## Stale Assumptions And Ownership

The CLI is fixed-suite only: no DB, private Session path, source ingest, model
installation, training, external service or organization write. Runtime reuses
the installed local model and existing evaluation-store contract. The source
policy, architecture, privacy rules, README and current planning owners describe
the new version/command and its lack of product admission. Older v1 and inference
APIs, original fixtures, previous reports and UI stay unchanged by this Run.

The generated schema ledger gained lexical code references from the new modules;
it was regenerated from unchanged decision/manifest sources, not a schema change.
All 649 object decisions remain 543 keep, zero change/remove and 106 defer.
No new permanent persistence, correction ledger or source identity service exists.

## Limits And Route

Route: `pass` for this contract. This does not certify the semantics of structurally
valid model statements or their bindings. The actual model rejects every extraction
prerequisite and passes only three conditioned cases; the separate
[Functional evaluation](eval-0100-functional-source-claim-extraction-and-binding-trial.md)
therefore FAILS and blocks the Feature. Fault paths have injected test evidence,
not a claim that a real crash, maximum-size input or budget exhaustion was induced.
No in-scope contract defect or required contract evidence gap remains. RUN-112
owns final repository checks and the post-run boundary; no automatic retry follows.
