import re


def _fts_expression(query: str) -> str:
    tokens = re.findall(r"[\w.-]+", query, flags=re.UNICODE)
    return " AND ".join('"{}"'.format(token.replace('"', '""')) for token in tokens[:12])
