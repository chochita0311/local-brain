# FIX-0018: Subsession Terminology

## Metadata

- ID: `fix-0018-subsession-terminology`
- Status: `complete`
- Run ID: `run-20260717-18`
- Attempt: `2`
- Feature: [feat-0018-conversation-focused-session-details](../feature/feat-0018-conversation-focused-session-details.md)
- Spec: [spec-0018-conversation-focused-session-details](../spec/spec-0018-conversation-focused-session-details.md)
- Execution Profile: `fullstack-product`
- Surface Lane: Session hierarchy terminology → detail UI → lazy compatibility route → owner documentation
- Created: `2026-07-19`
- Updated: `2026-07-19`

## Input Reports

- Human post-run review selected `Subsession` as LocalBrain's single product term and requested PRD-0002 closure.
- Previous FEAT-0018 contract, design, functional, and UX reports remained the accepted behavior baseline.

## Fix Scope

- Replace the remaining product-facing `Subagent` labels and implementation-facing detail names with `Subsession`.
- Make `/sessions/{id}/subsessions/{file}` the canonical lazy compatibility route without breaking existing `/subagents/` links.
- Preserve source-native Claude `subagents/` directories, Codex `source.subagent` metadata, and agent-orchestration prompt terms as explicit boundaries rather than product labels.
- Align PRD-0002, Product Model, Architecture, Design Constitution, FEAT-0017, FEAT-0018, and their Specs.

## Changes Applied

- Parent and child Session details now use `Subsessions`, `Subsession`, and `상위 Session` consistently, including accessible labels.
- The lazy detail template and CSS component names now use `subsession`; source provenance marks remain `CL` or `CX`.
- The canonical lazy route uses `/subsessions/`; the legacy `/subagents/` route returns a permanent redirect.
- Source-native parser and directory identifiers remain unchanged.

## Contract Or Lane Impact

- Contract surfaces touched: product terminology, detail template context, canonical and compatibility routes, accessible source/role labels.
- Surface lanes touched: backend route composition, detail reading UI, durable product/design documentation.
- Stale-assumption check needed: yes; no current product UI or owner contract may require `Subagent` as the child Session label.

## Verification

- 142 repository tests passed.
- Python compilation and the repository privacy check passed.
- Synthetic local HTTP checks returned `200` for Sessions, primary detail, child detail, and Session-only synchronization.
- A repeated warm request retained the same file-versioned CSS and JavaScript assets.
- The legacy `/subagents/` URL returned `308` to the canonical `/subsessions/` URL.
- New browser-only pixel and transient interaction-state capture was unavailable in the current control environment; the human owner accepted that explicit non-blocking evidence limit for PRD closure.

## Remaining Issues

- FEAT-0019's viewport captures and browser-only synchronization state sequence remain in the project quality backlog.

## Return Decision

- `accept`

## Continuity Notes

- `2026-07-19`: completed the bounded terminology alignment and retained only source-native and redirect-only `subagent` compatibility boundaries.
