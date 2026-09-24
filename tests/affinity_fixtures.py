"""Synthetic full-history map fixture; never invokes a model."""

import re
import sqlite3
from collections import defaultdict
from pathlib import Path

from localbrain.session_simulation import simulate
from localbrain.work_reconstruction import digest


class Encoder:
    contract = {"model_id": "synthetic-fixture", "dimension": 3, "max_tokens": 128}

    def encode(self, texts):
        return [[int(a) + 1, int(b) + 1, 1] for text in texts
                for a, b in [re.search(r"topic:(\d+) slice:(\d+)", text).groups()]]


def grouping(vectors, parameters):
    topics = defaultdict(lambda: defaultdict(list))
    for key, v in vectors.items():
        topics[round(v[0] / v[2])][round(v[1] / v[2])].append(key)
    areas = []
    for parts in topics.values():
        members = sorted(k for values in parts.values() for k in values)
        areas.append({"id": digest(["area", members]), "members": members,
                      "work_groups": [{"id": digest(["work", sorted(v)]), "members": sorted(v)} for v in parts.values()]})
    keys = sorted(vectors)
    edges = [{"left": a, "right": b, "similarity": 0.78} for a, b in zip(keys, keys[1:])]
    return {"engine": {"method": "cosine-knn-louvain-v2-ordered", "runtime": "synthetic"},
            "authority": "inferred-affinity-only", "areas": sorted(areas, key=lambda a: a["id"]),
            "node_count": len(keys), "edge_count": len(edges), "edges": edges,
            "singleton_areas": sum(len(a["members"]) == 1 for a in areas)}


def seed(database, count=96, *, topics=32):
    schema = Path(__file__).resolve().parents[1] / "src/localbrain/schema.sql"
    with sqlite3.connect(database) as db:
        db.executescript(schema.read_text(encoding="utf-8"))
        db.execute("INSERT INTO sources(id,kind,name,root_path) VALUES (1,'codex','Synthetic Codex','/synthetic')")
        db.execute("INSERT INTO workstreams(id,name,summary) VALUES (1,'검색 경험 개선','기존 구성 보존')")
        for i in range(1, count + 1):
            identity = 1 if i == 2 else i
            title = ["검색 경험 개선", "분석 지표 유지 보수", "배포와 운영 자동화", "데이터 품질 관찰"][identity % 4] + " · {}".format(identity)
            if i == count - 3:
                title += " 긴 제목과 mixed-English-identifier " * 7
            date = "2026-{:02d}-{:02d}T09:00:00Z".format(1 + i % 8, 1 + i % 27)
            db.execute("""INSERT INTO sessions(id,source_id,external_id,source_path,title,event_count,started_at,last_event_at)
                VALUES (?,1,?,?,?,2,?,?)""", (i, "synthetic-{}".format(i), "/synthetic/{}".format(i), title, date, date))
            for j in range(2):
                text = "topic:{} slice:{}\n합성 자료: {} 단계 {}.\n<script>syntheticOnly()</script>".format((identity + j * 3) % topics, j, title, j)
                db.execute("""INSERT INTO activity_events(id,session_id,sequence,event_type,role,text,occurred_at,source_line)
                    VALUES (?,?,?,'message','user',?,?,1)""", ("event-{}-{}".format(i, j), i, j, text, date))
            db.execute("""INSERT INTO session_reference_scans(session_id,source_fingerprint,extractor_version,status,scanned_at,updated_at)
                VALUES (?,?,'synthetic','ok',?,?)""", (i, "0" * 64, date, date))
        db.execute("UPDATE sessions SET session_class='maintenance' WHERE id=?", (count,))
        db.execute("UPDATE sessions SET session_role='subsession' WHERE id=?", (count - 1,))
        db.execute("UPDATE activity_events SET text='' WHERE session_id=?", (count - 2,))


def prepare(database):
    return simulate(database, database.parent / "session-simulation", Encoder(), grouper=grouping)
