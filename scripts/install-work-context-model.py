#!/usr/bin/env python3
"""Explicitly install/verify the approved public model; never opens user sources."""

import argparse
import contextlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from localbrain.work_context_model import MODEL_ID, MODEL_IDS, install, verify
from localbrain.work_reconstruction import ExperimentError


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ExperimentError("INVALID_ARGUMENTS")


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--model", choices=MODEL_IDS,
                        help="Install only this pinned model; defaults to Qwen3-4B. Verify infers the owned model when omitted.")
    parser.add_argument("--xet-cache", type=Path,
                        help="Optional new empty private transfer directory outside Git; remove after the installer exits.")
    try:
        args = parser.parse_args(argv)
        print("MODEL_VERIFYING" if args.verify else "MODEL_INSTALLING", flush=True)
        with open(os.devnull, "w") as quiet, contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            verify(args.root, args.model) if args.verify else install(
                args.root, args.model or MODEL_ID, transfer_cache=args.xet_cache)
        print("MODEL_VERIFIED" if args.verify else "MODEL_INSTALLED")
        return 0
    except KeyboardInterrupt:
        print("MODEL_INTERRUPTED")
        return 130
    except ExperimentError as error:
        print(str(error))
        return 2
    except Exception:
        print("MODEL_INSTALL_FAILED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
