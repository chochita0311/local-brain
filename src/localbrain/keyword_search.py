"""Existing FTS5 matching with the common local source admission boundary."""

from urllib.parse import urlencode

from .config import settings
from .natural_search.source import _private_derived
from .queries import _fts_expression
from .source_settings import registered_session_roots


def keyword_search(connection, query, *, scope="all", limit=80, config=settings):
    expression = _fts_expression(query)
    if not expression:
        return []
    roots = registered_session_roots(config)
    keys = list(roots)
    marks = ",".join("?" for _ in keys) or "NULL"
    clauses, params = [], [expression]
    if scope in {"all", "sessions"}:
        clauses.append("""(entity_type='session' AND EXISTS (
            SELECT 1 FROM sessions s JOIN sources o ON o.id=s.source_id
            WHERE s.id=entity_id AND s.session_class='work' AND s.session_role='primary'
              AND s.index_policy='full' AND o.id IN (""" + marks + ")))")
        params.extend(keys)
    if scope in {"all", "documents"}:
        clauses.append("""(entity_type='document' AND EXISTS (
            SELECT 1 FROM context_documents d JOIN context_roots r ON r.id=d.context_root_id
            WHERE d.id=entity_id AND r.enabled=1 AND r.readable=1))""")
    if not clauses:
        return []
    rows = connection.execute("""
        SELECT entity_type, entity_id, source_kind, title, path,
               snippet(search_index, 4, '[[', ']]', ' ... ', 26) AS excerpt,
               bm25(search_index) AS score
        FROM search_index WHERE search_index MATCH ? AND (""" + " OR ".join(clauses) + ") ORDER BY score", params)
    results = []
    for row in rows:
        item = dict(row)
        if item["entity_type"] == "document" and not str(item["path"]).startswith("apple-notes://") and _private_derived(item["path"], config):
            continue
        if item["entity_type"] == "session":
            owner = connection.execute("SELECT o.root_path,o.id FROM sessions s JOIN sources o ON o.id=s.source_id WHERE s.id=?", (item["entity_id"],)).fetchone()
            if not owner or roots.get(owner["id"]) != owner["root_path"]:
                continue
            item["source_id"] = owner["id"]
        item["url"] = ("/sessions/" if item["entity_type"] == "session" else "/documents/") + str(item["entity_id"])
        item["anchor"] = "natural-result-{}-{}".format(item["entity_type"], item["entity_id"])
        return_to = "/natural-search?" + urlencode({"q": query, "mode": "keyword"}) + "#" + item["anchor"]
        item["url"] += "?" + urlencode({"search_return": return_to})
        results.append(item)
        if len(results) >= limit:
            break
    return results
