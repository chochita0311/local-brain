# Run235: Identifiable macOS Trial Build

## Metadata

- ID: `run-20261105-235`
- Status: `passed`
- Feature: [FEAT-0159](../feature/feat-0159-identifiable-macos-trial-build.md)
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Active Spec: [SPEC-0159](../spec/spec-0159-identifiable-macos-trial-build.md)
- Execution Profile: `infra-devtool`
- Required Evaluators: contract, functional
- Attempt: `1`
- Created: `2026-11-05`
- Updated: `2026-11-05`

## Final Evaluation

- Result: `PASS`
- Evidence Coverage: `complete` for the approved local Mac increment.
- [Integrated delivery evidence and limits](../evaluation/eval-0155-early-access-macos-delivery.md).
- Human review: pending real-user trial; no recipient/Windows/public signing pass.
- Earlier checkpoints below retain their observations; final integration resolved
  their pending source/browser/independent/frozen/native verification items.

## Execution Record

- Active Spec: [SPEC-0159](../spec/spec-0159-identifiable-macos-trial-build.md)
- Profile: `infra-devtool`; evaluators: Primary contract/functional and named fresh
  non-executing review_challenger for frozen cross-feature code candidate.

## Scope And Gates

Integrate Features155–158; preserve pre-existing dirty installation/planning changes.
App version remains 0.0.1 across manifests; source identity/time/fingerprint
identify the changed build. Full Python suite, privacy, independent omission review,
browser regression, code-sign/private-path verification, frozen routes and native
WebKit startup are separate evidence scopes. Actual recipient and Windows tests
cannot be inferred. No real personal runtime will be launched for automation.

## Independent Challenge Allocation

One fresh bounded review of authored runtime changes and immediate producers/
consumers; no code execution, edits, publication or worker delegation. Primary
retains architecture/authority/integration/acceptance. Adjudicate every finding,
request a focused delta only if a material repair needs independent confirmation.
No user token/time hard cap was specified. Scope/coverage gaps remain explicit.

## Review And Verification Checkpoint

- Initial full suite PASS 1,531; privacy PASS 1,774; sandbox-only initial loopback
  bind failure resolved by rerunning the unchanged suite with loopback permission.
- Frozen v1 independent review: supported prior-output preservation gap in default
  builder path; fixed verified staging plus backup/rollback publication, validated
  with synthetic failure and success test (9 build tests). Initial build into
  separate output completed; canonical dist remained unchanged. Final rebuild uses
  repaired builder and updated guide copy.
- Supported guidance mismatch: desktop no longer retires optional Auto Work cache,
  so app guide/desktop UI now promise only inactive search cache cleanup. Web copy
  remains conditional on actual package selection. Owner-doc language corrected.
- Guide8 and build9 tests renewed after repair; independent v2 confirmation pending.

- V2 delta review found an interrupt-after-successful-rename bookkeeping gap.
  Primary reproduced it with synthetic old/new rename interruption (old path
  failed before repair); fixed recovery to reconcile actual staging/output/backup
  paths and require a complete candidate. Build11 tests pass, including ordinary
  publication failure, post-rename interrupts and retained backup on rollback
  failure. Full suite PASS 1,532 before the last helper/test-only repair; final
  helper11 renewed. One additional focused static confirmation is justified by
  this new concrete failure, not an unchanged search for more findings.
