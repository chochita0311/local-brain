# Agent Workflow

This directory contains LocalBrain's installed agent workflow package. The repository owns this copy; normal planning and execution must not depend on an external source package.

## Start Here

- Use [workflow.md](flows/workflow.md) for the role sequence, approval stops, and handoff model.
- Use [runner.md](operations/runner.md) to start or continue one bounded execution Run.
- Use [Execution Profiles](profiles/README.md) to select the smallest profile that matches the approved work.
- Use [PRD And Feature Management](../policies/harness/prd-feature-management.md) for planning approval and traceability rules.
- Use [Execution Loop Governance](../policies/harness/execution-loop-governance.md) for failure routing and artifact ownership.
- Use [Execution Profile Policy](../policies/harness/execution-profiles.md) for profile selection, surface lanes, and evaluator routing.
- Use [Traceability And Link Hygiene](../policies/harness/traceability-and-link-hygiene.md) for source-of-truth paths and portable references.
- Use [Competence-First Delegation](../policies/harness/competence-first-delegation.md) before delegating bounded work.
- Use [Operator Briefing And Review Receipts](../policies/harness/operator-briefing-and-review-receipts.md) when prior context materially affects orientation, execution, review, block, or handoff.
- Use [Harness Improvement](operations/harness-improvement.md) for configured stage experience, reflection, bounded comparisons, and authorized common export.

## Roles

Planning roles:

- [PRD Normalizer](roles/prd-normalizer.md): turn raw product input into a bounded PRD
- [Feature Planner](roles/feature-planner.md): decompose an approved PRD into loop-sized features

Execution roles:

- [Orchestrator](roles/orchestrator.md): select profile, lanes, and evaluators and route one execution loop
- [Spec Agent](roles/spec-agent.md): convert one approved feature into an implementation-facing spec
- [Builder](roles/builder.md): implement one approved spec without expanding scope
- [Contract Evaluator](roles/contract-evaluator.md): evaluate schemas, APIs, ownership, and integration boundaries
- [Design Evaluator](roles/design-evaluator.md): evaluate visual and design-surface fidelity
- [Functional Evaluator](roles/functional-evaluator.md): evaluate runtime behavior, state, workflow, and regressions
- [UX Heuristic Evaluator](roles/ux-heuristic-evaluator.md): identify interaction friction without inventing scope
- [Fix Agent](roles/fix-agent.md): apply bounded fixes from approved findings

## Execution Profiles

- [Frontend Product](profiles/frontend-product.md): screens, routes, components, interactions, and presentation
- [Backend Product](profiles/backend-product.md): APIs, persistence, commands, jobs, and server behavior
- [Fullstack Product](profiles/fullstack-product.md): coordinated frontend and backend surfaces
- [Foundation Contract](profiles/foundation-contract.md): schemas, invariants, identity, and ownership boundaries
- [Infra Devtool](profiles/infra-devtool.md): development tooling, CI, runtime configuration, and operational surfaces
- [Docs Content](profiles/docs-content.md): documentation, policy, content, and information architecture

## Screen And Surface Work

User-visible work uses the Frontend Product profile, or the Fullstack Product profile when the same feature also changes backend contracts.

- Declare affected screens, routes, components, states, and browser behavior in the Feature and Spec artifacts.
- Split multi-surface work into explicit lanes when frontend, backend, data, or connector changes can be evaluated independently.
- Use the [Design Constitution](../policies/design/design-constitution.md) as the durable implementation baseline for visible surfaces.
- Use [Design Evaluation](../policies/design/design-evaluation.md) for visible layout and presentation changes.
- Use [Interaction Evaluation](../policies/experience/interaction-evaluation.md) for navigation continuity, state transitions, control behavior, and interaction regressions.
- Run functional evaluation for user-visible workflows even when a separate design evaluator is used.
- Keep UX heuristic findings non-blocking unless they reveal a severe contradiction in the approved interaction contract.

## Harness Experience

[Harness Improvement policy](../policies/harness/harness-improvement.md) and its [operation](operations/harness-improvement.md) govern ordinary planning and execution stage entry, observed component use, and closing reflection. With a ready private binding, agents retrieve relevant experience and save the actual stage outcome without a separate user command. Experiments start only for an authorized comparison; ordinary completion does not require one.

Discover the private binding at `docs/evidence/STORE.md`, or reuse its approved override. The default binding/index, `stages/`, `improvements/`, and `experiments/` are ignored consumer outputs and stay outside the import manifest. Preserve them on refresh. Missing or conflicting persistence means session-only observations with the gap reported. Application runtime data and original development evaluation evidence keep their existing storage owners.

Shared blank store/stage/experiment/Improvement Record templates and the metadata schema live under `docs/agents/`. Public Improvement Records and their catalog require a separate explicit selection; they do not activate private history transfer or export. Use the [record contract](../policies/harness/improvement-record-contract.md) for identity, evidence limits, local applicability, and exchange receipts.

## Planning Artifacts

Templates and generated artifacts live under `docs/plans/`:

- `prd/`: bounded product requirements
- `feature/`: approved loop-sized features
- `spec/`: implementation-facing specifications
- `run/`: execution records
- `evaluation/`: contract, design, functional, and UX reports
- `fix/`: bounded fix logs
- `heuristic/`: non-blocking UX suggestion backlog

Templates are named `template-*.md` in their owning directories. Generated artifacts must use repository-relative links and must not contain private runtime data.

The optional [Operator Briefing Template](templates/operator-briefing.md) is a user-facing scaffold, not a new workflow phase or source of truth.

## Local Ownership

- Shared role and policy text remains general unless LocalBrain requires a documented specialization.
- LocalBrain-specific product, architecture, privacy, and Maintenance Task Runner contracts remain under `docs/policies/project/` and `docs/policies/operations/`.
- Refreshing the shared package must preserve local plans, completed Runs, evaluations, and project policy.
- Reusable improvements may be promoted upstream only after removing LocalBrain-specific assumptions.

## Shared Harness Refresh

[Harness Import Manifest](harness-import-manifest.json) records the committed `ai-assets` source revision, selected files, export mapping version, ownership, and separate source and rendered SHA-256 baselines. Use the source package's adoption guide for a controlled refresh; normal work continues to use this repository's installed docs.

- Refresh `managed` files only after their current bytes match the recorded rendered baseline. Reconcile unexplained changes before replacing them.
- Preserve `local` files and their detachment baselines. During the initial controlled merge, the accepted shared rendering was recorded separately from the retained LocalBrain specializations; its hash does not claim that a local file equals the shared rendering. These baselines predate Harness Improvement selection; restoring the evaluation template's two capability links did not rebase its local entry. Later refreshes require an explicit ownership decision to reattach or rebase them.
- Local specializations retain design-constitution and creative-source inputs, execution-artifact lifecycle rules, completed-foundation prerequisites, linked Run references, navigation wording, and the existing mandatory evaluation conditions.
- The installed selection includes design, interaction evaluation, and Harness Improvement. Its stage hooks use the private binding described above. Public Improvement Records are a separate explicit selection.
- Apply source-layout link rewrites before comparison, keep omitted optional references as conditional plain text, and localize consuming-repository prose to the installed repository. Validate links and hashes before replacing the manifest as the final successful step.
- Personal runtime instructions, worker bindings, and skill installation follow their separate adoption procedures.
