# Session Detail Uses Direct References Only

## Log Type

- Type: `Batch`
- Date: `2026-10-30`
- Related track: [REFACTOR-0004](../refactor-0004-direct-session-materials.md)
- Scope: 사용자 요청에 따른 세션 상세의 작업 연결·간접 자료 제거.

## Summary

- Goal: 재정의 예정인 작업 조직과 세션 상세의 조회 결합을 제거한다.
- Outcome: `Pass` — 이 한정 범위의 구현·검증 완료.
- 직접 발견한 자료와 대화는 유지하며, 작업 조직의 기존 데이터는 변경하지 않는다.

## What Changed

- `resources/related_context.py`에서 조직 후보 SQL, 간접 자료 조합, 조직별 중복 병합·경고, 로컬 경로 대상 로더와 미사용 필드를 제거했다.
- `sessions/web.py`에서 Workstream membership import/조회와 미사용 workspace 인자를 제거했다.
- Session 상세 상단의 ‘연결된 작업’, 관련 자료의 조직 그룹·배지와 전용 CSS를 제거했다. Desktop adapter의 사라진 조직 처리도 정리했다.
- 제품·아키텍처·데이터 모델·앱 가이드 및 이전 계획의 인계 상태를 갱신했다.
- 데이터 모델 설명을 반영해 schema presentation과 cleanup audit provenance를 재생성했다. DDL, 관계 데이터, 기존 audit 판정은 변경하지 않았다.
- 기존 Markdown 모델을 확인했다: Local Context의 `context_documents`가 절대/상대 경로·본문·변경 정보를 목록화하고 상대 경로에서 폴더 트리를 구성한다. 별도 `local_resources`는 일반 경로 메타데이터 등록이며 같은 파일의 문서 identity와 자동 통합되지 않는다.

## Behavior / Parity Notes

- Parity claim status: `Intentional deltas present`.
- 직접 근거가 없는 조직 연결만 있으면 관련 자료는 빈 상태가 된다. 조직 전용 제목·총수·경고·배지를 더 이상 제공하지 않는다.
- 직접 Markdown/URL/등록 Atlassian 참조의 identity·근거·순서·100개 보존 상한·stale/partial/error 처리는 유지했다.
- 조직 테이블을 읽으려 하면 실패시키는 SQLite authorizer로 projection과 Session route를 검증했다. 예외가 화면에서 숨겨지더라도 읽기 시도 자체가 실패하도록 검사한다.
- 기존 Thread/Workstream 링크가 남고 projection 전후 DB 변경 횟수가 같음을 synthetic DB로 확인했다.
- 이 기록은 전체 선택 기능 독립화나 strict parity/merge 승인을 뜻하지 않는다.

## Validation

- Baseline: 미커밋 패키징 배치 이후 작업 트리. HEAD `6c03265701d0d8b552fc8bb60e346ba1971f4bb3` 단독 비교가 아니다. 대상 7파일의 수정 전 manifest digest는 계획에 기록했다.
- Syntax: 변경 Python 모듈/테스트의 AST 파싱 통과. 패키지 경로·의존성·진입점 변경은 없으며 wheel/frozen build는 재실행하지 않았다.
- Targeted: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests .venv/bin/python -m unittest test_session_related_context test_session_references test_session_details test_session_contract test_workstreams test_desktop_boundary -q` — 63개 통과.
- Full suite: `unittest.defaultTestLoader.discover('tests')` 결과에서 `test_google_drive_transport.PoolTests.*` 11개를 제외하여 실행 — 1,451개 통과, 31.061초. 제외 수가 11인지도 검증했다.
- 마지막 테스트 보강(URL query 변형 2개)과 사용되지 않는 그룹 구분 CSS 제거 후 `test_session_related_context` 17개 재검증 통과. 앱의 나머지 Python 동작은 전체 검사 이후 변경하지 않았다.
- 문서/생성 검사: `check-data-model-docs.py`, `build-schema-presentation.py check`, `check-schema-cleanup-audit.py --check` 통과. Audit은 732개 객체, keep 620 / defer 112 / change 0 / remove 0을 유지한다.
- Browser: 기존 로컬 Session 상세에서 직접 참조 링크 8개, JIRA/MARKDOWN/URL 종류, 대화 표시를 확인했다. ‘연결된 작업’, membership strip, 조직 그룹은 없고 참조 오류도 없었다. 외부 링크는 `noopener`와 `noreferrer`를 유지한다.
- 실제 viewport 1440×841: 796px 본문과 340px 관련 자료 열. 820×900 emulation: 568px 단일 열에서 세션 정보→관련 자료→대화 순서. 두 경우 document client/scroll width가 viewport와 같아 가로 넘침이 없다. 일반 window resize는 적용되지 않아 실제 emulation 값으로 검증했다.
- 빈 상태·조회 오류·disabled 문서·unsafe URL·Subsession rail 부재는 synthetic route/projection 테스트로 확인했다. 브라우저 검증은 기존 자료가 있는 화면 범위다.
- Privacy 검사와 `git diff --check` 통과. 기존 Starlette TemplateResponse 인자 순서 deprecation warning은 남아 있다.

## Risks / Limitations

- 사용자 지시에 따라 Google Drive loopback 전송 검증은 보류했다.
- 등록 Atlassian 메타데이터 조회와 Session evidence의 기존 Atlassian FK는 그대로다. 공용 자원 identity/FK 재설계는 별도 후속 작업이다.
- 운영 데이터 재수집·마이그레이션·원본 파일 변경·앱 재시작·커밋·배포는 수행하지 않았다.

## Next Action

기존 문서 목록과 일반 경로 등록의 소유권을 구분한 상태에서 공용 자원 identity,
미등록 Markdown 경로, 연동 제거 시 참조 보존 규칙을 후속 설계한다. 현재 완료 범위는
세션 상세에서 조직 연결을 제거하는 데 한정한다.
