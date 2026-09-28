# EVAL-0105 Functional: Skill Observation And Retention

## Metadata

- ID: `eval-0105-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Evidence Coverage: `complete`
- Run: [RUN-20260928-123](../run/run-20260928-123-skill-observation-retention.md)
- Attempt: `2`
- Feature: [FEAT-0105](../feature/feat-0105-skill-observation-retention.md)
- Spec: [SPEC-0105](../spec/spec-0105-skill-observation-retention.md)
- Execution Profile: `foundation-contract`
- Lane: `data`
- Created: `2026-09-28`

## Evidence And Finding

- `.venv/bin/python -m unittest discover -s tests -p test_skill_observations.py -v`: 8 passed. Claude `Skill` tool calls and generated Codex `<skill>` records with native IDs count; direct `SKILL.md` reads, mentions, and missing IDs do not.
- Repeated scan, source-path move, replay, and unchanged native ID add zero; one appended admitted event adds exactly one. A deleted source file or Session preserves prior counts. Matching names aggregate across Claude, Codex, and Codex Company; tied counts use stable name order, and missing last-use time remains unknown.
- Work subsessions count; maintenance rows are excluded or corrected. A targeted native-event correction invalidates only that event after the Session disappears and replay cannot reinsert it. Tracked files with 1/2 or 0/2 current extraction versions report partial coverage; 2/2 reports current, and no tracked files reports not scanned even when historical observations remain.
- `.venv/bin/python -m unittest discover -s tests -p test_parsers.py -q`: 16 passed. `test_session_sync.py`: 17 passed, including Session-contract backfill without Usage Record repair. `test_schema_migrations.py`: 29 passed. Compatible startup addition of the ledger and retained Session row is covered by the focused skill test.

## Limit And Route

All records were synthetic. The checks cover first-sync and incremental behavior without asserting that the owner's private source inventory has already been rescanned. Route `pass`.
