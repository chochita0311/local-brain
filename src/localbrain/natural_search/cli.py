"""Explicit local preparation, aggregate status and retrieval diagnostics."""

import argparse
import json

from ..config import settings
from .index import prepare, read_settings, save_settings
from .model import SearchEncoder
from .molecules import Profile
from .retrieval import Retriever
from .service import SearchService


def main(argv=None):
    parser = argparse.ArgumentParser(prog="localbrain search")
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("status")
    build = commands.add_parser("prepare")
    build.add_argument("--target", type=int, choices=(256, 512, 768), default=512)
    build.add_argument("--dimension", type=int, choices=(512, 1024), default=512)
    build.add_argument("--overlap", type=int, choices=(0, 64), default=0)
    build.add_argument("--cutoff", type=float, default=Profile().cutoff)
    build.add_argument("--device", choices=("auto", "mps", "cpu"), default="auto")
    build.add_argument("--batch-size", type=int, default=8)
    build.add_argument("--rebuild", action="store_true", help="Recompute an owned index without reusing vectors")
    query = commands.add_parser("query")
    query.add_argument("text")
    query.add_argument("--mode", choices=("dense", "lexical", "hybrid"), default="hybrid")
    query.add_argument("--cutoff", type=float)
    query.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        if args.action == "status":
            print(json.dumps(SearchService(settings).status(), ensure_ascii=False))
            return 0
        if args.action == "prepare":
            profile = Profile(args.target, args.dimension, args.overlap, args.cutoff)
            encoder = SearchEncoder(settings, profile, device=args.device, batch_size=args.batch_size)
            save_settings(settings, profile)
            last = [-1]

            def progress(value):
                bucket = value["parents"] // 25
                if bucket != last[0] or value["state"] != "preparing":
                    print(json.dumps(value, ensure_ascii=False), flush=True)
                    last[0] = bucket
            prepare(settings, encoder, profile, progress=progress, force=args.rebuild)
            return 0
        enabled, profile = read_settings(settings)
        if not enabled:
            raise ValueError("SEARCH_DISABLED")
        encoder = SearchEncoder(settings, profile)
        retriever = Retriever(settings, profile, encoder)
        try:
            print(json.dumps(retriever.search(args.text, mode=args.mode, cutoff=args.cutoff,
                                              page_size=args.limit), ensure_ascii=False))
        finally:
            retriever.close()
        return 0
    except KeyboardInterrupt:
        print("SEARCH_INTERRUPTED")
        return 130
    except Exception as error:
        code = str(error)
        known = {"SEARCH_DISABLED", "SEARCH_MODEL_MISSING", "SEARCH_BUSY", "SEARCH_INDEX_UNAVAILABLE",
                 "SEARCH_INDEX_INCOMPATIBLE", "INVALID_SEARCH_PROFILE", "INVALID_SEARCH_CUTOFF",
                 "INVALID_SEARCH_QUERY", "INVALID_SEARCH_SETTINGS", "SEARCH_INPUT_TOO_LONG"}
        print(code if code in known else "SEARCH_OPERATION_FAILED")
        return 2
