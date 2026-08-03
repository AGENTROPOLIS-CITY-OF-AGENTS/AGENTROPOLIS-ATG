"""Receipt generator and verifier — produces and checks RFC-0001 authorization receipts.

Usage:
    from atralith.receipt import generate_receipt, verify_receipt

    receipt = generate_receipt(
        envelope=envelope,
        result=b'{"status":"deployed","tx":"0x..."}',
        receipt_chain=[...],
        verification_state="deployed",
    )

    is_valid, findings = verify_receipt(receipt, envelope, result)
"""

import hashlib
import json
import time
import uuid

from pathlib import Path
from typing import Any

import jsonschema

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "contracts"
SCHEMA_PATH = SCHEMA_DIR / "core" / "receipt.schema.json"


def _load_schema() -> dict[str, Any]:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def _sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode()
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def generate_receipt(
    envelope: dict[str, Any],
    result: bytes | str | dict[str, Any],
    verification_state: str = "pending_verification",
    receipt_chain: list[dict[str, str]] | None = None,
    policy_decision_hash: str | None = None,
    rendered_intent_hash: str | None = None,
    verifier: str | None = None,
    receipt_id: str | None = None,
) -> dict[str, Any]:
    """Generate an ATG authorization receipt from a signed envelope and execution result.

    Args:
        envelope: A validated authorization envelope (from sign_envelope).
        result: The executed result — bytes, string, or dict.
        verification_state: Verified, pending_verification, unsigned_preview, simulated, etc.
        receipt_chain: Optional list of {"step", "component", "hash"} dicts.
        policy_decision_hash: Optional hash of the policy decision.
        rendered_intent_hash: Optional hash of the reviewed rendering.
        verifier: Optional identifier of the verifying agent.
        receipt_id: Optional override receipt_id.

    Returns:
        A validated receipt dict.
    """
    schema = _load_schema()

    # Normalize result
    if isinstance(result, dict):
        result_bytes = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    elif isinstance(result, str):
        result_bytes = result.encode()
    else:
        result_bytes = result

    mandate_hash = envelope["proposal"]["mandate_hash"]
    payload_hash = envelope["proposal"]["payload_hash"]
    result_hash = _sha256_hex(result_bytes)

    auth = envelope["authorization"]

    receipt: dict[str, Any] = {
        "receipt_id": receipt_id or f"rcpt_{uuid.uuid4().hex[:12]}",
        "mandate_hash": mandate_hash,
        "payload_hash": payload_hash,
        "authorization_class": auth["class"],
        "verification_state": verification_state,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "display_trust": auth.get("display_trust", "host_rendered"),
        "signer_type": auth.get("signer_type", "software_session"),
        "confirmation": auth.get("confirmation", "none"),
        "blind_signing": auth.get("blind_signing", False),
        "fallback_used": auth.get("fallback_used", False),
        "result_hash": result_hash,
    }

    if policy_decision_hash:
        receipt["policy_decision_hash"] = policy_decision_hash
    if rendered_intent_hash:
        receipt["rendered_intent_hash"] = rendered_intent_hash
    if verifier:
        receipt["verifier"] = verifier
    if receipt_chain:
        receipt["receipt_chain"] = receipt_chain

    # Validate
    validator = jsonschema.validators.validator_for(schema)(schema)
    errors = list(validator.iter_errors(receipt))
    if errors:
        msgs = [f"{e.message} (path: {' → '.join(str(p) for p in e.path)})" for e in errors]
        raise ValueError(f"Receipt validation failed:\n" + "\n".join(msgs))

    return receipt


def verify_receipt(
    receipt: dict[str, Any],
    envelope: dict[str, Any] | None = None,
    result: bytes | str | dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Verify an ATG receipt against its envelope and result.

    Checks that:
    - receipt is valid against the receipt schema
    - mandate_hash and payload_hash match the envelope (if provided)
    - result_hash matches the result (if provided)

    Args:
        receipt: The receipt to verify.
        envelope: Optional envelope to cross-check hashes against.
        result: Optional result to cross-check the result_hash against.

    Returns:
        (valid, findings) — True and empty list if all checks pass.
    """
    schema = _load_schema()
    findings: list[str] = []

    # Schema validation
    validator = jsonschema.validators.validator_for(schema)(schema)
    errors = list(validator.iter_errors(receipt))
    if errors:
        for e in errors:
            findings.append(f"Schema: {e.message} (path: {' → '.join(str(p) for p in e.path)})")
        return False, findings

    # Envelope cross-check
    if envelope:
        if receipt["mandate_hash"] != envelope["proposal"]["mandate_hash"]:
            findings.append("Hash mismatch: receipt mandate_hash != envelope mandate_hash")
        if receipt["payload_hash"] != envelope["proposal"]["payload_hash"]:
            findings.append("Hash mismatch: receipt payload_hash != envelope payload_hash")

    # Result cross-check
    if result is not None:
        if isinstance(result, dict):
            result_bytes = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
        elif isinstance(result, str):
            result_bytes = result.encode()
        else:
            result_bytes = result
        expected_result_hash = _sha256_hex(result_bytes)
        if receipt.get("result_hash") != expected_result_hash:
            findings.append("Hash mismatch: receipt result_hash != computed result hash")

    if findings:
        return False, findings

    return True, []
