# Agent Workflow

This directory contains LocalBrain's installed agent workflow package. The repository owns this copy; normal planning and execution must not depend on an external source package.

## Start Here

- Use [workflow.md](flows/workflow.md) for the role sequence, approval stops, and handoff model.
- Use [runner.md](operations/runner.md) to start or continue one bounded execution Run.
- Use [Execution Profiles](profiles/README.md) to select the smallest profile that matches the approved work.
- Use [PRD And Feature Management](../policies/harness/prd-feature-management.md) for planning approval and traceability rules.
- Use [Execution Loop Governance](../policies/harness/execution-loop-governance.md) for failure routing and artifact ownership.

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

## Local Ownership

- Shared role and policy text remains general unless LocalBrain requires a documented specialization.
- LocalBrain-specific product, architecture, privacy, and Claude Task Runner contracts remain under `docs/policies/project/` and `docs/policies/operations/`.
- Refreshing the shared package must preserve local plans, completed Runs, evaluations, and project policy.
- Reusable improvements may be promoted upstream only after removing LocalBrain-specific assumptions.
