#!/usr/bin/env python3
"""Explicit full-history simulation; no private content in command output."""

import argparse
import contextlib
import fcntl
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from localbrain.session_simulation import (
    OWNER, atomic_json, inventory, now, owned_store, read_json, simulate, sync_inventory,
)
from localbrain.work_reconstruction import ExperimentError, digest, require, timestamp
from localbrain.session_simulation_graph import validate_parameters


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ExperimentError("INVALID_ARGUMENTS")


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--inventory-only", action="store_true")
    modes.add_argument("--status", action="store_true")
    modes.add_argument("--purge", action="store_true")
    parser.add_argument("--model-manifest", type=Path)
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "mps", "cuda"))
    parser.add_argument("--chunk-chars", type=int, default=1800)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--neighbors", type=int, default=8)
    parser.add_argument("--similarity", type=float, default=0.65)
    parser.add_argument("--area-resolution", type=float, default=0.6)
    parser.add_argument("--work-resolution", type=float, default=1.2)
    parser.add_argument("--force-reembed", action="store_true")
    parser.add_argument("--show-counts", action="store_true", help="explicitly print non-identifying coverage/cache counts")
    try:
        args = parser.parse_args(argv)
        if args.status:
            marker = read_json(args.output / "owner.json")
            require(marker.get("owner") == OWNER, "UNOWNED_OUTPUT")
            require(not args.database.is_symlink() and args.database.is_file(), "INVALID_DATABASE")
            require(marker.get("database") == digest([str(args.database.resolve()), args.database.stat().st_dev,
                                                       args.database.stat().st_ino]), "UNOWNED_OUTPUT")
            require(timestamp(marker["expires_at"]) > now(), "SIMULATION_EXPIRED")
            progress = read_json(args.output / "progress.json")
            require(progress.get("owner") == OWNER and progress.get("state") in {
                "prepared", "inventory", "embedding", "grouping", "complete", "interrupted", "failed"})
            if progress["state"] in {"inventory", "embedding", "grouping"}:
                fd = os.open(args.output / "writer.lock", os.O_RDONLY | os.O_NOFOLLOW)
                try:
                    try:
                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        progress["state"] = "interrupted"
                    except BlockingIOError:
                        pass
                finally:
                    os.close(fd)
            if progress["state"] == "complete":
                manifest = progress["manifest"]
                require(inventory(args.database, manifest["chunk_chars"]) == manifest, "SOURCE_CHANGED")
            print("SIMULATION_" + progress["state"].upper())
            if args.show_counts:
                print(json.dumps({"coverage": progress.get("manifest", {}).get("coverage", {}),
                                  "encoded": progress.get("encoded", 0), "reused": progress.get("reused", 0),
                                  "total_vectors": progress.get("total_vectors", 0)}, sort_keys=True))
            return 0
        if args.purge:
            with owned_store(args.output, args.database, purge=True):
                pass
            print("SIMULATION_PURGED")
            return 0
        if args.inventory_only:
            with owned_store(args.output, args.database) as store:
                manifest = sync_inventory(store, args.database, args.chunk_chars)
                atomic_json(args.output / "progress.json", {"owner": OWNER, "state": "prepared", "manifest": manifest,
                            "updated_at": now().isoformat(), "quality": "unassessed"})
            print("SIMULATION_PREPARED")
            if args.show_counts:
                print(json.dumps(manifest["coverage"], sort_keys=True))
            return 0
        require(args.model_manifest is not None, "EXPLICIT_MODEL_REQUIRED")
        parameters = {"neighbors": args.neighbors, "similarity": args.similarity,
                      "area_resolution": args.area_resolution, "work_resolution": args.work_resolution, "seed": 0}
        validate_parameters(parameters)
        # Third-party progress/warnings/exceptions must never print private input.
        with open(os.devnull, "w") as quiet, contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            from localbrain.session_simulation_model import LocalEncoder, block_network
            block_network()
            encoder = LocalEncoder(args.model_manifest, device=args.device)
            report = simulate(args.database, args.output, encoder, chunk_chars=args.chunk_chars,
                              batch_size=args.batch_size, force=args.force_reembed,
                              parameters=parameters)
        print("SIMULATION_COMPLETE_UNASSESSED")
        if args.show_counts:
            print(json.dumps({"coverage": report["manifest"]["coverage"], "cache": report["cache"]}, sort_keys=True))
        return 0
    except KeyboardInterrupt:
        print("SIMULATION_INTERRUPTED")
        return 130
    except ExperimentError as error:
        print(str(error))
        return 2
    except Exception:
        print("SIMULATION_FAILED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
