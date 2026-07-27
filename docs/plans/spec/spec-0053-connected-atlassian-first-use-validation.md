# SPEC-0053: Connected Atlassian First-Use Validation

## Metadata

- ID: `spec-0053`
- Status: `approved`
- Run ID: `run-20260724-58`
- Attempt: `2`
- Parent Feature: [feat-0053-connected-atlassian-first-use-validation](../feature/feat-0053-connected-atlassian-first-use-validation.md)
- Parent PRD: [prd-0008-connected-atlassian-validation-and-schema-erd-routing](../prd/prd-0008-connected-atlassian-validation-and-schema-erd-routing.md)
- Surface: `mixed`
- Execution Profile: `foundation-contract`
- Surface Lanes: private fixture inventory → bounded connected reads → local-only regression → finding classification
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-24`
- Updated: `2026-07-24`

## Source Set

- Human approval on `2026-07-24`: approve and execute both PRDs' Features automatically and sequentially.
- Passed FEAT-0044 through FEAT-0051 contracts and tests.
- Current official Atlassian MCP connector inventory and the current host tool catalog.
- Private runtime database inspected only through aggregate counts.

## Approved Private Inventory

| Alias | Target | MCP connection | Runner | Permitted read | Expected retention |
| --- | --- | --- | --- | --- | --- |
| `site-a/jira` | one owner-accessible Atlassian Site | official Atlassian MCP | Codex | accessible-resource metadata; one Jira metadata result bounded to the latest 30 days | success/error shape and payload length only |
| `site-a/confluence` | the same Site | official Atlassian MCP | Codex | capability/installation availability only | status and bounded error class only |
| `site-a/jira` | the same Site | company MCP Gateway | Codex | host tool availability only; no dispatch when absent | catalog presence only |
| `site-a/confluence` | the same Site | company MCP Gateway | Codex | host tool availability only; no dispatch when absent | catalog presence only |

- Tracked artifacts use these aliases only. Site names, URLs, Cloud IDs, account data, project/Space names, issue keys, titles, content, and credentials are not retained.
- The successful connected content read is limited to Jira fields already allowed by FEAT-0044: key, status, and updated timestamp.
- The LocalBrain runtime database contains zero registered Source Instances and zero capability observations at the start of this Run. No production record is created to manufacture an end-to-end path.

## Implementation Goal

- Establish privacy-safe direct evidence for currently available connected paths and explicitly classify unavailable paths without changing product behavior or persistent runtime state.

## In-Scope Behavior

1. Inspect accessible-resource metadata for the official connector.
2. Perform one bounded Jira metadata search through the official connector.
3. Record official Confluence installation availability without reading Page content.
4. Inspect whether Gateway tools are exposed to the current host; do not dispatch when absent.
5. Exercise synthetic LocalBrain capability, isolation, stale, unavailable, unauthorized, partial-failure, retry, local-only, and no-hidden-read contracts.
6. Classify every observation and route corrections to later Features.

## Out-Of-Scope Behavior

- Registration, refresh, candidate confirmation, capability writes, external writes, broad discovery, Page or ticket-body reads, and opportunistic fixes.

## State And Interaction Contract

- Connected success: keep structural success evidence only.
- Connected unavailable: retain a bounded environment class and do not retry automatically.
- No registered runtime connection: use the passed synthetic LocalBrain boundary tests instead of mutating the owner's database.
- Local-only screens and routes: prove zero executor activity through isolated fixtures.

## Contract Surfaces

- FEAT-0044 read policy and capability state.
- Official connector read boundary and current host tool catalog.
- Local Atlassian registration, browse, refresh-preview, classification, and UI contracts.
- Repository privacy boundary.

## Acceptance Mapping

- Exact inventory → approved alias table above.
- Official MCP evidence → accessible-resource success and one bounded Jira metadata success.
- Gateway evidence → direct host-catalog absence plus synthetic provider isolation and dispatch tests.
- Failure/recovery states → focused external-access and Atlassian suites.
- Private evidence boundary → aggregate-only runtime queries and structural tracked reports.
- Finding routing → Run finding ledger and FEAT-0054 dependency notes.

## Evaluation Focus

- No external write or persistent runtime mutation.
- No private connected value in tracked artifacts.
- Distinguish direct, synthetic, and unavailable evidence.
- Do not claim official Confluence or Gateway execution when the environment does not expose them.

## Open Blockers

- None. Environment limitations are expected evidence states and do not authorize connector installation or database setup.

## Continuity Notes

- `2026-07-24`: Attempt 1 used broad connector metadata probes while reducing the inventory. Their payloads were not retained. Attempt 2 narrowed the executable inventory to FEAT-0044-compatible resource inspection and bounded Jira metadata search.
