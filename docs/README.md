# Documentation Map

This directory separates current project contracts from project plans and approval, change, execution, and evaluation records.

## Start Here

- Use [the root README](../README.md) for the product overview and quick start.
- Use the [Developer Guide](policies/project/developer-guide.md) for source setup, development-web workflows, builds, configuration and verification.
- Use [AGENTS.md](../AGENTS.md) for repository-local operating rules and source-of-truth routing.
- Use [Agent Workflow](agents/README.md) for structured PRD, feature, spec, build, and evaluation loops.
- Use this file to find the document that owns a product, implementation, or planning fact.

## User Guides

The distributed app's English user guides live in `src/localbrain/content/docs/`
and are read through **Docs** in the app. They own ordinary screen usage and
settings procedures; [In-App Documentation](policies/project/app-documentation.md)
owns their content and delivery rules.

| Guide | Responsibility |
| --- | --- |
| [Getting Started](../src/localbrain/content/docs/getting-started.md) | Setup, first use, quitting and updates |
| [Settings](../src/localbrain/content/docs/settings.md) | Preferences, source registration, synchronization, backup and recovery |
| [Sessions](../src/localbrain/content/docs/sessions.md) | Conversations, projects, pins and Chart |
| [Sessions Dashboard](../src/localbrain/content/docs/sessions-dashboard.md) | Usage, cost estimates and coverage |
| [Local Contexts](../src/localbrain/content/docs/local-contexts.md) | Document sources, reading and format limits |
| [Search](../src/localbrain/content/docs/search.md) | Keyword/meaning search, Context Search answers, models and readiness |

The [macOS test distribution guide](policies/project/standalone-test-app-guide.md)
owns artifact-specific first-launch requirements and distribution verification
limits. Build commands belong to the Developer Guide. Internal product contracts
and development progress remain in the layers below.

## Policies

Durable rules and current contracts live under `docs/policies/`.

- [Product Model](policies/project/product.md): product purpose, scope, terminology, source roles, and user-facing organization rules
- [Project Architecture](policies/project/architecture.md): stack, runtime boundaries, source adapters, storage model, and current capability ownership
- [macOS Installation And Local Storage](policies/project/installation-and-storage.md): installed wheel/archive setup, optional models, configurable private storage, updates, migration and cleanup
- [Local Natural Language Search](policies/project/natural-language-search.md): eligible sources, molecularization, model roles, query interpretation, ranking, refresh and evidence navigation
- [Context Search](policies/project/context-search.md): read-only folder questions, selectable4B/8B, shared-model/private-cache separation, evidence and transient dialogue
- [Source Claims And Work State](policies/project/source-claims-and-work-state.md): pure supplied-claim state projection and inferred provenance; not an admitted source extractor or map producer
- [Data Model](policies/project/data-model.md): complete effective SQLite map, global and subject ERDs, table/column catalogs, relationships, lifecycle, recovery, and delta maintenance ownership
- [Value Dictionaries](policies/project/data-model/value-dictionaries.md): generated subject map from physical and derived bounded values to complete presentation modes, labels, fallbacks, and consumer ownership
- [Schema Presentation](policies/project/schema-presentation.md): deterministic package manifest, source ownership, loader/failure behavior, and downstream Schema consumer contract
- [Google Drive Synchronization](policies/project/google-drive-sync.md): selected directional sync, private state, Google CLI authentication and distribution/live-validation boundaries.
- [Privacy And Data Handling](policies/project/privacy-and-data.md): repository boundary, local persistence, external access, and disclosure constraints
- [Developer Guide](policies/project/developer-guide.md): source setup, development-web workflows, distribution builds, configuration, model experiments, private evaluation archives and verification
- [Markdown Rendering Contract](policies/project/markdown-rendering.md): shared syntax, trust, local-reference, highlighting, consumer, and fallback rules
- [Maintenance Task Runner](policies/operations/claude-task-runner.md): in-app Claude/Codex maintenance execution, retrieval, external-sync boundaries, persistence, and review behavior
- [Harness Policies](policies/harness): planning approval, execution routing, profiles, delegation, operator continuity, and traceability
- [Competence-First Delegation](policies/harness/competence-first-delegation.md): delegation admission, worker suitability, context transfer, fallback, and binding lifecycle
- [Operator Briefing And Review Receipts](policies/harness/operator-briefing-and-review-receipts.md): orientation, work-start, direction-change, review, block, and handoff continuity
- [Harness Improvement](policies/harness/harness-improvement.md): configured private stage experience, reusable improvement records, comparisons, and reviewed common export
- [Interaction Evaluation](policies/experience/interaction-evaluation.md): reusable interaction continuity and UX checks

- [Work-Grounded Learning](policies/project/work-grounded-learning.md): reviewed
  packets, provenance, personal attempts, scheduling and learning home;
  [Code And Command Learning](policies/project/code-command-learning.md) owns
  exact scenes, question depth and daily selection;
  [Personal Learning data](policies/project/data-model/personal-learning.md) owns
  the durable tables. The Plans Index links its PRD and Feature chain.

- [Desktop App And Common Local Settings](policies/project/desktop-app-and-settings.md): settings, source identity/lifecycle, synchronization and recovery contracts
- [In-App Documentation](policies/project/app-documentation.md): bundled English user-guide ownership, /help routes, reader and shared Markdown link authority, packaging and privacy
- [macOS Test Distribution Guide](policies/project/standalone-test-app-guide.md): artifact-specific first launch, manual replacement, environment evidence and recipient-validation limits

## Feature Contracts And Development Operations

[Product Model](policies/project/product.md#feature-contracts) maps product domains;
[Architecture](policies/project/architecture.md#current-capabilities-and-owners)
maps runtime responsibilities. Their detailed current contracts are:

| Area | Owner |
| --- | --- |
| Native Session capture, revisions, repair and references | [Session Ingestion](policies/project/session-ingestion.md) |
| Session inventory, pins, Chart and detail | [Sessions](policies/project/sessions.md) |
| Direct usage, frozen cost/Project snapshots and dashboard | [Usage And Cost](policies/project/usage-and-cost.md) |
| Registered document collection/reading | [Local Context](policies/project/local-context.md) |
| Episode Focus and user assertions | [Session Workflow](policies/project/workflow.md) |
| Pure provisional candidate descriptors | [Workstream Candidates](policies/project/workstream-candidates.md) |
| Skill reach, evidence, frozen guides/reports and analysis | [Personal Insights](policies/project/personal-insights.md) |
| Local Atlassian memory and approved remote reads | [Atlassian](policies/project/atlassian.md) |
| Explicit simulation, passive affinity and sample inspection | [Auto Work](policies/project/auto-work.md) |
| Isolated model-free comparison | [Work Reconstruction](policies/project/work-reconstruction.md) |
| Quoted model protocols and diagnostics | [Work Context Inference](policies/project/work-context-inference.md) |
| Explicit model setup, comparisons, trials and replay | [Model Tool Operations](policies/project/development/model-tools.md) |

Runtime versions, supported legacy formats, immutable content fingerprints and
failure/migration conditions remain current contracts. Per-trial approvals,
consumed budgets and evaluation outcomes remain with their plans and records;
moving documentation grants no fresh execution or review authority.

## Design System

- [Creative Design Brief](../DESIGN.md): visual north star, source interpretation, and creative rationale
- [Design Constitution](policies/design/design-constitution.md): common tokens, layout, states and component/family law; linked [Chart](policies/design/surfaces/sessions-chart.md) and [Session reading](policies/design/surfaces/session-reading.md) companions own detailed screen contracts
- [Design Document Governance](policies/design/design-document-governance.md): design document ownership, source hierarchy, and update rules
- [Design Evaluation](policies/design/design-evaluation.md): reusable visual and screen-surface checks

## Agent Package

- `docs/agents/roles/`: planning, build, evaluation, orchestration, and fix role contracts
- `docs/agents/flows/`: default baton flow and stop points
- `docs/agents/operations/`: prompts for starting and continuing a Run, plus Harness Improvement procedures
- `docs/agents/profiles/`: frontend, backend, fullstack, foundation, infrastructure, and docs profiles
- `docs/agents/templates/`: reusable operator-facing briefing and blank harness experience scaffolds
- `docs/agents/schemas/`: shared Improvement Record metadata schema
- `docs/evidence/`: ignored local harness experience outputs and separately selected public references; [Harness Experience](agents/README.md#harness-experience) owns discovery and separation

## Plans

Project plans, sequencing, unresolved work, approvals, change history, and execution/evaluation records live under `docs/plans/`.

- [Plans Index](plans/README.md): open planning boundaries, active execution, recently completed chains, and artifact locations
- [Project Roadmap](plans/project/roadmap.md): phase direction, current priorities, validation strategy, and risk controls
- [Project Backlog](plans/project/backlog.md): detailed open work and decisions ordered by priority
- [Planning Artifact Catalog](plans/artifact-catalog.md): generated navigation for tracked PRD, Feature, Spec, Run, Evaluation, Fix, and heuristic artifacts
- `docs/plans/prd/`, `feature/`, and `spec/`: planning and implementation boundaries across their lifecycle
- `docs/plans/run/`, `evaluation/`, `fix/`, and `heuristic/`: execution and review artifacts
- `docs/plans/refactoring/`: scoped refactor tracks and their validation or merge-check logs
- [Design System Change History](plans/design/design-system-change-history.md): dated design changes; current visual rules remain in the Design Constitution
- [Harness Import History](plans/project/harness-import-history.md): repository import and local-detachment events; current refresh and compatibility rules remain in Agent Workflow

## Ownership Rules

- `README.md` owns the public product overview, installation entry and short first-use path; detailed screen usage belongs to the app guides above.
- `src/localbrain/content/docs/` owns the distributed app's user-guide bodies. Update the relevant guide with a public behavior change, following [In-App Documentation](policies/project/app-documentation.md).
- `AGENTS.md` routes contributors and agents without duplicating deeper contracts.
- `docs/policies/` owns current definitions, behavior, constraints, and operational contracts. Project approval, delivery, and evaluation chronology does not belong in policy bodies or appendices.
- `docs/plans/` owns project plans, priorities, unresolved work, approvals, changes, and execution/evaluation records, including completed historical facts. Records reference canonical current contracts rather than owning their definitions.
- `docs/agents/` owns reusable role, flow, operation, and execution-profile contracts.
- Machine-specific workflow inventories and handoff context stay outside Git and must not become dependencies of tracked documentation.

When a fact changes, update its owner document and replace repeated explanations elsewhere with a link.
