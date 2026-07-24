# FIX-0047: Session Source-File Evidence Cardinality

## Metadata

- ID: `fix-0047-session-source-file-evidence-cardinality`
- Status: `complete`
- Run ID: `run-20260723-52`
- Attempt: `2`
- Feature: [feat-0047-bounded-atlassian-url-evidence-extraction](../feature/feat-0047-bounded-atlassian-url-evidence-extraction.md)
- Spec: [spec-0047-bounded-atlassian-url-evidence-extraction](../spec/spec-0047-bounded-atlassian-url-evidence-extraction.md)
- Execution Profile: `foundation-contract`
- Surface Lane: source-backed reconciliation
- Created: `2026-07-23`
- Updated: `2026-07-23`

## Input Reports

- Evaluator report addressed: [Functional Attempt 1](../evaluation/eval-0047-functional-bounded-atlassian-url-evidence-extraction-attempt-1.md).

## Fix Scope

- Preserve one Session as the evidence owner while allowing every contributing JSONL source path to retain an independent extractor fingerprint and sighting lifecycle.
- Remove scan/sighting rows for a disappeared source path without deleting the normalized Session or stable Atlassian Item.

## Changes Applied

- Session evidence scans are unique by `(session_id, source_path)` rather than Session alone.
- Session evidence rows retain the bounded source path as part of their source location and stable evidence key.
- Scanner skip lookup resolves current evidence by source ID plus source path, even when the Session row's latest source path belongs to another contributing file.
- Missing source-file reconciliation removes only scan/sighting rows for that path.
- Data-model owners, generated schema, cleanup audit, and focused tests were updated.

## Contract Or Lane Impact

- No Feature or Spec change. This is a cardinality correction inside the approved source-backed reconciliation lane.

## Remaining Issues

- None.

## Return Decision

- `re-evaluate`

## Continuity Notes

- `2026-07-23`: targeted implementation repair applied after the complete suite exposed a shared-Session multi-file regression.
