#!/usr/bin/env python3
"""Smoke tests for governed internal $XENTS settlement."""

from atralith.economic import compile_economic_mandate
from atralith.economic_runtime import execute_economic_action
from atralith.internal_xents import InternalXentsLedger, InternalXentsSettlementAdapter
from atralith.mandate import build_mandate


def main() -> None:
    parent = build_mandate(
        agent_id="agent:hermes.market",
        action_type="internal_purchase",
        enforcement="enforced",
        scope={
            "maximum_value": "50.00",
            "allowed_assets": ["$XENTS"],
            "allowed_destinations": ["acct:merchant-01"],
        },
        issued_by="principal:neuro",
    )

    economic = compile_economic_mandate(
        parent,
        purpose="Purchase an approved AGENTROPOLIS service with internal XENTS",
        amount="20.00",
        asset="$XENTS",
        settlement_mode="internal_xents",
        adapter="atralith.internal_xents",
        counterparty_scope={"allowed_addresses": ["acct:merchant-01"]},
        approval={
            "required": True,
            "method": "human_passkey",
            "approvers": ["principal:neuro"],
        },
    )

    ledger = InternalXentsLedger()
    ledger.set_balance("acct:user-01", "100.00")
    ledger.set_balance("acct:merchant-01", "0.00")
    adapter = InternalXentsSettlementAdapter(ledger)

    tx = {
        "amount": "20.00",
        "asset": "$XENTS",
        "source": "acct:user-01",
        "destination": "acct:merchant-01",
        "approval_receipt": "approval:test-only",
        "idempotency_key": "order-001",
        "memo": "GPU render credit",
    }

    result = execute_economic_action(economic, tx, adapter=adapter, allow_live=True)
    entry = result["settlement_result"]["entry"]
    assert result["settlement_result"]["status"] == "settled_internal"
    assert result["settlement_result"]["on_chain"] is False
    assert entry["asset"] == "$XENTS"
    assert ledger.get_balance("acct:user-01") == "80.0"
    assert ledger.get_balance("acct:merchant-01") == "20.0"

    # Same idempotency key + same transfer returns the same entry and does not debit twice.
    repeat = execute_economic_action(economic, tx, adapter=adapter, allow_live=True)
    assert repeat["settlement_result"]["entry"]["entry_id"] == entry["entry_id"]
    assert ledger.get_balance("acct:user-01") == "80.0"

    # Same idempotency key + changed parameters must fail.
    conflict = dict(tx)
    conflict["amount"] = "19.00"
    conflict_failed = False
    try:
        execute_economic_action(economic, conflict, adapter=adapter, allow_live=True)
    except ValueError:
        conflict_failed = True
    assert conflict_failed, "idempotency key reuse with changed parameters must fail"

    # Insufficient funds must fail without mutating balances.
    low_balance_tx = dict(tx)
    low_balance_tx["amount"] = "20.00"
    low_balance_tx["idempotency_key"] = "order-002"
    ledger.set_balance("acct:user-01", "5.00")
    insufficient = False
    try:
        execute_economic_action(economic, low_balance_tx, adapter=adapter, allow_live=True)
    except PermissionError:
        insufficient = True
    assert insufficient, "insufficient balance must fail closed"
    assert ledger.get_balance("acct:user-01") == "5.0"

    print("PASS: internal XENTS settlement is bounded, atomic, idempotent, and truth-labeled internal-only")


if __name__ == "__main__":
    main()
