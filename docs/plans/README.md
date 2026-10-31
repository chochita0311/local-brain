# Plans Index

Use this index for current work, review boundaries and the next owning record.
PRDs/Features own approval and acceptance; Runs/evaluations/refactor records own
execution history and evidence limits. [Current contracts](../README.md#feature-contracts-and-development-operations)
are defined independently of those records.
Each PRD, Feature, Spec, Run and Evaluation retains its detailed status and history.

## Start Here

- [Roadmap](project/roadmap.md): direction and sequencing.
- [Backlog](project/backlog.md): unresolved implementation work and decisions ordered by priority.
- [Agent Workflow](../agents/README.md): approval gates and PRD → Feature → Spec → Run → Evaluation.
- [Artifact Catalog](artifact-catalog.md): complete generated historical navigation.

## Open Planning Boundaries

| Boundary | Current position and next review |
| --- | --- |
| [Context Search](prd/prd-0026-context-search-grounded-local-answers.md) | Approved bounded delivery and native integration are implemented; broader model quality, native recipient and release evidence remain separate. |
| [Google Drive](prd/prd-0025-google-drive-connection-and-incremental-sync.md) | Approved Features 0145–0150 and gcloud revision are implemented; final two-account My Drive/Shared Drive acceptance remains open. |
| [In-app Docs](prd/prd-0024-deployed-app-docs.md) | Six English guides are delivered; PRD remains in-loop for human acceptance. Native recipient execution is separate. |
| [Code/command learning](prd/prd-0023-code-and-command-learning.md) | Reviewed manual reader is implemented; required functional transitions remain untested and block formal pass. Automatic discovery, official updates and generation are not running. |
| [Work-grounded learning](prd/prd-0022-work-grounded-learning-dashboard.md) | Pilot returned to planning for the code/command successor; preserved contracts are reused and the earlier functional gap remains open. Learning benefit is unproven. |
| [Standalone test app](prd/prd-0021-macos-standalone-test-app-and-local-settings.md) | Local implementation is complete; final native/recipient acceptance remains blocked. Signed/notarized public release is separate from the ad-hoc test ZIP. |
| [Natural-language search](prd/prd-0020-local-natural-language-search.md) | Approved local baseline is implemented; additional tuning depends on observed burden. Quality evidence retains its recorded source/hardware/holdout limits. |
| [Observed Sessions Chart](prd/prd-0019-observed-session-chart.md) | First-phase documentation/verification closeout is complete; physical wheel-gesture evidence remains unverified. Relationship proposals need separate approval. |
| [Workflow reconstruction and map](prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md) | Owner-paused after continuous-map inspection. [Design handoff](design/workflow-map-design-plan.md#handoff-to-next-track) owns resumption; failed extraction trials are not queued to restart. |
| [Workflow/skill intelligence](prd/prd-0005-workflow-and-skill-intelligence.md) | Approved for later proposals; bounded skill ranking passed. The analyzer has its own PRD below. |
| [Personal improvement](prd/prd-0018-personal-ai-use-improvement-insights.md) | First analysis-only Run increment and corrections are delivered; actual intervention benefit and later review-state features remain open. [Backlog](project/backlog.md#personal-improvement-insights) owns follow-up. |
| [Atlassian UI reconciliation](prd/prd-0010-atlassian-ui-and-interaction-reconciliation.md) | Current child Features are passed; the approved incremental boundary remains open for later owner observations. |

<a id="active-execution"></a>

## Execution State

The workflow-map track has no active calculation or implementation Run. Its
completed inspection boundary is [Run117](run/run-20260924-117-continuous-affinity-canvas.md).
The separate Insights track retains its delivered analysis-only behavior and
evidence limits under [PRD-0018](prd/prd-0018-personal-ai-use-improvement-insights.md).

| Unresolved experiment boundary | Route |
| --- | --- |
| [Source-claim extraction/binding](feature/feat-0100-source-claim-extraction-and-binding-trial.md) | Quality-blocked after one frozen trial; no holdout/private/UI processing or automatic new trial. [Run112](run/run-20260923-112-source-claim-extraction-and-binding-trial.md) owns the outcome and consumed allowance. |
| [Quoted work-context inference](feature/feat-0098-local-work-context-inference.md) | Admission-blocked; diagnostics and zero-generation replay do not approve an extractor. [PRD-0017](prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md) owns the trial lineage. |
| [Model-free reconstruction](feature/feat-0095-bounded-work-reconstruction-experiment.md) | Blocked on independent quality evidence; unassessed execution is not a viability pass. Its one-time review allowance is not renewed by replay or documentation work. |

## Active Refactoring

No active code-refactoring track. Completed tracks retain their own remaining
parity, release and feature-removal limits.

## Completed Refactoring

| Track | Result and retained boundary |
| --- | --- |
| [Session-centered packages](refactoring/refactor-0003-session-centered-package-boundaries.md) | Completed after the cache-boundary correction; strict parity remains provisional and Drive transport/native installation/whole-feature removal retain separate scopes. |
| [Shared resources](refactoring/refactor-0005-shared-resource-ownership.md) | Completed shared identity/bindings and operational migration/restart preservation; whole-feature removal and deferred Drive checks remain separate. |
| [Direct Session materials](refactoring/refactor-0004-direct-session-materials.md) | Completed direct-only detail behavior; Workstream/Thread data is preserved. |
| [Ingestion layers/revisions](refactoring/refactor-0002-ingestion-layers-and-session-revisions.md) | Completed revision admission and DDL correction; older app copies require rebuild/replacement and recipient/native-browser acceptance remain separate. |

## Recently Completed Chains

This section keeps only a compact view of notable recent outcomes. Use each
owning PRD or refactor and the [Artifact Catalog](artifact-catalog.md) for the
complete Feature, Spec, Run, Evaluation, and Fix lineage.

| Boundary | Outcome | Canonical result |
| --- | --- | --- |
| [PRD-0016: Atlassian Standard URL Structure References](prd/prd-0016-atlassian-standard-url-recognition.md) | FEAT-0082 and FEAT-0083 passed; deterministic locators now feed durable Explorer references. | [Final Run](run/run-20260901-93-atlassian-structure-reference-sync-and-explorer.md) and [design rationale](design/atlassian-structure-reference-plan.md) |
| [PRD-0015: Atlassian Site-First URL Organization](prd/prd-0015-atlassian-site-first-url-organization.md) | FEAT-0081 passed and remains the Site-first historical baseline beneath PRD-0016. | [Final Run](run/run-20260901-91-atlassian-deterministic-site-first-hierarchy.md) and [design rationale](design/atlassian-site-first-hierarchy-plan.md) |
| [PRD-0014: Atlassian Explorer And Unified Retrieval](prd/prd-0014-atlassian-explorer-and-unified-retrieval.md) | FEAT-0075 through FEAT-0080 passed; FEAT-0077 required the preserved structural-scope correction and AI retrieval remains deferred. | [Final Run](run/run-20260829-90-atlassian-local-evidence-sync.md), [FIX-0077](fix/fix-0077-atlassian-structural-scope-parity.md), and [design rationale](design/atlassian-explorer-reframe-plan.md) |
| [REFACTOR-0001: Session Sync Repair Performance](refactoring/refactor-0001-session-sync-repair-performance.md) | Concern-specific repair lanes, request-local caches, batched writes, and bounded progress completed parity and performance review. | [Wrap-up](refactoring/logs/2026-08-24_refactor-0001_session-sync-performance.md) and [final merge check](refactoring/logs/2026-08-24_refactor-0001_final-merge-check.md) |
| [PRD-0013: Session-Centric Related Context Evidence](prd/prd-0013-session-centric-related-context-evidence.md) | FEAT-0072 through FEAT-0074 passed; the final presentation correction and all evaluator evidence remain in the owning chain. | [Final Run](run/run-20260803-84-session-centric-related-materials-rail.md) and [FIX-0074](fix/fix-0074-related-material-evidence-density.md) |
| [PRD-0012: Multiple Local AI Session Sources And Inventory Integrity](prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md) | FEAT-0065 through FEAT-0071 passed with the latest detail-provenance behavior retained by the FEAT-0069-R5 lineage. | [Latest detail Run](run/run-20260803-81-session-detail-metadata-and-subsession-stats.md) |
| [PRD-0011: Shared Native Select Control Geometry](prd/prd-0011-shared-native-select-control-geometry.md) | FEAT-0064 passed its shared disclosure geometry and design, functional, and UX evaluation. | [Final Run](run/run-20260727-69-shared-native-select-disclosure-geometry.md) |

## Artifact Locations

- `prd/`: product boundaries, decisions, and approval status
- `feature/`: approved loop-sized outcomes and acceptance contracts
- `spec/`: change-scoped implementation contracts and verification plans; settled
  behavior belongs to its current policy owner
- `run/`: execution state, attempts, evidence coverage, and routing
- `evaluation/`: contract, design, functional, and UX results
- `fix/`: bounded corrections from evaluator findings
- `heuristic/`: non-blocking UX suggestion backlog
- `refactoring/`: scoped refactor tracks and their validation or merge-check logs
- `project/`: roadmap, backlog, and [harness import history](project/harness-import-history.md)
- `design/`: tracked design reconciliation, sequencing, validation gates, and
  handoff plans and [design-system change history](design/design-system-change-history.md);
  durable visual law remains under `docs/policies/design/`
- `research/`: source-backed method reviews and proposed experiments linked to
  an owning PRD; research alone does not approve execution or change acceptance
- [Artifact Catalog](artifact-catalog.md): complete generated navigation for its
  catalog-managed artifact families

## Maintenance Rule

Keep this index to current position, remaining judgment and next owner. Put
attempt chronology, test counts and detailed delivery changes in the relevant
PRD, Feature, Run, evaluation or refactor record. Those records retain the
detailed snapshots formerly repeated here.
Update this index when open boundaries, active execution or recent completion
changes; keep detailed metadata and continuity with the owning artifacts.

Regenerate [Artifact Catalog](artifact-catalog.md) with
`uv run python scripts/build-plan-artifact-catalog.py build` when a catalog-managed
PRD, Feature, Spec, Run, Evaluation, Fix or heuristic artifact is added, removed
or renamed. Current contract-owner moves do not alter historical artifact IDs.
