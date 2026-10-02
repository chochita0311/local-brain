# RUN-20261002-137: Insight Closeout Corrections

## Metadata

- ID: `run-20261002-137`
- Status: `passed`
- Feature: [FEAT-0110](../feature/feat-0110-executable-personal-insight-runs.md)
- Parent PRD: [PRD-0018](../prd/prd-0018-personal-ai-use-improvement-insights.md)
- Active Spec: [SPEC-0110](../spec/spec-0110-executable-personal-insight-runs.md#approved-closeout-corrections)
- Execution Profile: `fullstack-product`
- Surface: `data`, `backend`, `frontend`, `docs`
- Required Evaluators: `contract`, `functional`, `design`, `ux-heuristic`
- Created: `2026-10-02`
- Current Phase: implementation, runtime application and publication review complete

## Trigger And Boundary

The owner approved the three closeout corrections and exact GPT-6.1 Sol price registration, including calculation of retained unpriced usage. This bounded continuation exposes existing analysis cost, corrects shared narrow-screen containment, reconciles eight stale regression expectations with their authoritative contracts, and extends the existing Usage price registry. Broader analyzer options and the ordinary-work intervention trial remain separate.

The primary owns requirements, implementation, persistence and semantic review. Existing unrelated edits and saved product reports are preserved. No paid analysis is part of verification.

## Surface Lanes And Checks

- Data/backend: add immutable GPT-6.1 Sol Standard/Fast rates effective 2026-09-29, including its distinct cached-input price; backfill only eligible previously unpriced records, preserving usage identity, tokens, attribution and already-priced records. Synthetic tests establish date/tier/context boundaries and idempotency before runtime application.
- Backend/frontend: read a Run's normalized Usage record and frozen price basis without recalculating on GET; display estimated cost or an explicit missing/partial/failed state separately from a CLI-reported amount.
- Frontend: correct the shared document minimum width with classic scrollbars; check Insights and peer Usage & Cost and Auto Work surfaces at 320px and desktop widths, including disclosure keyboard behavior and download access.
- Docs/generated contracts: retain executable schema and semantic owners; update the explicit schema baseline and admit reviewed public documentation citations while excluding private/runtime URLs. Rebuild/check the derived schema artifact and verify existing consumers.

## Price Evidence

- [GPT-6.1 Sol model](https://developers.openai.com/api/docs/models/gpt-6.1-sol): Standard input/cache-read/output per million tokens is $2/$0.10/$10; Fast is 2x; above 272,000 input tokens the full request uses 2x input/cache and 1.5x output rates.
- [OpenAI changelog](https://developers.openai.com/api/docs/changelog): release and initial pricing effective 2026-09-29.
- Inspected 2026-10-02 using OpenAI Docs. These are API-equivalent estimates, not subscription billing. Existing model selections are unchanged.

## Outcome

The [contract](../evaluation/eval-0110-contract-closeout-corrections.md), [functional](../evaluation/eval-0110-functional-closeout-corrections.md), [design](../evaluation/eval-0110-design-closeout-corrections.md) and [UX](../evaluation/eval-0110-ux-closeout-corrections.md) evaluations pass with complete coverage of the approved correction. The initial affected regression set has 216 tests; the entire repository suite was not run at that point. Chrome confirms 18 report/peer viewport combinations, four expanded-price-settings cases, native keyboard disclosure and retained download behavior. No new paid analysis ran. The later [publication review](#post-run-publication-review--2026-10-02) records the full-suite check separately.

The actual missing-model records were priced using retained evidence and independently checked arithmetic. Existing rates, other-model Usage rows, product Runs and reports remain unchanged; repeating the backfill changes zero rows. The local server was restarted with its environment captured only in memory, and health/report/download checks pass. The initial restart preflight expected module-style invocation; it was corrected to admit the installed direct Uvicorn script before any runtime mutation.

The original eight failed expectations are resolved. Wider consumer checks identified two further stale counts for the existing value families and Schema explorer; those now match the same canonical owners. The shared sizing correction reuses an already-established containment rule, and cost presentation uses existing metric/state patterns. No reusable policy addition or extra owner decision is required.

Final repository checks pass: Data Model parity, generated schema and value dictionaries, artifact catalog, whitespace, privacy across 1,150 candidate files, and 1,397 local document links/anchors. A final server restart refreshes the generated value-registry cache while preserving the completed repair and all retained product Runs.

## Preservation And Next Use

Private diagnostics and the scoped runtime before-image backup belong to `personal-insight-evaluations/eval-20261002-137` under the [archive owner](../../policies/project/developer-guide.md#personal-improvement-analysis). They preserve failed/intermediate checks as well as final evidence. Temporary browser profiles and task scratch are removed after archival verification. The replacement server's active log belongs to the runtime `server-logs` owner.

The completed repair items leave the [backlog](../project/backlog.md#personal-improvement-insights); the bounded ordinary-work intervention trial and later analyzer choices remain open. These checks establish implementation correctness within the stated scope, not provider billing or recommendation benefit.

## Post-Run Publication Review · 2026-10-02

The owner requested subagent review with docs-structuring and docs-shaping, consolidation of the session's work, and commit/push. A read-only reviewer examined all 75 session Markdown documents and guide resources, their catalog coverage, and the related durable owners. Incremental structuring and bounded reshaping preserve the existing ownership: README and Product Model explain current use, FEAT-0108/0110 and their Specs state accepted contracts, RUN-125 through RUN-137 retain execution and evaluation history, and the backlog owns the remaining work. No additional summary artifact or document split is needed.

The review corrected the Product Model's stale four-playbook description to the current eleven-playbook contract and explained independent analysis accounting. Data Model diagrams now include the optional application relationship between an insight Run and its metadata-only accounting Session, with no physical Run FK or Maintenance Run ownership. Value producers and consumers include the analysis accounting path. The docs entrance no longer hard-codes a stale subject count, and SPEC-0108 separates historical comparison limits from the subsequent owner-started product observation.

The first full-suite pass found two additional schema-audit parity failures: its decision inventory omitted the existing `skill_observations` and `personal_insight_runs` tables. The current decision source and generated ledger now cover 697 objects: 45 tables, 515 columns, 51 indexes, 57 physical relations and 29 application relations. Existing decisions are preserved; the six new timestamp entries join the existing deferred contract. The July audit narrative is explicitly historical, and no cleanup migration or new deferred-work approval is implied.

Final checks use the repository virtual environment with `PYTHONPATH=src` and `PYTHONDONTWRITEBYTECODE=1`:

| Check | Final result |
| --- | --- |
| `python -m unittest discover -s tests -v` | 1,023 tests; no failures or errors, three skips with the existing `optional semantic runtime` reason |
| `python scripts/check-data-model-docs.py` | Pass: 44 ordinary tables plus one FTS5 object, ten subject owners |
| `python scripts/build-schema-presentation.py check` | Pass: generated manifest matches the implementation and semantic owners |
| `python scripts/build-data-model-value-dictionaries.py check` | Pass: all ten generated dictionaries are current |
| `python scripts/build-plan-artifact-catalog.py check` | Pass: generated planning navigation is current |
| `python scripts/check-schema-cleanup-audit.py --check` | Pass: 697 objects, `keep=585`, `change=0`, `remove=0`, `defer=112` |
| `node scripts/check-data-model-mermaid.mjs` | Pass: ten ERD diagrams parse |
| `./scripts/check-repo-privacy.sh` | Pass: 1,150 candidate files |
| Changed Markdown local links/anchors and `git diff --check` | Pass |

This publication check adds full regression and document evidence to the earlier bounded 216-test and 18-browser-combination evaluation; it does not replace that historical receipt or rerun its browser checks. No paid analysis or runtime mutation occurs during this review. Historical failed attempts, partial behavioral passes and the unverified adoption/benefit boundary remain intact. Task-owned publication scratch is temporary; the durable commands and outcomes are recorded here.
