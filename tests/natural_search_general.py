"""Authored multi-domain work retrieval, with labels fixed before model runs.

Each topic has a Korean Session and an independently worded English Context.
Broad queries expect several concrete activities; titles do not reveal topics.
No source or query is copied or adapted from the private corpus.
"""

import sqlite3

from natural_search_fixtures import fixture


DEVELOPMENT = [
    ('db', '주문 조회 API가 느려 실행 계획을 확인했다. 고객 번호와 주문일에 복합 인덱스를 추가하여 전체 테이블 스캔을 없애고 응답 시간을 줄였다.',
     'Investigated slow order lookups and added a composite database index on customer and date. Query plans now avoid scanning every row.'),
    ('cache', '상품 목록을 요청할 때마다 같은 계산을 반복했다. 계산 결과를 메모리 캐시에 보관하고 상품이 변경될 때만 무효화하여 응답 지연을 줄였다.',
     'Reused computed catalog results in a memory cache with invalidation on product changes, reducing repeated work and request latency.'),
    ('payload', '웹 화면을 열 때 내려받는 자바스크립트가 너무 컸다. 경로별로 번들을 분리하고 사용하지 않는 라이브러리를 제거해 첫 화면 로딩을 빠르게 했다.',
     'Split JavaScript bundles by route and removed unused libraries to reduce download size and improve initial page loading.'),
    ('pipeline', '커밋 후 수동으로 하던 컴파일과 단위 검사를 CI에서 자동 실행했다. 성공한 빌드 산출물만 스테이징 환경으로 전달하도록 파이프라인을 연결했다.',
     'Automated compilation and unit checks after each commit. Only successful build artifacts are promoted to the staging environment.'),
    ('rollback', '신규 버전을 운영에 올린 뒤 오류율이 증가했다. 직전 이미지로 되돌리는 롤백 절차를 실행하고 트래픽을 정상 버전으로 복구했다.',
     'A production release increased the error rate. Restored the previous container image and routed traffic back to the healthy version.'),
    ('layout', '관리 화면 오른쪽 패널 때문에 저장 버튼이 가려졌다. 그리드 열과 버튼의 화면 배치를 조정하고 작은 창에서도 조작할 수 있게 했다.',
     'Rearranged the administration screen panels and grid columns so the Save button remains reachable in small windows.'),
    ('keyboard', '폼을 마우스 없이 작성할 수 있게 탭 이동 순서와 포커스 표시를 수정했다. 스크린리더가 입력 오류의 설명을 읽도록 연결했다.',
     'Improved keyboard navigation and visible focus for a form. Screen readers can now announce validation errors associated with each input.'),
    ('events', '결제 한 건이 분석 보고서에 두 번 잡혔다. 이벤트 발행 경로를 추적하고 거래 식별자로 중복을 제거하여 집계 수치를 맞췄다.',
     'Traced duplicate purchase notifications that inflated measurement totals and deduplicated events by transaction identifier.'),
    ('schema', '여러 서비스가 보내는 이벤트 속성 이름이 달라 분석이 누락됐다. 공통 스키마를 정하고 필수 필드 검증을 수집 단계에 추가했다.',
     'Unified inconsistent event property names across services and validated required fields at collection time to prevent missing measurements.'),
    ('docs', '같은 설치 절차가 여러 문서에 흩어져 서로 다른 설명을 했다. 정본 안내를 한 곳에 두고 나머지 문서는 링크로 연결해 중복을 정리했다.',
     'Consolidated conflicting installation instructions into one authoritative guide and linked the remaining documents to it.'),
    ('setup', '새 개발자가 프로젝트를 실행할 수 있도록 의존성 설치와 환경 설정 순서를 문서로 작성했다. 빈 환경에서 안내를 따라 실행되는지 확인했다.',
     'Wrote and verified a getting-started guide for new developers, covering dependencies, environment configuration and first launch.'),
    ('retry', '네트워크가 잠깐 끊기면 업로드가 영구 실패했다. 재시도 횟수와 지수 백오프를 추가하고 같은 파일이 중복 등록되지 않도록 했다.',
     'Made uploads survive transient network failures through bounded retries and exponential backoff while preventing duplicate registrations.'),
    ('backup', '장애 후 복구를 준비하려고 데이터베이스 백업을 별도 환경에 복원했다. 실제 레코드와 권한이 돌아오는지 확인하고 복구 절차를 보완했다.',
     'Restored a database backup in an isolated environment and verified records and permissions as part of disaster recovery preparation.'),
    ('credentials', '진단 로그에 비밀 인증 값이 남는 경로를 제거했다. 액세스 토큰을 출력하지 않도록 로깅 코드를 바꾸고 노출된 자격 증명을 교체했다.',
     'Removed secret credentials from diagnostic logging and rotated exposed access tokens after reviewing the leakage path.'),
    ('permission', '읽기 전용 사용자도 설정을 변경할 수 있었다. 서버에서 역할별 권한을 검사하고 허용되지 않은 수정 요청을 거절하도록 고쳤다.',
     'Enforced server-side role checks after discovering read-only users could edit configuration. Unauthorized updates are now rejected.'),
    ('batch', '야간 데이터 배치 작업의 실행 시간이 겹쳤다. 일괄 처리 스케줄을 나누고 작업당 레코드 수를 낮춰 데이터베이스 부하를 분산했다.',
     'Rescheduled overlapping nightly data-processing batches and limited records per job to spread database load.'),
    ('book', '인쇄할 책 뒤에 붙는 색인을 정리했다. 용어를 가나다순으로 나열하고 본문에서 등장하는 페이지 번호를 대조했다.',
     'Edited the printed book index, sorted terms alphabetically and checked page references against the manuscript.'),
    ('dictionary', '검색어 사전을 위한 단어 목록이다. 실제 구현이나 장애 해결 기록은 아니다. ' + '앱 개발 성능 화면 배치 배포 데이터 문서 운영 보안 캐시 인덱스 ' * 18,
     'A vocabulary inventory for search suggestions, without implementation evidence. ' + 'application performance layout deployment data documentation operations security index cache ' * 18),
]

# id, natural-language query, expected topics, explicit source kind, category
DEVELOPMENT_QUERIES = [
    ('performance', '내가 작업하던 응답 속도 개선 관련 세션을 찾아줘', ['db', 'cache', 'payload'], 'session', 'broad'),
    ('delivery', '새 버전 배포를 준비하고 문제 생기면 복구했던 작업 자료 보여줘', ['pipeline', 'rollback'], '', 'broad'),
    ('usability', '사용자가 화면을 더 편하게 쓰도록 개선한 기록을 찾아줘', ['layout', 'keyboard'], '', 'broad'),
    ('measurement', '분석 수치가 믿을 만하게 나오도록 고친 작업 관련 자료 찾아줘', ['events', 'schema'], '', 'broad'),
    ('knowledge', '다른 사람이 개발 환경을 이해하기 쉽게 정리한 문서만 보여줘', ['docs', 'setup'], 'document', 'broad'),
    ('recovery', '작업이 실패해도 다시 이어갈 수 있게 만든 내용 찾아줘', ['retry', 'backup', 'rollback'], '', 'broad'),
    ('security', '내가 작업하던 보안 관련 세션을 찾아줘', ['credentials', 'permission'], 'session', 'broad'),
    ('db-index', '조회 속도를 높이려고 색인을 만든 작업 기록을 찾아줘', ['db'], '', 'ambiguous'),
    ('layout', '화면 배치를 조정한 문서만 찾아줘', ['layout'], 'document', 'ambiguous'),
    ('batch', '야간 데이터 배치를 조정한 세션을 보여줘', ['batch'], 'session', 'ambiguous'),
    ('book', '인쇄용 책의 색인을 편집하던 기록 찾아줘', ['book'], '', 'ambiguous'),
    ('dictionary', '업무 검색어 사전 단어 목록을 보여줘', ['dictionary'], '', 'list'),
    ('cache', '내가 작업하던 같은 계산을 매번 하지 않게 한 내용 찾아줘', ['cache'], '', 'purpose'),
    ('payload', '첫 화면이 늦게 뜨는 걸 줄이던 세션을 찾아줘', ['payload'], 'session', 'purpose'),
    ('pipeline', '커밋하면 자동으로 검사하고 빌드하던 작업 자료 보여줘', ['pipeline'], '', 'purpose'),
    ('rollback', '업데이트 후 문제가 생겨 이전 상태로 돌린 세션 찾아줘', ['rollback'], 'session', 'purpose'),
    ('keyboard', '마우스를 쓰기 어려운 사람도 폼을 작성할 수 있게 한 기록 찾아줘', ['keyboard'], '', 'purpose'),
    ('events', '한 번 산 물건이 매출에 두 번 잡히던 문제 관련 자료 찾아줘', ['events'], '', 'purpose'),
    ('schema', '서비스마다 보내는 분석 항목이 달라 누락되던 문제 문서만 보여줘', ['schema'], 'document', 'purpose'),
    ('docs', '서로 다른 설명이 여러 곳에 있던 걸 한 군데로 모은 세션 찾아줘', ['docs'], 'session', 'purpose'),
    ('setup', '처음 온 동료가 프로젝트를 실행하도록 안내한 기록 찾아줘', ['setup'], '', 'purpose'),
    ('retry', '연결이 잠깐 끊겨도 파일을 끝까지 보내게 고친 작업 찾아줘', ['retry'], '', 'purpose'),
    ('backup', '사고가 나도 보관한 데이터로 되살릴 수 있는지 확인한 문서만', ['backup'], 'document', 'purpose'),
    ('credentials', '로그에 비밀 값이 남지 않게 수정한 세션을 보여줘', ['credentials'], 'session', 'purpose'),
    ('permission', '설정을 바꾸면 안 되는 사람이 수정하던 문제 찾아줘', ['permission'], '', 'purpose'),
    ('english', 'Find work about reducing database query latency', ['db'], '', 'english'),
    ('negation', '화면 배치 말고 야간 데이터 처리 배치를 바꾼 작업 찾아줘', ['batch'], '', 'negative'),
    ('quoted', '"화면 배치" 관련 작업을 찾아줘', ['layout'], '', 'quoted'),
    ('empty', '내가 작성했던 화성 착륙선의 궤도 계산 문서 찾아줘', [], 'document', 'no-answer'),
]

HOLDOUT = [
    ('queue', '메시지 소비자가 처리 전에 확인 응답을 보내 작업이 유실됐다. 처리가 끝난 뒤에만 ack를 보내고 실패한 메시지는 큐에 남기도록 고쳤다.',
     'Stopped acknowledging queue messages before processing finished. Failed jobs remain available for redelivery instead of disappearing.'),
    ('webhook', '외부에서 같은 웹훅을 재전송할 때 주문이 여러 개 생겼다. 요청 식별자를 저장하고 이미 처리한 호출에는 기존 응답을 돌려준다.',
     'Made webhook processing idempotent by remembering request identifiers and reusing prior responses when notifications are redelivered.'),
    ('timezone', '시간대가 다른 사용자에게 예약 시각이 하루 어긋났다. UTC로 저장하고 표시할 때 현지 시간대로 변환하도록 수정했다.',
     'Fixed appointment dates shifting for users in different time zones. Store UTC timestamps and convert to the local zone only for display.'),
    ('encoding', '파일에서 읽은 한글이 깨져 보였다. 문자 인코딩을 명시적으로 UTF-8로 맞추고 저장과 읽기 경로가 같은 규칙을 쓰도록 했다.',
     'Repaired garbled Korean text by explicitly using UTF-8 consistently for file writing and reading.'),
    ('alert', '서비스 오류가 늘어도 담당자가 늦게 알았다. 오류율과 지연 시간에 경보를 걸고 일시적인 튀는 값은 대기 구간으로 걸렀다.',
     'Added alerts for sustained error rates and latency so operators learn about incidents quickly without reacting to transient spikes.'),
    ('trace', '한 요청이 여러 서비스 중 어디서 느려지는지 몰랐다. 공통 추적 식별자를 전달하고 구간별 소요 시간을 연결해 병목 위치를 찾았다.',
     'Propagated trace identifiers across services and joined span durations to locate the slow stage of a distributed request.'),
    ('pool', '요청마다 데이터베이스 연결을 새로 만들어 지연이 컸다. 연결 풀을 도입하고 최대 연결 수와 대기 시간을 제한했다.',
     'Reused database connections through a bounded connection pool instead of opening a new connection for every request.'),
    ('connection', '사용하지 않은 네트워크 소켓이 계속 남아 메모리가 증가했다. 응답 종료와 오류 경로에서 연결을 닫아 누수를 고쳤다.',
     'Closed unused network sockets on normal completion and error paths to stop a growing memory leak.'),
    ('swimming', '수영장 풀의 수질을 검사했다. 여과 장치의 순환 시간을 늘리고 염소 농도가 기준에 들어오는지 확인했다.',
     'Checked water quality in a swimming pool, increased filtration time and measured chlorine concentration.'),
    ('craft', '종이 모형에서 부품 간 연결이 헐거웠다. 접합 탭을 넓히고 접착제 건조 시간을 늘려 모형이 무너지지 않게 했다.',
     'Strengthened loose connections in a paper model by enlarging joining tabs and allowing glue to dry fully.'),
]

HOLDOUT_QUERIES = [
    ('delivery', '실패하거나 중복 전송돼도 작업이 제대로 처리되게 만든 자료 찾아줘', ['queue', 'webhook'], '', 'broad'),
    ('international', '언어나 지역이 달라도 제대로 표시되게 고친 작업 세션 찾아줘', ['timezone', 'encoding'], 'session', 'broad'),
    ('operations', '서비스에 문제가 생겼는지 빨리 파악하도록 만든 문서만 보여줘', ['alert', 'trace'], 'document', 'broad'),
    ('resources', '서버 자원이 낭비되지 않게 관리한 내용 찾아줘', ['pool', 'connection'], '', 'broad'),
    ('queue', '실패한 일감이 사라지지 않게 고쳤던 세션을 보여줘', ['queue'], 'session', 'purpose'),
    ('webhook', '같은 알림이 여러 번 와도 주문은 한 번만 생기게 한 작업 찾아줘', ['webhook'], '', 'purpose'),
    ('timezone', '외국에서 보면 예약 날짜가 달라지는 문제 문서만 찾아줘', ['timezone'], 'document', 'purpose'),
    ('encoding', '저장한 한글이 이상한 문자로 보였던 기록 찾아줘', ['encoding'], '', 'purpose'),
    ('alert', '장애를 뒤늦게 발견하지 않도록 고친 세션을 찾아줘', ['alert'], 'session', 'purpose'),
    ('trace', '여러 서버를 거치는 요청이 어디서 막혔는지 찾은 문서만', ['trace'], 'document', 'purpose'),
    ('pool', '요청마다 연결을 만들지 않게 풀을 구성한 기록 보여줘', ['pool'], '', 'ambiguous'),
    ('connection', '서버 연결을 정리해 메모리를 줄인 세션을 찾아줘', ['connection'], 'session', 'ambiguous'),
    ('swimming', '물이 깨끗하게 유지되도록 풀을 관리한 내용 찾아줘', ['swimming'], '', 'ambiguous'),
    ('craft', '종이 모형 연결을 튼튼하게 만든 기록 찾아줘', ['craft'], '', 'ambiguous'),
    ('english', 'Find work about tracing latency across services', ['trace'], '', 'english'),
    ('negative', '수영장 말고 데이터베이스 연결 풀을 관리한 작업 찾아줘', ['pool'], '', 'negative'),
    ('quoted', '"메모리" 누수를 고친 세션을 보여줘', ['connection'], 'session', 'quoted'),
    ('empty', '예전에 작성한 중세 왕조의 계보 문서 찾아줘', [], 'document', 'no-answer'),
]


def seed(root, *, held_out=False):
    config = fixture(root)
    topics = HOLDOUT if held_out else DEVELOPMENT
    prompts = HOLDOUT_QUERIES if held_out else DEVELOPMENT_QUERIES
    relevance = {}
    with sqlite3.connect(config.database_path) as connection:
        for table in ('search_index', 'activity_events', 'sessions', 'context_documents'):
            connection.execute('DELETE FROM ' + table)
        for position, (topic, korean, english) in enumerate(topics):
            for variant, body in enumerate((korean, english)):
                ident = position * 2 + variant + 1
                kind = 'session' if variant == 0 else 'document'
                title, path = '작업 메모 {:02d}'.format(ident), '/synthetic/general/{}/{}'.format(topic, variant)
                if kind == 'session':
                    connection.execute("""INSERT INTO sessions
                        (id,source_id,external_id,source_path,title,session_class,session_role,index_policy,last_event_at)
                        VALUES (?,1,?,?,?,'work','primary','full','2026-10-06T05:00:00Z')""", (ident, str(ident), path, title))
                    connection.execute("""INSERT INTO activity_events
                        (id,session_id,sequence,event_type,role,text,source_line)
                        VALUES (?,?,0,'message','user',?,1)""", ('general-'+str(ident), ident, body))
                else:
                    connection.execute("""INSERT INTO context_documents
                        (id,source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash)
                        VALUES (?,2,1,?,?,?,?,?,1791252000000000000,?)""",
                        (ident, path, path.rsplit('/', 1)[-1], title, body, len(body.encode()), 'general-'+str(ident)))
                relevance[kind+':'+str(ident)] = {'topic': topic, 'kind': kind}
    queries = [{'id': ident, 'query': query, 'category': category,
                'expected': {key: 2 for key, info in relevance.items()
                             if info['topic'] in selected and (not kind or kind == info['kind'])}}
               for ident, query, selected, kind, category in prompts]
    return config, queries, relevance
