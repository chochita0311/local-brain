# PRD-0024: Deployed App Docs

## Metadata

- ID: `prd-0024`
- Status: `in-loop`
- Owner role: `human`
- Created: `2026-10-26`
- Updated: `2026-10-27`
- Planning role: `PRD Normalizer`
- Approval boundary: The owner requested proceeding with English Docs on 2026-10-26, authorizing this bounded increment and its necessary app integration. The later 2026-10-27 closeout request authorizes committing and pushing session-owned source/documentation after review and checks. Native app/ZIP distribution remains separate.

## Request Summary

Provide a small set of English Docs that helps users set up the distributed LocalBrain app and understand its main screens. Place **`Docs` immediately above Settings** in the app navigation and let users read it inside the app. Explain settings scope, Sessions Dashboard, Sessions, Local Contexts, and related usage without excessive length or complexity.

The original request covered PRD authoring only. The subsequent instruction authorized English Docs and necessary in-app integration. The owner's 2026-10-27 correction selects six canonical guides, removes the Troubleshooting destination, per-guide Settings action and version badge, and requires preserving necessary information in the remaining feature guides. The later closeout authorizes the reviewed source/documentation push; it does not close the separate native distribution boundary.

## Source Set

Source links below that use a fixed Git revision preserve the referenced
pre-refactor implementation as historical evidence. Use the
[current contract map](../../policies/project/product.md#feature-contracts)
for present implementation ownership; the old source layout is not a live path.

| Source | Adopted scope and limits |
| --- | --- |
| User request and follow-up choices, `2026-10-26` | Cover only the distributed app, keep the content concise and proportionate, explain settings and main screens, and place Docs above Settings. Follow-up choices confirmed **reading inside the app** and **English**. |
| [ChatGPT Docs](https://learn.chatgpt.com/docs) | Reference its task-oriented organization into getting started, features, and configuration. Do not inherit its feature count or full navigation. |
| [Quartz Getting Started](https://quartz.jzhao.xyz/getting-started/) | Reference its concise introduction and links to the next relevant topics. This does not require adopting Quartz or building a documentation website. |
| [Desktop App And Common Local Settings](../../policies/project/desktop-app-and-settings.md) | Distributed-app boundaries, current settings categories and application timing, and source, synchronization, search, and recovery contracts. |
| [Existing App Guide](../../policies/project/standalone-test-app-guide.md) | User-facing evidence for first launch, setup, quitting, app replacement, and data storage. Do not transfer internal test distribution, build instructions, or development validation records into Docs. |
| [Shared App Shell](https://github.com/chochita0311/local-brain/blob/6e38b58dad017bf1d176a3cf4edf0099e8619fd9/src/localbrain/templates/base.html), [Settings Dialog](https://github.com/chochita0311/local-brain/blob/6e38b58dad017bf1d176a3cf4edf0099e8619fd9/src/localbrain/templates/_settings.html), [Packaged Edition Boundary](https://github.com/chochita0311/local-brain/blob/6e38b58dad017bf1d176a3cf4edf0099e8619fd9/src/localbrain/edition.py) | Draft-time navigation and exposed functionality: before this increment, the shell and packaged-route allowlist had no product Docs entry. The implemented state is owned by the delivery contract and Run 207. |
| [Sessions Dashboard](../../../src/localbrain/templates/sessions_dashboard.html), [Sessions](../../../src/localbrain/templates/sessions.html), [Session Detail](../../../src/localbrain/templates/session.html), [Local Contexts](../../../src/localbrain/templates/context.html), [Search](../../../src/localbrain/templates/natural-search.html) | Current screen names and user flows. Inspecting the development working tree does not establish that a particular distributed binary has been validated. |
| [Usage Contract](../../policies/project/data-model/usage-and-cost-records.md) | Usage and estimated-cost limitations and the meaning of Project aggregation. |
| [Design Constitution](../../policies/design/design-constitution.md), [Design Evaluation](../../policies/design/design-evaluation.md), [Interaction Evaluation](../../policies/experience/interaction-evaluation.md) | Consistency with the existing shell and reading surfaces, plus accessibility, navigation, and responsive review criteria. |
| [PRD Management](../../policies/harness/prd-feature-management.md), [Agent Workflow](../../agents/flows/workflow.md) | The sequence from draft to human PRD review and approval, then Feature boundary review. |

## Product Intent

New users must be able to use Docs as their sole guide to connect the sources they need and open or search their first Session or document. Returning users must be able to quickly find where a setting applies, when a change takes effect, and what to check when material is missing.

Docs describe **the distributed app the user is running**. Keep them focused on that app rather than expanding into the repository's full design, planning, and development knowledge.

## Confirmed Scope

- User documentation read inside the app, with a shared entry immediately above Settings.
- English for this PRD and the in-app Docs. Use recognizable current UI labels when directing users to screens and controls.
- First-use guidance, settings, Sessions Dashboard, Sessions, Local Contexts, search, and the necessary operation/recovery guidance within those feature pages.
- Concise explanations of settings meaning and scope, what users can do on each screen, the basic sequence, and relevant limitations.
- A small contents structure and body proportionate to the current public feature set. Do not create lengthy developer documentation or an exhaustive reference to internal options.

### Information Architecture

Provide **six pages in total, including Getting Started**, following the owner's 2026-10-27 correction. The table fixes this increment's content boundary; later regrouping that changes scope returns to planning.

| Page | Questions to answer and content boundary |
| --- | --- |
| **Getting Started · Docs Home** | What does the app do? Describe ordinary download, installation and launch, then a short sequence: connect needed sources → open collected material → run a first search. Include the remaining Docs contents and explain early that users can start without a model. |
| **Settings** | What can I change, where, and when does it apply? Summarize General, Session Sources, Local Context, Search Model, Synchronization and Storage, distinguishing source registration, synchronization, search preparation and storage scope. |
| **Sessions Dashboard** | How do I select a period and source, then read usage, estimated costs, trends, and Source/Model/Project composition? Briefly explain partial coverage, unavailable calculations, and the different Project scope. |
| **Sessions** | How do I use Sessions/Projects, List/Chart, source and path filters, pins, conversation detail, Session IDs, and subsessions? Explain basic chart navigation and the meaning of observed activity. |
| **Local Contexts** | How do I find and preview documents from connected folders, files, and optional Apple Notes? Explain supported material, permissions, reading status, and the consequences of unregistering a source. |
| **Search** | When should I use keyword or AI search? Explain eligible material, optional model download and preparation, opening originals through result evidence, and what to do when preparation is in progress, partial, failed, or a search returns no results. |

Give each detailed procedure, such as registration, model preparation, or restoration, one owning page; link to it from other pages. Settings owns option meaning, registration and Storage/backup/restore/cache guidance. Search owns preparation and readiness; Sessions and Local Contexts own material visibility; Getting Started owns installation, quitting and updates. There is no separate Troubleshooting destination.

### Settings Explanation Boundary

This draft interprets **settings levels** as the categories and application scopes visible to users. The following describes current behavior; it does not introduce a new settings hierarchy.

| Current category | Explanation users need |
| --- | --- |
| **General** | Startup screen and time zone are application preferences. Sessions is the default startup screen, and a new choice applies on the next app launch. Selectable time zones are `UTC` and `Asia/Seoul`; another valid previously saved zone remains until explicitly changed. Time zone affects displayed times and date-based aggregation on the next navigation or reload. It does not change original timestamps, the system clock, or synchronization intervals. General selections save automatically. |
| **Session Sources** | For Codex and Claude Code, explain Tool, profile name, agent Home versus the actual Session folder, default versus custom locations, explicit registration and saving, and confirmation when reconnecting the same profile at a new location. Choosing a path or a detected candidate only fills the form; registration is still required. The full Home is not collected. Unregistering excludes the source from collection and ordinary search while preserving imported records and originals; it can be registered again. |
| **Local Context** | Users explicitly connect the folders, files, and optional Apple Notes they need. Selection alone does not register a source; saving is explicit. Explain Notes permissions and supported-format and reading limitations. Unregistering requires confirmation, stops collection, removes the source from search/browsing and clears its search entries. Saved source details, imported documents, original files and Notes remain, and the source can be registered again. Internal cleanup of evidence for excluded integrations stays with its behavior owner. |
| **Search Model** | Default keyword search needs no model. Model download, manual preparation/retry, cancellation and disabling are user-initiated. A successful model download also starts AI preparation automatically. Model download requires internet access; queries and documents are not sent outside the machine. Opening Settings or Docs alone does not start model download or preparation. |
| **Synchronization** | Sessions and Local Context have independent schedules. Defaults are **10 minutes after Session collection completes and 30 minutes after Local Context collection completes**. Selecting `10 / 20 / 30 / 60 minutes / Off` automatically saves that schedule, takes effect at the next scheduling decision, and does not interrupt an active collection. Off preserves the saved interval and imported material; selecting minutes enables that schedule. Other valid saved intervals remain displayed until changed. |
| **Storage** | Explain actual data and cache locations, sizes, and the scope of backup, restore, and cache cleanup. Backups include the DB, app settings, and model registration metadata; they exclude original Session and document files, model weights, caches, logs, and external authentication information. Restore is limited to the same Mac and a backup with the current app's DB schema. It requires explicit replacement confirmation, applies on the next launch, and preserves a pre-restore copy. Cache cleanup targets only inactive derived material and preserves originals and public models. |

General settings use valid saved values and defaults only for missing fields. Session sources, search, and document registration retain their existing domain owners. Do not present developer environment-variable precedence or internal storage formats as settings levels users must understand.

Omit About and app-versus-data-format version explanations. Keep the fixed path-display explanation with conversation metadata in Sessions rather than Settings: `~` represents home, `~/…` its descendants, and paths outside home remain fully displayed. Saved locations and historical Project attribution remain unchanged.

### Reading Size And Presentation

- Write the content in English, as requested. Retain recognizable screen names such as `Sessions Dashboard`, `Sessions`, and `Local Contexts` when referring to the existing UI.
- Aim for **roughly 2–4 minutes to understand basic usage per page**. Use the sequence: title and short purpose → basic usage → relevant limitations → related Docs. Do not remove necessary conditions or cautions to meet a length target.
- Usually use 3–5 steps for a basic procedure and prioritize a short summary table for settings. Link to the relevant feature section for detailed conditions and recovery. Fixed word or card counts are not acceptance criteria.
- Preserve existing app navigation and provide compact Docs contents and a current-page indication within the content area. Keep the structure around two levels: home → article. Add section links only for longer pages; avoid accumulating additional navigation panels.
- Follow existing reading-width, typography, spacing, and emphasis rules. Use synthetic screenshots only when they help explain something; they are not mandatory for the first version.

### User Flows

1. **First use:** Docs above Settings → Getting Started → required-source registration guidance → register in the actual Settings dialog → inspect material in Sessions or Local Contexts → run keyword search without a model. Explain the setup sequence of Welcome → Sessions → Documents → Search and how to reopen Settings. Next saves inputs in the Session and Document steps; Back preserves drafts; Skip does not register a draft path. Final Start, final Skip, or Set Up Later completes setup. If the app quits before completion, setup opens again on the next launch and already saved sources remain.
2. **Understand a screen:** Docs → Sessions Dashboard / Sessions / Local Contexts → read its purpose, main controls, and limitations → open the actual screen. Links and Back navigation must let users continue exploring Docs.
3. **Understand a setting:** Docs → Settings → check scope, saving, and application timing → change it in the existing Settings dialog. Do not duplicate settings editors inside Docs.
4. **Check missing material or preparation:** Docs → the relevant Sessions, Local Contexts, Dashboard or Search guide → check registration, selected source or period, permissions, synchronization or model readiness → open the actual screen. Settings/Storage owns backup, restore and cache procedures. Do not describe status cards, buttons or recovery features that do not exist.

### Content Accuracy Requirements

- **Sessions:** The chart shows recorded activity, not actual Git ancestry or inferred work relationships. Pins target primary work Sessions. Do not equate displayed conversation messages with original tool-event counts.
- **Sessions Dashboard:** Costs are estimates calculated from local records and pricing evidence, not guaranteed bills. Do not describe unavailable calculations or partial coverage as zero. Project includes ordinary work Sessions and work subsessions only; visible overall usage, history and Source/Model composition retain eligible analysis and Maintenance usage. Internal month-to-date/projection aggregation remains unchanged but is outside the current screen guide because those values are not rendered. Explain ordinary work without attribution under the existing `프로젝트 미지정` (Unassigned project) label. Do not claim that Project attribution by Git root or launch folder is identical to the path grouping in Sessions or Chart.
- **Local Contexts:** Operation is limited to registered scope, readable formats, and permissions. PDF content requires text available through Spotlight; do not promise OCR. Distinguish unregistering from deleting originals.
- **Search:** Eligible registered primary work Sessions and readable Local Contexts are searchable. Subsessions are excluded from search and are opened through their parent in Sessions. Distinguish AI readiness from no results; switching to keyword search is the user's choice. Do not describe an automatic mode change on preparation failure or an empty result.
- **Synchronization and quitting:** Collect only registered material while the app is running. Preserve the existing manual synchronization action in Sessions. Completion does not force a refresh of the current reading view; reopening or reloading the view shows current material. Closing the window hides it; `⌘Q` quits the app and stops synchronization. Do not describe a separate AI-index scheduling setting.
- **Storage and updates:** Default local data and private cache locations are `~/Library/Application Support/LocalBrain` and `~/Library/Caches/LocalBrain`, respectively; actual locations are available in Settings. Distinguish personal backups from program distribution files. Fully quit before replacing the app. Replacing or deleting the app does not automatically delete personal data. Do not present cross-Mac transfer, changing storage locations while running, or automatic updates as available features.
- **Release state:** Supported environments, installation, first-launch guidance, and limitations must match the release containing the Docs. Do not generalize internal ad-hoc test instructions or developer-Mac validation into signing, notarization, or supported-OS validation for every public release. Adding Docs does not close existing unverified release acceptance items.

## Excluded Scope

- Guidance for development-only top-level Dashboard/learning, Workstreams, Auto Work, Atlassian, Insights, Session workflow, or Schema.
- API/DB/ERD references, source code, architecture, agent harnesses, PRD/Feature/Spec/Run artifacts, development, build, CI, operator deployment procedures, and internal validation history.
- Automatically inserting personal Sessions, documents, queries, or local setting values into content or examples.
- New settings, search, synchronization, or backup behavior; Project reassignment; data transfer; or automatic updates based on this PRD.
- A separate public Docs website, hosting or domain, Docs-specific search, AI chatbot, feedback server, CMS, multilingual support, version selector, or separate changelog portal in this first increment. Review these separately if needed.

## Uncertainty

| Item | Draft proposal / review point |
| --- | --- |
| Later page regrouping | The owner selected six pages in the 2026-10-27 correction. Revisit grouping only when actual usage justifies a scope change; preserve the small scale and distributed-app-only boundary. |
| Future settings levels | The requested increment explains existing general, per-source and per-function scope. Any new settings hierarchy requires a separate scope decision. |
| Installation wording for each public release | Finalize against that version's supported environment, signing, notarization, and first-launch evidence. This PRD does not decide the release method or resolve existing incomplete acceptance items. |

**Reading inside the app** and **English content** are selected through the user's follow-up requests and are no longer open items. The [delivery contract](../../policies/project/app-documentation.md) now fixes six /help guide routes, including the home, package-local content in src/localbrain/content/docs/, a fixed registry, shared Markdown rendering and release bundling. Existing API documentation remains separate.

## Constraints

- **In-app delivery:** Bundle the content, required styles, and assets with the release so ordinary reading needs neither internet access nor a model. Basic usage guidance must remain readable when external reference links are unavailable.
- **Release alignment:** Provide one set of Docs matching the running app. Update the relevant guidance in the same change whenever a public feature, UI, setting, or supported environment changes. A detailed version-selection UI is unnecessary.
- **Content ownership:** Establish one explicit canonical source for app-user guidance; use development contracts as factual references. Do not automatically publish the repository's entire `docs/` tree. The [delivery contract](../../policies/project/app-documentation.md) fixes the canonical location and packaging boundary.
- **Separation from personal material:** Docs are static app-provided guidance. Reading must not register or collect personal sources, download models, or automatically register Docs in Local Context or a personal search index. Use synthetic examples and images; add no external reading trackers.
- **Product boundary:** Docs and their in-app links must work in the packaged edition. Avoid addresses confused with API technical documentation and preserve restrictions on development-only features.
- **Design and execution boundary:** The implemented screen profile is **Frontend Product**. Its surface lanes are **Shared Navigation / Docs Contents and Reader / Narrow Viewports and Keyboard Navigation**. Documentation delivery uses foundation-contract; content authoring uses docs-content. Their child Features own the execution boundaries.
- **Verification:** Apply Design Evaluation, functional checks, and Interaction Evaluation during implementation. Check entry, contents, article links, Back navigation, opening Settings, long content, narrow layouts, focus, and offline reading in the installed app. Authoring this PRD does not mean those implementation checks have been performed.
- **Approval:** Do not proceed to Feature decomposition, Spec, implementation, or evaluation while this PRD is `draft`. Follow the human review sequence in [Agent Workflow](../../agents/flows/workflow.md).

## Acceptance Envelope

These are the child-Feature acceptance criteria. Actual results and evidence limits are owned by the linked Runs and evaluations below.

1. **Docs appears immediately above Settings** in the distributed app's shared navigation, and users can read contents and articles inside the app. First-time users with no sources or model can access it.
2. The selected small contents structure covers Getting Started, Settings, Sessions Dashboard, Sessions, Local Contexts and Search, with necessary operation/recovery details in their owning pages without exposing development-only features or developer documentation.
3. Getting Started lets a new user register only needed sources and open material or run keyword search. It must not imply that installing an AI model or configuring every setup step is mandatory.
4. Settings guidance accurately explains the six documented categories: scope, automatic versus explicit saving, application timing, and relevant restrictions. Users can find independent Session/Context schedules, original preservation, backup inclusions and exclusions, and restore conditions in the relevant topic. About is omitted; Sessions owns the short path-label explanation.
5. Screen guides pair representative usage flows with interpretation limits. Estimated costs, partial coverage, chart meaning, supported material and permissions, search preparation, and empty results match actual behavior.
6. Pages present a short purpose, basic sequence, and necessary limits first. Avoid repeating long procedures across pages; make required detail reachable through Docs links.
7. Contents, current-page indication, links, Back navigation, and Settings access work with a keyboard and narrow viewports. Preserve the app's navigation and reading rules, and link to actually available screens.
8. Required content, styles, contents navigation, and internal links work in the installed app with networking disabled. Reading starts no model action, personal-material collection, or external transmission.
9. Docs match the bundled app's feature scope and version-specific installation state. They do not depend on the source checkout or personal runtime material, and existing unverified release acceptance items remain separate.

## Candidate Features

The owner's instruction to proceed is applied to the bounded child Features below. Execute sequentially: delivery contract, English content, then reader integration. The content contract fixes the reading requirements before implementation; content does not depend on an unfinished reader.

| Candidate | Type and proposed profile | Single outcome and boundary |
| --- | --- | --- |
| **C01 · Distributed App Docs Delivery Contract** | foundation · foundation-contract | Fix the canonical user-content owner, product Docs versus API-documentation routes, release bundling and version alignment, and separation from personal material. Does not own detailed screens or the complete content. |
| **C02 · Docs Entry and Reading** | product · frontend-product | Let users navigate contents and articles from the entry above Settings and open actual screens or Settings. Covers shared-navigation, reading, and responsive lanes; depends on C01's delivery contract. |
| **C03 · Initial Release User Guidance** | product · docs-content | Provide concise first-use, settings, main-screen, and troubleshooting guidance within the current six-page structure. Align with existing behavior and release evidence, C01's content ownership, and C02's reading structure. |

## Continuity Notes

- `2026-10-26`: Created a new PRD for distributed-app-only Docs. The user required the entry above Settings and concise settings and screen guidance; seven pages and Korean-first content were initial draft proposals. A follow-up selected reading inside the app. Status remained `draft`; implementation, deployment, and existing release acceptance state were unchanged.
- `2026-10-26`: The user requested English. Rewrote this PRD in English and selected English for the in-app Docs, superseding the Korean-first proposal. The seven-page structure and settings-level interpretation remain subject to review. Other requirements and the `draft` approval boundary are unchanged.

- `2026-10-26`: The owner requested proceeding with English Docs. Accepted the existing seven-page increment and settings-scope interpretation for sequential execution, including the necessary in-app reader. C01 maps to FEAT-0141, C03 to FEAT-0143, and C02 to FEAT-0142. External publication, transfer and native distribution are not implied.

## Implementation And Review — 2026-10-26

- [FEAT-0141](../feature/feat-0141-app-docs-delivery-contract.md) / [Run 205](../run/run-20261026-205-app-docs-delivery-contract.md): delivery and shared-renderer authority fixed.
- [FEAT-0143](../feature/feat-0143-english-app-guides.md) / [Run 206](../run/run-20261026-206-english-app-guides.md): seven concise English guides authored and source-reviewed.
- [FEAT-0142](../feature/feat-0142-app-docs-reader.md) / [Run 207](../run/run-20261026-207-app-docs-reader.md): Docs entry, reading, Settings, setup access and compact layout integrated; local browser and package checks pass.
- All seven guides render at 1440px and 320px with external internet blocked and browser cache disabled. A relocated wheel passes all six guide tests. The full suite's five schema/value inventory failures reproduce without these Docs changes.
- Source/content integration is ready for human review. A new native app/ZIP and recipient-Mac execution were not produced or verified; existing release acceptance remains open. This PRD stays in-loop rather than implying final installed-binary or human acceptance.

## Canonical Product Docs Correction — 2026-10-27

The owner requested ordinary downloaded/installed-application documentation rather than development/private-machine framing. Remove Troubleshooting, the per-guide Open settings button and For LocalBrain version badge. Retain necessary facts in Settings/Storage, Search, Sessions, Local Contexts and Getting Started; preserve eligibility, timing, original protection and recovery conditions. Do not expose unfinished-feature lists or test/build instructions, and do not imply wider platform support through neutral terminology.

[FEAT-0144](../feature/feat-0144-canonical-product-docs.md), [SPEC-0144](../spec/spec-0144-canonical-product-docs.md) and [Run 208](../run/run-20261027-208-canonical-product-docs.md) own this correction. The earlier seven-guide implementation and evaluation remain historical evidence for that version, not current acceptance.

The [correction evaluation](../evaluation/eval-0144-canonical-product-docs.md) passes its content-preservation, six-page reader, authenticated desktop/narrow browser and package-content checks. Necessary recovery guidance is now feature-owned; the removed route has no packaged body. Human review and the existing native/recipient release boundary remain open.

## Subsequent Owner Review And Closeout — 2026-10-27

- Omit About and app-versus-data-format version prose from Settings, including its summary row and jump link. Retain the useful home-path abbreviation rule beside Session metadata, where it helps interpret displayed paths; saved locations and historical Project attribution remain unchanged.
- Two separately tasked subagents reviewed all six public guide bodies and the registry. Public-user scope and the six-topic ownership/reading structure were sound; no broad reorganization was needed. The owner authorized the reported factual corrections and plain-language cleanup.
- Search now distinguishes automatic preparation after a successful model download from manual preparation/retry for an installed model. It explicitly excludes subsessions from search and links to reading them through their parent in Sessions, preserving all existing eligibility and source exclusions.
- Settings and Local Contexts now state unregister confirmation, collection/search/browsing exclusion and search-entry cleanup, while retaining saved source details, imported documents, originals/Notes and re-registration. Internal cleanup for excluded integrations remains in its behavior owner rather than public app guidance.
- [Run 208](../run/run-20261027-208-canonical-product-docs.md) owns closeout checks and publication scope; the [evaluation](../evaluation/eval-0144-canonical-product-docs.md) distinguishes original evidence, follow-up corrections and final verification. No separate session log is created. Unrelated learning/schema work remains outside this session's commit.

## Documentation Index Reconciliation — 2026-10-31

The following preserves the detailed navigation snapshot relocated from the
Plans Index. Its dated execution/approval facts and evidence limits remain with
this owning record and its linked artifacts; it is not a new execution grant or
an update to unrelated acceptance. Current definitions remain in policy owners.

### Boundary And Delivery Context

- [PRD-0024: Deployed App Docs](prd-0024-deployed-app-docs.md)
  has delivered English in-app Docs immediately above settings, fixed /help routes,
  first-use access and offline package content. The owner's latest correction
  selects six canonical guides, removes reader clutter and keeps necessary recovery
  guidance in feature pages under [FEAT-0144](../feature/feat-0144-canonical-product-docs.md)
  and [Run 208](../run/run-20261027-208-canonical-product-docs.md). Later owner review
  removed About, retained path-label meaning in Sessions and corrected search and
  source-removal guidance. The final Docs-only snapshot passes all 1,257 tests,
  six-guide desktop/narrow browser checks and relocated-wheel guide tests.
  Earlier [Run 207](../run/run-20261026-207-app-docs-reader.md)
  owns the initial reader/offline/relocated-wheel evidence and five unrelated
  schema/value inventory failures reproduced without Docs. The PRD remains `in-loop`
  for human review. [Run226](../run/run-20261029-226-publication-and-native-integration.md)
  now owns the rebuilt native app/ZIP and bounded frozen-runtime checks;
  Docs human acceptance and recipient execution remain open.
