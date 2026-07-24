# EVAL-0047: Bounded Atlassian URL Evidence Extraction — Functional

## Metadata

- ID: `eval-0047-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260723-52`
- Attempt: `2`
- Feature: [feat-0047-bounded-atlassian-url-evidence-extraction](../feature/feat-0047-bounded-atlassian-url-evidence-extraction.md)
- Spec: [spec-0047-bounded-atlassian-url-evidence-extraction](../spec/spec-0047-bounded-atlassian-url-evidence-extraction.md)
- Execution Profile: `foundation-contract`
- Surface Lane: parser fixtures → evidence lifecycle → scanner integration → complete regression
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated Claude/Codex visible and approved-result extraction, recognition, Source/Site ambiguity, Session and Document reconciliation, changed/unchanged/removed state, maintenance/subsession exclusion, multi-file Session compatibility, generated schema, privacy, and complete regressions.

## Checks And Evidence

- Eight focused parser/evidence tests passed, covering visible URLs, approved and unapproved calls, bounded remote ID/title, key-only and Space rejection, configured Jira/Confluence recognition, ambiguity, idempotent reuse, evidence removal with Item retention, source locations, maintenance/subsession exclusion, configured-Site invalidation, Context skipping/reconciliation, and disabled-root cleanup.
- The pre-existing shared-Session multi-file regression test now proves that two current JSONL files retain independent evidence scan fingerprints and both skip after source-contract repair.
- Repeated evidence retains one row identity. Changed or removed Document content replaces only that Document's sightings. Site configuration changes cause a local re-evaluation without external activity.
- Schema/document parity, nine Mermaid diagrams, deterministic presentation, the 489-object cleanup audit, privacy, compilation, and whitespace checks passed.
- The complete Python suite passed 233 tests.

## Evidence Gaps

- None for FEAT-0047's approved synthetic foundation contract.
- Live Session company content, live Atlassian access, model calls, and visible evidence navigation remain outside this Feature.

## Findings

- None remaining.

## Regression Notes

- One pre-existing Starlette template deprecation warning remains unrelated and non-blocking.
- No external request or model process ran.

## Route

- Next action: `pass` and return FEAT-0047 to the Orchestrator; FEAT-0048 is now dependency-ready.
