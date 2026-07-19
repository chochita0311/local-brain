import argparse
from pathlib import Path

from schema_presentation_builder import (
    PACKAGE_OUTPUT,
    PresentationBuildError,
    check_manifest,
    write_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build LocalBrain schema presentation")
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--output", type=Path, default=PACKAGE_OUTPUT)
    args = parser.parse_args()
    try:
        if args.mode == "build":
            write_manifest(args.output)
            print(f"Built schema presentation: {args.output}")
        else:
            check_manifest(args.output)
            print("LocalBrain schema presentation is current.")
    except PresentationBuildError as error:
        print(str(error))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
