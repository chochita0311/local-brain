# FEAT-0121: Natural Search Local Comparison

## Metadata

- ID: `feat-0121`
- Status: `passed`
- Type: `foundation`
- Surface: `infra`
- Execution Profile: `infra-devtool`
- Required Evaluators: contract, functional
- Parent PRD: [PRD-0020](../prd/prd-0020-local-natural-language-search.md)
- Created: `2026-10-12`
- Updated: `2026-10-12`
- Approval: human의 PRD 전체와 테스트까지 연속 진행 승인에 따라 이 범위를 구체화함.

## Goal

이 Mac의 재현 가능한 검색 비교 결과와 기본 설정 근거.

## Acceptance Contract

공개 합성 fixture, 실제 corpus 로컬 색인, 크기·차원·threshold 비교, Qwen 단독 및 추가 판정 모델의 회수·속도·메모리·디스크 분석.

## Scope Boundary

- In: 위의 단일 결과와 이를 입증하는 테스트/문서.
- Out: PRD의 제외 범위 전체. 원문 수정·개인 자료 외부 전송·기존 검색 교체·Windows 배포·개인 학습·공개 게시 없음.

## Contract Surfaces

[자연어 검색 계약](../../policies/project/natural-language-search.md)의 해당 책임. 기존 FTS, 원문/source 권한, 모델 설치, data/cache 경계를 보존한다.

## Dependencies

- [FEAT-0118](feat-0118-natural-search-evaluation-contract.md)
- [FEAT-0119](feat-0119-local-natural-search-engine.md)

## Surface Lanes

하나의 책임 범위를 primary가 순차 수행한다. 다른 Feature의 미해결 계약을 흡수하지 않는다.

## Entry And Exit

PRD의 경계에서 시작해 아래 검증이 가능한 계약/비교 산출물로 끝난다.

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

- Spec doc: [SPEC-0121](../spec/spec-0121-natural-search-local-comparison.md)
- Run: [RUN-158](../run/run-20261012-158-natural-search-local-comparison.md)
- Execution profile: `infra-devtool`
- Latest evaluator reports: [contract](../evaluation/eval-0121-contract-natural-search-local-comparison.md) PASS, [functional](../evaluation/eval-0121-functional-natural-search-local-comparison.md) PASS WITH SUGGESTIONS. 전체 private 색인·별도 합성 검증·갱신 중 검색·독립 설치의 실제 모델 실행까지 완료했다.

## Continuity Notes

- `2026-10-12`: Qwen 임베딩+한국어 어휘 순위 결합, 본문512/차원512/cutoff0.45/batch8을 공통 기본값으로 선택했다. Laya와 reranker는 선택적 비교에 남긴다. 회수율 향상과 실제 실행·저장 비용을 확인했으며, 낮은 반환 정밀도와 일부 순위 잡음은 개선 후보로 명시했다. 개인 정답 검토나 다른 기기의 품질을 승인한 상태는 아니다.
- `2026-10-12`: human의 전체 승인과 테스트까지 연속 진행 지시에 따라 범위를 잠갔다. 다음 단계의 실행 결과까지 미리 승인되었다고 취급하지 않는다.
