"""Separate authored topic families, evaluated after freezing the search defaults."""

import sqlite3

from natural_search_fixtures import fixture

SUBJECTS = [
    ('paper', 'Paperbox', '종이 영수증을 카메라로 찍고 OCR로 날짜와 금액을 추출하는 스캐너를 만들었다. 인식이 틀린 부분은 사용자가 직접 고친다.',
     '사진 찍은 종이에서 글자와 숫자를 읽어내던 작업'),
    ('printer', 'Layer repair', '3D 프린터 첫 레이어가 바닥에서 떨어졌다. 노즐 높이와 베드 온도를 조정하고 표면을 닦아 출력 접착을 개선했다.',
     '입체 출력물이 시작부터 바닥에 붙지 않던 문제'),
    ('battery', 'Power budget', '노트북 배터리가 빨리 닳는 원인을 조사했다. 화면이 꺼져도 계속 실행되던 타이머를 멈추고 백그라운드 깨우기 횟수를 줄였다.',
     '컴퓨터를 쓰지 않을 때 전력이 많이 소모되던 이유'),
    ('audio', 'Sound desk', '녹음한 음성의 배경 잡음을 줄이고 구간별 음량을 맞췄다. 잡음 제거를 세게 걸면 목소리가 변하므로 원본과 번갈아 들었다.',
     '녹음 파일에서 주변 소리를 줄이는 방법'),
    ('backup', 'Restore drill', '외장 디스크에 파일을 복사한 뒤 복원 시험을 했다. 파일 목록과 체크섬을 비교하고 손상된 백업은 재생성했다.',
     '복사해 둔 자료를 실제로 되살릴 수 있는지 확인한 기록'),
    ('bicycle', 'Wheel care', '자전거 타이어에 작은 구멍이 생겨 공기가 샜다. 튜브를 물에 담가 기포 위치를 찾고 패치를 붙인 뒤 압력을 확인했다.',
     '바퀴에서 바람 빠지는 곳을 찾아 수리한 내용'),
    ('rain', 'Weather station', '옥외 센서의 강우량 기록에 빈 구간이 있었다. 전원 접촉을 고치고 버퍼에 남은 관측값을 다시 읽어 시계열을 복구했다.',
     '비가 얼마나 왔는지 측정하던 장치의 기록 누락'),
    ('subtitle', 'Caption tool', '영상 자막의 시작 시각이 소리보다 늦었다. 구간별 시간 오프셋을 조정하고 SRT 파일로 저장하는 편집 도구를 구현했다.',
     '화면의 대사 글자가 말소리와 어긋나던 문제'),
]


def seed(root):
    config = fixture(root)
    queries, relevance = [], {}
    with sqlite3.connect(config.database_path) as connection:
        for table in ('search_index', 'activity_events', 'sessions', 'context_documents'):
            connection.execute('DELETE FROM ' + table)
        for position, (topic, title, text, query) in enumerate(SUBJECTS):
            expected = {}
            for variant in range(3):
                ident = position * 3 + variant + 1
                kind = 'document' if variant == 2 else 'session'
                body = text if variant == 0 else ('검토 기록을 보존했다.\n\n' * 100 + text)
                path = '/synthetic/holdout/{}-{}'.format(topic, variant)
                if kind == 'session':
                    connection.execute("""INSERT INTO sessions
                        (id,source_id,external_id,source_path,title,session_class,session_role,index_policy,last_event_at)
                        VALUES (?,1,?,?,?,'work','primary','full','2026-10-06T05:00:00Z')""",
                        (ident, str(ident), path, title))
                    connection.execute("""INSERT INTO activity_events
                        (id,session_id,sequence,event_type,role,text,source_line)
                        VALUES (?,?,0,'message','user',?,1)""", ('holdout-'+str(ident), ident, body))
                else:
                    connection.execute("""INSERT INTO context_documents
                        (id,source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash)
                        VALUES (?,2,1,?,?,?,?,?,1791252000000000000,?)""",
                        (ident, path, path.rsplit('/', 1)[-1], title, body, len(body.encode()), 'holdout-'+str(ident)))
                connection.execute('INSERT INTO search_index VALUES (?,?,?,?,?,?)',
                                   (kind, str(ident), 'context' if kind == 'document' else 'codex', title, body, path))
                expected[kind+':'+str(ident)] = 2
                relevance[kind+':'+str(ident)] = topic
            queries.append({'id': topic, 'query': query, 'expected': expected})
            if topic in {'paper', 'backup'}:
                queries.append({'id': topic+'-document', 'query': query+' 문서만',
                                'expected': {key: value for key, value in expected.items() if key.startswith('document:')}})
        for name, query in [('empty-chess', '체스 오프닝 시칠리안 방어'),
                            ('empty-volcano', '화산 분화와 지각판 충돌'),
                            ('empty-music', '바로크 시대 작곡가의 생애')]:
            queries.append({'id': name, 'query': query, 'expected': {}})
    return config, queries, relevance
