"""Authorization envelope builder — separates proposal from authorization.

Usage:
    from atralith.envelope import sign_envelope

    envelope = sign_envelope(
        mandate=mandate,
        payload=b'{"target":"0xabc..."}',
        authorization_class="A2_BOUNDED",
        authorizer="signer:treasury-01",
        signer_type="hardware_signer",
        key_residency="non_exportable",
        display_trust="independent_trusted_path",
        confirmation="human_physical",
    )
"""

import hashlib
import json

from pathlib import Path
from typing import Any

import jsonschema

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "contracts"
SCHEMA_PATH = SCHEMA_DIR / "core" / "authorization-envelope.schema.json"


def _load_schema() -> dict[str, Any]:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def _sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode()
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def sign_envelope(
    mandate: dict[str, Any],
    payload: bytes | str | dict[str, Any],
    authorization_class: str,
    authorizer: str,
    signer_type: str = "software_session",
    key_residency: str = "unknown",
    display_trust: str = "host_rendered",
    confirmation: str = "none",
    blind_signing: bool = False,
    fallback_used: bool = False,
) -> dict[str, Any]:
    """Construct and validate an ATG authorization envelope.

    The envelope separates the proposing agent from the authorizing component.
    The mandate_hash and payload_hash bind the envelope to those exact inputs.
    It records caller-provided authorization claims; it does not perform
    cryptographic signing or authenticate the authorizer.

    Args:
        mandate: A validated mandate dict (from build_mandate).
        payload: The executable payload — bytes, string, or dict.
        authorization_class: A0_OBSERVE through A4_ROOT.
        authorizer: Identifier of the authorizing component.
        signer_type: Class of signing device.
        key_residency: Whether the key can be exported.
        display_trust: How the action was rendered for review.
        confirmation: How authorization was confirmed.
        blind_signing: True if payload was opaque.
        fallback_used: True if a weaker path was used.

    Returns:
        A validated authorization envelope dict.
    """
    schema = _load_schema()

    # Normalize payload to canonical form for hashing
    if isinstance(payload, dict):
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    elif isinstance(payload, str):
        payload_bytes = payload.encode()
    else:
        payload_bytes = payload

    mandate_hash = mandate.get("mandate_hash", _sha256_hex(json.dumps(mandate, sort_keys=True).encode()))
    payload_hash = _sha256_hex(payload_bytes)

    envelope: dict[str, Any] = {
        "proposal": {
            "agent_id": mandate["agent_id"],
            "mandate_hash": mandate_hash,
            "payload_hash": payload_hash,
        },
        "authorization": {
            "class": authorization_class,
            "authorizer": authorizer,
            "signer_type": signer_type,
            "key_residency": key_residency,
            "display_trust": display_trust,
            "confirmation": confirmation,
            "blind_signing": blind_signing,
            "fallback_used": fallback_used,
        },
    }

    # Validate against normative schema
    validator = jsonschema.validators.validator_for(schema)(schema)
    errors = list(validator.iter_errors(envelope))
    if errors:
        msgs = [f"{e.message} (path: {' → '.join(str(p) for p in e.path)})" for e in errors]
        raise ValueError(f"Envelope validation failed:\n" + "\n".join(msgs))

    return envelope
