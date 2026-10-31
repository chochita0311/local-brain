# Session URL Parsing And Optional Atlassian Binding

## Log Type

- Type: `Batch`
- Date: `2026-10-30`
- Related track: [REFACTOR-0003](../refactor-0003-session-centered-package-boundaries.md), Step 8 continuation.
- Scope: 순수 URL 해석의 공용 소유권과 선택적인 Atlassian 등록 항목 연결.

## Summary

- Goal: 세션의 Jira/Confluence URL 인식을 Atlassian 탭 설정과 분리하고, 나중에 다른 제품 URL 분류를 추가할 공용 위치를 만든다.
- Outcome: `Pass` for this bounded batch; 전체 기능 독립화 트랙은 진행 중이다.
- Short conclusion: 세션은 공용 URL 해석을 사용한다. 등록 DB 조회는 Atlassian 소유 adapter로 옮겼고 수집 조립이 같은 connection에서 명시적으로 연결한다. 기존 앱의 URL/내부 항목 연결 결과는 비교한 입력에서 동일하다.

## What Changed

| 이전 소유자 | 현재 소유자 | 책임 |
| --- | --- | --- |
| `atlassian/locators.py` | `references/atlassian.py`, `references/contracts.py` | 제품 URL grammar와 순수 locator description. 선택 기능, 등록, SQLite, ingest 의존 없음. |
| `sessions/references.py` URL 정규화·표시 identity·key 및 locator 분기 | `references/urls.py` | `parse_url` 공용 진입점, `ParsedUrl`, generic HTTP(S) 처리, semantic identity. |
| `ingest/evidence/reference_candidates.py::trim_url_token` | `references/urls.py` | 기존 괄호/구두점 처리. 수집·관련 자료·Atlassian sync가 동일 함수를 사용. |
| `sessions/references.py` 등록 항목 SQL·payload | `atlassian/session_references.py` | Site/service/alias/identity 및 bare tool hint 매칭. 항목 생성과 외부 호출 없음. |
| 세션 reconciler의 암묵적인 Atlassian 호출 | `external_resolver`와 `ingest/sync/sessions.py`의 명시적 전달 | 세션 기본 처리와 선택 기능 연결의 방향을 분리. 기존 evidence → references 호출 순서 유지. |

- Atlassian registration/browse/evidence/sync/structure 소비자도 공용 parser를 사용한다. 옛 locator 모듈 facade를 남기지 않았다.
- `sessions/references.py`에 Atlassian import와 등록 테이블 조회가 없다. 공용 `references/`에는 기능·DB·ingest import가 없다. 패키지 최상위 Python 파일은 기존 4개를 유지한다.
- 기존 package-boundary 검사에 공용 references와 세션 references를 포함했다. URL/등록 분리, 빈 DB에서의 해석, unsafe/Markdown 처리, resolver 실패 rollback, 실제 수집 시 연결 순서를 검증하는 8개 테스트를 추가했다.
- Architecture, Data Model producer 소유권, active plan/index와 생성 schema audit ledger를 갱신했다. schema audit의 620 keep/112 defer 결정은 변경하지 않았다.

## Behavior / Parity Notes

- Behavior-preserving intent: 앱에서 관측되는 URL 분류·안전성·정규화·identity/key·중복 묶기·등록 항목 링크, evidence payload·제한·freshness·transaction/오류 의미를 보존한다.
- Intentional deltas: 내부 import/type 경로를 `references.contracts.UrlLocator`로 옮겼다. 내부 reconciler의 `external_resolver=None`은 등록 조회를 수행하지 않는 기본 경계다. URL은 `url` target으로 남으며 bare Jira/Page hint는 연결하지 않는다. 기존 앱 수집은 adapter를 명시적으로 공급한다. UI, Slack 기능, schema, 저장 kind, locator/extractor version은 변경하지 않았다.
- Query/selection: URL의 configured domain/service 확인 → 원래 URL의 정규화 alias 우선 → 유일한 Site-scoped identity fallback을 유지했다. bare hint는 기존처럼 전체 등록 항목 중 유일해야 한다. 모호하거나 없는 항목은 URL fallback 또는 hint 미해결로 남는다.
- Output: recognized item/structure/site의 domain/service/kind/identity tuple과 generic URL 문자열을 동일 JSON/SHA256 규칙으로 해시한다. 구조/site는 URL target이다. unsafe는 generic fallback을 하지 않는다. 모든 evidence field, 표시 identity 500자 제한, safe locator/query 보존과 generic query 제거가 유지된다.
- Write/failure: 기존 savepoint, evidence 교체, aggregate finalization, source fingerprint와 exception chaining을 유지했다. adapter는 같은 caller connection을 쓰며 새 commit/background 실행/오류 무시가 없다. 실패 테스트는 adapter 변경만 rollback되고 caller의 미커밋 변경과 이전 evidence가 유지되며 error scan이 기록됨을 확인한다.
- 기존 SQL·DDL와 저장 버전은 그대로다. `session_reference_evidence.external_resource_id → atlassian_items.external_resource_id` FK와 기존 `atlassian_item` 목적지 분기는 남긴다. URL을 해석하는 독립성과 해당 테이블을 삭제할 수 있는 독립성은 다르다.
- Parity claim status: `Provisional` for the overall track. 이 배치의 비교·회귀·runtime 근거는 아래 범위에 한정하며 strict merge approval이나 전체 기능 제거를 뜻하지 않는다.

## Validation

- Baseline: 직전 패키지 배치의 dirty working tree, HEAD `6c03265701d0d8b552fc8bb60e346ba1971f4bb3`; 202 Python modules; inventory SHA256 `4a45727e605f06c90da6ad2df3aa706fc7006172fd576b6dbb49b35689eeac0a`를 수정 전에 확인/고정했다. 이전 변경을 보존했다.
- Final source: 206 Python modules; 같은 경로/파일 SHA256 inventory 방식의 digest `1d86c38b0e451f67ae71cdb4fa98389dbebe2189d2beacd9644a406563d8f260`.
- Structural audit: 변경된 기존 10개 모듈의 함수/클래스 254개를 대응했다. 타입/함수 이름, resolver 인자와 reconciler 설명을 정규화한 251개 AST가 동일했다. 나머지 기존 URL 해석/후보 조립 함수 3개는 공용 해석 → 선택 resolver → evidence payload로 대응하여 조건·모든 필드·fallback을 검토했다. SQL을 이동한 세 helper, `schema.sql` 및 value registry bytes는 동일하다. schema presentation은 Data Model 소유 문서의 지문과 Session reference producer 설명 두 값만 바뀌었고 audit manifest 지문을 함께 갱신했다.
- Differential: 동일 140개 URL과 Markdown/bare hint를 등록 항목 있음·없음·bare hint 모호함의 3개 상태에 입력했다. 이전/현재 resolution, persisted evidence/scans와 Session projection 전체 JSON이 같았다. 이 비교는 session reconciler 시계를 고정했으며 값이나 필드를 제외하지 않았다.
- Targeted: URL/locator/session references/related-context/package-boundary 63개 통과 후 실제 수집 연결 테스트 1개를 추가해 통과했다. 빈 DB 테스트는 URL 해석/후보 resolution 범위이며 저장의 FK 제거를 주장하지 않는다.
- Full suite: 기존 Python 3.11.15 `.venv`와 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests`로 unittest discovery를 실행했다. `test_google_drive_transport.PoolTests.`의 정확히 11개는 사용자 보류에 따라 제외했고 **1,451개 통과**. 초기 실행의 stale schema audit ledger 1개 실패를 생성기로 갱신한 후 전체 suite를 다시 통과했다. 새 수집 fixture의 초기 확인은 stub에 remote_key가 있다고 가정해 실패했으나 기존 URL alias identity 계약으로 검증을 수정했다.
- Build/package: 기존 cached Hatchling으로 wheel을 만들고 offline/no-deps로 격리 설치했다. 최종 문서 metadata 생성 후 다시 만든 wheel의 206개 Python module 및 schema/value/presentation bytes가 현재 source와 동일했다. Wheel SHA256 `c30b9a529d9d1ccf42622c09aa3eddf969aa60b954b0cf1c3d90a072a7ae22b8`.
- Runtime: baseline source와 installed wheel 각각 web/desktop 실제 lifespan 시작·종료 및 synthetic Codex 파일 수집을 실행했다. 등록된 기존 항목·같은 Site의 새 URL stub·미등록 Confluence URL을 검증했다. 각 조합에서 health, Session 목록/상세, Atlassian의 4개 ASGI 요청 status와 상세 링크 표식, projection/evidence, 114개 route 순서/정의 및 OpenAPI가 같았다. 격리 runtime 경로와 synthetic 관측 시각만 정규화했으며 전체 HTML 동일성을 주장하지 않는다. 모델 import와 socket 연결을 차단한 실행이다.
- Runtime fixture adjustments: httpx가 없어 추가 설치 없이 직접 ASGI를 호출했다. wheel의 보호된 설치 경계 밖으로 synthetic runtime을 배치했다. desktop 상세 전체 HTML의 링크 존재는 baseline에도 관측되어 기존 출력과 비교했으며 제품 동작을 변경하지 않았다.
- 최종 metadata 생성 후 전체 suite를 다시 통과했다. 문서/schema/value/presentation/audit 검사와 owner/plan 문서의 로컬 링크 209개를 확인했다. Privacy와 whitespace도 통과했다. 새 synthetic userinfo URL 2개는 개인정보 email 패턴에 걸려 기존 테스트처럼 문자열 조합으로 표현하고 동일한 unsafe 입력 검사 4개를 다시 통과했다.

## Risks / Limitations

- 빈 DB URL 해석은 통과한다. 전체 reference reconciliation에서 Atlassian 테이블을 삭제한 초기 실험은 기존 FK 때문에 실패했다. FK 검사를 끄거나 DDL을 바꿔 독립성을 가장하지 않았다. 저장 분리는 별도 migration과 삭제·기존 데이터 보존 결정이 필요하다.
- `resources/related_context.py`의 교차 SQL, 다른 ingestion/context cleanup, legacy search, lifecycle와 기존 저장 목적지 연결은 남는다. 폴더만 삭제하면 기능 제거가 끝난다고 주장하지 않는다.
- Slack grammar·새 product label은 추가하지 않았다. UI 재설계, live provider/data, 모델 품질, full optional-feature-free 앱 조립, native browser 및 새 frozen build는 이 배치 검증 범위 밖이다. 이전 frozen build 결과를 이번 source 검증으로 재사용하지 않는다.
- Drive 11개 검사는 재승인을 요청하지 않고 사용자 보류를 유지했다. 커밋·push·설치 앱 교체는 수행하지 않았다.

## Next Action

- 다음 독립화는 active plan의 나머지 ingestion/Local Context/related-resource 연결부를 대상으로 같은 transaction과 삭제 계약을 확인하며 진행한다. 저장 FK 제거는 별도 Semantic 범위다.
- 이 배치의 snapshot/build/runtime/drafting scratch는 검증 소비자 종료 후 제거했다. 지속 근거는 이 log와 owner 문서에 남기며 임시 경로에 의존하지 않는다.
