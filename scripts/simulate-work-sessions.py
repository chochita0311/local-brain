#!/usr/bin/env python3
"""Explicit full-history simulation; compatibility entry point for source users."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from localbrain.session_simulation_cli import main


if __name__ == "__main__":
    raise SystemExit(main())
