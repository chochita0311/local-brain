# SPEC-0147: Drive Settings Connection

## Metadata

- ID: `spec-0147`
- Status: `approved`
- Run: [run-20261028-218](../run/run-20261028-218-drive-settings-connection.md)
- Attempt: 3
- Parent Feature: [feat-0147](../feature/feat-0147-drive-settings-connection.md)
- Parent PRD: [PRD-0025](../prd/prd-0025-google-drive-connection-and-incremental-sync.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Created: `2026-10-28`
- Updated: `2026-10-28`

## Approved Revised Contract

This consumer must preserve the [OAuth adapter contract](spec-0146-drive-oauth-adapter.md#approved-revised-contract), whose producer owns SDK discovery, full Drive scope, account pinning, exact login arguments, environment isolation, timeouts, cancellation, token/credential boundaries and account validation. The [Drive policy](../../policies/project/google-drive-sync.md) remains the durable behavior owner. Use its existing-login versus explicit browser-login distinction; preserve selected-root operations, saved sync state on failures and scope disclosure. No provider project or app-owned Desktop Client is required.

Frontend: same Settings family and tab, optional account field (blank uses the existing bound/current/unambiguous gcloud account), existing-login connection and explicit Google-login actions, cached readiness and inline errors. No extra sharing consent or write probes. Fullstack profile contract→backend→frontend→docs, with contract/functional and rendered design/interaction checks. Installer guide must describe gcloud installation, exact approved login command and root permissions; provider-project creation is no longer required. Frozen GUI environment discovery must be verified independently of browser source execution.

## Acceptance Mapping

Producer tests in SPEC0146 supply the auth/SDK prerequisite evidence; this consumer preserves that contract rather than owning another implementation. Integration checks cover argv/environment isolation, token redaction and memory-only caching, explicit account pinning, SDK absence/reauth/network errors, timeout/shutdown, existing-login reuse and browser login completion, API account mismatch, cached status/no CLI calls, unchanged sync/scheduler behavior and native request boundary. Browser checks cover real controls at desktop/320px and error/retry transitions. Package checks prove removal of embedded Client/Keychain dependency and SDK availability in a frozen backend. Live user Google/Drive operations remain unverified until performed through an authorized real connection; no new project creation is required for the documented SDK path.

## Evidence Limits

Earlier Run210/211/214 and their Desktop Client evidence remain historical. Revised implementation uses new Runs215/216/217. Real Google account/root access and write permissions remain separate from synthetic/frozen checks. No product choice remains open for this revision.

## Approved Usability Repair

Run218 repairs reported setup confusion within the approved Settings contract. A deliberate **Save and check connection** action saves the URL/target, reuses existing gcloud credentials, verifies identity and browses the root in sequence; retry uses **Check connection**. OAuth browser login remains a separate explicit action. No page-open, polling or scheduled action initiates login or new Google probes. Retain full scope explanation and guidance in visible supporting copy/expandable account options. Display one useful connection summary; detailed auth/API/root observations remain available in diagnostics. Initial sync configuration appears after first successful root check; existing selected/configured targets remain accessible on later failures. Unselected receive rows show folder selection before their run/schedule/report controls. Empty result timestamps do not crowd the initial view. All underlying state, independent schedules and manual actions remain available.

On supported macOS/Python, the Drive client uses truststore.SSLContext with HTTPSHandler, retaining certificate/hostname verification and NoRedirect without global SSL injection. Declare truststore as a base macOS dependency so browser-only installations have it. Certificate validation failures are distinct from OAuth/network failures and do not request browser login. Never disable verification or bundle organizational certificates. Use synthetic SDK/API data in UI evidence and an unauthenticated public endpoint only for live transport checks.
