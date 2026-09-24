"""Supervised local experiment command. Private payloads never print by default."""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .work_reconstruction import (
    VERSION, ExperimentError, digest, eligible, identifier, metadata_baseline, metadata_view, reconstruct,
    require, timestamp, validate_snapshot,
)
from .work_reconstruction_input import load_snapshots, validate_manifest
from .work_reconstruction_preparation import prepare_current, unassessed_expectations
from .work_reconstruction_scoring import score, stability, validate_expectations


MAX_BYTES = 10 * 1024 * 1024
WALL_SECONDS = 120
MEMORY_BYTES = 512 * 1024 * 1024


def encode_bounded(value, limit=MAX_BYTES):
    output = bytearray()
    for part in json.JSONEncoder(ensure_ascii=False, sort_keys=True, allow_nan=False,
                                 separators=(",", ":")).iterencode(value):
        piece = part.encode("utf-8")
        require(len(output) + len(piece) <= limit, "OUTPUT_LIMIT")
        output.extend(piece)
    return bytes(output)


def decode_bounded(raw):
    require(len(raw) <= MAX_BYTES, "INPUT_LIMIT")
    def pairs(rows):
        result = {}
        for k, v in rows:
            require(k not in result, "INVALID_JSON"); result[k] = v
        return result
    def invalid(_):
        raise ExperimentError("INVALID_JSON")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, UnicodeError, RecursionError):
        raise ExperimentError("INVALID_JSON") from None


def read_json(path):
    source = Path(path)
    require(source.is_file() and not source.is_symlink(), "INVALID_INPUT")
    with source.open("rb") as handle:
        return decode_bounded(handle.read(MAX_BYTES + 1))


def _memory_usage():
    import resource
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return usage if sys.platform == "darwin" else usage * 1024


def _child(channel, operation, args, memory_bytes):
    stopped = threading.Event()
    try:
        os.setsid()
        # Observe only this task-owned, spawn-free process. No process inventory
        # or privileged ps/proc access is needed in restricted environments.
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (WALL_SECONDS, WALL_SECONDS))
        require(0 < _memory_usage() <= memory_bytes, "MEMORY_LIMIT")
        def watch():
            while not stopped.wait(0.01):
                try:
                    if not 0 < _memory_usage() <= memory_bytes:
                        os._exit(71)
                except BaseException:
                    os._exit(72)  # A lost monitor is never ignored.
        monitor = threading.Thread(target=watch, daemon=True)
        monitor.start()
        operations = {"load": load_snapshots, "prepare": prepare_current, "text": reconstruct, "metadata": metadata_baseline, "score": score}
        result = operations[operation](*args)
        payload = encode_bounded({"ok": True, "value": result})
        peak = _memory_usage()
        require(peak <= memory_bytes, "MEMORY_LIMIT")
        channel.send_bytes(payload)
        channel.send_bytes(encode_bounded({"peak_bytes": _memory_usage()}))
    except BaseException:
        # Never pickle/print an exception containing a record, path, or body.
        try:
            channel.send_bytes(b'{"ok":false}')
        except BaseException:
            pass
    finally:
        stopped.set()
        channel.close()


def supervise(operation, args, wall_seconds=WALL_SECONDS, memory_bytes=MEMORY_BYTES):
    require(operation in {"load", "prepare", "text", "metadata", "score"})
    require(0 < wall_seconds <= WALL_SECONDS and 0 < memory_bytes <= MEMORY_BYTES)
    require(sys.platform in {"darwin", "linux"}, "MONITOR_UNAVAILABLE")
    context = multiprocessing.get_context("fork")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_child, args=(sender, operation, args, memory_bytes), daemon=True)
    started, peak = time.monotonic(), 0
    process.start(); sender.close()
    try:
        message = None
        while True:
            require(time.monotonic() - started <= wall_seconds, "TIME_LIMIT")
            if receiver.poll(0.01):
                message = decode_bounded(receiver.recv_bytes(MAX_BYTES))
                break
            require(process.is_alive(), "WORKER_FAILED")
        require(message.get("ok"), "WORKER_FAILED")
        require(receiver.poll(max(0.001, wall_seconds - (time.monotonic() - started))), "TIME_LIMIT")
        metrics = decode_bounded(receiver.recv_bytes(1000))
        process.join(timeout=max(0.01, wall_seconds - (time.monotonic() - started)))
        require(not process.is_alive() and process.exitcode == 0 and message.get("ok"), "WORKER_FAILED")
        peak = metrics["peak_bytes"]
        require(peak <= memory_bytes and time.monotonic() - started <= wall_seconds, "RESOURCE_LIMIT")
        return message["value"], {"duration_seconds": round(time.monotonic() - started, 6), "peak_bytes": peak}
    except (EOFError, OSError):
        raise ExperimentError("WORKER_FAILED") from None
    finally:
        receiver.close()
        if process.is_alive():
            # Only the task-owned child/group may be killed, never the parent
            # group inherited during the brief interval before setsid().
            try:
                if os.getpgid(process.pid) == process.pid:
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
        process.join()
        process.close()


def evaluate_history(snapshots, expectations, private=False):
    require(isinstance(snapshots, list) and 0 < len(snapshots) <= 12)
    require(isinstance(expectations, dict) and set(expectations) == {"version", "snapshots"} and expectations["version"] == 1)
    names = [data.get("name") for data in snapshots]
    require(len(set(names)) == len(names) and set(expectations["snapshots"]) == set(names))
    # Bind and validate every answer key before executing either arm.
    for data in snapshots:
        validate_snapshot(data); validate_expectations(expectations["snapshots"][data["name"]], data)
    reports, history = [], []
    prior = None
    for data in snapshots:
        expected = expectations["snapshots"][data["name"]]
        report = {"name": data["name"], "snapshot_digest": digest(data), "expectations_digest": digest(expected), "resources": {}}
        for arm in ("text", "metadata"):
            for organization in (True, False):
                field = arm if organization else arm + "_without_organization"
                args = (data, (), organization) if arm == "text" else (metadata_view(data), organization)
                report[field], report["resources"][field] = supervise(arm, args)
                report[field + "_scores"], report["resources"][field + "_scoring"] = supervise("score", (report[field], expected))
        replay, report["resources"]["replay"] = supervise("text", (data,))
        report["deterministic"] = replay == report["text"]
        require(report["deterministic"], "NONDETERMINISTIC")
        if prior is not None:
            history.append(stability(prior, report["text"]))
        prior = report["text"]
        reports.append(report)
    last, last_expected = snapshots[-1], expectations["snapshots"][names[-1]]
    records = {r["key"]: r for r in last["records"]}
    longest = max((len({records[m["record_key"]].get("session_id") for m in g["members"]
                       if records[m["record_key"]].get("session_id") is not None}) for g in last_expected["groups"]), default=0)
    sessions = {s["id"] for s in last["sessions"] if eligible(s)}
    has_no_refs = len(last["references"]) == 0
    sufficient = private and 40 <= len(sessions) <= 60 and len(last_expected["groups"]) >= 10 and longest > 24 and len(snapshots) >= 3
    qualities = [r[arm + "_scores"]["quality"] for r in reports for arm in ("text", "text_without_organization")]
    quality = "insufficient" if not sufficient or "insufficient" in qualities else "fail" if "fail" in qualities else "pass"
    return {"version": VERSION, "technical": "pass", "input_kind": "private" if private else "supplied-fixture",
            "private_quality": quality, "viability": "unverified", "snapshots": reports, "history": history,
            "sample": {"sessions": len(sessions), "expected_efforts": len(last_expected["groups"]),
                       "longest_effort_sessions": longest, "all_references_absent": has_no_refs},
            "required_review": ["independent-local-expectations", "mandatory-synthetic-safety-witnesses",
                                "weak-reference-and-unrelated-append-assessment"]}


def publish(output_dir, report, owner, expires_at, private=False):
    identifier(owner)
    require(timestamp(expires_at) > datetime.now(timezone.utc), "INVALID_EXPIRY")
    output = Path(output_dir)
    require(output.is_absolute() and not output.exists() and not output.is_symlink(), "INVALID_OUTPUT")
    parent = output.parent.resolve(strict=True)
    require(str(output.parent) == str(parent), "INVALID_OUTPUT")
    repo = Path(__file__).resolve().parents[2]
    # A supplied fixture can also contain private content. Only authored tests
    # and examples belong in Git, never command-generated runtime reports.
    require(repo != parent and repo not in parent.parents, "INVALID_OUTPUT")
    payload = encode_bounded({"owner": owner, "expires_at": expires_at, "report": report})
    # No partial result survives a write failure; remove only these exact paths
    # created by this invocation, never an existing output or another task.
    created = False
    target = output / "comparison.json"
    try:
        output.mkdir(mode=0o700); created = True
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
    except BaseException:
        if created:
            if target.exists():
                target.unlink()
            output.rmdir()
        raise


class QuietParser(argparse.ArgumentParser):
    def error(self, message):
        raise ExperimentError("INVALID_ARGUMENTS")


def main(argv=None):
    parser = QuietParser(description="Explicit bounded work-reconstruction experiment; no default database access.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fixture")
    group.add_argument("--database")
    parser.add_argument("--manifest")
    parser.add_argument("--expectations")
    parser.add_argument("--prepare-through", help="Explicit UTC cutoff for deterministic existing-history sampling.")
    parser.add_argument("--unassessed", action="store_true", help="Run preparation without a quality answer key; viability remains unverified.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--owner")
    parser.add_argument("--expires-at")
    parser.add_argument("--share-summary", action="store_true", help="Explicitly print non-identifying aggregate outcomes.")
    try:
        args = parser.parse_args(argv)
        preparing = bool(args.prepare_through)
        require(not preparing or (args.database and not args.manifest and args.unassessed and not args.expectations), "INVALID_ARGUMENTS")
        require(not args.unassessed or preparing, "INVALID_ARGUMENTS")
        require(preparing or bool(args.database) == bool(args.manifest), "INVALID_ARGUMENTS")
        expected = None if preparing else read_json(args.expectations)
        if args.database and not preparing:
            manifest = validate_manifest(read_json(args.manifest))
            owner, expiry = manifest["owner"], manifest["expires_at"]
        else:
            manifest = None
            owner, expiry = args.owner, args.expires_at
        identifier(owner); require(timestamp(expiry) > datetime.now(timezone.utc), "INVALID_EXPIRY")
        # Check output scope before private content admission, without creating it.
        output = Path(args.output_dir)
        repo = Path(__file__).resolve().parents[2]
        require(output.is_absolute() and not output.exists() and not output.is_symlink(), "INVALID_OUTPUT")
        parent = output.parent.resolve(strict=True)
        require(output.parent == parent and repo != parent and repo not in parent.parents, "INVALID_OUTPUT")
        prepared = None
        if preparing:
            prepared, admission = supervise("prepare", (args.database, args.prepare_through, owner, expiry))
            snapshots = prepared["snapshots"]
            expected = unassessed_expectations(snapshots)
        elif args.database:
            snapshots, admission = supervise("load", (args.database, manifest))
        else:
            bundle = read_json(args.fixture)
            require(isinstance(bundle, dict) and set(bundle) == {"version", "snapshots"} and bundle["version"] == 1)
            snapshots, admission = bundle["snapshots"], None
        report = evaluate_history(snapshots, expected, private=bool(args.database))
        report["admission_resources"] = admission
        report["assessment"] = "unassessed" if preparing else "supplied-expectations"
        if prepared is not None:
            report["input_manifest"] = prepared["manifest"]
            report["preparation"] = prepared["preparation"]
        publish(args.output_dir, report, owner, expiry, private=bool(args.database))
        if args.share_summary:
            print(json.dumps({k: report[k] for k in ("technical", "private_quality", "viability")}))
        else:
            print("EXPERIMENT_RECORDED")
        return 0
    except KeyboardInterrupt:
        print("EXPERIMENT_CANCELLED"); return 130
    except Exception:
        print("EXPERIMENT_FAILED"); return 2


if __name__ == "__main__":
    raise SystemExit(main())
