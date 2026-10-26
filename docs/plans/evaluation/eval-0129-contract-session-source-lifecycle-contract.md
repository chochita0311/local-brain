# EVAL-0129: 사용자 세션 소스와 수집 소유 계약 contract

## Metadata

- ID: `eval-0129`
- Status: `complete`
- Evaluator Type: `contract`
- Result: `PASS`
- Run: [RUN-167](../run/run-20261018-167-session-source-lifecycle-contract.md)
- Feature: [FEAT-0129](../feature/feat-0129-session-source-lifecycle-contract.md)
- Spec: [SPEC-0129](../spec/spec-0129-session-source-lifecycle-contract.md)
- Execution Profile: `foundation-contract`
- Surface Lane: shared configuration and persistence contracts
- Evidence Coverage: `complete` for this foundation contract
- Created: `2026-10-18`

## Initial Checks And Evidence — 2026-10-18

This dated foundation receipt preserves the original string-key contract. The
[current numeric-ID contract](../../policies/project/desktop-app-and-settings.md#generalized-session-profiles)
and Run196 supersede that identity choice while retaining record IDs and the
source lifecycle. This original PASS does not by itself validate the later migration.

## Checks And Evidence

The primary agent reviewed the owning [desktop/settings policy](../../policies/project/desktop-app-and-settings.md), implementation and consumers against the approved PRD. No delegation or external publication occurred.

The settings/source/sync tests exercise empty fresh registrations, stable identity on rename/re-enable, disabled-source exclusion, overlaps, per-source failures, thread/process writer exclusion and retained records. The synthetic browser flow checks reconnect with unchanged Session IDs.

- 고유 source_key/provider와 표시 이름·에이전트 홈·실제 세션 root 구분.
- 추가·수정·명시적 같은 소스 재연결·해제. 해제 기록 보존/기본 검색 제외, 기존 목록의 보존 기록 조회 유지.
- 설정·수집·복원은 같은 로컬 잠금으로 조정; 실패는 원본·기존 기록 보존.

## Boundaries

This accepts field ownership, identity, admission and failure semantics. It does
not certify native GUI behavior, another Mac, every corpus, or distribution.
The [integration evaluation](eval-0139-functional-standalone-test-app.md) owns
those implementation checks and outstanding evidence.

## Route

`pass` for the foundation contract; product checks remain independently scoped.
