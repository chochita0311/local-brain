"""Authored homonyms/list distractors; no copied or adapted private source text.

Expected topics are fixed before running the model. The holdout is observed only
after choosing the ranking policy from the development and prior selection sets.
"""

import sqlite3

from natural_search_fixtures import fixture


# topic, Korean source, independent English source, Korean query, English query
DEVELOPMENT = [
    ('layout', '설정 화면에서 저장 버튼이 화면 밖으로 밀렸다. CSS grid의 열 너비와 패널 간격을 조정하고 좁은 화면에서도 버튼이 보이게 배치를 수정했다.',
     'We rearranged the settings page panels and action buttons. Responsive CSS grid columns now keep the Save control visible on narrow screens.',
     '화면 배치를 조정한 문서만', 'Rearranging the interface panels so controls fit on small displays'),
    ('batch', '야간 배치 작업이 한꺼번에 시작되어 데이터베이스가 느려졌다. 데이터 처리 배치의 실행 시간을 나누고 작업당 처리 건수를 줄였다.',
     'Nightly batch jobs overloaded the database. We staggered their schedules and reduced the number of records processed in each batch.',
     '새벽에 몰리던 일괄 데이터 처리 작업', 'Staggering scheduled batch processing to reduce database load'),
    ('mobile', '휴대전화에서 복약 시간을 기록하는 앱을 개발했다. 알림 설정 화면과 복용 완료 버튼을 구현하고 Android 기기에 설치해 동작을 확인했다.',
     'We built a medication reminder application for phones, implemented the schedule screen and completion button, and tested it on an Android device.',
     '휴대전화용 앱을 개발한 내용', 'Building a smartphone application that reminds people to take medicine'),
    ('wordlist', '상품 검색용 단어 목록을 정리했다. 다음은 개발 기록이 아니라 검색어 사전이다.\n' +
     '휴대전화 모바일 앱 휴대폰 스마트폰 phone mobile application Android tablet\n' * 22,
     'A product-search vocabulary inventory, not an application implementation.\n' +
     'phone smartphone mobile app application tablet 휴대전화 모바일 앱 휴대폰\n' * 22,
     '휴대폰 상품 검색어 사전을 정리한 자료', 'The keyword inventory used for product search'),
    ('auth', '웹 서비스 로그인에서 세션 쿠키 탈취를 막는 보안 작업을 했다. HttpOnly와 Secure 속성을 적용하고 인증 토큰 재사용을 제한했다.',
     'We hardened web authentication against session-cookie theft, enabled HttpOnly and Secure, and limited reuse of authentication tokens.',
     '로그인 쿠키가 도난당하지 않게 한 보안 작업', 'Protecting web sign-in sessions from stolen cookies'),
    ('door', '사무실 출입문이 제대로 잠기지 않아 보안 점검을 했다. 문틀과 잠금 장치를 교체하고 출입 카드로 열고 닫히는지 시험했다.',
     'We inspected office physical security, replaced the faulty door lock and frame, and tested entry with access cards.',
     '출입문 잠금 장치를 고친 보안 점검', 'Repairing the physical lock on the office entrance'),
    ('auth-token', 'API 인증 토큰이 로그에 남는 문제를 수정했다. 비밀 토큰 값은 출력하지 않고 만료 여부와 요청 식별자만 기록한다.',
     'We removed API authentication tokens from logs. The system records expiry status and request identifiers without writing credential values.',
     '인증 토큰이 로그에 노출되던 문제', 'Preventing API credentials from leaking through diagnostic logs'),
    ('text-token', '언어 모델 입력을 토큰으로 나누고 한국어와 영어의 토큰 수를 비교했다. 최대 입력 길이를 넘는 문장은 여러 구간으로 잘랐다.',
     'We counted language-model tokens in Korean and English text and split long inputs into spans that fit the context window.',
     '한국어 문장을 모델 입력 길이에 맞춰 나눈 처리', 'Counting text tokens and splitting long model inputs'),
    ('db-index', '회원 조회가 느려 쿼리 실행 계획을 확인했다. 이메일 열에 데이터베이스 인덱스를 만들고 전체 테이블 스캔이 사라지는지 확인했다.',
     'We added an index to the email column after inspecting a slow member-lookup query plan. The database no longer scans the whole table.',
     '조회 속도를 높이려고 색인을 만든 작업', 'Adding a database index to speed up email lookups'),
    ('book-index', '책 뒤의 색인을 편집했다. 주요 인물과 용어를 가나다순으로 배열하고 해당 내용을 다루는 쪽 번호를 확인했다.',
     'We edited the back-of-book index, sorted names and terms alphabetically, and verified the page references.',
     '책의 용어별 쪽 번호를 정리한 내용', 'Editing the alphabetical index at the back of a book'),
    ('git-branch', '기능 브랜치의 변경을 main에 병합하다 충돌이 났다. 두 브랜치의 수정 의도를 비교하고 테스트 후 merge commit을 만들었다.',
     'We resolved a Git merge conflict between a feature branch and main, checked both edits and created the merge commit after testing.',
     '개발 브랜치를 합치다가 충돌을 해결한 기록', 'Resolving conflicts when merging a feature branch'),
    ('tree-branch', '나무 가지가 창문에 닿아 가지치기를 했다. 죽은 가지를 제거하고 살아 있는 가지는 새눈 위에서 잘라 상처를 줄였다.',
     'We pruned tree branches touching the window, removed dead growth and cut living branches above new buds.',
     '창문에 닿던 나뭇가지를 잘라낸 기록', 'Pruning tree branches beside a window'),
]

HOLDOUT = [
    ('tls', '웹 서버 인증서가 만료되어 HTTPS 연결이 실패했다. 새 TLS 인증서와 중간 체인을 설치하고 호스트 이름과 만료 시각을 확인했다.',
     'HTTPS stopped working after the server certificate expired. We installed a renewed TLS certificate and intermediate chain, then checked hostname validation.',
     '웹사이트 암호화 연결이 인증서 때문에 안 되던 문제', 'Renewing the expired certificate used by an HTTPS server'),
    ('diploma', '교육 과정 수료 인증서에 이름이 잘못 인쇄됐다. 수강 기록을 확인하고 이름을 수정한 새 인증서를 발급했다.',
     'A course-completion certificate had a misspelled student name. We verified attendance and reissued the corrected document.',
     '수료증에 잘못 적힌 이름을 고친 기록', 'Correcting a name on a course completion certificate'),
    ('shell', '셸 스크립트에서 공백이 든 파일 경로가 여러 인수로 분리됐다. 변수 확장에 따옴표를 넣고 반복문을 수정해 파일 이름을 보존했다.',
     'A shell script split filenames containing spaces into several arguments. Quoting variable expansions fixed the command-line processing.',
     '터미널 명령에서 공백 든 파일 이름이 깨지던 문제', 'Quoting shell variables to preserve filenames with spaces'),
    ('seashell', '해변에서 주운 조개껍데기를 씻고 말렸다. 깨진 껍질은 골라내고 크기와 무늬에 따라 표본을 분류했다.',
     'We cleaned seashells collected on the beach, removed broken shells and sorted the specimens by size and pattern.',
     '바닷가에서 모은 껍데기를 정리한 기록', 'Cleaning and sorting shells collected from the beach'),
    ('tcp-port', '서버의 포트가 닫혀 클라이언트 연결이 거부됐다. 방화벽 허용 규칙과 서비스 listen 주소를 확인하고 TCP 접속을 시험했다.',
     'Clients could not connect to a closed server port. We checked firewall allow rules and the listen address, then tested the TCP connection.',
     '서버에 네트워크 연결이 거절되어 포트를 확인한 작업', 'Opening a blocked service port after checking firewall rules'),
    ('harbor', '항구 부두에 선박이 몰려 하역이 지연됐다. 입항 시간표를 조정하고 크레인 배정을 바꿔 대기 시간을 줄였다.',
     'Vessels crowded the harbor and cargo unloading was delayed. We changed arrival slots and crane assignments at the port.',
     '항구에서 배들이 하역을 기다리던 문제', 'Scheduling cargo unloading at a crowded port'),
    ('gpu-driver', '그래픽 드라이버를 갱신한 뒤 화면이 깜박였다. 이전 드라이버로 되돌리고 모니터 연결과 주사율 설정을 확인했다.',
     'The display flickered after a graphics driver update. We rolled back the driver and checked monitor connections and refresh rate.',
     '그래픽 장치 업데이트 뒤 화면이 깜박이던 문제', 'Rolling back a graphics driver to fix display flicker'),
    ('bus-driver', '버스 운전자의 교대 시간을 조정했다. 장거리 운행 사이 휴식 시간을 확보하고 다음 운전자에게 차량 상태를 인계했다.',
     'We adjusted bus driver shifts, added rest time between long routes and handed vehicle-condition notes to the next driver.',
     '버스 운전 교대와 쉬는 시간을 정한 기록', 'Planning rest breaks and shift handover for bus drivers'),
]


def seed(root, *, held_out=False):
    config = fixture(root)
    topics = HOLDOUT if held_out else DEVELOPMENT
    expected_by_topic, relevance = {}, {}
    with sqlite3.connect(config.database_path) as connection:
        for table in ('search_index', 'activity_events', 'sessions', 'context_documents'):
            connection.execute('DELETE FROM ' + table)
        for position, (topic, korean, english, _, _) in enumerate(topics):
            expected_by_topic[topic] = {}
            # Each language exists as a Session and a Context document. Filters
            # therefore cannot succeed merely by excluding a distractor's kind.
            for variant in range(4):
                ident = position * 4 + variant + 1
                kind = 'session' if variant < 2 else 'document'
                body = korean if variant % 2 == 0 else english
                path = '/synthetic/precision/{}/{}'.format(topic, variant)
                title = '검토 기록 {:02d}'.format(ident)
                if kind == 'session':
                    connection.execute("""INSERT INTO sessions
                        (id,source_id,external_id,source_path,title,session_class,session_role,index_policy,last_event_at)
                        VALUES (?,1,?,?,?,'work','primary','full','2026-10-06T05:00:00Z')""",
                        (ident, str(ident), path, title))
                    connection.execute("""INSERT INTO activity_events
                        (id,session_id,sequence,event_type,role,text,source_line)
                        VALUES (?,?,0,'message','user',?,1)""", ('precision-'+str(ident), ident, body))
                else:
                    connection.execute("""INSERT INTO context_documents
                        (id,source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash)
                        VALUES (?,2,1,?,?,?,?,?,1791252000000000000,?)""",
                        (ident, path, path.rsplit('/', 1)[-1], title, body, len(body.encode()), 'precision-'+str(ident)))
                key = kind+':'+str(ident)
                expected_by_topic[topic][key] = 2
                relevance[key] = {'topic': topic, 'kind': kind}
    queries = []
    for topic, _, _, korean_query, english_query in topics:
        for language, query in (('ko', korean_query), ('en', english_query)):
            expected = expected_by_topic[topic]
            if '문서만' in query:
                expected = {key: grade for key, grade in expected.items() if key.startswith('document:')}
            queries.append({'id': topic+'-'+language, 'query': query, 'expected': expected})
    if not held_out:
        queries.extend([
            {'id': 'auth-session', 'query': '로그인 세션을 보호한 작업 세션 찾아줘',
             'expected': {key: grade for key, grade in expected_by_topic['auth'].items() if key.startswith('session:')}},
            {'id': 'exact-identifier', 'query': 'HttpOnly', 'expected': expected_by_topic['auth']},
        ])
    negatives = [('eclipse', '일식 관측에 필요한 태양 필터 선택'), ('pottery', '도자기 유약을 구운 온도 기록'),
                 ('whale', '혹등고래 이동 경로 연구')] if held_out else [
        ('origami', '색종이로 학을 접는 순서'), ('volleyball', '배구 리그 경기 결과'),
        ('concert', '바이올린 협주곡 공연 감상')]
    queries.extend({'id': 'empty-'+name, 'query': query, 'expected': {}} for name, query in negatives)
    return config, queries, relevance
