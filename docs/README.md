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
- [Data Model](policies/project/data-model.md): complete effective SQLite map, global and subject ERDs, table/column catalogs, relationships, lifecycle, recovery, and delta maintenance ownership
- [Schema Presentation](policies/project/schema-presentation.md): deterministic package manifest, source ownership, loader/failure behavior, and downstream Schema consumer contract
- [Privacy And Data Handling](policies/project/privacy-and-data.md): repository boundary, local persistence, external access, and disclosure constraints
- [Developer Guide](policies/project/developer-guide.md): setup, configuration, development workflow, and verification
- [Markdown Rendering Contract](policies/project/markdown-rendering.md): shared syntax, trust, local-reference, highlighting, consumer, and fallback rules
- [Maintenance Task Runner](policies/operations/claude-task-runner.md): in-app Claude/Codex maintenance execution, retrieval, external-sync boundaries, persistence, and review behavior
- [Harness Policies](policies/harness/): planning approval, execution routing, profiles, surface lanes, and traceability
- [Interaction Evaluation](policies/experience/interaction-evaluation.md): reusable interaction continuity and UX checks

## Design System

- [Creative Design Brief](../DESIGN.md): visual north star, source interpretation, and creative rationale
- [Design Constitution](policies/design/design-constitution.md): durable tokens, layout rules, state-to-UI mapping, and component contracts
- [Design Document Governance](policies/design/design-document-governance.md): design document ownership, source hierarchy, and update rules
- [Design Evaluation](policies/design/design-evaluation.md): reusable visual and screen-surface checks

## Agent Package

- `docs/agents/roles/`: planning, build, evaluation, orchestration, and fix role contracts
- `docs/agents/flows/`: default baton flow and stop points
- `docs/agents/operations/`: prompts for starting and continuing a Run
- `docs/agents/profiles/`: frontend, backend, fullstack, foundation, infrastructure, and docs profiles

## Plans

Sequencing and unresolved work live under `docs/plans/`.

- [Project Roadmap](plans/project/roadmap.md): phase direction, current priorities, validation strategy, and risk controls
- [Project Backlog](plans/project/backlog.md): detailed open work and decisions ordered by priority
- [UI Design-System Realignment PRD](plans/prd/prd-0001-ui-design-system-realignment.md): passed PRD with fourteen accepted Feature runs, evaluation and fix evidence, and a deferred nonblocking graphical-regression follow-up
- [Session Browsing And Subsession Organization PRD](plans/prd/prd-0002-session-browsing-and-subsession-organization.md): passed boundary for source-neutral Subsessions, Session-owned branch metadata, combined navigation, paginated inventory, conversation-focused detail views, and Session-only synchronization
- [Data Model Visibility And Schema Cleanup PRD](plans/prd/prd-0003-data-model-visibility-and-schema-cleanup.md): passed boundary for local Mermaid, the complete 20-table plus FTS5 baseline, deterministic presentation, `System > Schema`, audited cleanup decisions, and approved schema-maintenance migrations
- [Session Usage And Cost Dashboard PRD](plans/prd/prd-0004-session-usage-and-cost-dashboard.md): passed boundary for source-neutral Usage Records, estimated trend cost, activity and Project attribution, responsive history, composition, and trust
- [Workflow And Skill Intelligence PRD](plans/prd/prd-0005-workflow-and-skill-intelligence.md): draft boundary for evidence-backed personal workflow patterns, repeated-process analysis, skill use, and reviewable skill suggestions
- [Markdown Reading And Context Continuity PRD](plans/prd/prd-0006-markdown-reading-and-context-continuity.md): passed boundary for shared safe Markdown, source-local references, Local Context preview and full reading, Session conversation rendering, and navigation continuity; image and attachment rendering remains deferred
- [Atlassian Source Memory And Explicit Refresh PRD](plans/prd/prd-0007-atlassian-source-memory-and-refresh.md): passed boundary for read-only MCP capability policy, source-neutral maintenance synchronization, stable Atlassian identity and freshness, URL evidence, registration, explicit refresh, local browse/search/classification, and URL-first connection onboarding
- [Connected Atlassian Validation And Schema ERD Routing PRD](plans/prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md): draft next-session boundary for connected Atlassian first-use validation and official Mermaid ELK orthogonal-routing evaluation
- `docs/plans/prd/`, `feature/`, and `spec/`: planning and implementation boundaries across their lifecycle
- `docs/plans/run/`, `evaluation/`, `fix/`, and `heuristic/`: execution and review artifacts

## Ownership Rules

- `README.md` explains what LocalBrain is and how to start it.
- `AGENTS.md` routes contributors and agents without duplicating deeper contracts.
- `docs/policies/` owns facts that should remain true across implementation cycles.
- `docs/plans/` owns facts expected to change as work is completed or reprioritized.
- `docs/agents/` owns reusable role, flow, operation, and execution-profile contracts.
- Machine-specific workflow inventories and handoff context stay outside Git and must not become dependencies of tracked documentation.

When a fact changes, update its owner document and replace repeated explanations elsewhere with a link.
