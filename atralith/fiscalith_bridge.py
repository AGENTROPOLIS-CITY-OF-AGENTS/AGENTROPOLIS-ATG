"""ATRALITH <-> FISCALITH bridge.

ATG transports financial meaning without owning it. This module validates the
ATG-owned envelope, delegates payload validation to an injected FISCALITH
validator, and hands the compiled context to the Execution Envelope corridor.
It never selects a rail or provider and never grants authority.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

FISCALITH_SCHEMA_ID = "https://agentropolis.dev/fiscalith/financial-intent.v1.json"

SPEECH_ACTS = frozenset(
    {"REQUEST", "PROPOSE", "OFFER", "ACCEPT", "DELEGATE", "REFUSE", "VERIFY", "RECEIPT", "ESCALATE"}
)
AUTHORITY_REQUIRED_ACTS = frozenset({"REQUEST", "ACCEPT", "DELEGATE"})
FORBIDDEN_KEYS = frozenset({"rail", "provider", "chain", "wallet", "signer"})

REQUIRED_FIELDS = (
    "speech_act",
    "from_agent_entity_ref",
    "to_agent_entity_ref",
    "correlation_id",
    "mandate_ref",
    "delegation_chain",
    "capability_refs",
    "execution_envelope_ref",
    "requested_proof_classes",
    "fiscalith_payload",
    "schema_ref",
)

RESULT_STATUS_TO_SPEECH_ACT = {
    "SETTLED": "RECEIPT",
    "REFUSED": "REFUSE",
    "FAILED": "REFUSE",
    "PENDING": "VERIFY",
    "PARTIAL": "VERIFY",
}

NEXT_HOP = "EXECUTION_ENVELOPE"


class BridgeError(ValueError):
    """Envelope failed ATG-level validation."""


class BoundaryViolation(BridgeError):
    """Envelope or payload carries a field ATG must never own (rail, provider, chain, wallet, signer)."""


class AuthorityRequired(BridgeError):
    """Speech act carrying a financial payload requires a mandate_ref."""


@dataclass(frozen=True)
class CorridorHandoff:
    correlation_id: str
    from_agent_entity_ref: str
    to_agent_entity_ref: str
    mandate_ref: Optional[str]
    delegation_chain: List[str]
    capability_refs: List[str]
    execution_envelope_ref: Optional[str]
    requested_proof_classes: List[str]
    fiscalith_payload: Dict[str, Any]
    next_hop: str = NEXT_HOP
    grants_authority: bool = field(default=False, init=False)


def detect_financial_speech_act(message: Dict[str, Any]) -> bool:
    return isinstance(message, dict) and "fiscalith_payload" in message


def _forbidden_keys(obj: Dict[str, Any]) -> List[str]:
    return sorted(k for k in obj if isinstance(k, str) and k.lower() in FORBIDDEN_KEYS)


def _require_string_list(value: Any, name: str) -> List[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise BridgeError(f"{name} must be an array of non-empty strings")
    return list(value)


def _require_nullable_string(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise BridgeError(f"{name} must be a non-empty string or null")
    return value


def validate_envelope(message: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(message, dict):
        raise BridgeError("message must be an object")

    missing = [f for f in REQUIRED_FIELDS if f not in message]
    if missing:
        raise BridgeError(f"missing required fields: {', '.join(missing)}")

    unknown = sorted(set(message) - set(REQUIRED_FIELDS))
    if unknown:
        forbidden = [k for k in unknown if k.lower() in FORBIDDEN_KEYS]
        if forbidden:
            raise BoundaryViolation(f"envelope carries forbidden fields: {', '.join(forbidden)}")
        raise BridgeError(f"unknown fields: {', '.join(unknown)}")

    speech_act = message["speech_act"]
    if speech_act not in SPEECH_ACTS:
        raise BridgeError(f"unknown speech_act: {speech_act!r}")

    for name in ("from_agent_entity_ref", "to_agent_entity_ref", "correlation_id"):
        if not isinstance(message[name], str) or not message[name]:
            raise BridgeError(f"{name} must be a non-empty string")

    mandate_ref = _require_nullable_string(message["mandate_ref"], "mandate_ref")
    execution_envelope_ref = _require_nullable_string(message["execution_envelope_ref"], "execution_envelope_ref")
    delegation_chain = _require_string_list(message["delegation_chain"], "delegation_chain")
    capability_refs = _require_string_list(message["capability_refs"], "capability_refs")
    requested_proof_classes = _require_string_list(message["requested_proof_classes"], "requested_proof_classes")

    payload = message["fiscalith_payload"]
    if not isinstance(payload, dict):
        raise BridgeError("fiscalith_payload must be an object")
    forbidden = _forbidden_keys(payload)
    if forbidden:
        raise BoundaryViolation(f"fiscalith_payload carries forbidden top-level fields: {', '.join(forbidden)}")

    if message["schema_ref"] != FISCALITH_SCHEMA_ID:
        raise BridgeError(f"schema_ref must be {FISCALITH_SCHEMA_ID}")

    if speech_act in AUTHORITY_REQUIRED_ACTS and mandate_ref is None:
        raise AuthorityRequired(f"{speech_act} carrying a FISCALITH payload requires mandate_ref")

    return {
        "speech_act": speech_act,
        "from_agent_entity_ref": message["from_agent_entity_ref"],
        "to_agent_entity_ref": message["to_agent_entity_ref"],
        "correlation_id": message["correlation_id"],
        "mandate_ref": mandate_ref,
        "delegation_chain": delegation_chain,
        "capability_refs": capability_refs,
        "execution_envelope_ref": execution_envelope_ref,
        "requested_proof_classes": requested_proof_classes,
        "fiscalith_payload": payload,
        "schema_ref": FISCALITH_SCHEMA_ID,
    }


def compile_financial_message(
    message: Dict[str, Any],
    payload_validator: Callable[[Dict[str, Any]], Any],
) -> CorridorHandoff:
    if not detect_financial_speech_act(message):
        raise BridgeError("not a financial speech act: fiscalith_payload absent")
    env = validate_envelope(message)
    payload_validator(env["fiscalith_payload"])
    return CorridorHandoff(
        correlation_id=env["correlation_id"],
        from_agent_entity_ref=env["from_agent_entity_ref"],
        to_agent_entity_ref=env["to_agent_entity_ref"],
        mandate_ref=env["mandate_ref"],
        delegation_chain=env["delegation_chain"],
        capability_refs=env["capability_refs"],
        execution_envelope_ref=env["execution_envelope_ref"],
        requested_proof_classes=env["requested_proof_classes"],
        fiscalith_payload=env["fiscalith_payload"],
    )


def map_result_to_atg(
    fiscalith_result: Dict[str, Any],
    correlation_id: str,
    from_agent_entity_ref: str = "FISCALITH",
    to_agent_entity_ref: str = "AGENTENTITY",
) -> Dict[str, Any]:
    if not isinstance(fiscalith_result, dict):
        raise BridgeError("fiscalith_result must be an object")
    forbidden = _forbidden_keys(fiscalith_result)
    if forbidden:
        raise BoundaryViolation(f"fiscalith_result carries forbidden top-level fields: {', '.join(forbidden)}")

    if fiscalith_result.get("escalation_required") is True:
        speech_act = "ESCALATE"
    else:
        status = fiscalith_result.get("status")
        if status not in RESULT_STATUS_TO_SPEECH_ACT:
            raise BridgeError(f"unknown FISCALITH result status: {status!r}")
        speech_act = RESULT_STATUS_TO_SPEECH_ACT[status]

    message = {
        "speech_act": speech_act,
        "from_agent_entity_ref": from_agent_entity_ref,
        "to_agent_entity_ref": to_agent_entity_ref,
        "correlation_id": correlation_id,
        "mandate_ref": None,
        "delegation_chain": [],
        "capability_refs": [],
        "execution_envelope_ref": None,
        "requested_proof_classes": [],
        "fiscalith_payload": dict(fiscalith_result),
        "schema_ref": FISCALITH_SCHEMA_ID,
    }
    return validate_envelope(message)
