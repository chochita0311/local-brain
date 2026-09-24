#!/usr/bin/env python3
"""Run frozen synthetic work-context cases locally. Never opens a source DB."""

import argparse
import contextlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
from localbrain.work_context_evaluation import evaluate, verify_evidence_development
from localbrain.work_reconstruction import ExperimentError
from work_context_cases import CASES, assess


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ExperimentError("INVALID_ARGUMENTS")


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    parser.add_argument("--split", choices=("development", "holdout", "all"), default="development")
    parser.add_argument("--decoding", choices=("greedy", "sampled"), default="greedy")
    parser.add_argument("--thinking", action="store_true")
    parser.add_argument("--strategy", choices=("single", "staged", "classified", "selected", "evidence"), default="single")
    parser.add_argument("--development-report", type=Path)
    try:
        args = parser.parse_args(argv)
        suite, scorer = CASES, assess
        settings = {}
        if args.strategy == "evidence":
            from work_context_evidence_cases import CASES as suite, assess as scorer
            if (args.split == "all" or args.thinking or args.decoding != "greedy"
                    or args.device not in {"auto", "mps"}
                    or (args.split == "holdout") != (args.development_report is not None)):
                raise ExperimentError("INVALID_ARGUMENTS")
            settings = {"max_tokens": 8192, "max_output": 128, "max_seconds": 30}
        elif args.development_report is not None:
            raise ExperimentError("INVALID_ARGUMENTS")
        selected_splits = {args.split}
        if args.strategy == "evidence" and args.split == "development":
            selected_splits.add("compositional")
        cases = [case for case in suite if args.split == "all" or case["split"] in selected_splits]
        print("SYNTHETIC_EVALUATION_RUNNING", flush=True)
        with open(os.devnull, "w") as quiet, contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            from localbrain.work_context_model import LocalGenerator
            generator = LocalGenerator(args.model_root, device=args.device,
                                       decoding=args.decoding, thinking=args.thinking, **settings)
            if args.strategy == "evidence":
                from localbrain.work_context_evidence import validate_runtime
                validate_runtime(generator)
                if args.split == "holdout":
                    development = [c for c in suite if c["split"] in {"development", "compositional"}]
                    verify_evidence_development(generator, development, scorer, args.development_report)
            report = evaluate(generator, cases, scorer, args.output, strategy=args.strategy)
        print("SYNTHETIC_" + args.split.upper() + ("_PASS" if report["gate_passed"] else "_FAIL"))
        return 0 if report["gate_passed"] else 3
    except KeyboardInterrupt:
        print("SYNTHETIC_EVALUATION_INTERRUPTED")
        return 130
    except ExperimentError as error:
        print(str(error))
        return 2
    except Exception:
        print("SYNTHETIC_EVALUATION_FAILED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
