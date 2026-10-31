# Persistence Ownership And Recovery Delivery Split

## Log Type

- Type: `Batch / Wrap-Up`
- Date: `2026-10-30`
- Related track: [REFACTOR-0003 Step 10](../refactor-0003-session-centered-package-boundaries.md#step-10---separate-persistence-bootstrap-and-recovery-responsibilities).
- Scope: 점검 결과 3번에 대한 사용자 후속 지시. DB 연결/초기화/주제별 migration 및 backup/recovery HTTP 책임을 분리한다. 기능 유지 여부·검색·작업 실행·DDL/운영 데이터 변경은 포함하지 않는다.

## Summary

- Goal: migration 이력을 선택 기능의 런타임 코드와 구별하고, DB의 공개 진입점·초기화 순서·영역별 repair·복구 전달 책임을 분리한다.
- Outcome: `Pass` for Step 10. 전체 트랙은 검색 HTTP와 Maintenance/선택 기능 조립 잔여 때문에 `in-progress`를 유지한다.
- DB 공개 진입점은 2,002줄에서 35줄로 줄었다. 완료 근거는 줄 수가 아니라 아래 책임 이동과 검사 결과다. 코드 변경만 수행했으며 기존 운영 DB와 실행 중 서버를 다시 변경하지 않았다.

## What Changed

| 이전 책임 | 현재 소유자 |
| --- | --- |
| `persistence/db.py` connect/init/transaction | 공개 API는 같은 파일에 유지. init은 explicit config/connection을 bootstrap에 전달한다. |
| init 순서·preflight backup·DDL 적용·가격 snapshot·commit 후 백업 정리 | `persistence/bootstrap.py` |
| schema 확인·열 추가/제거·동일 legacy backup 절차 | `persistence/migrations/support.py` |
| Source identity와 TOML/기존 PK 이행 | `persistence/migrations/sources.py` |
| Session 제약·skill evidence·activity metadata / Session revision | `persistence/migrations/sessions.py`, `session_revisions.py` |
| Local Context legacy root 연결 | `persistence/migrations/local_context.py` |
| Usage 이름/귀속 / Maintenance 조직 FK / Atlassian catalog 계약 | `persistence/migrations/usage.py`, `maintenance.py`, `atlassian.py` |
| 공용 자원 identity·binding·evidence·본문/메모 및 External URL scope 이행 | `persistence/migrations/resources.py` |
| 이행 순서·호환 열/index 적용 / index 수선 / 완료 계약 확인 | `persistence/migrations/compatible.py`, `indexes.py`, `contracts.py` |
| 복구 작업 + HTTP route가 섞인 `app/storage/recovery.py` | 작업·backend lease는 유지하고 HTTP 등록/업로드/내보내기/응답은 `app/storage/web.py`로 분리 |

- Added: migration 하위 package와 경계 검사. schema 생성/문서 검사는 `db.py` 하나 대신 공개 진입점·bootstrap·모든 migration module의 정렬된 경로/내용 manifest를 검증한다. 도메인 migration만 바뀌어도 fingerprint가 변하는 검사를 추가했다.
- Updated: 실제 호출자·test import/patch target·문서 소유권·값 사전·schema presentation과 cleanup audit의 manifest digest. schema audit disposition은 keep 643/defer 112를 유지했다. Schema Presentation 문서의 이전 object 수 표기도 실제 기존 baseline 수치와 맞췄다.
- Moved/Renamed: 기존 `resource_migration.py`, `source_identity_migration.py`, `source_revision_migration.py`를 위 migration 소유자로 이동했다. 이전 경로를 일괄 재수출하는 facade는 만들지 않았다.
- Removed: `storage → db → storage` 순환 의존. backup retirement는 독립 `migrations.contracts`를 명시적으로 import한다. 동일 AST를 확인한 6개의 legacy backup 절차만 공통화했고, shared-resource와 Session-revision의 별도 권한/검증 계약은 유지했다.

## Behavior / Parity Notes

- Type: `Structural / Internal Interface`. 새 데이터 의미나 product 동작 변경은 없다.
- Baseline: HEAD `6c03265701d0d8b552fc8bb60e346ba1971f4bb3` 위의 REFACTOR-0005 적용 후 작업 트리. src/tests/scripts/build 설정 475개 파일 manifest digest `1d3efabf6dac2774bceabbf373ee732dca1d391dd468428ee8fe2aaf9868ff51`. 기존 미커밋 작업을 별도 기준으로 복사했으며 HEAD diff 전체를 이번 변경으로 취급하지 않는다.
- public `connect/init_db/transaction` signature, SQLite timeout/busy_timeout/FK, BEGIN/commit/rollback/close, migration 순서·조건·backup 이름/재사용/실패 정리, SQL string 및 fresh schema bytes를 유지했다.
- 내부 변화는 migration 함수의 실제 import/module 위치, 설정을 인자로 전달하는 경로, 동일 backup procedure의 함수 추출, HTTP handler 소유 module 및 생성 metadata의 소스 fingerprint다. migration registry, 새 도메인 DB 또는 feature toggle을 도입하지 않았다.
- moved 함수 102개를 기준 AST와 대조했다. 명시적 config/connection 전달을 정규화하고 공통 backup 함수를 inline했을 때 SQL·분기·write·예외·transaction 처리가 일치했다. recovery 작업과 HTTP handler 함수 본문도 그대로다. storage의 계약 확인 함수 조회 위치 변경은 별도로 검사했다.
- Parity claim status: 이 배치의 검사된 흐름에는 보존 근거를 확보했다. 전체 REFACTOR-0003의 strict behavioral parity는 계속 `Provisional`이며 merge 판단은 수행하지 않았다.

## Validation

- Focused: schema/Atlassian/Session revision/shared-resource/installation/storage/desktop/foundation **123개 통과**. 옛 `db.migration_contracts_current` test 참조 1개는 실제 소유자로 옮긴 뒤 다시 검사했다. 이어 경계/schema presentation/Source/Context 검사 **67개 통과**.
- Full suite: Drive loopback `PoolTests`가 정확히 11개인지 확인하고 사용자 보류대로 제외한 **1,466개 통과**. 새 검사는 migration의 entrypoint/선택 기능 역의존 금지, recovery/contract의 HTTP/bootstrap 없는 import, migration 단독 변경의 fingerprint 반영이다.
- Runtime comparison: baseline과 current source를 각각 독립 runtime으로 실행했다. web/desktop 두 edition의 실제 lifespan 시작·종료, ordered HTTP route 113개(static mount 제외), 각 7개 요청의 status/header/body 및 effective schema가 일치했다. health·Sessions·Context·Settings·storage GET은 200, 잘못된 backup export는 기존 409, 미확인 restore는 422를 유지했다. 경로와 가용 디스크 공간만 비교에서 정규화했고 응답 길이는 경로 정규화 때문에 제외했다. 원문·provider·모델은 사용하지 않았다.
- Packaging: 로컬에 이미 있는 build dependency cache로 wheel 생성, 새 migration/bootstrap/storage-web 포함과 이전 migration 파일 부재 확인. 설치 layout의 Python 및 package resource bytes를 source와 비교했다. source checkout을 import 경로에서 배제한 설치 wheel에서도 실제 lifespan과 동일한 7개 요청, DB integrity/FK 검사를 통과했다. wheel 압축 해제로 달라지는 정적 자산 mtime 기반 `?v=` 값만 추가 정규화하여 baseline 응답과 비교했다.
- Docs/generated: `check-data-model-docs.py`, value dictionary generation/check, schema presentation build/check, cleanup audit check, Python AST parse, `git diff --check`, privacy 검사 통과. fresh DDL은 바뀌지 않았고 ordinary tables 52 + FTS5 1, FK 66, effective named index 51을 유지했다.
- Runtime DB 적용·서버 재시작·수동 수집·기능 활성화·커밋·배포를 하지 않았다. 임시 baseline/DB/wheel/검증 결과는 종료 시 제거했고 durable 문서는 임시 경로에 의존하지 않는다.

## Risks / Limitations

- ordered compatibility coordinator는 여러 주제의 기존 적용 순서를 명시적으로 유지한다. 일반적인 migration framework나 모든 table의 개별 실행기를 새로 만든 것이 아니다.
- 기존 함수 본문/SQL 대조와 synthetic failure/retry 검사, 두 edition 비교의 범위다. 모든 가능한 운영 중단 지점과 native/Tauri 새 바이너리까지 검증하지 않았다. packaged Python wheel과 설치된 native 앱의 적용 상태를 구별한다.
- 검색 HTTP의 Atlassian form/error 역의존과 Maintenance의 기능별 작업 연결은 이 배치에서 수정하지 않았다. 앱이 기능을 등록하는 정상 composition 자체를 잘못된 의존으로 분류하지 않는다.

## Next Action

Step 10은 완료로 유지한다. 향후 검색 공통 HTTP 처리와 Maintenance 작업별 adapter를
정리하고, 선택 기능 없는 전체 앱 fixture를 검증할 때 Step 8/9/11을 이어간다.
이번 migration 코드 이동 때문에 운영 DB를 다시 마이그레이션할 필요는 없다.
