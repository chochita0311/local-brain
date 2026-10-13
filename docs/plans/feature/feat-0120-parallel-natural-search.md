# FEAT-0120: Parallel Natural Search

## Metadata

- ID: `feat-0120`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: contract, functional, design, ux-heuristic
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Created: `2026-10-12`
- Updated: `2026-10-12`
- Approval: human의 PRD 전체와 테스트까지 연속 진행 승인에 따라 이 범위를 구체화함.

## Goal

상단 왼쪽 새 입력에서 관련 원문으로 이동.

## Acceptance Contract

기존 검색 보존; 새 검색·준비·진행·실패·무결과 상태; 원문 근거/복귀; 320/700/920/1440px; 한국어 IME·키보드.

## Scope Boundary

- In: 위의 단일 결과와 이를 입증하는 테스트/문서.
- Out: PRD의 제외 범위 전체. 원문 수정·개인 자료 외부 전송·기존 검색 교체·Windows 배포·개인 학습·공개 게시 없음.

## Contract Surfaces

[자연어 검색 계약](../../policies/project/natural-language-search.md)의 해당 책임. 기존 FTS, 원문/source 권한, 모델 설치, data/cache 경계를 보존한다.

## Dependencies

- [FEAT-0115](feat-0115-search-molecule-contract.md)
- [FEAT-0116](feat-0116-natural-search-query-contract.md)
- [FEAT-0117](feat-0117-natural-search-storage-contract.md)
- [FEAT-0119](feat-0119-local-natural-search-engine.md)

## Surface Lanes

데이터/서비스 계약 → route/상태 → header/results/원문 복귀 → browser 평가. src/localbrain/natural_search*, main.py, templates/, static/가 각각 소유한다. primary가 순차 수행하고 contract/functional/design/ux 평가로 확인한다.

## Entry And Exit

등록된 corpus와 명시적 준비/검색 요청에서 시작해 관련 부모 원문 또는 정확한 준비·오류 상태로 끝난다.

## State Expectations

미활성/모델 없음/준비 중/부분 준비/준비 완료/실패/자료 없음/일치 없음은 구분한다.

## Likely Affected Surfaces

src/localbrain/natural_search*, tests/test_natural_search*, scripts/; 필요 시 main.py, cli.py, templates/, static/의 소유 경로.

## Pass Or Fail Checks

- 위 acceptance의 각 요소를 Spec에 명시하고 구현/계약과 일치하는지 확인한다.
- 합성 자동 테스트, 필요한 browser 조작과 실제 로컬 실행을 구분해 결과를 기록한다. 필요한 상태를 관측하지 않았으면 통과 근거로 사용하지 않는다.
- 모델 품질·속도는 실제 측정 범위로만 보고한다. 공개 합성을 개인 corpus 전체의 보증으로 확장하지 않는다.

## Regression Surfaces

기존 `/search`, source Sync/제외 정책, 원문 읽기, 공개 모델 cache, data/cache override, 기존 affinity.

## Harness Trace

- Spec doc: [SPEC-0120](../spec/spec-0120-parallel-natural-search.md)
- Run: [RUN-157](../run/run-20261012-157-parallel-natural-search.md)
- Execution profile: `fullstack-product`
- Latest evaluator reports: [contract](../evaluation/eval-0120-contract-parallel-natural-search.md), [functional](../evaluation/eval-0120-functional-parallel-natural-search.md), [design](../evaluation/eval-0120-design-parallel-natural-search.md), [ux-heuristic](../evaluation/eval-0120-ux-heuristic-parallel-natural-search.md).

## Continuity Notes

- `2026-10-12`: human의 전체 승인과 테스트까지 연속 진행 지시에 따라 범위를 잠갔다. 다음 단계의 실행 결과까지 미리 승인되었다고 취급하지 않는다.
