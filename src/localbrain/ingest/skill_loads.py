"""Extract skill references and literal executions without running logged commands."""

import bisect
import json
import posixpath
import re
import shlex
from dataclasses import replace
from typing import Any, Optional

import yaml

from .common import ParsedSkillObservation, source_native_event_id, stable_id
from .skill_usage import SkillReferenceMatcher


_JS_WORD = re.compile(r"[A-Za-z_$][\w$]*")


def _js_tokens(source: str):
    """A bounded literal lexer, not a JavaScript interpreter."""
    index = 0
    while index < len(source):
        char = source[index]
        if char.isspace():
            index += 1
            continue
        if source.startswith("//", index):
            end = source.find("\n", index)
            index = len(source) if end < 0 else end + 1
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = len(source) if end < 0 else end + 2
            continue
        if char in "\"'`":
            quote = char
            index += 1
            decoded = []
            valid = True
            while index < len(source) and source[index] != quote:
                char = source[index]
                if quote == "`" and source.startswith("${", index):
                    valid = False
                if char == "\\":
                    index += 1
                    if index >= len(source):
                        valid = False
                        break
                    char = source[index]
                    escapes = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f"}
                    if char in {"u", "x"}:
                        width = 4 if char == "u" else 2
                        value = source[index + 1:index + 1 + width]
                        if len(value) == width and re.fullmatch(r"[0-9a-fA-F]+", value):
                            decoded.append(chr(int(value, 16)))
                            index += width + 1
                            continue
                        valid = False
                    elif char != "\n":
                        decoded.append(escapes.get(char, char))
                else:
                    decoded.append(char)
                index += 1
            if index >= len(source):
                valid = False
            index += 1
            yield ("string", "".join(decoded) if valid else None)
            continue
        word = _JS_WORD.match(source, index)
        if word:
            value = word.group()
            index += len(value)
            yield ("word", value)
        else:
            index += 1
            yield ("symbol", char)


def _script_commands(source: str):
    tokens = list(_js_tokens(source))
    for index in range(len(tokens) - 5):
        if [value for _, value in tokens[index:index + 5]] != [
            "tools", ".", "exec_command", "(", "{"
        ] or tokens[index][0] != "word":
            continue
        fields = {}
        depth = 1
        cursor = index + 5
        while cursor < len(tokens) and depth:
            kind, value = tokens[cursor]
            if kind == "symbol" and value in {"{", "[", "("}:
                depth += 1
            elif kind == "symbol" and value in {"}", "]", ")"}:
                depth -= 1
            elif depth == 1 and value in {"cmd", "workdir"} and cursor + 2 < len(tokens):
                if tokens[cursor + 1][1] == ":" and tokens[cursor + 2][0] == "string":
                    # Concatenated expressions are not static command literals.
                    following = tokens[cursor + 3][1] if cursor + 3 < len(tokens) else None
                    if following in {",", "}"}:
                        fields[value] = tokens[cursor + 2][1]
            cursor += 1
        if isinstance(fields.get("cmd"), str):
            yield fields


def _read_paths(command: str, workdir: Optional[str] = None) -> list:
    workdir = workdir if isinstance(workdir, str) else None
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()<>")
        lexer.whitespace = " \t\r"
        lexer.wordchars += "$`"
        tokens = list(lexer)
    except ValueError:
        return []
    # Heredoc bodies are text, not independent shell commands.
    if any(token in {"<<", "<<-", "<<<"} for token in tokens):
        return []
    segments = [[]]
    for token in tokens:
        if token in {"\n", ";", "&&", "||", "|", "(", ")"}:
            segments.append([])
        else:
            segments[-1].append(token)
    paths = []
    for segment in segments:
        if not segment or posixpath.basename(segment[0]) not in {
            "cat", "sed", "head", "tail", "nl"
        }:
            continue
        if any(">" in token for token in segment) or (
            posixpath.basename(segment[0]) == "sed"
            and any(token.startswith(("-i", "--in-place")) for token in segment[1:])
        ):
            continue
        for token in segment[1:]:
            if posixpath.basename(token) != "SKILL.md" or any(c in token for c in "$`*?[]"):
                continue
            path = posixpath.join(workdir, token) if workdir and not token.startswith(("/", "~")) else token
            paths.append(posixpath.normpath(path))
    return list(dict.fromkeys(paths))


def _execution_paths(command: Any, workdir: Optional[str] = None) -> list:
    """Recognize script arguments in a small, literal-only command grammar."""
    if isinstance(command, list):
        if not command or not all(isinstance(token, str) for token in command):
            return []
        if (posixpath.basename(command[0]) in {"sh", "bash", "zsh"}
                and len(command) == 3 and command[1] in {"-c", "-lc", "-ilc"}):
            return _execution_paths(command[2], workdir)
        segments = [command]
    elif isinstance(command, str):
        try:
            lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()<>")
            lexer.whitespace = " \t\r"
            lexer.wordchars += "$`"
            tokens = list(lexer)
        except ValueError:
            return []
        if any(token in {"<<", "<<-", "<<<"} for token in tokens):
            return []
        segments = [[]]
        for token in tokens:
            if token in {"\n", ";", "&&", "||", "|", "(", ")"}:
                segments.append([])
            else:
                segments[-1].append(token)
    else:
        return []
    paths = []
    for segment in segments:
        if not segment or any(token in {"<", ">", "<<", ">>", "<<<"} for token in segment):
            continue
        arguments = list(segment)
        if posixpath.basename(arguments[0]) == "env":
            arguments.pop(0)
        while arguments and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", arguments[0]):
            arguments.pop(0)
        if not arguments:
            continue
        executable = arguments.pop(0)
        program = posixpath.basename(executable)
        if program in {"python", "python3", "node", "bash", "sh", "zsh", "ruby", "perl"} or re.fullmatch(r"python3\.\d+", program):
            while arguments and arguments[0] in {"-B", "-u", "-I", "-E", "-s", "-S"}:
                arguments.pop(0)
            path = arguments[0] if arguments else None
        else:
            path = executable
        if (not isinstance(path, str) or path.startswith("-")
                or "/" not in path or any(char in path for char in "$`*?[]")):
            continue
        if not path.startswith(("/", "~")):
            if not isinstance(workdir, str):
                continue
            path = posixpath.join(workdir, path)
        path = posixpath.normpath(path)
        if "/scripts/" in path:
            paths.append(path)
    return list(dict.fromkeys(paths))


def _call_paths(tool_name: str, arguments: Any) -> tuple:
    tool = tool_name.rsplit(".", 1)[-1]
    if isinstance(arguments, str) and "SKILL.md" not in arguments:
        return ()
    if tool == "exec" and isinstance(arguments, str):
        return tuple(path for fields in _script_commands(arguments)
                     for path in _read_paths(fields["cmd"], fields.get("workdir")))
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except ValueError:
            return ()
    if not isinstance(arguments, dict):
        return ()
    if tool in {"Read", "read_file"}:
        path = arguments.get("file_path") or arguments.get("path")
        return (posixpath.normpath(path),) if isinstance(path, str) and posixpath.basename(path) == "SKILL.md" else ()
    if tool in {"exec_command", "Bash"}:
        command = arguments.get("cmd") or arguments.get("command")
        return tuple(_read_paths(command, arguments.get("workdir"))) if isinstance(command, str) else ()
    return ()


def _successful_contents(value: Any, *, direct_read: bool = False, depth: int = 0):
    if depth > 12:
        return
    if isinstance(value, str):
        if any(code != "0" for code in re.findall(r"Process exited with code (-?\d+)\b", value)):
            return
        try:
            decoded = json.loads(value)
        except ValueError:
            decoded = None
        if isinstance(decoded, (dict, list)):
            yield from _successful_contents(decoded, direct_read=direct_read, depth=depth + 1)
        elif direct_read or re.search(r"Process exited with code 0\b", value):
            yield value
        return
    if isinstance(value, list):
        # A bare printed file also needs a completed enclosing script.
        completed = any(isinstance(item, dict) and str(item.get("text", "")).startswith("Script completed") for item in value)
        for child in value:
            yield from _successful_contents(child, direct_read=direct_read or completed, depth=depth + 1)
        return
    if not isinstance(value, dict) or value.get("is_error") or value.get("isError"):
        return
    if "exit_code" in value:
        if value["exit_code"] == 0 and isinstance(value.get("output"), str):
            yield value["output"]
        return
    if (value.get("success") is False or value.get("status") in {
        "failed", "failure", "error", "cancelled", "rejected"
    } or value.get("error")):
        return
    for key in ("content", "text", "result", "value", "output"):
        if key in value:
            yield from _successful_contents(value[key], direct_read=direct_read, depth=depth + 1)


def _skill_names(text: str) -> set:
    # Both Claude Read and `nl` prefix source lines; preserve actual YAML text.
    text = re.sub(r"(?m)^\s*\d+(?:→|\s+)\s?", "", text)
    names = set()
    for block in re.finditer(r"(?m)^---[ \t]*\n([\s\S]{1,16000}?)^---[ \t]*$", text):
        try:
            metadata = yaml.safe_load(block.group(1))
        except yaml.YAMLError:
            continue
        name = metadata.get("name") if isinstance(metadata, dict) else None
        if isinstance(name, str) and 0 < len(name.strip()) <= 160 and not any(ord(c) < 32 for c in name):
            names.add(name.strip())
    return names


class SkillReadCollector:
    """Keep only bounded call/skill identity until its result is observed."""

    def __init__(self, provider: str):
        self.provider = provider
        self.pending = {}
        self.reads = []
        self.requests = []
        self.event_requests = {}
        self.message_ids = {}
        self.message_requests = {}
        self.executions = []
        self.cwd = None

    def observe(self, record: dict, source_line: int) -> None:
        timestamp = record.get("timestamp")
        occurred_at = timestamp if isinstance(timestamp, str) else None
        if self.provider == "codex":
            payload = record.get("payload")
            if not isinstance(payload, dict):
                return
            if isinstance(payload.get("cwd"), str):
                self.cwd = payload["cwd"]
            if record.get("type") == "turn_context" or (
                record.get("type") == "event_msg" and payload.get("type") == "task_started"
            ):
                turn = payload.get("turn_id")
                if isinstance(turn, str) and turn:
                    self.requests.append((source_line, stable_id("skill-request", "codex", turn)))
            if record.get("type") == "event_msg":
                if payload.get("type") in {"user_message", "agent_message"}:
                    self.message_ids[source_line] = source_native_event_id(payload, "")
                item = payload.get("item")
                if (payload.get("type") == "item_completed" and isinstance(item, dict)
                        and item.get("type") == "CommandExecution"
                        and item.get("status") in {"completed", "failed"}
                        and isinstance(item.get("exit_code"), int)
                        and isinstance(item.get("id"), str) and item["id"]):
                    paths = _execution_paths(item.get("command"), item.get("cwd") or self.cwd)
                    if paths:
                        self.executions.append((item["id"], paths, source_line, occurred_at))
            if record.get("type") != "response_item":
                return
            native_id = payload.get("call_id") or payload.get("id")
            metadata = payload.get("internal_chat_message_metadata_passthrough")
            turn = metadata.get("turn_id") if isinstance(metadata, dict) else None
            if isinstance(native_id, str) and isinstance(turn, str) and turn:
                self.event_requests[native_id] = stable_id("skill-request", "codex", turn)
            if payload.get("type") == "message" and payload.get("role") in {"user", "assistant"}:
                self.message_ids[source_line] = source_native_event_id(payload, "")
                if isinstance(turn, str) and turn:
                    self.message_requests[source_line] = stable_id("skill-request", "codex", turn)
            if payload.get("type") in {"function_call", "custom_tool_call"}:
                self._call(payload.get("name"), native_id,
                           payload.get("arguments") or payload.get("input"), source_line, occurred_at)
            elif payload.get("type") in {"function_call_output", "custom_tool_call_output"}:
                self._result(native_id, payload.get("output"))
        elif not record.get("isMeta"):
            if isinstance(record.get("cwd"), str):
                self.cwd = record["cwd"]
            if record.get("type") in {"user", "assistant"}:
                self.message_ids[source_line] = source_native_event_id(record, "")
            message = record.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            is_result = (record.get("sourceToolAssistantUUID") or "toolUseResult" in record
                         or (isinstance(content, list) and any(isinstance(item, dict)
                             and item.get("type") == "tool_result" for item in content)))
            if record.get("type") == "user" and not is_result:
                native_id = record.get("uuid")
                if isinstance(native_id, str) and native_id:
                    self.requests.append((source_line, stable_id("skill-request", "claude", native_id)))
            if not isinstance(content, list):
                return
            for item in content:
                if not isinstance(item, dict):
                    continue
                if record.get("type") == "assistant" and item.get("type") == "tool_use":
                    self._call(item.get("name"), item.get("id"), item.get("input"), source_line, occurred_at)
                elif record.get("type") == "user" and item.get("type") == "tool_result" and not item.get("is_error"):
                    self._result(item.get("tool_use_id"), item.get("content"))

    def _call(self, tool_name, native_id, arguments, source_line, occurred_at):
        if not isinstance(tool_name, str) or not isinstance(native_id, str) or not native_id.strip():
            return
        paths = _call_paths(tool_name, arguments)
        scripts = []
        if self.provider == "claude" and tool_name == "Bash" and isinstance(arguments, dict):
            scripts = _execution_paths(arguments.get("command"), arguments.get("workdir") or self.cwd)
        if paths or scripts:
            self.pending[native_id] = (tool_name, paths, scripts, source_line, occurred_at)

    def _result(self, native_id, value):
        call = self.pending.get(native_id) if isinstance(native_id, str) else None
        if not call:
            return
        tool_name, paths, scripts, source_line, occurred_at = call
        if scripts:
            # Claude emits this only for a non-error tool result.
            self.executions.append((native_id, scripts, source_line, occurred_at))
        direct_read = tool_name.rsplit(".", 1)[-1] in {"Read", "read_file"}
        names = set()
        for text in _successful_contents(value, direct_read=direct_read):
            names.update(_skill_names(text))
        for path in paths:
            parent = posixpath.basename(posixpath.dirname(path)).casefold()
            for name in names:
                if parent != name.rsplit(":", 1)[-1].casefold():
                    continue
                self.reads.append(ParsedSkillObservation(
                    native_event_id=native_id,
                    skill_name=name,
                    signal_kind=self.provider + "_skill_read",
                    source_line=source_line,
                    occurred_at=occurred_at,
                    skill_locator=path,
                ))

    def finish(self, explicit: list, events: list) -> list:
        user_requests = [
            (event.source_line, stable_id("skill-request", self.provider, event.event_id))
            for event in events if event.event_type == "message" and event.role == "user"
        ]
        if self.provider == "claude":
            native_requests = dict(self.requests)
            requests = [(line, native_requests.get(line, key)) for line, key in user_requests]
        else:
            requests = self.requests or user_requests
        requests.sort()
        lines = [line for line, _ in requests]
        locator_names = {posixpath.normpath(item.skill_locator): item.skill_name
                         for item in explicit if item.skill_locator}
        observations = []
        for item in sorted(explicit + self.reads, key=lambda item: item.source_line):
            key = self.event_requests.get(item.native_event_id)
            index = bisect.bisect_right(lines, item.source_line) - 1
            if key is None and index >= 0:
                key = requests[index][1]
            # Generated context can precede the first native turn context.
            if key is None and self.requests and item.signal_kind == "codex_skill_context":
                key = requests[0][1]
            name = locator_names.get(item.skill_locator, item.skill_name) if item.signal_kind.endswith("_read") else item.skill_name
            observations.append(replace(item, skill_name=name, request_key=key))
        known_skills = {}
        for item in observations:
            if item.skill_locator or item.skill_name not in known_skills:
                known_skills[item.skill_name] = item.skill_locator
        matcher = SkillReferenceMatcher(known_skills)
        for event in events:
            if event.event_type != "message" or event.role not in {"user", "assistant"} or not event.text:
                continue
            # Generated instructions/catalogs are availability, not references.
            if event.text.strip().startswith(("# AGENTS.md instructions for ", "<environment_context>", "<skills_instructions>")):
                continue
            index = bisect.bisect_right(lines, event.source_line) - 1
            key = self.message_requests.get(event.source_line)
            if key is None and index >= 0:
                key = requests[index][1]
            identity = self.message_ids.get(event.source_line) or event.event_id
            for name in sorted(matcher.match(event.text)):
                observations.append(ParsedSkillObservation(
                    native_event_id="mention:" + identity,
                    skill_name=name,
                    skill_locator=known_skills[name],
                    signal_kind=self.provider + "_skill_mention",
                    source_line=event.source_line,
                    occurred_at=event.occurred_at,
                    request_key=key,
                ))
        roots = {posixpath.dirname(item.skill_locator): item.skill_name for item in observations
                 if item.skill_locator and posixpath.basename(item.skill_locator) == "SKILL.md"}
        for identity, paths, source_line, occurred_at in self.executions:
            index = bisect.bisect_right(lines, source_line) - 1
            key = requests[index][1] if index >= 0 else None
            for root, name in roots.items():
                if any(path.startswith(root + "/scripts/") for path in paths):
                    observations.append(ParsedSkillObservation(
                        native_event_id="script:" + identity,
                        skill_name=name,
                        skill_locator=known_skills[name],
                        signal_kind=self.provider + "_skill_script",
                        source_line=source_line,
                        occurred_at=occurred_at,
                        request_key=key,
                    ))
        observations.sort(key=lambda item: (item.source_line, item.skill_name))
        return observations
