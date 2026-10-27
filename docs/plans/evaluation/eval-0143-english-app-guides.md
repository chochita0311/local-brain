# EVAL-0143: English App Guides

> Historical scope: this record describes the initial seven-guide increment evaluated on 2026-10-26. [FEAT-0144](../feature/feat-0144-canonical-product-docs.md) and [Run 208](../run/run-20261027-208-canonical-product-docs.md) own the current six-guide correction and later content follow-ups. Earlier evidence retains its original scope.

## Metadata

- Feature: [FEAT-0143](../feature/feat-0143-english-app-guides.md)
- Parent PRD: [PRD-0024](../prd/prd-0024-deployed-app-docs.md)
- Active Spec: `writing-contract-0143` — [Writing Contract](../feature/feat-0143-english-app-guides.md#writing-contract)
- Run: [Run 206](../run/run-20261026-206-english-app-guides.md)
- Attempt: 1
- Execution Profile: `docs-content`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `complete`

## Source And Content Contract

Compared all seven package-owned guide bodies with the PRD, current desktop/settings contract, existing app guide and screen templates. English prose retains current control labels where useful. No private examples, internal execution history or development-only feature guide was added.

| Topic | Preserved coverage |
| --- | --- |
| Getting Started | Supported-release caveat, model-free start, complete setup sequence, Next/Back/Skip/later behavior, saved-source persistence and first material. |
| Settings | All seven categories; local saved/default values; startup and time-zone timing; exact options and legacy-value preservation; Home versus record folder and custom-root eligibility; explicit source registration/reconnection/unregistration; independent completion-relative 10/30-minute schedules and Off preservation. |
| Dashboard | Source/date/metric scope, estimates and partial/unavailable values, Project work/subsession membership versus overall/history/MTD/projection/Source/Model totals, unassigned work and distinct grouping bases. |
| Sessions | List/Projects/Chart, filters, primary pins, native ID, messages versus tool events, child/parent navigation and current chart controls; observed activity does not establish Git ancestry or work causality. |
| Local Contexts | Explicit folder/file/optional Notes scope, permissions, reading/preview, supported formats, Spotlight-only PDF text, no OCR, derived-index removal versus preservation of registration/imported/original material. |
| Search | Model-free keyword/default AND semantics, explicit optional model download/preparation/cancel/disable, local queries/documents, network and space requirements, distinct readiness/partial/failure/no-result states, explicit keyword switch and original evidence links. |
| Recovery | Correct data/cache paths, complete backup inclusion/exclusion lists, same installation/Mac/schema constraints, explicit replacement/restart/recovery copy, inactive cache cleanup, close versus quit and data-preserving app replacement. |

Home's optionality with an explicit custom record folder was made explicit during review. Detailed registration, model preparation and restore procedures each have one owning page; related pages link to them. Developer-only source/storage/protocol mechanics are excluded by request scope rather than paraphrased into product promises.

## Functional Evidence

- Shared-renderer and page tests pass, including all registered guide and fragment links, first-use access, bounded missing/empty content and preserved default source-authored link behavior.
- The seven bodies are 340–842 words each; the longer Settings page begins with a category/saving summary and section links. No required condition was removed to force a word count.
- Final wheel bytes match all seven bodies. All six guide tests also pass against an extracted, relocated wheel, with every imported LocalBrain module coming from that package rather than the checkout.
- Actual browser integration, keyboard, viewport and offline evidence is owned by [Run 207](../run/run-20261026-207-app-docs-reader.md).

## Limits And Route

Primary-agent review, not independent certification. Release-specific signing, supported-Mac validation and a rebuilt native app are not established by content checks. Pass the authored guide set to the reader's final integration evaluation.
