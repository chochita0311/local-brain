# EVAL-0046: Atlassian Source Item Identity And Freshness Contract — Functional

## Metadata

- ID: `eval-0046-functional`
- Status: `complete`
- Evaluator Type: `functional`
- Result: `PASS`
- Run ID: `run-20260723-51`
- Attempt: `1`
- Feature: [feat-0046-atlassian-source-item-identity-and-freshness-contract](../feature/feat-0046-atlassian-source-item-identity-and-freshness-contract.md)
- Spec: [spec-0046-atlassian-source-item-identity-and-freshness-contract](../spec/spec-0046-atlassian-source-item-identity-and-freshness-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: fresh/upgrade persistence → identity/outcome matrix → normalization/FTS/recovery → complete regression
- Evidence Coverage: `complete`
- Created: `2026-07-23`

## Scope

- Evaluated fresh and upgraded databases, manual and URL stubs, cross-boundary identities, aliases, collisions, coverage, freshness clocks, result outcomes, metadata/content boundaries, normalization formats, FTS write suppression and rebuild, explicit purge, generated artifacts, privacy, and complete regressions.

## Checks And Evidence

- Twenty-one focused Atlassian tests passed. They cover URL normalization and same-Site reuse, same URL across Source Instances, multiple Sites per Source Instance, identical remote IDs/keys across Sites, strict one-to-one manual binding, automatic manual Resource reuse, canonical aliases, remote/URL collision rollback, Space containment, freshness state and exact due boundaries, first-success identity requirements, partial metadata merge, recursive body rejection, bounded failure codes, Jira and Confluence content, coverage mismatch rollback, explicit downgrade, no-change write suppression, unavailable retention, stale-without-body, FTS rebuild, Site restriction, and purge cleanup.
- Three migration paths passed: exact row/relation preservation and repeat safety, unexpected shape/index/target refusal, and file-backed startup with a valid non-overwriting pre-migration backup.
- Successful changed Jira ADF and Confluence storage HTML produced deterministic inert normalized text and one indexed FTS row. Reapplying an unchanged body preserved both the content row values and FTS row identity exactly.
- Changed indexed results without an eligible body became stale without deleting prior state. Unavailable results retained the exact content and FTS row while advancing last-attempt evidence.
- Reference/metadata coverage rejected ineligible facts inside the application savepoint, so even preceding identity binding rolled back. Explicit indexed downgrade removed content/FTS, and a later indexed refresh rebuilt them.
- Manual Resources retained their original title, summary, source role, URL, ID, and relations through source-specific binding and canonical URL change.
- Schema/document parity, all nine Mermaid diagrams, deterministic schema presentation, the 448-object cleanup audit, repository privacy, Python compilation, and whitespace checks passed.
- The complete Python suite passed 225 tests.

## Evidence

- Commands:
  - `uv run python scripts/check-data-model-docs.py`
  - `node scripts/check-data-model-mermaid.mjs`
  - `uv run python scripts/build-schema-presentation.py check`
  - `uv run python scripts/check-schema-cleanup-audit.py --check`
  - `uv run python -m unittest discover -s tests -v`
  - `./scripts/check-repo-privacy.sh`
  - `git diff --check`
- Environments checked: SQLite `:memory:`, temporary file-backed databases and backups, deterministic synthetic provider results, deterministic UTC clocks, and the package-generated schema consumer.

## Evidence Gaps

- None for FEAT-0046's approved synthetic foundation contract.
- Live Atlassian access, actual company Sites/Items, Session or Local Context URL evidence, visible registration/refresh/search surfaces, and browser interaction remain outside this Feature.

## Findings

- None remaining.

## Regression Notes

- One pre-existing Starlette template deprecation warning remains unrelated and non-blocking.
- No external request or model process ran during implementation or evaluation.

## Route

- Next action: `pass` and return FEAT-0046 to the Orchestrator for human acceptance; keep FEAT-0047 through FEAT-0050 draft until separately approved.
