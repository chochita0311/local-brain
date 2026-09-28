# FEAT-0107: Personal Insight Evidence Manifest

## Metadata

- ID: `feat-0107`
- Status: `passed`
- Type: `foundation`
- Surface: `data`
- Execution Profile: `foundation-contract`
- Required Evaluators: `contract`, `functional`
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Created: `2026-09-27`
- Updated: `2026-09-28`

## Goal

Define one source-backed, bounded evidence manifest that a later personal AI-use analysis Run can consume without making a Workstream, model, or vendor the owner of Session evidence.

## Acceptance Contract

- The manifest producer accepts an explicit `ask` or `discover` mode, optional question text for `ask`, a source/time scope with its timezone, and a frozen request time. `ask` requires a nonempty question; `discover` has no question. Date filters apply to message event time in the selected timezone; events with unknown time cannot satisfy a bounded date filter. These inputs select evidence only and never invoke a model or alter Sessions.
- Eligible rows are currently stored `work` and `primary` Sessions with `full` index policy and their admitted message Activity Events. Maintenance, provider-internal, metadata-only, and standalone subsession content do not enter evidence. A future child-attribution rule must be approved separately.
- A manifest contains: contract version, input scope, selection method, generation time, eligible and selected Session counts, source/time coverage, truncation or missing-evidence reasons, and ordered Session and Activity Event references. Every included excerpt identifies the underlying source, Session, event, time when known, role, and a digest of the complete normalized message text. The raw text excerpt is private Run evidence, never tracked documentation or an aggregate-only claim.
- An event reference can be resolved back to its existing `/sessions/{id}` view while the source-backed Session remains available. Review compares current source identity, eligibility, Event order/time/role, and full-text digest with the frozen reference. A missing Session or Event is unavailable; changed evidence or eligibility is stale. Neither is silently treated as currently verified.
- The first hard bounds are 100 Sessions, 300 message excerpts, 600 characters per excerpt, and 120,000 excerpt characters overall. The selection reports eligible totals and why evidence was omitted. These limits are not an assertion that the sample is exhaustive; later on-demand expansion requires its own scoped contract.
- Selection is deterministic for the same database state, mode, scope, question, and contract version. `ask` combines existing Session text search with a declared time/source spread; `discover` deliberately spans sources and dates. A query with no relevant indexed match may return a spread sample only when its lack of lexical match is explicit; it never calls that sample question-relevant evidence.
- The producer reads normalized local Session and Activity Event data only. It neither opens native JSONL nor duplicates opaque tool input/output, and it performs no network or model call.
- No new statistics snapshot or persistence layer is required for this contract. A later Run may write the frozen manifest into its private runtime artifact directory; this Feature owns the value shape and selection behavior, not Run lifecycle or report generation.

## Scope Boundary

- In: eligibility, explicit scope normalization, representative bounded selection, stable evidence references and text revisions, source coverage, empty/partial/stale signals, value-shape documentation, and a read-only producer API for later Features.
- Out: classification of improvement types, repeated-pattern inference, report prose, any AI call, proactive scheduling, UI, user review state, edits to skill observations, Workstream membership, and native source parsing beyond current normalized messages.

## Contract Surfaces

- Producers and authority: `sessions`, `activity_events`, and `sources` from current local ingestion.
- Consumer: future PRD-0018 guide and analysis Run Features. The manifest is Run input evidence, not a saved user conclusion.
- Public value shape: versioned manifest with source and event references, coverage, bounded excerpt, and revision.
- Existing navigation: `/sessions/{id}` resolves inspectable Session evidence while available.
- Owner documentation: [Workspace And Session Activity](../../policies/project/data-model/workspace-and-session-activity.md), [Project Architecture](../../policies/project/architecture.md), and [Privacy And Data Handling](../../policies/project/privacy-and-data.md).

## Pass Or Fail Checks

- A mixed source/time selection admits only in-scope primary work message events and reports excluded or missing coverage without treating it as zero activity.
- Both modes produce a stable ordered manifest under their bounds, including when no event qualifies and when more than the hard limits qualify.
- Changing an Event's content or eligibility, or removing its Session, makes a previously frozen reference stale or unavailable when reviewed; ordinary reading does not rewrite the old manifest.
- Maintenance, metadata-only, provider-internal, and standalone child evidence cannot enter by a broad date or source query.
- No native JSONL, tool input/output, network call, model invocation, or Workstream relation is needed to produce the manifest.
- The contract has synthetic positive, negative, boundary, and privacy examples and no unresolved value-shape or ownership question before Spec handoff.

## Dependencies

- Approved PRD-0018 upper boundary. The model execution choice is not needed to define this source manifest.
- Current Claude/Codex Session ingestion and normalized message Activity Events remain the source authority.

## Regression Surfaces

- Session and subsession browsing, maintenance exclusion, skill-observation retention, local retrieval, Usage & Cost opening path, and existing Workstream Task Runner evidence selection.

## Harness Trace

- Spec: [SPEC-0107](../spec/spec-0107-personal-insight-evidence-manifest.md)
- Run: [RUN-20260927-118](../run/run-20260927-118-personal-insight-evidence-manifest.md)
- Execution profile: `foundation-contract`
- Latest evaluator reports: [contract](../evaluation/eval-0107-contract-personal-insight-evidence-manifest.md) and [functional](../evaluation/eval-0107-functional-personal-insight-evidence-manifest.md)

## Continuity Notes

- `2026-09-27`: proposed as the first independent foundation target after the owner asked to start the personal AI-use improvement analyzer. It establishes what the analysis may read before any guide, model, or UI Feature consumes private Sessions.
- `2026-09-27`: the owner directed work to continue after this first target and its approval choice were presented. The bounded evidence-only target is approved for implementation; the separate model-execution decision remains open for later Features.
- `2026-09-27`: the evidence-only Run entered implementation from the approved boundary. Contract and functional review remain open; the feature is not yet marked passed.
- `2026-09-28`: synthetic functional evaluation passed after correcting Unicode casefold excerpt offsets. The evidence-only contract is complete; no personal analysis model Run was started.
