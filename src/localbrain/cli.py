import argparse
import contextlib
import json
import os
import platform
import sqlite3
import sys

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "simulate":
        from .session_simulation_cli import main as simulate_main
        return simulate_main(argv[1:], application_defaults=True)
    parser = argparse.ArgumentParser(prog="localbrain")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("init", help="Initialize the local database")
    serve_parser = subparsers.add_parser("serve", help="Start the local web application")
    serve_parser.add_argument("--host", choices=("127.0.0.1", "::1"), default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    subparsers.add_parser("doctor", help="Report installation and optional local-model readiness")
    subparsers.add_parser("simulate", help="Explicitly prepare or inspect the full-history map")
    models_parser = subparsers.add_parser("models", help="Manage pinned public local-model assets")
    model_commands = models_parser.add_subparsers(dest="model_action", required=True)
    model_commands.add_parser("status", help="Report presence without downloading or running models")
    for action in ("install", "verify"):
        model_parser = model_commands.add_parser(action)
        model_parser.add_argument("model", choices=("embedding", "4b", "8b"))
        if action == "install":
            model_parser.add_argument("--offline", action="store_true", help="Adopt only verified cached public assets")
    storage_parser = subparsers.add_parser("storage", help="Inspect and manage local data, derived cache and development archives")
    storage_commands = storage_parser.add_subparsers(dest="storage_action", required=True)
    storage_commands.add_parser("status")
    cleanup_parser = storage_commands.add_parser("cleanup", help="Preview inactive recovery-copy and expired-cache retirement")
    cleanup_parser.add_argument("--apply", action="store_true", help="Remove eligible recovery copies and derived results")
    migrate_parser = storage_commands.add_parser("migrate", help="Preview storage moves; stop the app before applying")
    migrate_parser.add_argument("--apply", action="store_true", help="Move recognized inactive directories")
    migrate_parser.add_argument("--include-development", action="store_true", help="Also move owned development archives")
    scan_parser = subparsers.add_parser("scan", help="Import changed local sources")
    scan_parser.add_argument(
        "--full", action="store_true", help="Reparse every source file"
    )
    args = parser.parse_args(argv)

    if args.command == "serve":
        if not 1 <= args.port <= 65535:
            parser.error("port must be between 1 and 65535")
        import uvicorn
        uvicorn.run("localbrain.main:app", host=args.host, port=args.port)
        return 0

    if args.command in {"models", "doctor"}:
        from .model_installation import install_model, model_status, verify_model
        if args.command == "doctor":
            print(json.dumps({"platform": platform.system(), "machine": platform.machine(),
                              "python": platform.python_version(), "local_models": model_status()}, indent=2))
            return 0
        if args.model_action == "status":
            print(json.dumps(model_status(), indent=2))
            return 0
        try:
            # Libraries must never include private paths, inputs or tokens in CLI diagnostics.
            with open(os.devnull, "w") as quiet, contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
                if args.model_action == "install":
                    install_model(args.model, local_only=args.offline)
                else:
                    verify_model(args.model)
            print("MODEL_INSTALLED" if args.model_action == "install" else "MODEL_VERIFIED")
            return 0
        except KeyboardInterrupt:
            print("MODEL_INTERRUPTED")
            return 130
        except ImportError:
            print("LOCAL_MODELS_EXTRA_REQUIRED")
            return 2
        except Exception as error:
            from .work_reconstruction import ExperimentError
            from .runtime_storage import StorageError
            print(str(error) if isinstance(error, (ExperimentError, StorageError)) else "MODEL_OPERATION_FAILED")
            return 2

    if args.command == "storage":
        from .config import cache_directory, development_directory, settings
        from .runtime_storage import inactive_files, maintain_migration_backups, storage_status
        from .storage_layout import maintain_derived_cache, migrate_storage
        if args.storage_action == "status":
            print(json.dumps(storage_status(settings.data_dir, cache_dir=cache_directory(settings),
                                            development_dir=development_directory(settings)), indent=2))
            return 0
        if args.storage_action == "migrate":
            from .runtime_storage import StorageError
            try:
                result = migrate_storage(settings, apply=args.apply, include_development=args.include_development)
                print(json.dumps(result, indent=2))
                return 0
            except Exception as error:
                print(str(error) if isinstance(error, StorageError) else "STORAGE_MIGRATION_FAILED")
                return 2
        database = settings.database_path.resolve()
        group = [p for p in (database, database.with_name(database.name + "-wal"),
                             database.with_name(database.name + "-shm")) if p.exists()]
        if not database.is_file() or not inactive_files(group) or any(
                p.name.endswith("-wal") and p.stat().st_size for p in group):
            print("DATABASE_UNAVAILABLE_OR_BUSY")
            return 2
        try:
            connection = sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True)
            connection.row_factory = sqlite3.Row
            try:
                result = {"migration_backups": maintain_migration_backups(database, connection, apply=args.apply)}
            finally:
                connection.close()
            result["derived_cache"] = maintain_derived_cache(cache_directory(settings), apply=args.apply)
            print(json.dumps(result, indent=2))
            return 0
        except Exception:
            print("STORAGE_CLEANUP_FAILED")
            return 2

    if args.command == "scan":
        from .ingest.scanner import scan_all
        print(json.dumps(scan_all(force=args.full), ensure_ascii=False, indent=2))
        return 0

    from .db import init_db
    init_db()
    print("LocalBrain database initialized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
