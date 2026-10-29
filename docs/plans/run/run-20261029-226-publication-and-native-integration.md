# Run226: Public Candidate Review And Native Integration

## Metadata

- ID: `run-20261029-226`
- Status: `passed`
- Feature: [FEAT-0153](../feature/feat-0153-context-search-conversation.md), with approved [Drive integration](../feature/feat-0150-drive-operation-guides.md) and existing Learning/schema pending changes.
- Parent: [PRD026](../prd/prd-0026-context-search-grounded-local-answers.md), [PRD025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Active spec: [SPEC0153](../spec/spec-0153-context-search-conversation.md#native-and-publication-closeout)
- Profile: `fullstack-product`; contract, functional, design and interaction evidence scoped to native integration; documentation/privacy review separate from release certification.
- Authorization: owner explicitly requested all-session wrap-up, user-requested subagent privacy/docs reviews, native build including Drive and Context Search, then commit/push. No private data, credential export, history rewrite or live Drive/model source publication is authorized.

## Scope And Sequence

Primary owns intent, source authority, publication/privacy decisions, integration and final semantic review. Read-only subagents review the fixed publication inventory and document contracts using docs-structuring incremental and docs-shaping reshape. Optional large reorganizations and major semantic rewrites are not included. Existing user server, data and jobs are preserved.

Reconcile current schema/checker/generated audit ownership, incorporate necessary review findings, build the native distribution using existing toolchain contracts, test frozen routes/model worker and isolated UI, scan repo and bundle, commit the exact reviewed candidate, push and verify the remote head. Public models are not bundled. Google credentials and Drive material remain per-user runtime state. Live two-account Google access and notarized release are separate boundaries.

## Evidence And Outcome

[Native/publication evaluation](../evaluation/eval-0153-native-publication-closeout.md) passes the bounded build/integration contract. The app/ZIP is built, ad-hoc signature and private-path checks pass, frozen4B/8B received-copy answers and syntheticSDK failure/env isolation are observed. Full suite1421tests and all schema/value/audit/12Mermaid checks pass. Existing defer decisions and historical evidence are preserved. Public-candidate privacy and both requested docs reviews are repeated on the final frozen inventory before source commit/push; the remote postcondition is recorded by the final receipt/private stage after the action.

Native window/recipient, live two-account Google and broader model-quality gates remain separate. An existing user app and servers/jobs were preserved. No private data or public model weights are bundled; no binary upload or installed-app replacement is included.

## Entry Validation Debt

The following item was open at Run226 entry; its original baseline, owner links and evidence limits are retained here after reconciliation rather than left as unresolved backlog:

> - [ ] Reconcile the pending learning/schema validation with its semantic owners.
>   The 2026-10-27 documentation cleanup refreshed the previously stale
>   `baseline.sources` fingerprints for the [Data Model entry](../../policies/project/data-model.md),
>   [Workspace And Session Activity](../../policies/project/data-model/workspace-and-session-activity.md)
>   and [Usage And Cost Records](../../policies/project/data-model/usage-and-cost-records.md);
>   the derived package now passes its existing freshness check. The legacy
>   `check-data-model-docs.py` still checks the published ten-subject baseline:
>   45 ordinary tables, 58 physical foreign keys, 43 fresh and 51 effective indexes.
>   The pending learning schema has eleven subjects, 48 ordinary tables, 59 physical
>   foreign keys, 44 fresh and 52 effective indexes. Extend that check's subject
>   ownership and count expectations with the pending package. The schema-cleanup
>   audit decisions and generated ledger also retain the published object census;
>   reconcile their manifest binding and new-object coverage with the pending
>   learning schema. These remaining validation gaps are separate from the
>   published baseline and the still-unverified learning behavior/benefit evidence.

