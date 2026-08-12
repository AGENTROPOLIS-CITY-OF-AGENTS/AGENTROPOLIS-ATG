"""Economic mandate compiler for ATG RFC-0003.

The compiler derives a bounded economic authority object from an existing ATG
mandate. It never creates generalized wallet/card/treasury authority and never
handles raw credentials.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import FormatChecker, validators

CONTRACTS = Path(__file__).resolve().parent.parent / "contracts" / "core"
MANDATE_SCHEMA_PATH = CONTRACTS / "mandate.schema.json"
ECONOMIC_SCHEMA_PATH = CONTRACTS / "economic-mandate.schema.json"


def _load(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(obj: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(obj).encode('utf-8')).hexdigest()}"


def _validate(schema: dict[str, Any], instance: Any, label: str) -> None:
    checker = FormatChecker()
    validator_cls = validators.validator_for(schema)
    validator = validator_cls(schema, format_checker=checker)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        rendered = []
        for error in errors:
            path = " -> ".join(str(part) for part in error.path) or "<root>"
            rendered.append(f"{label}: {error.message} (path: {path})")
        raise ValueError("\n".join(rendered))


def _decimal(value: str, label: str) -> Decimal:
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"{label} must be a decimal string") from exc
    if amount < 0:
        raise ValueError(f"{label} must be non-negative")
    return amount


def _assert_inherited_scope(mandate: dict[str, Any], economic: dict[str, Any]) -> None:
    """Prevent RFC-0003 authority from exceeding the parent ATG mandate."""
    scope = mandate.get("scope", {})
    value_limit = economic["value_limit"]
    settlement = economic["settlement"]
    counterparties = economic.get("counterparty_scope", {})

    maximum = scope.get("maximum_value")
    if maximum is not None:
        if _decimal(value_limit["amount"], "value_limit.amount") > _decimal(maximum, "scope.maximum_value"):
            raise ValueError("economic value limit exceeds parent mandate maximum_value")

    allowed_assets = scope.get("allowed_assets") or []
    if allowed_assets and value_limit["asset"] not in allowed_assets:
        raise ValueError("economic asset is outside parent mandate allowed_assets")

    allowed_chains = scope.get("allowed_chains") or []
    network = settlement.get("network")
    if allowed_chains and network and network not in allowed_chains:
        raise ValueError("economic settlement network is outside parent mandate allowed_chains")

    allowed_destinations = set(scope.get("allowed_destinations") or [])
    requested_destinations = set(counterparties.get("allowed_addresses") or [])
    if allowed_destinations and not requested_destinations.issubset(allowed_destinations):
        raise ValueError("economic counterparty address is outside parent mandate allowed_destinations")


def compile_economic_mandate(
    mandate: dict[str, Any],
    *,
    purpose: str,
    amount: str,
    asset: str,
    settlement_mode: str,
    network: str | None = None,
    adapter: str | None = None,
    credential_class: str = "capability_handle",
    counterparty_scope: dict[str, Any] | None = None,
    constraints: dict[str, Any] | None = None,
    approval: dict[str, Any] | None = None,
    risk: dict[str, Any] | None = None,
    enforcement: str | None = None,
    issued_by: str = "54-T:policy-decision-point",
    economic_mandate_id: str | None = None,
) -> dict[str, Any]:
    """Compile a bounded economic mandate from a validated parent ATG mandate.

    The parent mandate is authoritative. This function may narrow that authority,
    but it refuses to widen amount, asset, chain, destination, or enforcement.
    """
    _validate(_load(MANDATE_SCHEMA_PATH), mandate, "Parent mandate")

    effective_enforcement = enforcement or mandate["enforcement"]
    if mandate["enforcement"] != "enforced" and effective_enforcement == "enforced":
        raise ValueError("an advisory parent mandate cannot produce enforced economic authority")

    settlement: dict[str, Any] = {
        "mode": settlement_mode,
        "asset": asset,
        "credential_class": credential_class,
    }
    if network:
        settlement["network"] = network
    if adapter:
        settlement["adapter"] = adapter

    compiled: dict[str, Any] = {
        "economic_mandate_id": economic_mandate_id or f"econ_{uuid.uuid4().hex[:16]}",
        "mandate_id": mandate["mandate_id"],
        "agent_id": mandate["agent_id"],
        "purpose": purpose,
        "value_limit": {"amount": amount, "asset": asset},
        "settlement": settlement,
        "constraints": constraints or {"max_uses": 1, "delegation_allowed": False, "recurring": False, "retry_limit": 0},
        "approval": approval or {"required": True, "method": "human_passkey", "approvers": []},
        "risk": risk or {"authorization_class": "A2_BOUNDED", "contra_required": False, "third_party_impact_check": True},
        "enforcement": effective_enforcement,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "issued_by": issued_by,
    }
    if counterparty_scope:
        compiled["counterparty_scope"] = counterparty_scope

    _assert_inherited_scope(mandate, compiled)

    risk_class = compiled.get("risk", {}).get("authorization_class")
    if risk_class in {"A3_IRREVERSIBLE", "A4_ROOT"} and not compiled["approval"].get("required"):
        raise ValueError(f"{risk_class} economic authority requires explicit approval")

    compiled["economic_mandate_hash"] = _sha256(compiled)
    _validate(_load(ECONOMIC_SCHEMA_PATH), compiled, "Economic mandate")
    return compiled


def verify_economic_mandate_hash(economic_mandate: dict[str, Any]) -> bool:
    claimed = economic_mandate.get("economic_mandate_hash")
    if not isinstance(claimed, str):
        return False
    content = {key: value for key, value in economic_mandate.items() if key != "economic_mandate_hash"}
    return claimed == _sha256(content)
