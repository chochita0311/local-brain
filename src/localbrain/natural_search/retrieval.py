"""Semantic ordering with explicit lexical identifier admission and provenance."""

import json
import re
import threading
import time
from dataclasses import asdict
from urllib.parse import quote, urlencode

from .conditions import interpret
from .index import OWNER, folder, lexical_tokens, meta, open_index
from .query import focus_query
from .source import digest, read_sources

RANKING_VERSION = "semantic-dual-view-v3"


def database_stamp(path):
    values = []
    for candidate in (path, path.with_name(path.name + "-wal")):
        try:
            info = candidate.stat()
            values.append((info.st_ino, info.st_size, info.st_mtime_ns))
        except FileNotFoundError:
            values.append(None)
    return tuple(values)


class Retriever:
    def __init__(self, config, profile, encoder):
        self.config, self.profile, self.encoder = config, profile, encoder
        self._lock = threading.RLock()
        self._stamp = None
        self._source_stamp = None
        self._connection = None

    def close(self):
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
                self._stamp = None

    def _load(self):
        import numpy as np
        path = folder(self.config) / "index.sqlite3"
        if not path.is_file():
            raise ValueError("SEARCH_INDEX_UNAVAILABLE")
        info = path.stat()
        stamp = (info.st_ino, info.st_mtime_ns, info.st_size)
        if stamp == self._stamp:
            return
        connection = open_index(path)
        metadata = meta(connection)
        expected = digest({**self.encoder.contract, **self.profile.index_contract()})
        if (metadata.get("owner") != OWNER or not metadata.get("complete")
                or metadata.get("binding") != digest(str(self.config.database_path.resolve()))
                or metadata.get("identity") != expected):
            connection.close()
            raise ValueError("SEARCH_INDEX_INCOMPATIBLE")
        rows = connection.execute("""SELECT f.id, f.parent_key, f.body_hash, v.value FROM fragments f
                                     JOIN vectors v ON v.input_hash=f.input_hash ORDER BY f.id""").fetchall()
        try:
            vectors = [np.frombuffer(row["value"], dtype="<f4") for row in rows]
        except ValueError:
            connection.close()
            raise ValueError("INVALID_SEARCH_VECTORS") from None
        if any(vector.shape != (self.profile.dimension,) for vector in vectors):
            connection.close()
            raise ValueError("INVALID_SEARCH_VECTORS")
        matrix = np.vstack(vectors) if vectors else np.empty((0, self.profile.dimension), dtype=np.float32)
        if not np.isfinite(matrix).all() or not np.allclose(np.linalg.norm(matrix, axis=1), 1, atol=1e-4):
            connection.close()
            raise ValueError("INVALID_SEARCH_VECTORS")
        self._matrix = matrix
        self._ids = [row["id"] for row in rows]
        self._parent_keys = [row["parent_key"] for row in rows]
        self._body_hashes = [row["body_hash"] for row in rows]
        self._parents = {row["key"]: (row["revision"], json.loads(row["metadata"]))
                         for row in connection.execute("SELECT * FROM parents")}
        if self._connection:
            self._connection.close()
        # All access occurs under this retriever's lock, including different request threads.
        connection.close()
        import sqlite3
        self._connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True,
                                           check_same_thread=False, timeout=10)
        self._connection.row_factory = sqlite3.Row
        # An atomic publish between the two opens must force a fresh load.
        if meta(self._connection).get("generation") != metadata["generation"]:
            self._connection.close()
            self._connection = None
            self._stamp = None
            return self._load()
        self._stamp, self._metadata = stamp, metadata

    def _current(self):
        stamp = database_stamp(self.config.database_path)
        if stamp != self._source_stamp:
            sources, coverage = read_sources(self.config)
            self._sources = {source.key: source for source in sources}
            self._revisions = {source.key: source.revision for source in sources}
            self._coverage, self._source_stamp = coverage, stamp
        return self._sources

    def search(self, query, *, mode="hybrid", cutoff=None, page=1, page_size=20):
        import numpy as np
        if mode not in {"dense", "lexical", "hybrid"}:
            raise ValueError("INVALID_SEARCH_MODE")
        if len(query) > 300 or page < 1 or not 1 <= page_size <= 100:
            raise ValueError("INVALID_SEARCH_QUERY")
        cutoff = self.profile.cutoff if cutoff is None else cutoff
        if not 0 <= cutoff <= 1:
            raise ValueError("INVALID_SEARCH_CUTOFF")
        started = time.monotonic()
        with self._lock:
            self._load()
            self._current()
            conditions = interpret(query, self.config.timezone_name)
            valid = {key for key, (revision, data) in self._parents.items()
                     if self._revisions.get(key) == revision and conditions.matches(data)}
            if conditions.exclude:
                valid = {key for key in valid if not any(
                    excluded.casefold() in (self._sources[key].title + "\n" + "\n".join(
                        block["text"] for block in self._sources[key].blocks)).casefold()
                    for excluded in conditions.exclude)}
            indices = np.array([i for i, key in enumerate(self._parent_keys) if key in valid], dtype=np.int64)
            scores = np.zeros(len(self._ids), dtype=np.float32)
            rank_scores = scores
            views = [query]
            if mode == "hybrid" and not conditions.notices:
                focused = focus_query(query)
                if focused != query.strip():
                    views.append(focused)
            encode_started = time.monotonic()
            if mode != "lexical" and len(indices) and query.strip():
                vectors = np.asarray(self.encoder.encode(views, query=True), dtype=np.float32)
                if vectors.shape != (len(views), self.profile.dimension) or not np.isfinite(vectors).all():
                    raise ValueError("INVALID_SEARCH_VECTORS")
                norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                if not np.isfinite(norms).all() or (norms <= 0).any():
                    raise ValueError("INVALID_SEARCH_VECTORS")
                similarities = self._matrix @ (vectors / norms).T
                # Either view can retrieve evidence; their mean orders it. Keep
                # the original view so removing framing cannot erase its hits.
                scores = similarities.max(axis=1)
                rank_scores = similarities.mean(axis=1)
            encoded_at = time.monotonic()
            exact = query.strip().casefold() if re.fullmatch(r"[a-zA-Z0-9_./:+-]+", query.strip()) and re.search(r"[a-zA-Z]", query) else ""
            lexical_ranks = {}
            if mode == "lexical" or (mode == "hybrid" and exact):
                words = list(dict.fromkeys(lexical_tokens(query)))
                expression = " OR ".join('"' + word.replace('"', '""') + '"' for word in words)
                # Apply scope/freshness before the lexical candidate cap. Otherwise
                # many excluded Session hits can starve a document-only query.
                lexical = self._connection.execute("""SELECT terms.rowid, bm25(terms) AS score
                    FROM terms JOIN fragments f ON f.id=terms.rowid
                    WHERE terms MATCH ? AND f.parent_key IN (SELECT value FROM json_each(?))
                    ORDER BY score, terms.rowid LIMIT 500""",
                    (expression, json.dumps(sorted(valid)))).fetchall() if expression and valid else []
                lexical_ranks = {row["rowid"]: rank + 1 for rank, row in enumerate(lexical)}
            admitted = []
            for i in indices:
                rowid = self._ids[i]
                lexical_rank = lexical_ranks.get(rowid)
                if mode == "lexical":
                    if lexical_rank:
                        admitted.append((1 / (60 + lexical_rank), i, "lexical"))
                    continue
                score = float(scores[i])
                reason = "semantic"
                if score < cutoff:
                    if mode != "hybrid" or not exact or not lexical_rank:
                        continue
                    item = self._connection.execute("SELECT text,context FROM fragments WHERE id=?", (rowid,)).fetchone()
                    if not re.search(r"(?<![\w])" + re.escape(exact) + r"(?![\w])", (item["context"] + "\n" + item["text"]).casefold()):
                        continue
                    reason = "exact"
                # Fragment counts and lexical ranks cannot inflate relevance.
                admitted.append((float(rank_scores[i]), i, reason))
            admitted.sort(key=lambda item: (-item[0], self._parent_keys[item[1]], self._ids[item[1]]))
            groups, seen_evidence = {}, {}
            for rank, i, reason in admitted:
                key = self._parent_keys[i]
                if key not in groups:
                    groups[key] = {**self._parents[key][1], "score": round(float(scores[i]), 5),
                                   "rank_score": rank, "match_reason": reason, "evidence": []}
                    seen_evidence[key] = set()
                if len(groups[key]["evidence"]) < 3 and self._body_hashes[i] not in seen_evidence[key]:
                    seen_evidence[key].add(self._body_hashes[i])
                    groups[key]["evidence"].append(self._ids[i])
            total = len(groups)
            results = list(groups.values())[(page - 1) * page_size:page * page_size]
            return_url = "/natural-search?" + urlencode({"q": query, "page": page, "mode": "ai"})
            for item in results:
                # Rank and count all eligible parents, but load text only for
                # the displayed page. This bounds SQLite reads for broad queries.
                evidence = []
                for rowid in item["evidence"]:
                    row = self._connection.execute("SELECT * FROM fragments WHERE id=?", (rowid,)).fetchone()
                    evidence.append({"id": row["id"], "text": row["text"], "locator": json.loads(row["locator"]),
                                     "generation": self._metadata["generation"]})
                item["evidence"] = evidence
                item["anchor"] = "natural-result-{}-{}".format(item["kind"], item["entity_id"])
                result_return = return_url + "#" + item["anchor"]
                for evidence in item["evidence"]:
                    if item["kind"] == "session":
                        evidence["href"] = "/sessions/{}?{}#event-{}".format(item["entity_id"], urlencode({"search_return": result_return}), quote(evidence["locator"]["block_id"], safe=""))
                    else:
                        evidence["href"] = "/natural-search/evidence/{}?{}".format(evidence["id"], urlencode({"generation": evidence["generation"], "return_to": result_return}))
                item["href"] = item["evidence"][0]["href"]
            current_count = sum(self._revisions.get(key) == revision for key, (revision, _) in self._parents.items())
            return {"results": results, "total": total, "page": page, "page_size": page_size,
                    "conditions": asdict(conditions), "mode": mode, "cutoff": cutoff,
                    "ranking": ("lexical-bm25-v1" if mode == "lexical" else
                                "semantic-cosine-v2" if mode == "dense" else RANKING_VERSION),
                    "coverage": {**self._coverage, "indexed_parents": current_count,
                                 "fragments": len(self._ids)},
                    "partial": current_count != len(self._sources),
                    "timing": {"query_views": len(views) if mode != "lexical" and len(indices) and query.strip() else 0,
                               "query_encode_and_dot_ms": round((encoded_at - encode_started) * 1000, 2),
                               "total_ms": round((time.monotonic() - started) * 1000, 2)}}

    def evidence(self, rowid, generation):
        with self._lock:
            self._load()
            self._current()
            if generation != self._metadata["generation"]:
                raise ValueError("SEARCH_EVIDENCE_CHANGED")
            row = self._connection.execute("SELECT * FROM fragments WHERE id=?", (rowid,)).fetchone()
            if not row or self._revisions.get(row["parent_key"]) != self._parents[row["parent_key"]][0]:
                raise ValueError("SEARCH_EVIDENCE_CHANGED")
            return {"source": self._parents[row["parent_key"]][1], "text": row["text"],
                    "context": row["context"], "locator": json.loads(row["locator"])}
