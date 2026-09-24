"""Synthetic-only fixture shared by Auto Work route and browser checks."""

import sqlite3
from pathlib import Path


def seed(database):
    schema = Path(__file__).resolve().parents[1] / "src/localbrain/schema.sql"
    with sqlite3.connect(database) as connection:
        connection.executescript(schema.read_text(encoding="utf-8"))
        connection.execute("INSERT INTO sources(id,kind,name,root_path) VALUES (1,'codex','Synthetic Codex','/synthetic')")
        connection.execute("INSERT INTO workstreams(id,name,summary) VALUES (1,'검색 경험 개선','기존 Workstream 유지 확인')")
        for index in range(1, 17):
            title = "검색 응답과 검증 흐름 {}".format(index)
            at = "2026-01-{:02d}T09:00:00Z".format(index)
            connection.execute("""INSERT INTO sessions(id,source_id,external_id,source_path,title,event_count,
                started_at,last_event_at) VALUES (?,1,?,?,?,1,?,?)""",
                (index, "synthetic-{}".format(index), "/synthetic/{}".format(index), title, at, at))
            wording = "검색 응답을 개선하자.\nFix parser {}.\n관찰만 있고 구체적인 목표는 아직 없다.".format(index)
            if index == 16:
                wording += "\nFix " + "long-subject-" * 20 + ".\n<script>alert('synthetic')</script>"
            connection.execute("""INSERT INTO activity_events(id,session_id,sequence,occurred_at,event_type,role,text,source_line)
                VALUES (?,?,1,?,'message','user',?,1)""", ("synthetic-event-{}".format(index), index, at, wording))
            connection.execute("""INSERT INTO session_reference_scans(session_id,source_fingerprint,extractor_version,
                status,scanned_at,updated_at) VALUES (?,?,'synthetic','ok',?,?)""", (index, "0" * 64, at, at))
