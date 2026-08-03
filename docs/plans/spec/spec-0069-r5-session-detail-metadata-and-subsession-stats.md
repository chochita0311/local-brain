# SPEC-0069-R5: Session Detail Metadata And Subsession Stats

## Metadata

- ID: `spec-0069-r5`
- Status: `approved`
- Run ID: `run-20260803-81`
- Attempt: `1`
- Parent Feature: [feat-0069-session-source-scope-and-provenance](../feature/feat-0069-session-source-scope-and-provenance.md)
- Parent PRD: [prd-0012-multiple-local-ai-session-sources-and-inventory-integrity](../prd/prd-0012-multiple-local-ai-session-sources-and-inventory-integrity.md)
- Supersedes: [spec-0069-r4-session-detail-source-cues](spec-0069-r4-session-detail-source-cues.md) for visible detail metadata; its stable source-key cue contract remains in force
- Surface: `frontend`
- Execution Profile: `frontend-product`
- Alignment Mode: `extend`
- Surface Lanes: Session detail heading → Subsession list stats → lazy Subsession detail → owner docs
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-08-03`
- Updated: `2026-08-03`

## Source Set

- FEAT-0069 and the passed `CL`/`CX`/`CC` source-key cue contract.
- Ordinary Sessions inventory row metadata order: question, event, date.
- Session detail, normalized Subsession detail, detail child-list, and lazy Claude
  Subsession templates and route projections.
- Design Constitution detail/read, provenance, density, and repeated-row rules.

## Implementation Goal

- Remove redundant visible source-name copy from Session detail recovery surfaces
  while preserving compact source identity and accessibility, and align detail
  Subsession statistics with the Sessions inventory reading order.

## Consistency Requirements

- The stable source icon remains the first heading and row cue: Claude `CL`,
  personal Codex `CX`, and Codex Company `CC`.
- Configured source names remain available in `sr-only` text; source identity must
  not become color-only.
- Primary Session detail has no source-name eyebrow. Normalized Subsession detail
  may retain the source-neutral `SUBSESSION` role eyebrow.
- Lazy Subsession detail retains only the source-neutral `SUBSESSION · LAZY VIEW`
  eyebrow.
- A parent detail Subsession row renders the external ID without a configured
  source-name prefix.
- Each detail Subsession row presents `질문 {user_message_count}`, then
  `이벤트 {event_count}`, then the activity date.
- Desktop columns align as icon, title/ID, question, event, and date. Compact and
  narrow layouts preserve question-before-event order after metadata wraps
  beneath the title; the existing narrow rule may omit the secondary date.

## In-Scope Behavior

- Add `user_message_count` from the existing Session record to the normalized
  detail child view model. Lazy Claude children derive the same count from
  source `message + user` events already parsed for their summary.
- Update Session and lazy Subsession heading markup only for visible metadata.
- Update detail Subsession row markup and shared responsive CSS using existing
  semantic roles and breakpoints.
- Update rendered-route and UI-contract tests with synthetic source/session data.
- Reconcile PRD, Feature, product, architecture, README, and design owner wording.

## Out-Of-Scope Behavior

- No database schema, parser, ingestion, count eligibility, or Usage change.
- No source-cue color, initials, source filters, ordinary Session row, Pinned row,
  conversation speaker, navigation, or pin behavior change.
- No removal of external IDs, paths, timestamps, or accessible configured labels.

## Contract Surfaces

- `show_session` direct-child view model
- `session.html` heading and `.subsession-list` row markup
- `subsession.html` lazy-detail heading
- `.subsession-list` desktop, compact, and narrow grid rules
- synthetic rendered primary and normalized child detail fixtures

## Acceptance Mapping

- Primary detail heading → icon, title, path; no visible configured source eyebrow.
- Normalized child and lazy child heading → source-neutral Subsession role text;
  no visible configured source name.
- Parent detail child row → icon, title, external ID, question, event, date; no
  visible configured source-name prefix.
- Accessibility → configured source name remains in the cue's `sr-only` text.
- Responsive → no overflow or metadata-order inversion at `1440`, `920`, `700`,
  and `320` widths.
- Regression → detail routes, parent-child links, source-scope return URLs,
  conversation rendering, full suite, privacy, and diff checks pass.

## Evaluation Focus

- `contract`: existing count field is projected without a new denominator or
  persistence contract; configured source labels remain accessible.
- `design`: redundant provenance copy is removed without leaving dead space, and
  the five-column desktop row aligns with the Sessions family.
- `functional`: primary, normalized child, and lazy child routes keep correct
  parent/navigation/content behavior and render accurate child counts.
- `ux-heuristic`: source identity remains understandable from the stable cue while
  question/event/date metadata follows one predictable scan order.

## Open Blockers

- In-app browser control is not currently exposed in this session. Deterministic
  rendered-route and responsive contract evidence may pass, but visual browser
  coverage must remain explicitly partial if the capability stays unavailable.
