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

- [PRD-0017: Source-Backed Workflow Map And Workstream Lenses](prd/prd-0017-source-backed-workflow-map-and-workstream-lenses.md)
  is the `approved` upper boundary for eventually presenting Workstreams as
  user-owned lenses over a deterministic, source-backed directional
  projection. Its
  [design plan](design/workflow-map-design-plan.md) records the Quartz/Obsidian
  reference boundary, Focus-first interaction sequence, and model-free visual
  grammar. The first approved dependency-ordered Feature chain has passed:
  - [FEAT-0085: Workflow Episode And Direction Contract](feature/feat-0085-workflow-episode-and-direction-contract.md)
    (`passed`; Episode and direction foundation)
  - [FEAT-0086: Deterministic Cross-Source Workflow Projection](feature/feat-0086-deterministic-cross-source-workflow-projection.md)
    (`passed`; deterministic cross-source projection)
  - [FEAT-0087: Session Workflow Focus Map](feature/feat-0087-session-workflow-focus-map.md)
    (`passed`; separate read-only Session Focus map)
  - [FEAT-0088: Workflow Assertion And Correction Contract](feature/feat-0088-workflow-assertion-and-correction-contract.md)
    (`passed`; append-only correction ledger and Focus overlay)
  - [FEAT-0089: Workflow Boundary Corrections](feature/feat-0089-workflow-boundary-corrections.md)
    (`passed`; contextual Focus correction controls)

  The `2026-09-15` product review retained this chain as a useful Session
  Lineage layer, not the intended Workstream replacement. Workstream Candidate
  Discovery and Review returned to planning as the next possible boundary;
  Lens, Atlas, topic terrain, and model use remain later options.
- [PRD-0005: Workflow And Skill Intelligence](prd/prd-0005-workflow-and-skill-intelligence.md)
  is `draft` and must not enter Feature or execution work before approval.
- [PRD-0010: Atlassian UI And Interaction Reconciliation](prd/prd-0010-atlassian-ui-and-interaction-reconciliation.md)
  is an approved incremental boundary that remains open for later owner
  observations. Its current child Features are passed:
  - [FEAT-0062: Atlassian Local Site And Access-Binding Contract](feature/feat-0062-atlassian-local-site-and-access-binding-contract.md)
  - [FEAT-0063: Atlassian Local-Only Add And Access Setup](feature/feat-0063-atlassian-local-only-add-and-access-setup.md)

## Active Execution

- No Feature is currently in-loop. PRD-0017 is back in product planning for a
  bounded Workstream Candidate Discovery and Review definition after the passed
  FEAT-0085 through FEAT-0089 chain. That planning note does not approve
  implementation. Workstream Lens, Atlas, topic terrain, and Qwen remain outside
  implementation until separately reviewed and approved.

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
- `spec/`: implementation-facing contracts
- `run/`: execution state, attempts, evidence coverage, and routing
- `evaluation/`: contract, design, functional, and UX results
- `fix/`: bounded corrections from evaluator findings
- `heuristic/`: non-blocking UX suggestion backlog
- `refactoring/`: scoped refactor tracks and their validation or merge-check logs
- `project/`: roadmap and backlog ownership
- `design/`: tracked design reconciliation, sequencing, validation gates, and
  handoff plans; durable visual law remains under `docs/policies/design/`
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
