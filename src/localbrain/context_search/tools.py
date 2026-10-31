"""Server-admitted sources and bounded read-only model tools."""

import codecs
import hashlib
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from localbrain.foundation.config import cache_directory, development_directory
from localbrain.foundation.paths import hub_cache_root

MAX_READ = 2 * 1024 * 1024
MAX_FILES = 5000
MAX_MATCHES = 40
MAX_TEXT = 10000
MAX_SEARCH_BYTES = 32 * 1024 * 1024


class ToolError(ValueError):
    pass


@contextmanager
def database(path):
    connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, timeout=10)
    try:
        yield connection
    finally:
        connection.close()


def source_catalog(config, drive_store=None):
    """Never register a source, initialize Drive state, or traverse app data globally."""
    sources = []
    excluded = [Path(p).resolve() for p in (config.data_dir, cache_directory(config),
                                          development_directory(config), hub_cache_root())]
    with database(config.database_path) as db:
        for key, label, path, kind in db.execute("SELECT id,label,path,source_type FROM context_roots WHERE enabled=1 AND readable=1 ORDER BY id"):
            source = dict(id="context-" + str(key), name=label or Path(path).name,
                          kind="local", context_id=key, database=str(config.database_path))
            if kind == "apple_notes":
                sources.append({**source, "mode": "documents"})
            elif kind in ("folder", "file"):
                candidate = Path(path).expanduser().resolve()
                expected = candidate.is_file() if kind == 'file' else candidate.is_dir()
                if expected and not any(candidate == root or root in candidate.parents for root in excluded):
                    sources.append({**source, "mode": "files", "root": str(candidate), 'single_file': kind == 'file', "excluded": [str(p) for p in excluded]})
    if drive_store is not None:
        for connection in drive_store.connections():
            publishers = {p["id"]: p for p in drive_store.get("publishers:" + connection["id"], [])}
            for job_key, job in drive_store.jobs(connection["id"]).items():
                if not job_key.startswith("receive:"):
                    continue
                publisher = job_key[len("receive:"):]
                if not all(part and all(c.isascii() and (c.isalnum() or c in "-_") for c in part)
                           for part in (connection["id"], publisher)):
                    continue
                root = config.data_dir / "external-sources/google-drive" / connection["id"] / publisher
                if root.is_dir() and not any(p.is_symlink() for p in (root, root.parent, root.parent.parent)):
                    identity = hashlib.sha256((connection["id"] + ":" + publisher).encode()).hexdigest()[:16]
                    sources.append(dict(id="drive-" + identity, name=publishers.get(publisher, {}).get("name", "받은 폴더"),
                                        kind="received", mode="files", root=str(root.resolve()), single_file=False,
                                        observed_at=job.get("last_success"), syncing=bool(job.get("selected"))))
    return sources


def public_sources(sources):
    return [{k: source[k] for k in ("id", "name", "kind", "observed_at", "syncing") if k in source}
            for source in sources]


class FileTools:
    def __init__(self, sources):
        self.sources = {s['id']: {**s, **({'root': str(Path(s['root']).resolve())} if s.get('root') else {})} for s in sources}
        self.evidence = {}
        self._walk_limited = False

    def _source(self, key):
        if not isinstance(key, str) or key not in self.sources:
            raise ToolError("선택된 자료 범위에서 소스를 골라 주세요.")
        return self.sources[key]

    def _path(self, source, relative):
        root = Path(source["root"])
        pieces = Path(relative).parts
        if not relative or Path(relative).is_absolute() or any(p in (".", "..") or p.startswith('.localbrain-drive-') for p in pieces):
            raise ToolError("자료 안의 상대 파일 경로를 지정해 주세요.")
        if root.is_symlink() or root.resolve() != root:
            raise ToolError("자료 경로가 바뀌어 읽지 않았습니다.")
        single = source.get('single_file', root.is_file())
        if single != root.is_file():
            raise ToolError('선택한 자료의 파일·폴더 유형이 바뀌었습니다.')
        path = root.parent / relative if single else root / relative
        boundary = root.parent if single else root
        if single and relative != root.name:
            raise ToolError("선택한 파일만 읽을 수 있습니다.")
        current = boundary
        for piece in pieces:
            current = current / piece
            if current.is_symlink():
                raise ToolError("링크 경로는 읽지 않습니다.")
        if not path.resolve().is_relative_to(boundary.resolve()) or not path.is_file():
            raise ToolError("자료 안의 읽을 수 있는 파일을 선택해 주세요.")
        if any(path.resolve().is_relative_to(Path(p)) for p in source.get("excluded", [])):
            raise ToolError("앱 런타임·공용 모델 캐시는 자료로 읽지 않습니다.")
        return path

    def _files(self, source):
        if source["mode"] == "documents":
            with database(source["database"]) as db:
                rows = db.execute("SELECT id,title FROM context_documents WHERE context_root_id=? ORDER BY id LIMIT ?", (source["context_id"], MAX_FILES + 1))
                return [("document-" + str(key), title) for key, title in rows]
        root = Path(source["root"])
        if root.is_symlink() or root.resolve() != root:
            raise ToolError("자료 경로가 바뀌었습니다.")
        if source.get('single_file', root.is_file()) != root.is_file():
            raise ToolError('선택한 자료의 파일·폴더 유형이 바뀌었습니다.')
        if root.is_file():
            return [(root.name, root.name)]
        if not root.is_dir():
            raise ToolError("자료 폴더를 읽을 수 없습니다.")
        found = []
        started, walked = time.monotonic(), 0
        def unreadable(_error):
            self._walk_limited = True
        for parent, dirs, files in os.walk(root, followlinks=False, onerror=unreadable):
            walked += 1
            if walked > MAX_FILES or time.monotonic() - started > 2:
                self._walk_limited = True
                return found
            dirs[:] = sorted(d for d in dirs if not (Path(parent) / d).is_symlink()
                             and not any((Path(parent) / d).resolve().is_relative_to(Path(p)) for p in source.get("excluded", [])))
            for name in sorted(files):
                path = Path(parent) / name
                if not path.is_symlink() and not name.startswith(".localbrain-drive-") and path.is_file():
                    found.append((path.relative_to(root).as_posix(), name))
                    if len(found) > MAX_FILES:
                        return found
        return found

    def _text(self, source, relative):
        if source["mode"] == "documents":
            if not relative.startswith("document-") or not relative[9:].isdigit():
                raise ToolError("문서 목록의 파일 식별자를 사용해 주세요.")
            with database(source["database"]) as db:
                row = db.execute("SELECT substr(d.body,1,?),length(d.body),d.mtime_ns FROM context_documents d JOIN context_roots r ON r.id=d.context_root_id WHERE d.id=? AND r.id=? AND r.enabled=1 AND r.readable=1", (MAX_READ, int(relative[9:]), source["context_id"])).fetchone()
            if not row:
                raise ToolError("현재 읽을 수 없는 문서입니다.")
            return row[0] or "", row[1] > MAX_READ, str(row[2])
        path = self._path(source, relative)
        before = path.stat()
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns):
                raise ToolError("읽기 전에 자료가 바뀌었습니다.")
            raw = stream.read(MAX_READ + 1)
        self._path(source, relative)
        if (before.st_ino, before.st_size, before.st_mtime_ns) != tuple(getattr(path.stat(), k) for k in ("st_ino", "st_size", "st_mtime_ns")):
            raise ToolError("읽는 중 자료가 바뀌었습니다. 다시 읽어 주세요.")
        try:
            if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
                text = codecs.getincrementaldecoder("utf-16")().decode(raw[:MAX_READ], final=len(raw) <= MAX_READ)
            else:
                if b"\x00" in raw[:8192]:
                    raise UnicodeError()
                text = codecs.getincrementaldecoder("utf-8-sig")().decode(raw[:MAX_READ], final=len(raw) <= MAX_READ)
        except UnicodeError:
            # Reuse a current collected PDF body, without requiring new indexing.
            if source.get("context_id") and path.suffix.lower() == ".pdf":
                with database(source["database"]) as db:
                    row = db.execute("SELECT substr(body,1,?),length(body) FROM context_documents WHERE context_root_id=? AND path=? AND mtime_ns=?", (MAX_READ, source["context_id"], str(path), before.st_mtime_ns)).fetchone()
                if row and row[0]:
                    return row[0], row[1] > MAX_READ, str(before.st_mtime_ns)
            raise ToolError("이 파일은 현재 텍스트로 읽을 수 없습니다.") from None
        return text, len(raw) > MAX_READ, str(before.st_mtime_ns)

    def _reference(self, source, relative, line, text, version):
        key = (source["id"], relative, version, line)
        previous = self.evidence.get(key, {})
        value = dict(ref=previous.get("ref", "S" + str(len(self.evidence) + 1)),
                     source=source["name"], path=relative, line=line, text=text[:1600], version=version)
        self.evidence[key] = value
        return value

    def call(self, name, arguments):
        if not isinstance(arguments, dict):
            raise ToolError("도구 인자를 확인해 주세요.")
        if name == "list_sources":
            if arguments:
                raise ToolError("자료 목록에는 인자가 필요하지 않습니다.")
            return {"sources": public_sources(self.sources.values())}
        if name == "list_files":
            if not set(arguments) <= {"source", "offset"}:
                raise ToolError("파일 목록 인자를 확인해 주세요.")
            source = self._source(arguments.get("source"))
            offset = arguments.get("offset", 0)
            if type(offset) is not int or not 0 <= offset <= MAX_FILES:
                raise ToolError("파일 목록 위치를 확인해 주세요.")
            files = self._files(source)
            return dict(source=source["id"], offset=offset, files=[dict(path=p, name=n) for p, n in files[:MAX_FILES][offset:offset + 150]],
                        next_offset=offset + 150 if min(len(files), MAX_FILES) > offset + 150 else None,
                        limited=self._walk_limited or len(files) > MAX_FILES)
        if name == "search_text":
            if not set(arguments) <= {"query", "source"}:
                raise ToolError("검색 인자를 확인해 주세요.")
            query = arguments.get("query")
            if not isinstance(query, str) or not query.strip() or len(query) > 200:
                raise ToolError("짧은 검색어를 지정해 주세요.")
            sources = [self._source(arguments["source"])] if 'source' in arguments else self.sources.values()
            matches, scanned, unreadable, limited = [], 0, 0, False
            total_bytes, started = 0, time.monotonic()
            for source in sources:
                try:
                    files = self._files(source)
                except (OSError, ToolError):
                    unreadable += 1
                    limited = True
                    continue
                limited |= self._walk_limited or len(files) > MAX_FILES
                for relative, _ in files[:MAX_FILES]:
                    if scanned + unreadable >= MAX_FILES or total_bytes >= MAX_SEARCH_BYTES or time.monotonic() - started >= 6:
                        return dict(matches=matches, scanned=scanned, unreadable=unreadable, limited=True)
                    try:
                        text, partial, version = self._text(source, relative)
                    except (OSError, ToolError):
                        unreadable += 1
                        continue
                    scanned += 1
                    total_bytes += len(text.encode('utf-8'))
                    limited |= partial
                    lines = text.splitlines()
                    for number, line in enumerate(lines, 1):
                        if query.casefold() in line.casefold():
                            start = max(1, number - 2)
                            excerpt = '\n'.join(lines[start - 1:number + 2])[:1600]
                            value = self._reference(source, relative, start, excerpt, version)
                            matches.append({**value, "source_id": source["id"], 'match_line': number})
                            break
                    if len(matches) >= MAX_MATCHES:
                        return dict(matches=matches, scanned=scanned, unreadable=unreadable, limited=True)
            return dict(matches=matches, scanned=scanned, unreadable=unreadable, limited=limited)
        if name == "read_file":
            if not set(arguments) <= {"source", "path", "start_line", "end_line"}:
                raise ToolError("읽기 인자를 확인해 주세요.")
            source = self._source(arguments.get("source"))
            relative = arguments.get("path")
            start, end = arguments.get("start_line", 1), arguments.get("end_line", 100)
            if not isinstance(relative, str) or type(start) is not int or type(end) is not int or not 1 <= start <= end <= start + 199:
                raise ToolError("파일과 최대200줄의 읽기 구간을 지정해 주세요.")
            text, partial, version = self._text(source, relative)
            lines = text.splitlines()
            chunk = "\n".join(lines[start - 1:end])
            if not chunk:
                return dict(text="", limited=partial, message="해당 구간에 읽을 내용이 없습니다.")
            value = self._reference(source, relative, start, chunk, version)
            return {**value, "text": chunk[:MAX_TEXT], "source_id": source["id"],
                    "limited": partial or len(chunk) > MAX_TEXT or end < len(lines)}
        raise ToolError("허용되지 않은 도구입니다.")


def tool_schemas():
    specs = [
        ("list_sources", "사용 가능한 자료 목록. source id를 검색/읽기에 사용하세요.", {}, []),
        ("list_files", "자료의 파일 목록을 봅니다. 다음 페이지가 있으면 offset으로 이어 봅니다.", {"source": {"type": "string"}, "offset": {"type": "integer"}}, ["source"]),
        ("search_text", "실제 파일에서 문자열을 검색합니다. 정규식이 아니며 표현을 바꿔 다시 검색할 수 있습니다.", {"query": {"type": "string"}, "source": {"type": "string"}}, ["query"]),
        ("read_file", "목록/검색에서 찾은 파일의 필요한 줄을 읽습니다.", {"source": {"type": "string"}, "path": {"type": "string"}, "start_line": {"type": "integer"}, "end_line": {"type": "integer"}}, ["source", "path"]),
    ]
    return [dict(type="function", function=dict(name=name, description=description,
                 parameters=dict(type="object", properties=properties, required=required, additionalProperties=False)))
            for name, description, properties, required in specs]
