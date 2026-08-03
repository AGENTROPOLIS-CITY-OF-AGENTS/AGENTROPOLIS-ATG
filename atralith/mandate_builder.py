"""Mandate builder — turns a generic mandate spec into a hashed ATG mandate.

Chain semantics (shared across atralith-lite):
    mandate -> envelope -> receipt

Every artifact is JSON carrying a SHA-256 ``hash`` computed over canonical
serialization (sorted keys, compact separators). The envelope embeds the
mandate hash; the receipt embeds the envelope hash.

API:
    build(spec: dict) -> dict          validate spec, add id/created_at/hash
    hash_mandate(mandate: dict) -> str hex sha256 over canonical JSON
    validate(spec: dict) -> None       raise on a bad spec

Example:
    from atralith.mandate_builder import build

    mandate = build({
        "agent": "agent:cityflight-01",
        "action": "cityflight",
        "target": "contract:cityflight-runtime",
        "constraints": {"max_generations_per_hour": 10},
        "expires_at": "2026-08-08T00:00:00Z",
    })
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import FormatChecker

SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "mandate.schema.json"

__all__ = ["build", "hash_mandate", "validate", "canonical_dumps"]


def _load_schema() -> dict[str, Any]:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def canonical_dumps(obj: dict[str, Any]) -> str:
    """Serialize a dict to canonical JSON: sorted keys, compact separators.

    This is the serialization the SHA-256 ``hash`` is computed over, so every
    atralith-lite module uses the exact same bytes for a given logical object.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def hash_mandate(mandate: dict[str, Any]) -> str:
    """Return the hex SHA-256 of a mandate's canonical JSON.

    The ``hash`` key itself (if present) is excluded before hashing so the
    function is idempotent: ``hash_mandate(built)`` equals ``built["hash"]``.
    """
    content = {k: v for k, v in mandate.items() if k != "hash"}
    return hashlib.sha256(canonical_dumps(content).encode("utf-8")).hexdigest()


def validate(spec: dict[str, Any]) -> None:
    """Validate a mandate spec against the mandate schema.

    Raises:
        ValueError: if ``spec`` is not a dict.
        jsonschema.ValidationError: if the spec violates the schema.
    """
    if not isinstance(spec, dict):
        raise ValueError(f"mandate spec must be a dict, got {type(spec).__name__}")
    schema = _load_schema()
    jsonschema.validate(spec, schema, format_checker=FormatChecker())
    _check_date_time_fields(schema, spec)


def _check_date_time_fields(schema: dict[str, Any], spec: dict[str, Any]) -> None:
    """Enforce ``format: date-time`` fields with stdlib (jsonschema only checks
    date-time when the optional rfc3339-validator package is installed, which
    the no-extra-deps contract forbids relying on).

    Generic: walks the schema's declared properties, so any field marked
    ``format: date-time`` in the schema is checked, not just ``expires_at``.
    """
    props = schema.get("properties", {})
    for name, prop in props.items():
        if prop.get("type") == "string" and prop.get("format") == "date-time":
            value = spec.get(name)
            if value is None:
                continue
            if not isinstance(value, str):
                raise jsonschema.ValidationError(f"{name!r} must be a date-time string")
            normalized = value.replace("Z", "+00:00")
            try:
                datetime.fromisoformat(normalized)
            except ValueError as exc:
                raise jsonschema.ValidationError(
                    f"{name!r} is not a valid RFC3339/ISO8601 date-time: {value!r}"
                ) from exc


def build(spec: dict[str, Any]) -> dict[str, Any]:
    """Validate a mandate spec and produce a hashed mandate dict.

    Output keys: the original spec fields, plus ``id``, ``created_at``
    (ISO8601 UTC), and ``hash`` (hex SHA-256 over canonical JSON of the
    mandate content, excluding the ``hash`` key itself).

    Raises the same errors as :func:`validate` on a bad spec.
    """
    validate(spec)

    mandate: dict[str, Any] = dict(spec)
    mandate["id"] = f"mdt_{uuid.uuid4().hex}"
    mandate["created_at"] = (
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    mandate["hash"] = hash_mandate(mandate)
    return mandate
