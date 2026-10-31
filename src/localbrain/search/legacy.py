import sqlite3
from typing import Optional
from localbrain.search.lexical import _fts_expression


def search(
    connection: sqlite3.Connection,
    query: str,
    limit: int = 80,
    *,
    source_scope: str = "all",
    atlassian_filters: Optional[dict] = None,
):
    """Deprecated global keyword search retained for the legacy /search route."""
    expression = _fts_expression(query)
    if not expression:
        return []
    results = []
    if source_scope != "atlassian":
        entity_filter = {
            "sessions": "AND entity_type = 'session'",
            "documents": "AND entity_type = 'document'",
        }.get(source_scope, "AND entity_type IN ('session', 'document')")
        results.extend(
            dict(row)
            for row in connection.execute(
                """
                SELECT entity_type, entity_id, source_kind, title, path,
                       CASE WHEN entity_type='session' THEN (SELECT source_id FROM sessions WHERE id=entity_id)
                            WHEN entity_type='document' THEN (SELECT source_id FROM context_documents WHERE id=entity_id) END AS source_id,
                       snippet(search_index, 4, '[[', ']]', ' ... ', 26) AS excerpt,
                       bm25(search_index) AS score
                FROM search_index
                WHERE search_index MATCH ?
                  {entity_filter}
                ORDER BY score
                LIMIT ?
                """.format(entity_filter=entity_filter),
                (expression, limit),
            ).fetchall()
        )
    if source_scope not in {"sessions", "documents"}:
        from localbrain.atlassian.browse import atlassian_search_results

        results.extend(
            atlassian_search_results(
                connection,
                query,
                atlassian_filters,
                limit=limit,
            )
        )
    return sorted(
        results,
        key=lambda result: (
            result.get("score", 0),
            result.get("title") or "",
            result.get("entity_type") or "",
            result.get("entity_id") or "",
        ),
    )[:limit]
