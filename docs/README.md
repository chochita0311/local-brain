# Documentation Map

This directory separates durable project contracts from active planning artifacts.

## Start Here

- Use [the root README](../README.md) for the product overview and quick start.
- Use [AGENTS.md](../AGENTS.md) for repository-local operating rules and source-of-truth routing.
- Use [Agent Workflow](agents/README.md) for structured PRD, feature, spec, build, and evaluation loops.
- Use this file to find the document that owns a product, implementation, or planning fact.

## Policies

Durable rules and current contracts live under `docs/policies/`.

- [Product Model](policies/project/product.md): product purpose, scope, terminology, source roles, and user-facing organization rules
- [Project Architecture](policies/project/architecture.md): stack, runtime boundaries, source adapters, storage model, and current implementation baseline
- [Privacy And Data Handling](policies/project/privacy-and-data.md): repository boundary, local persistence, external access, and disclosure constraints
- [Developer Guide](policies/project/developer-guide.md): setup, configuration, development workflow, and verification
- [Claude Task Runner](policies/operations/claude-task-runner.md): in-app Claude maintenance execution, retrieval, persistence, and review behavior
- [Harness Policies](policies/harness/): planning approval, execution routing, profiles, surface lanes, and traceability
- [Design Evaluation](policies/design/design-evaluation.md): reusable visual and screen-surface checks
- [Interaction Evaluation](policies/experience/interaction-evaluation.md): reusable interaction continuity and UX checks

## Agent Package

- `docs/agents/roles/`: planning, build, evaluation, orchestration, and fix role contracts
- `docs/agents/flows/`: default baton flow and stop points
- `docs/agents/operations/`: prompts for starting and continuing a Run
- `docs/agents/profiles/`: frontend, backend, fullstack, foundation, infrastructure, and docs profiles

## Plans

Sequencing and unresolved work live under `docs/plans/`.

- [Project Roadmap](plans/project/roadmap.md): phase direction, current priorities, validation strategy, and risk controls
- [Project Backlog](plans/project/backlog.md): detailed open work and decisions ordered by priority
- `docs/plans/prd/`, `feature/`, and `spec/`: approved planning and implementation boundaries
- `docs/plans/run/`, `evaluation/`, `fix/`, and `heuristic/`: execution and review artifacts

## Ownership Rules

- `README.md` explains what LocalBrain is and how to start it.
- `AGENTS.md` routes contributors and agents without duplicating deeper contracts.
- `docs/policies/` owns facts that should remain true across implementation cycles.
- `docs/plans/` owns facts expected to change as work is completed or reprioritized.
- `docs/agents/` owns reusable role, flow, operation, and execution-profile contracts.
- Machine-specific workflow inventories and handoff context stay outside Git and must not become dependencies of tracked documentation.

When a fact changes, update its owner document and replace repeated explanations elsewhere with a link.
