"""Governed internal $XENTS settlement adapter for ATRALITH.

This module provides a reference in-memory ledger for AGENTROPOLIS internal
settlement. It is NOT an on-chain token implementation and does not claim custody
or blockchain finality. It is designed to exercise RFC-0003 authority controls,
idempotency, balance checks, and receipts before live rails are added.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(obj: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(obj).encode('utf-8')).hexdigest()}"


def _amount(value: Any) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("amount must be a valid decimal value") from exc
    if result <= 0:
        raise ValueError("amount must be greater than zero")
    return result


def _fmt(value: Decimal) -> str:
    normalized = value.normalize()
    rendered = format(normalized, "f")
    return rendered if "." in rendered else rendered + ".0"


@dataclass
class InternalXentsLedger:
    """Thread-safe reference ledger with atomic transfers and idempotency."""

    balances: dict[str, Decimal] = field(default_factory=dict)
    entries: list[dict[str, Any]] = field(default_factory=list)
    idempotency: dict[str, dict[str, Any]] = field(default_factory=dict)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def set_balance(self, account: str, amount: str) -> None:
        value = Decimal(amount)
        if value < 0:
            raise ValueError("balance cannot be negative")
        with self._lock:
            self.balances[account] = value

    def get_balance(self, account: str) -> str:
        with self._lock:
            return _fmt(self.balances.get(account, Decimal("0")))

    def transfer(
        self,
        *,
        source: str,
        destination: str,
        amount: str,
        capability_id: str,
        economic_mandate_hash: str,
        idempotency_key: str,
        memo: str | None = None,
    ) -> dict[str, Any]:
        value = _amount(amount)
        if source == destination:
            raise ValueError("source and destination must differ")
        if not idempotency_key:
            raise ValueError("idempotency_key is required")

        with self._lock:
            prior = self.idempotency.get(idempotency_key)
            if prior is not None:
                expected = {
                    "source": source,
                    "destination": destination,
                    "amount": _fmt(value),
                    "capability_id": capability_id,
                    "economic_mandate_hash": economic_mandate_hash,
                }
                for key, expected_value in expected.items():
                    if prior.get(key) != expected_value:
                        raise ValueError("idempotency key reused with different transfer parameters")
                return dict(prior)

            source_balance = self.balances.get(source, Decimal("0"))
            if source_balance < value:
                raise PermissionError("insufficient internal XENTS balance")

            destination_balance = self.balances.get(destination, Decimal("0"))
            new_source = source_balance - value
            new_destination = destination_balance + value

            entry = {
                "entry_id": f"xent_{uuid.uuid4().hex[:16]}",
                "asset": "$XENTS",
                "source": source,
                "destination": destination,
                "amount": _fmt(value),
                "capability_id": capability_id,
                "economic_mandate_hash": economic_mandate_hash,
                "idempotency_key": idempotency_key,
                "memo": memo,
                "source_balance_after": _fmt(new_source),
                "destination_balance_after": _fmt(new_destination),
                "settled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "finality": "internal_ledger",
                "on_chain": False,
            }
            entry["entry_hash"] = _sha256(entry)

            self.balances[source] = new_source
            self.balances[destination] = new_destination
            self.entries.append(entry)
            self.idempotency[idempotency_key] = entry
            return dict(entry)


class InternalXentsSettlementAdapter:
    """ATRALITH settlement adapter for the governed internal $XENTS ledger.

    This adapter mutates only the supplied internal ledger. It never signs or
    broadcasts blockchain transactions. `live=True` here means state-changing
    inside the local/internal ledger boundary, not on-chain financial finality.
    """

    name = "internal_xents"
    live = True

    def __init__(self, ledger: InternalXentsLedger):
        self.ledger = ledger

    def execute(self, capability: dict[str, Any], transaction: dict[str, Any]) -> dict[str, Any]:
        if transaction.get("asset") != "$XENTS":
            raise PermissionError("internal_xents adapter accepts only $XENTS")
        source = transaction.get("source")
        destination = transaction.get("destination")
        if not source or not destination:
            raise ValueError("source and destination are required")
        idempotency_key = transaction.get("idempotency_key")
        if not idempotency_key:
            raise ValueError("idempotency_key is required")

        entry = self.ledger.transfer(
            source=source,
            destination=destination,
            amount=transaction.get("amount"),
            capability_id=capability["capability_id"],
            economic_mandate_hash=capability["economic_mandate_hash"],
            idempotency_key=idempotency_key,
            memo=transaction.get("memo"),
        )
        return {
            "status": "settled_internal",
            "adapter": self.name,
            "live": self.live,
            "on_chain": False,
            "entry": entry,
        }
