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

## Open Planning Boundaries

- [PRD-0005: Workflow And Skill Intelligence](prd/prd-0005-workflow-and-skill-intelligence.md)
  is `draft` and must not enter Feature or execution work before approval.
- [PRD-0010: Atlassian UI And Interaction Reconciliation](prd/prd-0010-atlassian-ui-and-interaction-reconciliation.md)
  is an approved incremental boundary that remains open for later owner
  observations. Its current child Features are passed:
  - [FEAT-0062: Atlassian Local Site And Access-Binding Contract](feature/feat-0062-atlassian-local-site-and-access-binding-contract.md)
  - [FEAT-0063: Atlassian Local-Only Add And Access Setup](feature/feat-0063-atlassian-local-only-add-and-access-setup.md)

## Active Execution

- No Run is currently indexed as active. Start a new Run only from an approved
  Feature and its approved Spec.

## Recently Completed Chain

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
- `project/`: roadmap and backlog ownership

## Maintenance Rule

- Keep this index limited to open boundaries, active execution, and recent
  completed chains; do not turn it into a registry of every historical artifact.
- Update this index when one of those navigation states changes, but keep the
  owning artifact's metadata and continuity notes as the detailed truth.
