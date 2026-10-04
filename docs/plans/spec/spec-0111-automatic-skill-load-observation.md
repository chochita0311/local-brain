# SPEC-0111: Automatic Skill Load Observation

## Metadata

- ID: `spec-0111`
- Status: `approved`
- Feature: [FEAT-0111](../feature/feat-0111-automatic-skill-load-observation.md)
- Parent PRD: [PRD-0005](../prd/prd-0005-workflow-and-skill-intelligence.md)
- Run: [RUN-138](../run/run-20261002-138-automatic-skill-load-observation.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: `data`, `backend`, `frontend`, `docs`
- Created: `2026-10-02`

## Historical Projection

Continuity, 2026-10-03: [SPEC-0112](spec-0112-session-skill-use-estimate.md) supersedes the displayed load projection with a bounded use estimate, preserving this spec's load evidence.

The current use/reference Session projection is owned by [FEAT-0113](../feature/feat-0113-skill-reference-session-count.md).

## Admission And Identity

- Preserve explicit native signals. Add `claude_skill_read` and `codex_skill_read` for completed reads of literal paths ending in `SKILL.md` with a native call ID and recognizable returned skill front matter.
- Support Claude `Read`, shell `cat`, `sed` without in-place editing, `head`, `tail` and `nl`, and static `tools.exec_command({cmd: ...})` literals inside Codex `exec`. Parse literals without evaluating JavaScript or shell commands. Variables, interpolated paths, arbitrary code and mere mentions are outside this bounded extractor.
- Correlate returned content to the requested skill path/name. A successful enclosing script alone is insufficient for a failed nested read. Pending, missing, empty or failed results do not count.
- Add optional bounded `request_key` to `ParsedSkillObservation` and the ledger. Use native Codex turn IDs or Claude user-request identity; fall back to retained user-message identity when native turn metadata is absent. Unknown request scope leaves `request_key` null.
- Keep native call ID, normalized skill name and locator for read evidence. One call can read multiple skills; its read observations have distinct skill identities. Existing explicit native-event deduplication still prevents rewritten names from duplicating old events.

## Persistence And Projection

- Upgrade the bounded signal CHECK and add `request_key` through a transactional, row-preserving compatible migration. Keep observations independent of Session/Source deletion.
- On backfill, attach a known request key to existing native observations without changing their validity, time, original name or opaque ID. Insert only new read evidence. Bump only Session extraction versions.
- Derive counts from distinct `(source_key, external_session_id, request_key, skill_group_key)` groups. Null request keys fall back to native-event identity. Retain individual evidence; do not invalidate valid observations merely because they belong to the same request.
- Use the newest admitted timestamp for the last observed load. The ranking remains a database projection, with no transcript reread on GET.
- Preserve correction, maintenance exclusion, historical retention, source coverage and Usage pricing behavior.

## Visible Contract

Use observed-load wording in the existing Insights skill column, including heading, count, last-load label, empty states and a short explanation that skill-file reads are included. Do not imply that a load proves application or benefit. Keep existing navigation, controls and layout tokens.

## Validation And Limits

Meaningful synthetic tests cover success/failure, nested execution, mentions/edits, split reads, same-request context/read overlap, later requests, multi-skill calls, migration preservation, incremental replay and maintenance. Browser review covers actual updated wording, containment and navigation. Runtime backfill uses existing local sources after validation; no analysis service or paid Run is involved.

This is a bounded observable-load count. Dynamic or unsupported readers and source files that disappeared before observation cannot be reconstructed. Inspection reads with admitted evidence are included.

## Open Blockers

- None for the owner-approved boundary.
