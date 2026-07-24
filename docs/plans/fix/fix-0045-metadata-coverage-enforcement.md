# FIX-0045: Metadata Coverage Enforcement

## Metadata

- ID: `fix-0045-metadata-coverage-enforcement`
- Status: `complete`
- Run ID: `run-20260723-50`
- Attempt: `2`
- Feature: [feat-0045-provider-neutral-external-sync-run-contract](../feature/feat-0045-provider-neutral-external-sync-run-contract.md)
- Spec: [spec-0045-provider-neutral-external-sync-run-contract](../spec/spec-0045-provider-neutral-external-sync-run-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: manifest and authorization
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Input Reports

- Evaluator report addressed: [Contract Attempt 1](../evaluation/eval-0045-contract-provider-neutral-external-sync-run-contract.md).

## Fix Scope

- Close the provider-result path that accepted metadata for a target without selected metadata coverage.
- Prevent a Jira metadata request or retained provider result from exceeding the target's explicit field allowlist.
- Preserve the existing identity, content, version, hash, and bounded-error contracts.

## Changes Applied

- `validate_provider_result` now rejects every non-empty metadata object unless `metadata` is present in the target coverage.
- Jira metadata manifest validation now requires explicit request fields and rejects a request field set that is not a subset of the target allowlist.
- Provider-result validation uses only the target allowlist as persistence authority; request arguments cannot silently widen it.
- Focused tests prove that content-only coverage cannot retain metadata and that neither request nor result fields can exceed the selected target fields.

## Contract Or Lane Impact

- Contract surfaces touched: provider-result validation only.
- Surface lanes touched: manifest and authorization.
- Stale-assumption check needed: yes; rerun focused external-sync tests, both required evaluators, schema/generated checks, privacy, and the complete suite.

## Remaining Issues

- None.

## Return Decision

- `re-evaluate`

## Continuity Notes

- `2026-07-23`: applied the targeted implementation repair without changing the approved Feature or Spec boundary.
