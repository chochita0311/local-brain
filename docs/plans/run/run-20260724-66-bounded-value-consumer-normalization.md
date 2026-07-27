# RUN-20260724-66: Bounded-Value Consumer Normalization

## Metadata

- ID: `run-20260724-66`
- Status: `passed`
- Feature: [feat-0061-bounded-value-consumer-normalization](../feature/feat-0061-bounded-value-consumer-normalization.md)
- Parent PRD: [prd-0009-data-model-value-dictionaries-and-pinned-session-recall](../prd/prd-0009-data-model-value-dictionaries-and-pinned-session-recall.md)
- Active Spec: [spec-0061-bounded-value-consumer-normalization](../spec/spec-0061-bounded-value-consumer-normalization.md)
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Created: `2026-07-24`
- Updated: `2026-07-27`

## Goal And Selected Loop

- Replace mixed bounded-value output with one complete registry-backed vocabulary per ordinary-screen family without changing physical values or behavior.
- Route: `Orchestrator → Spec Agent → Fullstack Builder → Contract Evaluator → Design Evaluator → Functional Evaluator → UX Heuristic Evaluator`.
- Screen Alignment mode: `extend`.

## Delivered Contract

- Added strict, display-safe, and help registry accessors and exposed the display-safe helpers to ordinary Jinja consumers.
- Normalized all `40` logical-label families across the current `72` declared visible-consumer paths; `14` internal-only families remain hidden.
- Kept physical state values in stored rows, form values, query behavior, CSS state classes, payloads, and Run polling decisions.
- Added the visible `status_label` Run API projection while retaining raw `status` for behavior.
- Reconciled the machine inventory with actual template ownership and added bidirectional consumer drift checks.
- Added deterministic incomplete-mapping, unexpected-value, ordinary-template raw-output, and client polling tests.
- Regenerated the value-dictionary entrance and all nine subject dictionaries and updated product/developer ownership.

## Current Artifacts

- Spec: [spec-0061-bounded-value-consumer-normalization](../spec/spec-0061-bounded-value-consumer-normalization.md)
- Contract evaluation: [eval-0061-contract-bounded-value-consumer-normalization](../evaluation/eval-0061-contract-bounded-value-consumer-normalization.md) — `PASS`
- Design evaluation: [eval-0061-design-bounded-value-consumer-normalization](../evaluation/eval-0061-design-bounded-value-consumer-normalization.md) — `PASS`
- Functional evaluation: [eval-0061-functional-bounded-value-consumer-normalization](../evaluation/eval-0061-functional-bounded-value-consumer-normalization.md) — `PASS`
- UX heuristic evaluation: [eval-0061-ux-bounded-value-consumer-normalization](../evaluation/eval-0061-ux-bounded-value-consumer-normalization.md) — `PASS`
- Fix log: not created

## Verification Evidence

- `134` focused registry, UI, Session, usage, Atlassian, external-access, Workstream, context, runner, external-sync, and retrieval tests passed.
- Registry generation/check, Data Model documentation parity, Schema presentation parity, and all nine local Mermaid diagram parses passed.
- Browser checks used a temporary synthetic database and covered Sessions Dashboard, Workstream/Run, Atlassian browse/item, Search, Local Context, and Session detail.
- The dense Atlassian inventory had no horizontal document overflow at `1440`, `920`, `700`, or emulated `320`.
- Visible synthetic states used complete labels such as `링크만`, `조회 전`, `완료`, `우선순위 검토`, and `호출 예산 초과`; relevant physical tokens did not appear as ordinary labels.
- Browser evidence contained no console warning/error and no request outside localhost.
- The complete `288`-test repository suite passed after refreshing the Session-pin foreign-key presentation count, its deliberate schema-audit digest, and the final pin interaction regression.
- Repository privacy inspection passed across `628` candidate files after replacing one company-like synthetic label with producer-neutral test wording.
- Authored-file whitespace validation passed; the locally generated third-party Mermaid bundle retains an upstream template-literal trailing space and is governed by byte-freshness/package checks instead.

## Attempts

- Attempt 1:
  - status: passed
  - outcome: all declared ordinary consumers use the executable complete-family mapping.
  - notes: one UI contract expectation was updated from obsolete raw policy copy to the approved logical copy; no runtime behavior changed.

## Human Review Outcome

- Decision: automatic sequential approval authorized on `2026-07-24`.
- Returned layer if any: none.
- Follow-up run: repository-wide closure verification for PRD-0008 and PRD-0009.
