# Plans Index

Use this index for current planning and execution navigation. Each PRD, Feature,
Spec, Run, and Evaluation document owns its own detailed status and history.

## Start Here

- [Project Roadmap](project/roadmap.md): phase direction, current priorities,
  validation strategy, and risk controls
- [Project Backlog](project/backlog.md): unresolved implementation work and
  decisions ordered by priority
- [Agent Workflow](../agents/README.md): approval gates and the PRD → Feature →
  Spec → Run → Evaluation flow
- [Artifact Catalog](artifact-catalog.md): generated link index for every tracked
  historical PRD, Feature, Spec, Run, Evaluation, Fix, and heuristic artifact

## Open Planning Boundaries

- [PRD-0005: Workflow And Skill Intelligence](prd/prd-0005-workflow-and-skill-intelligence.md)
  is `draft` and must not enter Feature or execution work before approval.
- [PRD-0010: Atlassian UI And Interaction Reconciliation](prd/prd-0010-atlassian-ui-and-interaction-reconciliation.md)
  is an approved incremental boundary that remains open for later owner
  observations. Its current child Features are passed:
  - [FEAT-0062: Atlassian Local Site And Access-Binding Contract](feature/feat-0062-atlassian-local-site-and-access-binding-contract.md)
  - [FEAT-0063: Atlassian Local-Only Add And Access Setup](feature/feat-0063-atlassian-local-only-add-and-access-setup.md)

## Active Execution

- None.

## Recently Completed Chains

- [REFACTOR-0001: Session Sync Repair Performance](refactoring/refactor-0001-session-sync-repair-performance.md)
  completed concern-specific repair lanes, request-local lookup and pricing
  caches, batched derived writes, bounded synchronization progress, and final
  parity/performance review. See the [wrap-up](refactoring/logs/2026-08-24_refactor-0001_session-sync-performance.md)
  and [final merge check](refactoring/logs/2026-08-24_refactor-0001_final-merge-check.md).

- [PRD-0013: Session-Centric Related Context Evidence](prd/prd-0013-session-centric-related-context-evidence.md)
  (`passed`) completed [FEAT-0072](feature/feat-0072-session-reference-evidence-contract.md),
  [FEAT-0073](feature/feat-0073-deterministic-session-reference-capture-and-reconciliation.md),
  and [FEAT-0074](feature/feat-0074-session-centric-related-materials-rail.md).
  The final presentation chain is [SPEC-0074](spec/spec-0074-session-centric-related-materials-rail.md)
  → [RUN-20260803-84](run/run-20260803-84-session-centric-related-materials-rail.md)
  → [FIX-0074](fix/fix-0074-related-material-evidence-density.md)
  → [Contract](evaluation/eval-0074-contract-session-centric-related-materials-rail.md),
  [Design](evaluation/eval-0074-design-session-centric-related-materials-rail.md),
  [Functional](evaluation/eval-0074-functional-session-centric-related-materials-rail.md),
  and [UX](evaluation/eval-0074-ux-session-centric-related-materials-rail.md)
  evaluations.

- [PRD-0012: Multiple Local AI Session Sources And Inventory Integrity](prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
  (`passed`) completed
  [FEAT-0065](feature/feat-0065-session-source-enabled-field-removal.md),
  [FEAT-0066](feature/feat-0066-local-ai-source-identity-contract.md),
  [FEAT-0067](feature/feat-0067-local-session-source-settings-and-safe-registration.md),
  [FEAT-0068](feature/feat-0068-multi-source-session-synchronization-and-health.md),
  [FEAT-0069](feature/feat-0069-session-source-scope-and-provenance.md),
  [FEAT-0070](feature/feat-0070-usage-source-scope-and-composition.md), and
  [FEAT-0071](feature/feat-0071-meaningful-session-eligibility-and-empty-stub-reconciliation.md).
  The latest detail-provenance chain is
  [SPEC-0069-R5](spec/spec-0069-r5-session-detail-metadata-and-subsession-stats.md)
  → [RUN-20260803-81](run/run-20260803-81-session-detail-metadata-and-subsession-stats.md)
  → [Contract](evaluation/eval-0069-r5-contract-session-detail-metadata-and-subsession-stats.md),
  [Design](evaluation/eval-0069-r5-design-session-detail-metadata-and-subsession-stats.md),
  [Functional](evaluation/eval-0069-r5-functional-session-detail-metadata-and-subsession-stats.md),
  and [UX](evaluation/eval-0069-r5-ux-session-detail-metadata-and-subsession-stats.md)
  evaluations. Each Feature owns its complete Spec, Run, fix, and evaluation
  history.

- [PRD-0011: Shared Native Select Control Geometry](prd/prd-0011-shared-native-select-control-geometry.md)
  → [FEAT-0064](feature/feat-0064-shared-native-select-disclosure-geometry.md)
  → [SPEC-0064](spec/spec-0064-shared-native-select-disclosure-geometry.md)
  → [RUN-20260727-69](run/run-20260727-69-shared-native-select-disclosure-geometry.md)
  → [Design](evaluation/eval-0064-design-shared-native-select-disclosure-geometry.md),
  [Functional](evaluation/eval-0064-functional-shared-native-select-disclosure-geometry.md),
  and [UX](evaluation/eval-0064-ux-shared-native-select-disclosure-geometry.md)
  evaluations

## Artifact Locations

- `prd/`: product boundaries, decisions, and approval status
- `feature/`: approved loop-sized outcomes and acceptance contracts
- `spec/`: implementation-facing contracts
- `run/`: execution state, attempts, evidence coverage, and routing
- `evaluation/`: contract, design, functional, and UX results
- `fix/`: bounded corrections from evaluator findings
- `heuristic/`: non-blocking UX suggestion backlog
- `refactoring/`: scoped refactor tracks and their validation or merge-check logs
- `project/`: roadmap and backlog ownership
- [Artifact Catalog](artifact-catalog.md): complete generated navigation for its
  catalog-managed artifact families

## Maintenance Rule

- Keep this index limited to open boundaries, active execution, and recent
  completed chains; do not turn it into a registry of every historical artifact.
- Update this index when one of those navigation states changes, but keep the
  owning artifact's metadata and continuity notes as the detailed truth.
- Regenerate the complete historical catalog with
  `uv run python scripts/build-plan-artifact-catalog.py build` whenever a
  catalog-managed PRD, Feature, Spec, Run, Evaluation, Fix, or heuristic artifact
  is added, removed, or renamed.
