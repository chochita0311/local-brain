#!/usr/bin/env python3
"""Run/replay the frozen synthetic source-claim trial, never private Sessions."""

import argparse
import contextlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
from localbrain.work_claim_trial import preflight_tokenizer, run_trial, suite_identity
from localbrain.work_claims import LIMITS, producer
from localbrain.work_reconstruction import ExperimentError
from localbrain.work_state import WorkStateError
from work_claim_cases import CASES, HOLDOUT
from work_context_evidence_cases import assess


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ExperimentError("INVALID_ARGUMENTS")


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--describe", action="store_true")
    parser.add_argument("--model-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--holdout", action="store_true")
    try:
        args = parser.parse_args(argv)
        if args.describe:
            print(json.dumps({"suite": suite_identity(CASES, HOLDOUT), "development_cases": len(CASES),
                              "conditional_holdout": len(HOLDOUT), "limits": LIMITS}, sort_keys=True))
            return 0
        if args.model_root is None or args.output is None:
            raise ExperimentError("INVALID_ARGUMENTS")
        print("SYNTHETIC_CLAIM_REPLAY_RUNNING" if args.replay else "SYNTHETIC_CLAIM_TRIAL_RUNNING", flush=True)
        started = time.monotonic()
        with open(os.devnull, "w") as quiet, contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            from localbrain.work_context_model import LocalGenerator
            generator = LocalGenerator(args.model_root, device="mps", max_tokens=LIMITS["tokens"],
                max_output=LIMITS["output"], max_seconds=LIMITS["call_seconds"])
            if not args.replay:
                from transformers import AutoTokenizer
                tokenizer = AutoTokenizer.from_pretrained(str(generator.snapshot), local_files_only=True,
                                                           trust_remote_code=False, token=False)
                preflight_tokenizer(tokenizer, CASES, producer(generator.contract))
            report = run_trial(generator, CASES, HOLDOUT, assess, args.output, replay=args.replay,
                               include_holdout=args.holdout, initial_seconds=time.monotonic() - started)
        print(json.dumps({"state": report["state"], "development_gate": report["development_gate"],
            "calls": report["calls"], "reused": report["reused_observations"],
            "holdout_executed": report["holdout_executed"], "model_admission": report["model_admission"]}, sort_keys=True))
        return 0
    except KeyboardInterrupt:
        print("SYNTHETIC_CLAIM_TRIAL_INTERRUPTED")
        return 130
    except (ExperimentError, WorkStateError) as error:
        print(str(error))
        return 2
    except Exception:
        print("SYNTHETIC_CLAIM_TRIAL_FAILED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
