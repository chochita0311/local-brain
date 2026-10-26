# EVAL-0130: 모델 선택 검색 계약 contract

## Metadata

- ID: `eval-0130`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-168](../run/run-20261018-168-search-availability-contract.md)
- Feature: [FEAT-0130](../feature/feat-0130-search-availability-contract.md)
- Spec: [SPEC-0130](../spec/spec-0130-search-availability-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: shared configuration and persistence contracts
- Evidence Coverage: `complete` for this foundation contract
- Created: `2026-10-18`

## Checks And Evidence

The primary agent reviewed the owning [desktop/settings policy](../../policies/project/desktop-app-and-settings.md), implementation and consumers against the approved PRD. No delegation or external publication occurred.

The 41 existing natural-search tests pass with explicit AI mode. Synthetic browser requests exercise default keyword results over two Sessions and one Context document, registration removal exclusion, query/mode-preserving return links and missing-model recovery.

- 기존 FTS5 AND 토큰 검색을 모델 없이 제공.
- 자연어 검색의 유효 원문 허용 조건을 키워드 결과에도 적용.
- 사용자 질의 유지; 준비·실패·0건 구분; 모델 자동 설치/원격 fallback 없음.

## Boundaries

This accepts field ownership, identity, admission and failure semantics. It does
not certify native GUI behavior, another Mac, every corpus, or distribution.
The [integration evaluation](eval-0139-functional-standalone-test-app.md) owns
those implementation checks and outstanding evidence.

## Route

`pass` for the foundation contract; product checks remain independently scoped.
