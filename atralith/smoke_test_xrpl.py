#!/usr/bin/env python3
"""Smoke tests for the governed direct-XRP settlement adapter."""

from __future__ import annotations

from atralith.economic import compile_economic_mandate
from atralith.economic_runtime import execute_economic_action
from atralith.mandate import build_mandate
from atralith.xrpl_payment import XRPLAccountState, XRPLXRPSettlementAdapter, _sha256


SOURCE = "rEXAMPLEsourceAccount11111111111111"
DEST = "rEXAMPLEdestination22222222222222"


class MockStateReader:
    def get_account_state(self, account):
        assert account == SOURCE
        return XRPLAccountState(
            account=SOURCE,
            sequence=7,
            validated_ledger_index=1000,
            recommended_fee_drops="12",
        )


class MockSigner:
    def sign(self, transaction, capability):
        return {
            "tx_blob": "DEADBEEF",
            "hash": "ABC123",
            "prepared_hash": _sha256(transaction),
        }


class MockSubmitter:
    def __init__(self, *, validated=True, result="tesSUCCESS", tx_hash="ABC123"):
        self.validated = validated
        self.result = result
        self.tx_hash = tx_hash

    def submit_and_wait(self, tx_blob, *, last_ledger_sequence):
        assert tx_blob == "DEADBEEF"
        assert last_ledger_sequence == 1020
        return {
            "validated": self.validated,
            "hash": self.tx_hash,
            "meta": {"TransactionResult": self.result},
        }


def build_economic():
    parent = build_mandate(
        agent_id="agent:hermes.xrpl",
        action_type="payment",
        enforcement="enforced",
        scope={
            "maximum_value": "5.00",
            "allowed_assets": ["XRP"],
            "allowed_chains": ["xrpl:mainnet"],
            "allowed_destinations": [DEST],
        },
        issued_by="principal:neuro",
    )
    return compile_economic_mandate(
        parent,
        purpose="Bounded XRPL payment",
        amount="5.00",
        asset="XRP",
        settlement_mode="xrpl",
        network="xrpl:mainnet",
        counterparty_scope={"allowed_addresses": [DEST]},
        approval={"required": True, "method": "human_passkey", "approvers": ["principal:neuro"]},
    )


def tx(amount_drops="1000000", destination=DEST):
    return {
        "amount": "1.00",
        "asset": "XRP",
        "settlement_mode": "xrpl",
        "destination": destination,
        "amount_drops": amount_drops,
        "approval_receipt": "approval:test-only",
        "source_tag": 589,
        "xrpl_policy": {
            "network": "xrpl:mainnet",
            "account": SOURCE,
            "allowed_destinations": [DEST],
            "max_amount_drops": "5000000",
            "max_fee_drops": "20",
            "last_ledger_offset": 20,
            "required_source_tag": 589,
        },
    }


def main():
    economic = build_economic()
    adapter = XRPLXRPSettlementAdapter(MockStateReader(), MockSigner(), MockSubmitter())

    # Live rail must require explicit opt-in at the generic economic runtime layer.
    blocked = False
    try:
        execute_economic_action(economic, tx(), adapter=adapter)
    except PermissionError:
        blocked = True
    assert blocked, "live XRPL adapter must require allow_live=True"

    result = execute_economic_action(economic, tx(), adapter=adapter, allow_live=True)
    settled = result["settlement_result"]
    assert settled["status"] == "settled"
    assert settled["validated"] is True
    assert settled["transaction_result"] == "tesSUCCESS"
    assert settled["last_ledger_sequence"] == 1020

    # Over-budget amount must fail before signing/submission.
    denied = False
    try:
        execute_economic_action(economic, tx("6000000"), adapter=adapter, allow_live=True)
    except PermissionError:
        denied = True
    assert denied, "over-budget XRP amount must fail closed"

    # Destination substitution must fail closed.
    denied = False
    try:
        execute_economic_action(
            economic,
            tx(destination="rEVILdestination333333333333333"),
            adapter=adapter,
            allow_live=True,
        )
    except PermissionError:
        denied = True
    assert denied, "destination substitution must fail closed"

    # Non-validated success is not final.
    pending_adapter = XRPLXRPSettlementAdapter(
        MockStateReader(), MockSigner(), MockSubmitter(validated=False, result="tesSUCCESS")
    )
    result = execute_economic_action(economic, tx(), adapter=pending_adapter, allow_live=True)
    assert result["settlement_result"]["status"] == "pending_verification"

    # Validated non-success is a failed payment, not pending.
    failed_adapter = XRPLXRPSettlementAdapter(
        MockStateReader(), MockSigner(), MockSubmitter(validated=True, result="tecUNFUNDED_PAYMENT")
    )
    result = execute_economic_action(economic, tx(), adapter=failed_adapter, allow_live=True)
    assert result["settlement_result"]["status"] == "payment_failed"

    print("PASS: XRPL direct-XRP adapter is bounded, sealed-signer only, and finality-aware")


if __name__ == "__main__":
    main()
