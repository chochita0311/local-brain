#!/usr/bin/env python3
"""Compare frozen synthetic role formulations; never reads Sessions or holdout."""

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
from localbrain.work_role_comparison import LIMITS, compare, matrix, preflight_tokenizer, suite_identity
from localbrain.work_reconstruction import ExperimentError
from work_role_comparison_cases import CASES


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ExperimentError("INVALID_ARGUMENTS")


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--describe", action="store_true")
    parser.add_argument("--model-root", type=Path)
    parser.add_argument("--output", type=Path)
    try:
        args = parser.parse_args(argv)
        if args.describe:
            print(json.dumps({"suite": suite_identity(CASES), "base_cases": len(CASES),
                              "observations": len(matrix(CASES)), "limits": LIMITS}, sort_keys=True))
            return 0
        if args.model_root is None or args.output is None:
            raise ExperimentError("INVALID_ARGUMENTS")
        print("SYNTHETIC_COMPARISON_RUNNING", flush=True)
        with open(os.devnull, "w") as quiet, contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            from localbrain.work_context_model import LocalGenerator
            generator = LocalGenerator(args.model_root, device="mps", max_tokens=LIMITS["max_tokens"],
                                       max_output=LIMITS["max_output"], max_seconds=LIMITS["call_seconds"])
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(str(generator.snapshot), local_files_only=True,
                                                       trust_remote_code=False, token=False)
            preflight_tokenizer(tokenizer, CASES)
            compare(generator, CASES, args.output)
        print("SYNTHETIC_COMPARISON_COMPLETE_NOT_MODEL_ADMISSION")
        return 0
    except KeyboardInterrupt:
        print("SYNTHETIC_COMPARISON_INTERRUPTED")
        return 130
    except ExperimentError as error:
        print(str(error))
        return 2
    except Exception:
        print("SYNTHETIC_COMPARISON_FAILED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
