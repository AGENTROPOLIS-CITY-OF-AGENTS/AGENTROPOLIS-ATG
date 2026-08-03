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
    print("jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
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


def validate_doc(doc: dict, schema: dict, label: str) -> list[str]:
    """Validate a single document. Returns list of error strings (empty = valid)."""
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)
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
        errors = []
        for path in sorted(directory.rglob("*.json")):
            if str(path).startswith(str(SCHEMA_DIR)):
                continue  # skip schema files themselves
            try:
                doc = load_document(path)
            except json.JSONDecodeError as e:
                print(f"SKIP {path}: not valid JSON ({e})")
                continue

            matched = False
            for name, schema_path in {**SCHEMA_MAP, **EXISTING_SCHEMAS}.items():
                schema = load_schema(schema_path)
                validator = jsonschema.validators.validator_for(schema)(schema)
                if validator.is_valid(doc):
                    print(f"PASS {path}: matches '{name}'")
                    matched = True
                    break
            if not matched:
                print(f"FAIL {path}: does not match any ATG schema")

        if errors:
            for e in errors:
                print(f"FAIL: {e}")
            sys.exit(1)
        sys.exit(0)

    if args.schema_name not in SCHEMA_MAP:
        print(f"Unknown schema: {args.schema_name}. Choose from: {', '.join(SCHEMA_MAP)}", file=sys.stderr)
        sys.exit(2)

    schema = load_schema(SCHEMA_MAP[args.schema_name])
    doc = load_document(Path(args.file))
    errors = validate_doc(doc, schema, args.file)

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        sys.exit(1)

    print(f"PASS: {args.file} validates against {args.schema_name}")


if __name__ == "__main__":
    main()
