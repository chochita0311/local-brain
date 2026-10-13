"""Authored public retrieval fixture. Contains no adapted personal source material."""

import math
import sqlite3

from natural_search_fixtures import fixture

# Each subject has multiple relevant parents; titles alone are deliberately terse.
SUBJECTS = [
    ('mobile', 'Pocket', 'Flutter로 휴대전화용 가계부 앱을 만들었다. 지출 입력 화면과 월별 합계를 구현하고 iOS 시뮬레이터에서 실행했다.',
     'The Pocket mobile application records spending and shows monthly totals on iPhone. We implemented a Flutter screen and tested touch input.'),
    ('offline', 'Fieldnote', '인터넷 연결이 끊겨도 입력한 메모가 사라지지 않게 휴대폰 앱에 저장했다. 비행기 모드에서는 로컬 큐에 쌓고 연결 복구 후 서버와 동기화한다.',
     'Fieldnote keeps drafts on the device without a network. Background synchronization retries queued changes when connectivity returns.'),
    ('deploy', 'Release train', 'Jenkins CI 파이프라인에서 컨테이너 이미지를 빌드하고 staging에 배포했다. 운영 승인은 수동이며 실패하면 이전 이미지로 롤백한다.',
     'The release pipeline builds a container image, deploys it to staging and rolls back to the previous image on failure. Production requires manual approval.'),
    ('database', 'Lock ordering', 'MySQL 트랜잭션 두 개가 서로 다른 순서로 행을 잠가 교착 상태가 발생했다. 갱신 순서를 통일하고 deadlock victim만 재시도하도록 수정했다.',
     'Concurrent MySQL transactions acquired row locks in opposite order. Consistent lock ordering and a bounded retry resolved the deadlock.'),
    ('auth', 'Callback', 'OAuth 로그인 후 callback에서 state 검증이 실패하는 원인을 조사했다. CSRF 방어를 유지하면서 쿠키의 SameSite와 redirect_uri 설정을 수정했다.',
     'OAuth sign-in failed at the callback because the state cookie was missing. We corrected SameSite and redirect_uri while retaining CSRF validation.'),
    ('search', 'Retriever', '등록된 문서를 문단으로 나누고 임베딩 벡터를 생성했다. 사용자가 다른 말로 질문해도 의미가 비슷한 근거를 찾도록 어휘 순위와 결합했다.',
     'The retrieval system splits documents into passages, embeds them and combines lexical and vector ranking to find evidence for paraphrased questions.'),
    ('measurement', 'Measurement', 'OpenCount purchase 이벤트가 결제 완료 화면에서 두 번 전송됐다. receipt_ref로 중복을 방지하고 환불 이벤트와 매출 보고서를 대조했다.',
     'Duplicate OpenCount purchase events inflated revenue. A receipt_ref guard prevents double counting and refund events reconcile the report.'),
    ('storage', 'Cache ownership', 'macOS Application Support에는 사용자 설정과 원본 데이터베이스를 보관한다. 다시 만들 수 있는 미리보기는 Caches에 두고 앱 삭제 후 보존 범위를 설명했다.',
     'User preferences and the primary database live in Application Support. Rebuildable previews belong in Caches, with separate removal and recovery rules.'),
    ('accessibility', 'Focus path', '검색 화면을 키보드만으로 사용할 수 있도록 Tab 순서와 focus ring을 정리했다. 한글 IME 조합 중 Enter는 글자 확정만 하고 검색을 제출하지 않는다.',
     'Keyboard access to the search page preserves tab order and visible focus. Enter during Korean IME composition confirms text without submitting the form.'),
    ('garden', 'Balcony', '베란다 토마토 화분의 흙이 마르면 아침에 물을 주었다. 햇빛이 부족한 화분을 창가로 옮기고 새 잎의 상태를 기록했다.',
     'Balcony tomatoes need morning watering when the soil is dry. We moved the pot toward sunlight and recorded new leaf growth.'),
    ('cooking', 'Dinner', '양파를 볶고 토마토 소스를 넣어 파스타를 만들었다. 면수를 조금 섞어 농도를 맞추고 소금은 마지막에 조절했다.',
     'Dinner was tomato pasta with sautéed onions. A little pasta water thickened the sauce before the final seasoning.'),
    ('calendar', 'Team schedule', '다음 팀 회의는 목요일 오후로 옮겼다. 참석자의 시간대가 달라 UTC와 현지 시각을 함께 공지하고 중복 초대를 취소했다.',
     'We moved the team meeting to Thursday afternoon, included UTC and local times, and cancelled duplicate calendar invitations.'),
]

QUERIES = [
    ('mobile-purpose', '휴대전화에서 돈 쓴 내역을 입력하는 걸 만들던 세션', {'mobile':2}, 'session'),
    ('mobile-paraphrase', '지출을 기록하는 모바일 프로그램 개발', {'mobile':2}, ''),
    ('mobile-english', 'Which work covered building an iPhone spending tracker?', {'mobile':2}, ''),
    ('broad-app', '만들던 앱 관련 세션을 보여줘', {'mobile':2,'offline':2}, 'session'),
    ('offline-purpose', '네트워크가 없어도 작성하던 내용이 남게 한 작업', {'offline':2}, ''),
    ('offline-english', 'Find sessions about retrying background sync after reconnecting', {'offline':2}, ''),
    ('offline-docs', '비행기 모드에서 메모 저장하는 문서만', {'offline':2}, 'document'),
    ('deploy-paraphrase', '새 버전 올리다 실패하면 되돌리는 절차', {'deploy':2}, ''),
    ('deploy-id', 'Jenkins', {'deploy':2}, ''),
    ('database-cause', '서로 잠금을 기다리며 멈춘 데이터 갱신 문제', {'database':2}, ''),
    ('database-english', 'Concurrent row updates blocked each other', {'database':2}, ''),
    ('auth-purpose', '로그인하고 돌아오면 검증 실패하던 문제', {'auth':2}, ''),
    ('auth-id', 'redirect_uri', {'auth':2}, ''),
    ('search-paraphrase', '표현이 달라도 관련 글을 찾아주는 기능', {'search':2}, ''),
    ('search-docs', '문서만 의미 기반으로 찾는 방식', {'search':2}, 'document'),
    ('measurement-cause', '한 번 결제했는데 매출이 두 배로 잡힌 원인', {'measurement':2}, ''),
    ('measurement-id', 'receipt_ref', {'measurement':2}, ''),
    ('storage-purpose', '다시 만들 수 있는 파일과 보존할 데이터를 어디에 두는지', {'storage':2}, ''),
    ('keyboard-purpose', '마우스 없이 탐색하고 한글 입력 중 제출을 막는 처리', {'accessibility':2}, ''),
    ('keyboard-id', 'IME', {'accessibility':2}, ''),
    ('garden-purpose', '잎이 잘 자라도록 물과 햇빛을 조절한 기록', {'garden':2}, ''),
    ('cooking-purpose', '저녁에 면 요리를 준비한 방법', {'cooking':2}, ''),
    ('calendar-purpose', '다른 시간대 동료들에게 약속 변경을 알린 내용', {'calendar':2}, ''),
    ('no-answer-visa', '호주 관광 비자 신청 수수료', {}, ''),
    ('no-answer-physics', '중성자별 충돌의 중력파 스펙트럼', {}, ''),
    ('no-answer-pet', '고양이 예방 접종 일정', {}, ''),
    ('no-answer-poem', '고려 시대 시조 작품 해설', {}, ''),
]


def seed(root):
    config = fixture(root)
    relevance = {}
    with sqlite3.connect(config.database_path) as connection:
        connection.execute('DELETE FROM search_index')
        connection.execute('DELETE FROM activity_events')
        connection.execute('DELETE FROM sessions')
        connection.execute('DELETE FROM context_documents')
        for position, (topic, title, korean, english) in enumerate(SUBJECTS):
            for variant in range(6):
                ident = position * 6 + variant + 1
                kind = 'session' if variant < 4 else 'document'
                # Two long parents per topic contain decisive evidence at the tail.
                filler = ('작업 기록을 정리하며 날짜와 작성 순서를 확인했다. 아직 확정되지 않은 사항은 별도로 남겼다.\n\n' * 65) if variant in (3,5) else ''
                body = filler + (english if variant in (1,5) else korean)
                body += '\n' + ('검토 후 해당 결정을 반영했다.' if variant % 2 == 0 else 'The next review retains this decision.')
                path = f'/synthetic/benchmark/{topic}-{variant}'
                if kind == 'session':
                    connection.execute("""INSERT INTO sessions(id,source_id,external_id,source_path,title,session_class,session_role,index_policy,last_event_at)
                        VALUES (?,1,?,?,?,'work','primary','full','2026-10-06T05:00:00Z')""", (ident,str(ident),path,title))
                    connection.execute("INSERT INTO activity_events(id,session_id,sequence,event_type,role,text,source_line) VALUES (?, ?,0,'message','user',?,1)", ('benchmark-'+str(ident),ident,body))
                else:
                    connection.execute("""INSERT INTO context_documents(id,source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash)
                        VALUES (?,2,1,?,?,?,?,?,1791252000000000000,?)""",(ident,path,path.rsplit('/',1)[-1],title,body,len(body.encode()),'synthetic-'+str(ident)))
                connection.execute('INSERT INTO search_index VALUES (?,?,?,?,?,?)',(kind,str(ident),'codex' if kind=='session' else 'context',title,body,path))
                relevance[f'{kind}:{ident}'] = {'topic':topic,'kind':kind,'long_tail':variant in (3,5)}
    queries = []
    for name, query, grades, kind in QUERIES:
        expected = {key: grades[data['topic']] for key,data in relevance.items()
                    if data['topic'] in grades and (not kind or kind == data['kind'])}
        queries.append({'id':name,'query':query,'expected':expected})
    return config, queries, relevance


def metrics(results, expected, k=10):
    chosen = results[:k]
    hits = sum(key in expected for key in chosen)
    ideal = sum((2**grade-1)/math.log2(i+2) for i,grade in enumerate(sorted(expected.values(),reverse=True)[:k]))
    dcg = sum((2**expected.get(key,0)-1)/math.log2(i+2) for i,key in enumerate(chosen))
    return {'recall10':hits/len(expected) if expected else None,
            'hit10':int(hits>0) if expected else None,'ndcg10':dcg/ideal if ideal else None,
            'precision10':hits/len(chosen) if chosen else 0,
            'answerable_empty':int(not results) if expected else None,
            'no_answer_false_positive':int(bool(results)) if not expected else None}


def aggregate(rows):
    return {key:round(sum(values)/len(values),4) for key in rows[0]
            if (values := [row[key] for row in rows if row[key] is not None])}
