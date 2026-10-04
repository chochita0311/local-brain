# SPEC-0113: Skill Reference Session Count

## Metadata

- ID: `spec-0113`
- Status: `approved`
- Feature: [FEAT-0113](../feature/feat-0113-skill-reference-session-count.md)
- Parent PRD: [PRD-0005](../prd/prd-0005-workflow-and-skill-intelligence.md)
- Run: [RUN-140](../run/run-20261004-140-skill-reference-session-count.md)
- Execution Profile: `fullstack-product`
- Surface Lanes: `data`, `backend`, `frontend`, `docs`
- Created: `2026-10-04`

## Extraction And Projection

Replace application-phrase detection with exact known skill identifiers in normalized visible user/assistant messages. Names and unambiguous plugin aliases come from native invocation/context or successful instruction reads within the same Session. Availability catalogs, generated instructions and tool-output text are not conversation references; current installed skills do not rewrite history. Identifier matching is independent of surrounding language and does not classify examples, intent, negation or use verbs. A named discussion is a reference.

Identify literal script executions within a known skill's `scripts/` directory from completed Codex CommandExecution records or completed Claude Bash calls. Inspect the executable or supported interpreter's script argument; a file read or command string example is not an execution. Resolve only literal paths from recorded working directories and skill locators; never execute logged commands. Dynamic/unsupported commands and heredoc bodies are excluded; supported executions around those bodies may be missed.

Add mention/script signal values through the existing row-preserving ledger migration. Retain old declaration observations as historical named references, but generate no new declarations. Preserve per-event/request provenance. Project all valid evidence once per `(source_key, external_session_id, skill_group_key)`, regardless of request or signal. Existing `use_count` denotes Session count and `last_used_at` denotes the latest admitted reference timestamp for consumer compatibility. GET remains a database projection. Advance only Session parser versions for backfill and future syncs; preserve Usage prices and attribution.

## Visible Contract And Limits

Keep the current Insights layout and controls; show use/reference Session wording, Session units and the maximum-one-per-Session rule. Repeated reads cannot inflate a skill's count within a Session. Reads/discussions across distinct Sessions can contribute, so this measures reach/reference rather than successful application or execution frequency. Available-file coverage and historical retention remain visible. Review contract first, then served output, desktop/narrow containment and reciprocal navigation. Do not add or run automated tests without an owner request.

## Open Blockers

- None; the current owner approval fixes this boundary.
