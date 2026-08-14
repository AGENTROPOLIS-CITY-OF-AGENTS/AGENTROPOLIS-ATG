#!/usr/bin/env python3
"""Smoke tests for the governed EVM native-value adapter."""

from atralith.economic import compile_economic_mandate
from atralith.economic_runtime import execute_economic_action
from atralith.evm_native import EVMNativeTransferAdapter, EVMState
from atralith.mandate import build_mandate

SOURCE = "0x1111111111111111111111111111111111111111"
DEST = "0x2222222222222222222222222222222222222222"


class MockStateReader:
    def read_state(self, account, chain_id):
        assert account == SOURCE
        return EVMState(
            chain_id=chain_id,
            nonce=7,
            base_fee_per_gas=10_000_000_000,
            latest_block_number=100,
            finalized_block_number=95,
        )


class MockSigner:
    def sign_transaction(self, *, prepared_transaction, capability):
        from atralith.evm_native import _sha256

        return {
            "prepared_transaction_hash": _sha256(prepared_transaction),
            "raw_transaction": "0xdeadbeef",
            "transaction_hash": "0xabc123",
        }


class MockSubmitter:
    def __init__(self, receipt=None, finalized=120):
        self.receipt = receipt
        self.finalized = finalized

    def submit_raw_transaction(self, raw_transaction):
        assert raw_transaction == "0xdeadbeef"
        return {"transaction_hash": "0xabc123"}

    def get_transaction_receipt(self, transaction_hash):
        assert transaction_hash == "0xabc123"
        return self.receipt

    def get_finalized_block_number(self, chain_id):
        return self.finalized


def economic_mandate():
    parent = build_mandate(
        agent_id="agent:hermes.payments",
        action_type="native_transfer",
        enforcement="enforced",
        scope={
            "maximum_value": "1.0",
            "allowed_assets": ["ETH"],
            "allowed_chains": ["eip155:8453"],
            "allowed_destinations": [DEST],
        },
        issued_by="principal:neuro",
    )
    return compile_economic_mandate(
        parent,
        purpose="Pay one approved EVM-native invoice",
        amount="0.01",
        asset="ETH",
        settlement_mode="evm",
        network="eip155:8453",
        counterparty_scope={"allowed_addresses": [DEST]},
        approval={"required": True, "method": "human_passkey", "approvers": ["principal:neuro"]},
    )


def transaction():
    return {
        "amount": "0.01",
        "asset": "ETH",
        "settlement_mode": "evm",
        "destination": DEST,
        "approval_receipt": "approval:test-only",
        "amount_wei": "10000000000000000",
        "gas_limit": 21000,
        "max_fee_per_gas_wei": "20000000000",
        "max_priority_fee_per_gas_wei": "1000000000",
        "data": "0x",
        "evm_policy": {
            "chain_id": 8453,
            "source": SOURCE,
            "destination": DEST,
            "max_value_wei": "10000000000000000",
            "max_fee_per_gas_wei": "25000000000",
            "max_priority_fee_per_gas_wei": "2000000000",
            "max_total_fee_wei": "525000000000000"
        },
    }


def main():
    economic = economic_mandate()
    tx = transaction()

    adapter = EVMNativeTransferAdapter(
        state_reader=MockStateReader(),
        signer=MockSigner(),
        submitter=MockSubmitter(receipt={"status": "0x1", "blockNumber": "0x64"}, finalized=120),
    )

    blocked = False
    try:
        execute_economic_action(economic, tx, adapter=adapter)
    except PermissionError:
        blocked = True
    assert blocked, "live EVM adapter must require allow_live=True"

    result = execute_economic_action(economic, tx, adapter=adapter, allow_live=True)
    assert result["settlement_result"]["status"] == "settled"

    pending = execute_economic_action(
        economic,
        tx,
        adapter=EVMNativeTransferAdapter(
            state_reader=MockStateReader(),
            signer=MockSigner(),
            submitter=MockSubmitter(receipt={"status": "0x1", "blockNumber": "0x64"}, finalized=90),
        ),
        allow_live=True,
    )
    assert pending["settlement_result"]["status"] == "included_pending_finality"

    denied = False
    try:
        bad = dict(tx, amount_wei="10000000000000001")
        execute_economic_action(economic, bad, adapter=adapter, allow_live=True)
    except PermissionError:
        denied = True
    assert denied, "over-budget native value must fail closed"

    denied = False
    try:
        bad = dict(tx, destination="0x3333333333333333333333333333333333333333")
        execute_economic_action(economic, bad, adapter=adapter, allow_live=True)
    except PermissionError:
        denied = True
    assert denied, "destination substitution must fail closed"

    denied = False
    try:
        bad = dict(tx, data="0x1234")
        execute_economic_action(economic, bad, adapter=adapter, allow_live=True)
    except PermissionError:
        denied = True
    assert denied, "calldata must be denied in Phase 1"

    failed = execute_economic_action(
        economic,
        tx,
        adapter=EVMNativeTransferAdapter(
            state_reader=MockStateReader(),
            signer=MockSigner(),
            submitter=MockSubmitter(receipt={"status": "0x0", "blockNumber": "0x64"}, finalized=120),
        ),
        allow_live=True,
    )
    assert failed["settlement_result"]["status"] == "payment_failed"

    print("PASS: EVM native adapter is value-bounded, fee-bounded, calldata-free, and finality-aware")


if __name__ == "__main__":
    main()
