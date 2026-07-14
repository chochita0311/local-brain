import argparse
import json

from .db import init_db
from .ingest.scanner import scan_all


def main() -> None:
    parser = argparse.ArgumentParser(prog="localbrain")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("init", help="Initialize the local database")
    scan_parser = subparsers.add_parser("scan", help="Import changed local sources")
    scan_parser.add_argument(
        "--full", action="store_true", help="Reparse every source file"
    )
    args = parser.parse_args()

    if args.command == "scan":
        print(json.dumps(scan_all(force=args.full), ensure_ascii=False, indent=2))
        return

    init_db()
    print("LocalBrain database initialized")


if __name__ == "__main__":
    main()
