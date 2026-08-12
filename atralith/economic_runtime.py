"""Fail-closed economic execution runtime for ATG RFC-0003.

This module intentionally supports simulation only. Live custody and settlement
must be implemented by external adapters that satisfy the same interface and are
separately approved by 54-T.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from atralith.economic import verify_economic_mandate_hash


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(obj: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(obj).encode('utf-8')).hexdigest()}"


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    decision_id: str
    reason: str
    decision_hash: str


class PolicyDecisionPoint(Protocol):
    def evaluate(self, economic_mandate: dict[str, Any], transaction: dict[str, Any]) -> PolicyDecision: ...


class SettlementAdapter(Protocol):
    name: str
    live: bool

    def execute(self, capability: dict[str, Any], transaction: dict[str, Any]) -> dict[str, Any]: ...


class FailClosed54TPolicy:
    """Deterministic reference PDP.

    It approves only structurally bounded, hash-consistent economic mandates and
    transactions that stay within amount/asset/counterparty scope. It does not
    replace the production 54-T engine.
    """

    def evaluate(self, economic_mandate: dict[str, Any], transaction: dict[str, Any]) -> PolicyDecision:
        reasons: list[str] = []

        if not verify_economic_mandate_hash(economic_mandate):
            reasons.append("economic mandate hash invalid")
        if economic_mandate.get("enforcement") != "enforced":
            reasons.append("economic mandate is not enforced")

        limit = economic_mandate.get("value_limit", {})
        if transaction.get("asset") != limit.get("asset"):
            reasons.append("transaction asset outside mandate")

        try:
            tx_amount = float(transaction.get("amount"))
            max_amount = float(limit.get("amount"))
            if tx_amount < 0 or tx_amount > max_amount:
                reasons.append("transaction amount outside mandate")
        except (TypeError, ValueError):
            reasons.append("transaction amount invalid")

        scope = economic_mandate.get("counterparty_scope", {})
        merchant = transaction.get("merchant")
        address = transaction.get("destination")
        domain = transaction.get("domain")
        allowed_merchants = scope.get("allowed_merchants") or []
        allowed_addresses = scope.get("allowed_addresses") or []
        allowed_domains = scope.get("allowed_domains") or []
        if allowed_merchants and merchant not in allowed_merchants:
            reasons.append("merchant outside mandate")
        if allowed_addresses and address not in allowed_addresses:
            reasons.append("destination outside mandate")
        if allowed_domains and domain not in allowed_domains:
            reasons.append("domain outside mandate")

        approval = economic_mandate.get("approval", {})
        if approval.get("required") and not transaction.get("approval_receipt"):
            reasons.append("required approval receipt missing")

        allowed = not reasons
        body = {
            "allowed": allowed,
            "mandate": economic_mandate.get("economic_mandate_hash"),
            "transaction_hash": _sha256(transaction),
            "reason": "allowed" if allowed else "; ".join(reasons),
        }
        decision_hash = _sha256(body)
        return PolicyDecision(
            allowed=allowed,
            decision_id=f"pdp_{uuid.uuid4().hex[:12]}",
            reason=body["reason"],
            decision_hash=decision_hash,
        )


class SimulationSettlementAdapter:
    """Non-custodial adapter that never sends money or touches credentials."""

    name = "simulation"
    live = False

    def execute(self, capability: dict[str, Any], transaction: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "simulated",
            "adapter": self.name,
            "live": self.live,
            "capability_id": capability["capability_id"],
            "transaction_hash": _sha256(transaction),
            "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


def issue_capability_handle(economic_mandate: dict[str, Any], decision: PolicyDecision) -> dict[str, Any]:
    """Issue an opaque, bounded capability description after a positive PDP decision."""
    if not decision.allowed:
        raise PermissionError(f"54-T denied economic action: {decision.reason}")
    return {
        "capability_id": f"cap_{uuid.uuid4().hex[:16]}",
        "economic_mandate_hash": economic_mandate["economic_mandate_hash"],
        "policy_decision_hash": decision.decision_hash,
        "credential_class": economic_mandate["settlement"].get("credential_class", "none"),
        "max_uses": economic_mandate["constraints"]["max_uses"],
        "delegation_allowed": economic_mandate["constraints"]["delegation_allowed"],
        "expires_at": economic_mandate["constraints"].get("valid_until"),
    }


def execute_economic_action(
    economic_mandate: dict[str, Any],
    transaction: dict[str, Any],
    *,
    policy: PolicyDecisionPoint | None = None,
    adapter: SettlementAdapter | None = None,
    allow_live: bool = False,
) -> dict[str, Any]:
    """Evaluate, capability-bind, and execute a bounded economic action.

    Default behavior is safe simulation. Live adapters are rejected unless the
    caller explicitly opts in and the adapter independently exists.
    """
    policy = policy or FailClosed54TPolicy()
    adapter = adapter or SimulationSettlementAdapter()
    decision = policy.evaluate(economic_mandate, transaction)
    if not decision.allowed:
        raise PermissionError(f"54-T denied economic action: {decision.reason}")
    if adapter.live and not allow_live:
        raise PermissionError("live settlement adapter blocked: allow_live is false")

    capability = issue_capability_handle(economic_mandate, decision)
    result = adapter.execute(capability, transaction)
    return {
        "economic_mandate_hash": economic_mandate["economic_mandate_hash"],
        "policy_decision": {
            "decision_id": decision.decision_id,
            "allowed": decision.allowed,
            "reason": decision.reason,
            "decision_hash": decision.decision_hash,
        },
        "capability": capability,
        "settlement_result": result,
        "verification_state": "simulated" if not adapter.live else "pending_verification",
    }
