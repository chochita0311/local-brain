# FEAT-0157: Bilingual App Docs

## Metadata

- ID: `feat-0157`
- Status: `passed`
- Type: `product`
- Surface: `fullstack`
- Execution Profile: `fullstack-product`
- Required Evaluators: `contract`, `design`, `functional`, `ux-heuristic`
- Parent PRD: [PRD-0027](../prd/prd-0027-early-access-distribution-and-bilingual-docs.md)
- Created: `2026-11-05`
- Updated: `2026-11-05`

## Goal And Acceptance Contract

현재 앱 안의 여섯 가이드를 한국어로 바로 읽고 같은 주제의 영어 보기로 전환한다.
짧은 도입·작업 단계·표/목록으로 필요한 정보를 찾기 쉽게 하되 동작 조건은 보존한다.

- 언어를 선택하지 않은 Docs 진입은 한국어다. 언어 전환은 같은 가이드에 머물며,
  명시적 선택은 가이드 내부 이동·이전/다음·뒤로 가기에서도 유지한다. 새 전역 앱 언어
  설정을 추가하지 않는다. 임의 언어/slug는 안전한 고정 조회로 처리한다.
- 여섯 주제와 경로를 유지한다. 한국어/영어의 기본값·적용 시점·검색 제외/준비 조건,
  수집/등록/원본 보존, 비용 추정, 복원 자격/교체/재시작/실패 복구가 동등해야 한다.
- 고정 package content·공통 Markdown renderer·안전한 내부 링크·오프라인 읽기를 유지한다.
  실제 플랫폼만 설명하고 미검증 Windows 예상안을 Mac 앱의 지원 완료 안내로 넣지 않는다.
- 시작하기는 README의 에이전트 로컬 빌드·설치 진입점과 업데이트의 소스 갱신 → 재빌드 →
  앱 교체를 짧게 설명한다. 도구/빌드 명령은 설치·개발 가이드가 소유하며, 설치된 앱의
  일반 사용·오프라인 Docs가 checkout이나 외부 링크에 의존해서는 안 된다.

## Scope And Surface Lanes

- In: registry/언어 선택과 링크, 현재 6개 앱 가이드와 해당 reader의 기존 디자인 확장.
- Out: 저장소 문서 번역, 앱 전체 언어 전환, 새 Docs 웹사이트/주제, 대규모 의미 축약.
- Backend/content lane: 고정 언어/가이드 lookup과 package 포함; Contract/Functional 평가.
- Frontend lane: 기존 shell·제목/목차·언어 전환·페이지 이동·읽기; Design/Functional/UX 평가.
- Dependencies: FEAT-0155 제공 범위. 공개 Docs 내용/경로 소유자는 `app-documentation.md`다.
- Contract surfaces: `/help` 6개 경로, 인증·link exception·renderer·package data·무수집 읽기.

## Entry, State And Exit

Docs/온보딩 도움말로 진입한다. 한국어/영어 전환과 내부 이동은 읽기만 수행한다.
없는 가이드와 읽기 불가 본문은 안전한 안내이며 개인 경로나 대체 원본을 노출하지 않는다.
공통 설정·검색·주요 탐색은 유지하고 본문 언어/현재 주제를 접근성 정보로 표시한다.

## Pass Or Fail And Regression Checks

원문과 번역의 의미/조건 대조, 두 언어의 여섯 본문/내부 링크, 언어 전환·뒤로 가기,
인증/알 수 없는 경로, 키보드/320px/데스크톱/offline, wheel/package 포함을 확인한다.
원본 Session/Document Markdown의 링크 규칙과 모델/수집 부작용 없음도 확인한다.
소스 reader 검증과 재빌드된 Mac/향후 Windows의 패키지 검증은 별도 증거다.

## Harness Trace

- Spec: [SPEC-0157](../spec/spec-0157-bilingual-app-docs.md).
- Run: [Run233](../run/run-20261105-233-bilingual-app-docs.md).
- Evaluation: [Mac delivery](../evaluation/eval-0155-early-access-macos-delivery.md).
- Execution profile: `fullstack-product`; backend/content before rendered frontend checks.

## Execution Authorization

- `2026-11-05`: 사용자가 “모두 반영”을 지시했다. 숨긴 Workflow/Workstream의 내부 의존 경로까지 정리하고, 한국어 기본·영문 전환 Docs, 저장공간 안내, 로컬 재빌드를 실행한다. Windows 실제 실행은 검증 환경이 생긴 뒤 확인한다.

## Local Delivery Outcome

- `2026-11-05`: 승인된 Mac 구현과 로컬 빌드 검증을 마쳤다. [통합 평가](../evaluation/eval-0155-early-access-macos-delivery.md)에 source/browser/frozen/native 증거와 수신자·Windows·공개 서명 미검증을 구분했다. 원격 push는 수행하지 않았다.

## Shared Language Option Refinement — 2026-11-06

User requested a common website-style option scoped to Docs rather than controls
under every article title. This authorizes the narrow frontend refinement under
[Run236](../run/run-20261106-236-docs-language-option.md) and the updated existing
Spec. Preserve the previous bilingual content and fixed locale/navigation rules.

- Run236 passed local frontend/browser/frozen/WebKit checks. The candidate initially stayed separate while the original app was in use; after the owner questioned that path and the app closed, it was promoted to `dist/LocalBrain-apple-silicon/LocalBrain.app`.
