# Feature Availability

This record owns deliberate delivery suspensions and their return conditions.
Feature/Run pass states retain their original evidence meaning; they do not imply
that a feature is currently offered. Retired contracts for suspended features
are preserved as historical snapshots
in [Run230](../run/run-20261101-230-feature-availability-and-doc-boundary.md);
they are not current product-guide entries. The default assembly is selected in
`src/localbrain/app/features.py`, shared by the desktop app and development web.

## Suspended Delivery — 2026-11-01

The owner requested that these features be hidden while deciding whether to
resume, extend or replace them. This is a delivery decision, not a finding that
all prior implementation or evaluation failed. No reactivation is scheduled.

| Feature | Delivery state | Excluded surfaces | Preserved state |
| --- | --- | --- | --- |
| Context Search | Suspended in default app and development web | Navigation, page/API routes, 4B/8B answer-model Settings cards/actions, answer workers, user-guide instructions | Source code, tests, existing public model assets and app registrations; keyword/embedding search remains available |
| Google Drive | Suspended in default app and development web | Settings category/panel/script, API routes, service construction and automatic synchronization, user-guide instructions | Connections, selections, checkpoints, credentials owned by Google CLI and received local copies |

Exclusion must hold even with previously installed models and saved automatic
Drive jobs. It does not remove database tables, unregister sources, delete files
or rewrite saved preferences. Normal launches must not create Drive state merely
to offer a hidden feature. Existing backup scope is unchanged: Drive state and
received copies are not included in the built-in application backup.

The known package set remains available to explicitly composed synthetic tests.
This is an internal test/composition boundary, not a hidden user toggle.

## Parked Evidence And Scope

- Recipient/native-host interaction and two-account Google Drive evidence remain
  open. Existing source/frozen tests do not certify actual My Drive/Shared Drive
  permissions or every recipient Mac.
- Context Search needs broader missing/conflicting-source, contact/role,
  multi-folder, memory and latency evidence beyond bounded synthetic fixtures.
  Saved conversation history, additional retrieval indexes and quantization
  remain separately scoped.

## Return Decision

On an explicit owner decision to resume or replace a feature:

1. Choose continued implementation, a bounded redesign or retirement; do not infer
   that removing the suspension alone resolves the earlier evidence gaps.
2. Reconcile retained state and compatibility with the retained contracts and the
   new approved boundary:
   [Context Search](../run/run-20261101-230-feature-availability-and-doc-boundary.md#archived-context-search-contract) and
   [Google Drive](../run/run-20261101-230-feature-availability-and-doc-boundary.md#archived-google-drive-contract).
3. Update assembly, routes/jobs, Settings controls, app guides and README together.
   Repeat contract, functional, design and interaction checks in the delivered
   web and native targets before describing the feature as available.
4. Keep recipient/native-host, broad model-quality and live two-account Drive
   checks separate from bounded synthetic results.

Implementation and verification of this suspension are recorded in
[Run230](../run/run-20261101-230-feature-availability-and-doc-boundary.md).
