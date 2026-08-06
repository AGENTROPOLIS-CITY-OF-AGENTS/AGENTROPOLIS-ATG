#!/usr/bin/env python3
"""ATG Schema Validator — validates ATG JSON documents against normative schemas.

Usage:
    python3 validate_atg.py mandate path/to/mandate.json
    python3 validate_atg.py envelope path/to/envelope.json
    python3 validate_atg.py receipt path/to/receipt.json
    python3 validate_atg.py risk path/to/risk.json
    python3 validate_atg.py --all path/to/dir/       # find and validate all .json files
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("jsonschema not installed. Run: pip install 'jsonschema[format]'", file=sys.stderr)
    sys.exit(2)


SCHEMA_DIR = Path(__file__).resolve().parent / "contracts"
SCHEMA_MAP = {
    "mandate": SCHEMA_DIR / "core/mandate.schema.json",
    "envelope": SCHEMA_DIR / "core/authorization-envelope.schema.json",
    "receipt": SCHEMA_DIR / "core/receipt.schema.json",
    "risk": SCHEMA_DIR / "core/risk-condition.schema.json",
}

EXISTING_SCHEMAS = {
    "resolve-request": SCHEMA_DIR / "nft-gateway/resolve-request.schema.json",
    "resolve-response": SCHEMA_DIR / "nft-gateway/resolve-response.schema.json",
    "avatar-forge": SCHEMA_DIR / "nft-gateway/avatar-forge.schema.json",
}


def load_schema(schema_path: Path) -> dict:
    with open(schema_path) as f:
        return json.load(f)


def load_document(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


class MissingFormatSupportError(RuntimeError):
    """Raised when jsonschema lacks a format checker required by a schema."""


def schema_formats(value: object) -> set[str]:
    """Return every format keyword used anywhere in a JSON Schema value."""
    if isinstance(value, dict):
        formats = {
            format_name
            for key, format_name in value.items()
            if key == "format" and isinstance(format_name, str)
        }
        for nested_value in value.values():
            formats.update(schema_formats(nested_value))
        return formats
    if isinstance(value, list):
        return set().union(*(schema_formats(item) for item in value)) if value else set()
    return set()


def ensure_format_support(format_checker: jsonschema.FormatChecker, *schemas: dict) -> None:
    """Fail when a checker lacks a format keyword asserted by a schema."""
    required_formats = (
        set().union(*(schema_formats(schema) for schema in schemas)) if schemas else set()
    )
    missing_formats = sorted(required_formats - set(format_checker.checkers))
    if missing_formats:
        raise MissingFormatSupportError(
            "Missing JSON Schema format checker support for: "
            f"{', '.join(missing_formats)}. Install it with: "
            "pip install 'jsonschema[format]'"
        )


def format_checker_for(*schemas: dict) -> jsonschema.FormatChecker:
    """Return a checker only when every schema format has a registered checker."""
    format_checker = jsonschema.FormatChecker()
    ensure_format_support(format_checker, *schemas)
    return format_checker


def build_validator(schema: dict, format_checker: jsonschema.FormatChecker | None = None):
    """Build a validator only when every schema format has a registered checker."""
    format_checker = format_checker or jsonschema.FormatChecker()
    ensure_format_support(format_checker, schema)
    validator_cls = jsonschema.validators.validator_for(schema)
    return validator_cls(schema, format_checker=format_checker)


def validate_doc(doc: dict, schema: dict, label: str) -> list[str]:
    """Validate a single document. Returns list of error strings (empty = valid)."""
    validator = build_validator(schema)
    errors = []
    for err in sorted(validator.iter_errors(doc), key=str):
        errors.append(f"{label}: {err.message} (path: {' → '.join(str(p) for p in err.path)})")
    return errors


def validate_all_schemas() -> list[str]:
    """Validate that every schema file is itself valid JSON Schema."""
    errors = []
    for name, path in {**SCHEMA_MAP, **EXISTING_SCHEMAS}.items():
        try:
            schema = load_schema(path)
            jsonschema.validators.validator_for(schema).check_schema(schema)
        except Exception as e:
            errors.append(f"Schema '{name}' ({path}) is invalid: {e}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="ATG Schema Validator")
    parser.add_argument("schema_name", nargs="?", help="Schema to validate against: mandate, envelope, receipt, risk")
    parser.add_argument("file", nargs="?", help="JSON file to validate")
    parser.add_argument("--all", help="Validate all .json files in a directory")
    parser.add_argument("--check-schemas", action="store_true", help="Validate that all schemas are valid JSON Schema")
    args = parser.parse_args()

    if args.check_schemas:
        errors = validate_all_schemas()
        if errors:
            for e in errors:
                print(f"FAIL: {e}")
            sys.exit(1)
        print(f"OK: All {len(SCHEMA_MAP) + len(EXISTING_SCHEMAS)} schemas are valid")
        sys.exit(0)

    if args.all:
        directory = Path(args.all)
        if not directory.is_dir():
            parser.error(f"--all path must be a directory: {directory}")
        schemas = {
            name: load_schema(schema_path)
            for name, schema_path in {**SCHEMA_MAP, **EXISTING_SCHEMAS}.items()
        }
        try:
            format_checker = format_checker_for(*schemas.values())
            validators = {
                name: build_validator(schema, format_checker)
                for name, schema in schemas.items()
            }
        except MissingFormatSupportError as e:
            parser.error(str(e))

        errors = []
        for path in sorted(directory.rglob("*.json")):
            if str(path).startswith(str(SCHEMA_DIR)):
                continue  # skip schema files themselves
            try:
                doc = load_document(path)
            except json.JSONDecodeError as e:
                errors.append(f"{path}: not valid JSON ({e})")
                continue

            matched = False
            for name, validator in validators.items():
                if validator.is_valid(doc):
                    print(f"PASS {path}: matches '{name}'")
                    matched = True
                    break
            if not matched:
                errors.append(f"{path}: does not match any ATG schema")

        if errors:
            for e in errors:
                print(f"FAIL: {e}")
            sys.exit(1)
        sys.exit(0)

    if args.schema_name and not args.file:
        parser.error("file is required when a schema name is supplied")

    if args.schema_name not in SCHEMA_MAP:
        print(f"Unknown schema: {args.schema_name}. Choose from: {', '.join(SCHEMA_MAP)}", file=sys.stderr)
        sys.exit(2)

    schema = load_schema(SCHEMA_MAP[args.schema_name])
    doc = load_document(Path(args.file))
    try:
        errors = validate_doc(doc, schema, args.file)
    except MissingFormatSupportError as e:
        parser.error(str(e))

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        sys.exit(1)

    print(f"PASS: {args.file} validates against {args.schema_name}")


if __name__ == "__main__":
    main()
