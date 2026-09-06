"""Envelopes and contexts produced by the runtime must satisfy the published schemas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

from atg_core import ContextVector, Representation, parse, resolve_context  # noqa: E402

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas" / "atg"


def _load(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


def _validator(schema: dict):
    context_schema = _load("context-vector.schema.json")
    store = {context_schema["$id"]: context_schema, schema["$id"]: schema}
    resolver = jsonschema.RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return jsonschema.Draft7Validator(schema, resolver=resolver)


def test_context_vector_matches_schema():
    resolved = resolve_context(ContextVector(locale="en-GB", industry="TECH"))
    _validator(_load("context-vector.schema.json")).validate(resolved.context.to_dict())


def test_semantic_envelope_matches_schema():
    envelope = parse(
        "Deployment must support rollback within the service level agreement.",
        Representation(kind="human_text", name="natural_language", version="1"),
        ContextVector(locale="en-US", region="US", industry="TECH", jurisdiction="US"),
    )
    _validator(_load("semantic-envelope.schema.json")).validate(envelope.to_dict())
