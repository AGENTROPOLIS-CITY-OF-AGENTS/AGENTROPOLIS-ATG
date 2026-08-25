#!/usr/bin/env python3
"""Validate current ATG JSON contracts with fail-closed format checking."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("jsonschema not installed. Run: pip install 'jsonschema[format]'", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"


class MissingFormatSupportError(RuntimeError):
    pass


def schema_formats(value: object) -> set[str]:
    if isinstance(value, dict):
        found = {
            format_name
            for key, format_name in value.items()
            if key == "format" and isinstance(format_name, str)
        }
        for nested in value.values():
            found.update(schema_formats(nested))
        return found
    if isinstance(value, list):
        found: set[str] = set()
        for item in value:
            found.update(schema_formats(item))
        return found
    return set()


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_validator(schema: dict):
    checker = jsonschema.FormatChecker()
    required = schema_formats(schema)
    missing = sorted(required - set(checker.checkers))
    if missing:
        raise MissingFormatSupportError(
            "Missing JSON Schema format checker support for: "
            f"{', '.join(missing)}. Install it with: pip install 'jsonschema[format]'"
        )
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    return validator_cls(schema, format_checker=checker)


def schema_paths() -> list[Path]:
    return sorted(CONTRACTS.rglob("*.schema.json"))


def check_schemas() -> int:
    failures = 0
    for path in schema_paths():
        try:
            schema = load_json(path)
            if not isinstance(schema, dict):
                raise ValueError("schema root must be an object")
            build_validator(schema)
            print(f"PASS {path.relative_to(ROOT)}")
        except (json.JSONDecodeError, jsonschema.SchemaError, MissingFormatSupportError, ValueError) as exc:
            failures += 1
            print(f"FAIL {path.relative_to(ROOT)}: {exc}")
    return 1 if failures else 0


def validate_instance(schema_path: Path, document_path: Path) -> int:
    try:
        schema = load_json(schema_path)
        document = load_json(document_path)
        if not isinstance(schema, dict):
            raise ValueError("schema root must be an object")
        validator = build_validator(schema)
    except (OSError, json.JSONDecodeError, jsonschema.SchemaError, MissingFormatSupportError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors = sorted(validator.iter_errors(document), key=lambda err: list(err.path))
    if not errors:
        print(f"PASS {document_path} validates against {schema_path}")
        return 0

    for err in errors:
        location = ".".join(str(part) for part in err.path) or "<root>"
        print(f"FAIL {document_path}: {err.message} (path: {location})")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-schemas", action="store_true")
    parser.add_argument("schema", nargs="?", type=Path)
    parser.add_argument("document", nargs="?", type=Path)
    args = parser.parse_args()

    if args.check_schemas:
        if args.schema or args.document:
            parser.error("--check-schemas does not accept schema/document arguments")
        return check_schemas()

    if not args.schema or not args.document:
        parser.error("schema and document are required unless --check-schemas is used")
    return validate_instance(args.schema, args.document)


if __name__ == "__main__":
    raise SystemExit(main())
