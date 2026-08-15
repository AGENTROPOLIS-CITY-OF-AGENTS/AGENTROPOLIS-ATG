#!/usr/bin/env python3
"""Smoke tests for governed native SOL settlement."""

from __future__ import annotations

from atralith.economic import compile_economic_mandate
from atralith.economic_runtime import execute_economic_action
from atralith.mandate import build_mandate
from atralith.solana_native import SolanaBlockhashState, SolanaNativeTransferAdapter

SRC = "11111111111111111111111111111111"
DST = "SysvarRent111111111111111111111111111111111"


class StateReader:
    def __init__(self, recipient_kind="system_wallet", current_height=100, last_valid=150, fee=5000):
        self.recipient_kind = recipient_kind
        self.current_height = current_height
        self.last_valid = last_valid
        self.fee = fee

    def get_latest_blockhash(self, network):
        return SolanaBlockhashState(network, "11111111111111111111111111111111", self.last_valid, self.current_height)

    def classify_recipient(self, network, pubkey):
        return self.recipient_kind

    def estimate_fee_lamports(self, network, prepared_message):
        return self.fee

    def get_block_height(self, network):
        return self.current_height


class Signer:
    def sign_transaction(self, *, prepared_message, capability):
        import hashlib, json
        canonical = json.dumps(prepared_message, sort_keys=True, separators=(",", ":"), allow_nan=False)
        h = f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"
        return {"prepared_message_hash": h, "signed_transaction_base64": "dGVzdA==", "signature": "sig-test"}


class Submitter:
    def __init__(self, status="finalized", err=None):
        self.status = status
        self.err = err

    def submit_transaction(self, signed_transaction_base64):
        return {"signature": "sig-test"}

    def get_signature_status(self, signature):
        if self.status is None:
            return None
        return {"confirmationStatus": self.status, "slot": 12345, "err": self.err}


def economic():
    parent = build_mandate(
        agent_id="agent:hermes.payments",
        action_type="transfer_value",
        enforcement="enforced",
        scope={"maximum_value": "1.00", "allowed_assets": ["SOL"], "allowed_chains": ["solana:mainnet-beta"]},
        issued_by="principal:neuro",
    )
    return compile_economic_mandate(
        parent,
        purpose="Bounded SOL transfer",
        amount="0.001",
        asset="SOL",
        settlement_mode="solana",
        network="solana:mainnet-beta",
        counterparty_scope={"allowed_accounts": [DST]},
        approval={"required": True, "method": "human_passkey", "approvers": ["principal:neuro"]},
    )


def tx():
    return {
        "amount": "0.001",
        "asset": "SOL",
        "settlement_mode": "solana",
        "destination": DST,
        "approval_receipt": "approval:test-only",
        "amount_lamports": "1000000",
        "solana_policy": {
            "network": "mainnet-beta",
            "source": SRC,
            "destination": DST,
            "max_amount_lamports": "1000000",
            "max_fee_lamports": "10000",
            "max_validity_window_blocks": 200,
            "allowed_recipient_kinds": ["system_wallet"],
        },
    }


def main():
    adapter = SolanaNativeTransferAdapter(state_reader=StateReader(), signer=Signer(), submitter=Submitter())

    denied = False
    try:
        execute_economic_action(economic(), tx(), adapter=adapter)
    except PermissionError:
        denied = True
    assert denied, "live Solana adapter must require allow_live=True"

    result = execute_economic_action(economic(), tx(), adapter=adapter, allow_live=True)
    assert result["settlement_result"]["status"] == "settled"

    over = tx(); over["amount_lamports"] = "1000001"
    denied = False
    try:
        execute_economic_action(economic(), over, adapter=adapter, allow_live=True)
    except PermissionError:
        denied = True
    assert denied, "over-budget lamports must fail closed"

    bad_recipient = SolanaNativeTransferAdapter(state_reader=StateReader(recipient_kind="program_account"), signer=Signer(), submitter=Submitter())
    denied = False
    try:
        execute_economic_action(economic(), tx(), adapter=bad_recipient, allow_live=True)
    except PermissionError:
        denied = True
    assert denied, "unapproved recipient account kind must fail closed"

    expired = SolanaNativeTransferAdapter(state_reader=StateReader(current_height=200, last_valid=200), signer=Signer(), submitter=Submitter())
    denied = False
    try:
        execute_economic_action(economic(), tx(), adapter=expired, allow_live=True)
    except PermissionError:
        denied = True
    assert denied, "expired blockhash must fail closed"

    pending = SolanaNativeTransferAdapter(state_reader=StateReader(), signer=Signer(), submitter=Submitter(status="confirmed"))
    result = execute_economic_action(economic(), tx(), adapter=pending, allow_live=True)
    assert result["settlement_result"]["status"] == "confirmed_pending_finality"

    failed = SolanaNativeTransferAdapter(state_reader=StateReader(), signer=Signer(), submitter=Submitter(status="finalized", err={"InstructionError": [0, "Custom"]}))
    result = execute_economic_action(economic(), tx(), adapter=failed, allow_live=True)
    assert result["settlement_result"]["status"] == "payment_failed"

    print("PASS: Solana native adapter is recipient-classified, budgeted, expiry-bound, and finality-aware")


if __name__ == "__main__":
    main()
