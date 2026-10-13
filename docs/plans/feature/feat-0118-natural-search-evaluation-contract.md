# FEAT-0118: Natural Search Evaluation Contract

## Metadata

- ID: `feat-0118`
- Status: `passed`
- Type: `foundation`
- Surface: `docs`
- Execution Profile: `foundation-contract`
- Required Evaluators: contract
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Created: `2026-10-12`
- Updated: `2026-10-12`
- Approval: human의 PRD 전체와 테스트까지 연속 진행 승인에 따라 이 범위를 구체화함.

## Goal

같은 자료에서 모델·분해 크기별 품질·비용을 비교하는 기준 고정.

## Acceptance Contract

합성 정답과 private 관찰 분리; 기존FTS/어휘/Qwen/Hybrid/Laya/Reranker; cold/warm, 품질·디스크·메모리; 측정 미실시를 성공으로 처리 금지.

## Scope Boundary

- In: 위의 단일 결과와 이를 입증하는 테스트/문서.
- Out: PRD의 제외 범위 전체. 원문 수정·개인 자료 외부 전송·기존 검색 교체·Windows 배포·개인 학습·공개 게시 없음.

## Contract Surfaces

[자연어 검색 계약](../../policies/project/natural-language-search.md)의 해당 책임. 기존 FTS, 원문/source 권한, 모델 설치, data/cache 경계를 보존한다.

## Dependencies

- 없음. 기존 owner 정책을 따른다.

## Surface Lanes

하나의 책임 범위를 primary가 순차 수행한다. 다른 Feature의 미해결 계약을 흡수하지 않는다.

## Entry And Exit

PRD의 경계에서 시작해 아래 검증이 가능한 계약/비교 산출물로 끝난다.

## State Expectations

계약은 source 관측과 파생 결과, 미확정 품질과 확정 범위를 구분한다.

## Likely Affected Surfaces

docs/policies/project/natural-language-search.md와 이 Feature의 Spec/Run/평가.

## Pass Or Fail Checks

- 위 acceptance의 각 요소를 Spec에 명시하고 구현/계약과 일치하는지 확인한다.
- 범위·주체·입출력·허용 조건·무효화/실패의 의무가 구체적이며 downstream이 추측할 계약이 남지 않는다.
- 모델 품질·속도는 실제 측정 범위로만 보고한다. 공개 합성을 개인 corpus 전체의 보증으로 확장하지 않는다.

## Regression Surfaces

기존 `/search`, source Sync/제외 정책, 원문 읽기, 공개 모델 cache, data/cache override, 기존 affinity.

## Harness Trace

- Spec doc: [SPEC-0118](../spec/spec-0118-natural-search-evaluation-contract.md)
- Run: [run-20261012-155](../run/run-20261012-155-natural-search-evaluation-contract.md)
- Execution profile: `foundation-contract`
- Latest evaluator report: [contract](../evaluation/eval-0118-contract-natural-search-evaluation-contract.md)

## Continuity Notes

- `2026-10-12`: human의 전체 승인과 테스트까지 연속 진행 지시에 따라 범위를 잠갔다. 다음 단계의 실행 결과까지 미리 승인되었다고 취급하지 않는다.
