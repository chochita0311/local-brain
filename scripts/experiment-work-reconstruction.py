#!/usr/bin/env python3
"""Run the explicitly scoped, local-only work reconstruction experiment."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from localbrain.work_reconstruction_experiment import main


if __name__ == "__main__":
    raise SystemExit(main())
