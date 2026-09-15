import argparse

from data_model_value_registry import (
    RegistryCheckError,
    check_documents,
    write_documents,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build or check LocalBrain data-model value dictionaries"
    )
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()

    if args.mode == "build":
        try:
            write_documents()
        except RegistryCheckError as error:
            print(error)
            return 1
        print("Built the Data Model value-dictionary entrance and 10 subject dictionaries.")
        return 0

    errors = check_documents()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Data Model value registry and 10 generated dictionaries are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
