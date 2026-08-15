#!/usr/bin/env python3
"""Smoke tests for the governed ERC-20 transfer-only adapter."""

from __future__ import annotations

import hashlib
import json

from atralith.evm_erc20 import ERC20State, ERC20TokenInfo, EVMERC20TransferAdapter

SRC = "0x1111111111111111111111111111111111111111"
DST = "0x2222222222222222222222222222222222222222"
TOKEN = "0x3333333333333333333333333333333333333333"
CODE_HASH = "0xcodehash"


class StateReader:
    def read_state(self, account, chain_id):
        return ERC20State(chain_id=chain_id, nonce=7, base_fee_per_gas=10, latest_block_number=100, finalized_block_number=98)

    def inspect_token(self, contract, chain_id):
        return ERC20TokenInfo(contract=contract, code_hash=CODE_HASH, decimals=6, symbol="USDC")

    def estimate_gas(self, transaction):
        return 65000


class Signer:
    def sign_transaction(self, *, prepared_transaction, capability):
        canonical = json.dumps(prepared_transaction, sort_keys=True, separators=(",", ":"), allow_nan=False)
        h = f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"
        return {"prepared_transaction_hash": h, "raw_transaction": "0xdeadbeef", "transaction_hash": "0xabc"}


class Submitter:
    def __init__(self, receipt_status="0x1", block_number="0x60", finalized=100):
        self.receipt_status = receipt_status
        self.block_number = block_number
        self.finalized = finalized

    def submit_raw_transaction(self, raw_transaction):
        return {"transaction_hash": "0xabc"}

    def get_transaction_receipt(self, transaction_hash):
        return {"status": self.receipt_status, "blockNumber": self.block_number}

    def get_finalized_block_number(self, chain_id):
        return self.finalized


def capability():
    return {
        "capability_id": "cap:test",
        "economic_mandate_hash": "sha256:mandate",
        "policy_decision_hash": "sha256:policy",
    }


def tx():
    return {
        "settlement_mode": "evm_erc20",
        "token_contract": TOKEN,
        "destination": DST,
        "amount_units": "1500000",
        "max_fee_per_gas_wei": "100",
        "max_priority_fee_per_gas_wei": "2",
        "erc20_policy": {
            "chain_id": 8453,
            "source": SRC,
            "destination": DST,
            "token_contract": TOKEN,
            "token_code_hash": CODE_HASH,
            "token_decimals": 6,
            "max_amount_units": "2000000",
            "max_fee_per_gas_wei": "120",
            "max_priority_fee_per_gas_wei": "3",
            "max_gas_limit": 80000,
            "max_total_fee_wei": "9600000",
        },
    }


def main():
    adapter = EVMERC20TransferAdapter(state_reader=StateReader(), signer=Signer(), submitter=Submitter())
    result = adapter.execute(capability(), tx())
    assert result["status"] == "settled"
    assert result["token_contract"] == TOKEN
    assert result["destination"] == DST
    assert result["amount_units"] == "1500000"

    over = tx(); over["amount_units"] = "2000001"
    denied = False
    try:
        adapter.execute(capability(), over)
    except PermissionError:
        denied = True
    assert denied, "over-budget token amount must fail closed"

    wrong_token = tx(); wrong_token["token_contract"] = "0x4444444444444444444444444444444444444444"
    denied = False
    try:
        adapter.execute(capability(), wrong_token)
    except PermissionError:
        denied = True
    assert denied, "token substitution must fail closed"

    wrong_dst = tx(); wrong_dst["destination"] = "0x5555555555555555555555555555555555555555"
    denied = False
    try:
        adapter.execute(capability(), wrong_dst)
    except PermissionError:
        denied = True
    assert denied, "recipient substitution must fail closed"

    failed = EVMERC20TransferAdapter(state_reader=StateReader(), signer=Signer(), submitter=Submitter(receipt_status="0x0"))
    result = failed.execute(capability(), tx())
    assert result["status"] == "payment_failed"

    pending = EVMERC20TransferAdapter(state_reader=StateReader(), signer=Signer(), submitter=Submitter(block_number="0x70", finalized=100))
    result = pending.execute(capability(), tx())
    assert result["status"] == "included_pending_finality"

    print("PASS: ERC-20 transfer adapter is token-pinned, recipient-pinned, unit-bounded, fee-bounded, and finality-aware")


if __name__ == "__main__":
    main()
