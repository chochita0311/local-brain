"""Explicit preview command; no automatic preparation on package import."""
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
