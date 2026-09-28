# SPEC-0105: Skill Observation And Retention

## Metadata

- ID: `spec-0105`
- Status: `approved`
- Parent Feature: [FEAT-0105](../feature/feat-0105-skill-observation-retention.md)
- Parent PRD: [PRD-0005](../prd/prd-0005-workflow-and-skill-intelligence.md)
- Surface: `data`
- Execution Profile: `foundation-contract`
- Created: `2026-09-27`
- Updated: `2026-09-27`

## Implementation Goal

Persist each distinct admitted skill load as a local historical observation that survives the disappearance of its source Session and can be incrementally extended on resumed source files.

## Source And Identity Contract

- Claude: admit only assistant `tool_use` entries named `Skill` with a non-empty `input.skill` and native `tool_use.id`.
- Codex: admit only generated `response_item` user messages with a complete `<skill>` wrapper, one non-empty `<name>`, a `<path>`, and native message `id`. The wrapper is a source-log load signal; it is not a claim that the skill succeeded or improved work.
- Exclude direct `SKILL.md` reads, literal `$skill` text, ordinary mentions, malformed wrappers, and records without native IDs.
- The stable insertion identity is source key plus native Session external ID plus native event ID. Check those three native fields before insertion so an older row that also included the normalized name in its hash cannot be counted again. Normalize display-group names by trimming surrounding whitespace and case folding; retain the original readable name and Codex locator separately.
- Preserve source key, provider kind, native Session ID, native event ID, source line, time, signal kind, name, optional locator, first-observed time, and validity state. Store no full prompt, tool input, skill body, or result in the ledger.

## Persistence And Sync

- Add an independent `skill_observations` table without a cascading FK to `sessions` or `sources`; its native source keys provide an optional current-Session lookup.
- Use an indexed unique observation key and `INSERT OR IGNORE` during the same source-file scan transaction. Repeated scans and file moves remain idempotent; a newly appended event inserts once.
- Increase the Claude and Codex Session parser contract versions so the next source sync reads currently available files once to backfill. A Session-only contract repair must not recalculate Usage Record prices.
- Insert only from work-class Sessions, including direct subsessions; exclude maintenance-class Sessions. Ordinary source deletion never deletes an observation. A later targeted correction may mark a proven erroneous row invalid without conflating source disappearance with invalidity.
- Retain `source_key` and native Session identity for later provenance work. The first ranking does not need a current-Session join or evidence link.
- A first sync with no admitted events is distinct from files that have not yet been rescanned under the new Session contract.

## Ownership And Dependencies

- Parser shape: `ingest/common.py`, `ingest/claude.py`, `ingest/codex.py`.
- Persistence and scan: `schema.sql`, `db.py` only if compatible migration is required, `ingest/scanner.py`, and a bounded skill-observation module.
- Semantic owners: Project Architecture and Workspace And Session Activity; regenerate the Schema presentation after source docs and DDL agree.
- FEAT-0106 consumes this contract only after it is accepted as passed.

## Evaluation Focus

- Stable native identity, source-scoped deduplication, one-time backfill, append-only changed Session handling, no source-deletion cascade, corrected-state allowance, and coverage distinction.
- Confirm the existing Usage Record source and price paths are not changed by the skill extractor.

## Open Blockers

- None for this bounded first-release contract.
