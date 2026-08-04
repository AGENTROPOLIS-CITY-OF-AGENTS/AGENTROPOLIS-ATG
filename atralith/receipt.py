"""Receipt generator and verifier for structural/hash-consistent RFC-0001 receipts.

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
from jsonschema import FormatChecker, validators

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "contracts"
SCHEMA_PATH = SCHEMA_DIR / "core" / "receipt.schema.json"
ENVELOPE_SCHEMA_PATH = SCHEMA_DIR / "core" / "authorization-envelope.schema.json"
_MISSING_RESULT = object()
_FORMAT_CHECKER_UNAVAILABLE = (
    "Format validation unavailable: required date-time checker is unavailable; "
    "install jsonschema[format]."
)


class _ResultSerializationError(ValueError):
    """Raised when a Python result cannot be represented as canonical JSON."""


def _load_schema() -> dict[str, Any]:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def _load_envelope_schema() -> dict[str, Any]:
    with open(ENVELOPE_SCHEMA_PATH) as f:
        return json.load(f)


def _sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode()
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _serialize_result(result: Any) -> bytes:
    """Encode a result for hashing with stable semantics shared by both paths.

    Bytes and strings retain the legacy behavior of being hashed verbatim and as
    UTF-8 respectively. Every other JSON value is encoded as sorted, compact
    JSON, including lists, numbers, booleans, and explicit ``null``.
    """
    try:
        if isinstance(result, bytes):
            return result
        if isinstance(result, str):
            return result.encode()
        return json.dumps(
            result, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise _ResultSerializationError(
            f"result cannot be serialized as canonical JSON: {exc}"
        ) from exc


def _required_format_checker() -> FormatChecker | None:
    """Return the dependency-backed checker needed by these schemas, if present."""
    checker = FormatChecker()
    if "date-time" not in checker.checkers:
        return None
    return checker


def _validation_errors(
    schema: dict[str, Any], instance: Any, format_checker: FormatChecker | None
) -> list[jsonschema.ValidationError]:
    validator_cls = validators.validator_for(schema)
    validator = validator_cls(schema, format_checker=format_checker)
    return list(validator.iter_errors(instance))


def _format_error(error: jsonschema.ValidationError, prefix: str) -> str:
    path = " → ".join(str(part) for part in error.path)
    return f"{prefix}: {error.message} (path: {path})"


def generate_receipt(
    envelope: dict[str, Any],
    result: Any,
    verification_state: str = "pending_verification",
    receipt_chain: list[dict[str, str]] | None = None,
    policy_decision_hash: str | None = None,
    rendered_intent_hash: str | None = None,
    verifier: str | None = None,
    receipt_id: str | None = None,
) -> dict[str, Any]:
    """Generate an ATG receipt from an envelope and execution result.

    This records structural claims and hashes. It does not sign the envelope or
    make the receipt cryptographically verifiable.

    Args:
        envelope: A validated authorization envelope produced by the caller.
        result: The executed result — bytes, a string, or any JSON value.
        verification_state: Verified, pending_verification, unsigned_preview, simulated, etc.
        receipt_chain: Optional list of {"step", "component", "hash"} dicts.
        policy_decision_hash: Optional hash of the policy decision.
        rendered_intent_hash: Optional hash of the reviewed rendering.
        verifier: Optional identifier of the verifying agent.
        receipt_id: Optional override receipt_id.

    Returns:
        A validated receipt dict.

    Raises:
        ValueError: If the result is not serializable as canonical JSON, required
            date-time format validation is unavailable, or the receipt is invalid.
    """
    schema = _load_schema()
    format_checker = _required_format_checker()
    if format_checker is None:
        raise ValueError(f"Receipt validation failed:\n{_FORMAT_CHECKER_UNAVAILABLE}")

    result_bytes = _serialize_result(result)
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

    errors = _validation_errors(schema, receipt, format_checker)
    if errors:
        msgs = [_format_error(error, "Schema") for error in errors]
        raise ValueError("Receipt validation failed:\n" + "\n".join(msgs))

    return receipt


def verify_receipt(
    receipt: Any,
    envelope: dict[str, Any] | None = None,
    result: Any = _MISSING_RESULT,
) -> tuple[bool, list[str]]:
    """Check an ATG receipt against independently supplied envelope and result.

    Checks that:
    - receipt is valid against the receipt schema, including date-time formats
    - the supplied envelope is valid against its schema, including formats
    - receipt hashes and security-relevant claims match the supplied envelope
    - result_hash matches the supplied result

    This establishes structural/hash consistency only. It does not verify signer
    identity, cryptographic authorization, or cryptographic validity of receipt
    chain entries. Missing evidence always fails verification; an explicit JSON
    ``null`` result is evidence and hashes as canonical ``null``.
    """
    schema = _load_schema()
    findings: list[str] = []
    format_checker = _required_format_checker()

    receipt_errors = _validation_errors(schema, receipt, format_checker)
    if receipt_errors:
        findings.extend(_format_error(error, "Schema") for error in receipt_errors)
        if format_checker is None:
            findings.append(_FORMAT_CHECKER_UNAVAILABLE)
        return False, findings
    if format_checker is None:
        return False, [_FORMAT_CHECKER_UNAVAILABLE]

    # Envelope validation and cross-check.
    if envelope is None:
        findings.append("Evidence required: an independently supplied envelope is required for verification")
    else:
        envelope_schema = _load_envelope_schema()
        envelope_errors = _validation_errors(envelope_schema, envelope, format_checker)
        if envelope_errors:
            findings.extend(
                _format_error(error, "Envelope schema") for error in envelope_errors
            )
        else:
            if receipt.get("mandate_hash") != envelope["proposal"]["mandate_hash"]:
                findings.append("Hash mismatch: receipt mandate_hash != envelope mandate_hash")
            if receipt.get("payload_hash") != envelope["proposal"]["payload_hash"]:
                findings.append("Hash mismatch: receipt payload_hash != envelope payload_hash")

            for receipt_field, authorization_field in {
                "authorization_class": "class",
                "display_trust": "display_trust",
                "signer_type": "signer_type",
                "confirmation": "confirmation",
                "blind_signing": "blind_signing",
                "fallback_used": "fallback_used",
            }.items():
                receipt_value = receipt.get(
                    receipt_field, False if receipt_field == "fallback_used" else None
                )
                envelope_value = envelope["authorization"].get(
                    authorization_field,
                    False if authorization_field == "fallback_used" else None,
                )
                if receipt_value != envelope_value:
                    findings.append(
                        f"Claim mismatch: receipt {receipt_field} != envelope authorization {authorization_field}"
                    )

    # Result cross-check.
    if result is _MISSING_RESULT:
        findings.append("Evidence required: an independently supplied result is required for verification")
    else:
        try:
            expected_result_hash = _sha256_hex(_serialize_result(result))
        except _ResultSerializationError as exc:
            findings.append(f"Result serialization: {exc}")
        else:
            if receipt.get("result_hash") != expected_result_hash:
                findings.append("Hash mismatch: receipt result_hash != computed result hash")

    if findings:
        return False, findings
    return True, []
