"""Synthetic-only sources and a contract encoder; never a model quality oracle."""

import sqlite3
from pathlib import Path

from localbrain.foundation.config import Settings


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False, **kwargs):
        return list(range(len(text))) + ([0] if add_special_tokens else [])

    def __call__(self, text, **kwargs):
        return {"offset_mapping": [(i, i + 1) for i in range(len(text))]}


class ContractEncoder:
    def __init__(self, config=None, profile=None):
        from localbrain.natural_search.molecules import Profile
        self.profile = profile or Profile()
        self.contract = {"test_encoder": "synthetic-contract-v1"}
        self.tokenizer = CharacterTokenizer()
        self.batch_size = 2
        self.calls = []

    def encode(self, texts, query=False):
        import numpy as np
        self.calls.append((query, list(texts)))
        result = np.zeros((len(texts), self.profile.dimension), dtype=np.float32)
        for i, text in enumerate(texts):
            for axis, words in enumerate((("앱", "모바일", "atlas"), ("배포", "deploy"), ("정원", "화분"))):
                if any(word in text.lower() for word in words):
                    result[i, axis] = 1
            if not result[i].any():
                result[i, 3] = 1
        return result / np.linalg.norm(result, axis=1, keepdims=True)


def fixture(root):
    root = Path(root)
    data = root / "data"
    data.mkdir(parents=True)
    config = Settings(data, data / "localbrain.db", root / "context", root / "claude", root / "codex",
                      20, "Asia/Seoul", cache_dir=root / "cache", development_dir=root / "evidence")
    config.codex_root.mkdir()
    from localbrain.foundation.preferences import toml_text
    (data / "session-sources.toml").write_text(toml_text({"schema_version": 2, "session_sources": [
        {"source_id": 1, "provider_kind": "codex", "display_label": "synthetic-fixture", "root": str(config.codex_root)}]}))
    with sqlite3.connect(config.database_path) as connection:
        schema = Path(__file__).resolve().parents[1] / "src/localbrain/schema.sql"
        connection.executescript(schema.read_text())
        connection.execute("INSERT INTO sources(id, provider_kind, name, root_path) VALUES (1, 'codex', 'synthetic-fixture', '/synthetic/sessions')")
        connection.execute("INSERT INTO sources(id, provider_kind, name, root_path) VALUES (2, 'context', 'synthetic-fixture', '/synthetic/context')")
        connection.execute("INSERT INTO context_roots(id,path,label) VALUES (1,'/synthetic/context','synthetic-fixture')")
        for ident, title, body, kind, role in (
            (1, 'Atlas 모바일 앱', '모바일 앱의 로그인과 오프라인 저장을 구현했다. API 이름은 atlas.', 'work', 'primary'),
            (2, '배포 작업', '배포 파이프라인에서 deploy staging을 수정했다.', 'work', 'primary'),
            (3, '정원 관리', '화분과 정원에 물을 주었다.', 'work', 'primary'),
            (4, '분석 Run 출력', '모바일 앱 분석 결과가 만들어졌다.', 'maintenance', 'primary'),
            (5, '자식 작업', '모바일 앱 내용을 보조 조사했다.', 'work', 'subsession'),
        ):
            connection.execute("""INSERT INTO sessions
                (id,source_id,external_id,source_path,title,session_class,session_role,index_policy,last_event_at)
                VALUES (?,1,?,?,?, ?,?,'full','2026-10-06T05:00:00Z')""",
                (ident, str(ident), '/synthetic/session-' + str(ident), title, kind, role))
            connection.execute("""INSERT INTO activity_events
                (id,session_id,sequence,event_type,role,text,source_line) VALUES (?, ?,0,'message','user',?,1)""",
                ('synthetic-event-' + str(ident), ident, body))
            if kind == 'work' and role == 'primary':
                connection.execute("INSERT INTO search_index VALUES ('session',?,'codex',?,?,?)",
                                   (str(ident), title, body, '/synthetic'))
        connection.execute("""INSERT INTO context_documents
            (id,source_id,context_root_id,path,relative_path,title,body,size_bytes,mtime_ns,content_hash)
            VALUES (1,2,1,'/synthetic/context/mobile.md','mobile.md','모바일 앱 설계',
                    '오프라인에서도 입력한 기록을 저장하는 모바일 앱 설계 문서.',100,1791252000000000000,'synthetic')""")
        connection.execute("UPDATE sources SET root_path=? WHERE provider_kind='codex'", (str(config.codex_root),))
    return config
