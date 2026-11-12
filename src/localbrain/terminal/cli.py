"""Explicit terminal and service commands; no web server or database required."""
import argparse
import json
import sys

from .runtime import TerminalError, TerminalService


def main(argv=None, *, config=None, factory=TerminalService):
    parser = argparse.ArgumentParser(prog="lb terminal")
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="List managed terminals without starting the service")
    listing.add_argument("--json", action="store_true")
    stop = commands.add_parser("stop", help="End one terminal or all managed terminals")
    targets = stop.add_mutually_exclusive_group(required=True)
    targets.add_argument("id", nargs="?")
    targets.add_argument("--all", action="store_true")
    for flag in ("--json", "--yes", "--force"):
        stop.add_argument(flag, action="store_true")
    service = commands.add_parser("service", help="Manage the independent background service")
    actions = service.add_subparsers(dest="action", required=True)
    for action in ("install", "status", "start", "stop", "restart"):
        child = actions.add_parser(action)
        child.add_argument("--json", action="store_true")
        if action in ("stop", "restart"):
            child.add_argument("--yes", action="store_true")
            child.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if config is None:
        from localbrain.foundation.config import settings
        config = settings
    control = factory(config)
    destructive = ((args.command == "stop" and args.all) or
                   (args.command == "service" and args.action in {"stop", "restart"}))
    try:
        expected = None
        if destructive:
            current = control.list()
            if current.get("service", {}).get("unclean"):
                raise TerminalError("identity", "이전 작업의 종료를 확인할 수 없습니다. 해당 프로그램에서 확인해 주세요.")
            count = sum(item["state"] == "running" for item in current["terminals"])
            if count and not args.yes:
                if not sys.stdin.isatty():
                    raise TerminalError("confirmation_required", "--yes를 사용해 종료 범위를 확인해 주세요.")
                print(f"터미널 {count}개를 종료할까요? [y/N] ", end="", file=sys.stderr, flush=True)
                answer = sys.stdin.readline().strip()
                if answer.lower() not in {"y", "yes"}:
                    raise TerminalError("cancelled", "취소했습니다.")
            expected = {"generation": current["generation"], "terminals": [item["id"] for item in current["terminals"]]}
        if args.command == "list":
            result = control.list()
        elif args.command == "stop":
            params = {"id": args.id, "all": args.all, "force": args.force}
            if args.all:
                params["expected"] = expected
            result = (current if args.all and not current["running"] else control.rpc("stop", params))
        else:
            result = (control.stop(force=args.force, expected=expected) if args.action == "stop" else
                      control.restart(force=args.force, expected=expected) if args.action == "restart" else
                      getattr(control, args.action)())
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        elif args.command == "list":
            for terminal in result["terminals"]:
                state = terminal["state"] + (" · 종료 확인 필요" if terminal.get("error") else
                                             " · 입력 오류" if terminal.get("inputError") else "")
                print(terminal["id"], state, terminal["name"], terminal["cwd"], sep="\t")
            if not result["terminals"]:
                print("서비스 비정상 종료 · 이전 작업은 별도 확인 필요" if result["service"].get("unclean") else
                      "서비스 중지됨" if not result["running"] else "터미널 없음")
        elif args.command == "service" and args.action == "status":
            print("비정상 종료 · 이전 작업은 별도 확인 필요" if result.get("unclean") else
                  {"running": "실행 중", "stopped": "중지됨", "unsupported": "macOS 웹 전용",
                   "unknown": "상태 미확인", "incompatible": "버전 확인 필요"}[result["state"]])
        else:
            print("완료")
        if isinstance(result, dict) and result.get("state") in {"unknown", "incompatible"}:
            return 1
        return 0
    except (TerminalError, OSError) as error:
        code = error.code if isinstance(error, TerminalError) else "runtime_error"
        message = str(error) if isinstance(error, TerminalError) else "터미널 작업을 완료하지 못했습니다."
        print(json.dumps({"error": {"code": code, "message": message}}, ensure_ascii=False)
              if args.json else message, file=sys.stderr)
        return 1
