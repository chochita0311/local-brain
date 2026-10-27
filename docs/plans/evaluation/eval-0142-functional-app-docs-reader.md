# EVAL-0142: Docs Functional Evaluation

> Historical scope: this record describes the initial seven-guide increment evaluated on 2026-10-26. [FEAT-0144](../feature/feat-0144-canonical-product-docs.md) and [Run 208](../run/run-20261027-208-canonical-product-docs.md) own the current six-guide correction and later content follow-ups. Earlier evidence retains its original scope.

## Metadata

- Feature: [FEAT-0142](../feature/feat-0142-app-docs-reader.md)
- Parent PRD: [PRD-0024](../prd/prd-0024-deployed-app-docs.md)
- Active Spec: [SPEC-0142](../spec/spec-0142-app-docs-reader.md)
- Run: [Run 207](../run/run-20261026-207-app-docs-reader.md)
- Attempt: 1
- Execution Profile: `frontend-product`
- Status: `complete`
- Result: `PASS`
- Evidence Coverage: `partial`

## Observed Behavior

All seven authenticated guides render through the running app. Guide/app links and local heading links remain anchors; direct entry and ordinary history identify the current topic. Settings opens the intended category, closes with Escape and restores focus. Incomplete onboarding can reach Docs without changing its completion state. Unknown/missing content and source-authored Markdown trust regressions pass the targeted tests.

For offline verification, a fresh headless Chrome profile used an unreachable external proxy with an explicit loopback bypass and a disabled browser cache. A controlled external navigation failed with `ERR_PROXY_CONNECTION_FAILED`; all seven guides then rendered at 1440px and 320px with styles, contents, current selection, live links and no horizontal page overflow. The run observed 122 loopback requests and no unexpected HTTP requests. Browser-wide Offline emulation was not used as proof: it also blocked localhost, unlike an unavailable internet connection with a running local app.

An offline-built wheel contains the exact seven guide bodies, reader module, template and CSS. Six guide tests pass against its relocated extraction, independently of checkout content. Desktop-boundary tests pass 7/7. The earlier full-suite run passed 1,251 of 1,256; the five schema/value inventory failures reproduce after removing the Docs changes in an isolated copy. No unrelated schema/value fix was made.

## Evidence Limits And Acceptance Impact

| Feature acceptance | Result within checked scope |
| --- | --- |
| AC1: guide rendering and bounded errors | PASS: seven guides and their links render; root-query, unknown-name and unavailable-body cases pass. |
| AC2: entry, shell and narrow access | PASS: Docs is above Settings; 1440/320px and exact 920/700px transitions preserve access and contain layout. |
| AC3: history, Settings and first use | PASS: keyboard/focus return, Back/Forward, section targeting and Welcome-to-Docs behavior are observed without completing setup. |
| AC4: auth, offline and packaged content | PASS for source/browser/relocated-wheel integration; a newly built native binary remains unverified. |

- Complete evidence for the changed source/backend, packaged content, local browser states, keyboard/history/Settings flow and internet-independent reading with loopback available.
- No newly rebuilt native `.app`/ZIP, WKWebView session for this change, native file chooser/shortcut probe or recipient-Mac run. These are unverified; source/browser/package checks do not close those release claims.
- Acceptance impact: non-blocking for this bounded source/content integration Run; native-binary release acceptance and final PRD acceptance remain open. No external release, upload, commit or push was performed.

## Route

Pass the source integration for human review with the native-release evidence limit retained. The temporary synthetic runtime, browser profile, baseline copy, wheel and logs are removed after verification; durable conclusions do not depend on temporary paths.
