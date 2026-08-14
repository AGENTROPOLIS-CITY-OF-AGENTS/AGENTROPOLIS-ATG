"""Governed EVM native-value transfer adapter for ATG RFC-0003.

Phase 1 deliberately supports only EIP-1559 native transfers with empty calldata.
No ERC-20 approvals, no arbitrary contract calls, no delegatecall surfaces, and no
private key material enter the adapter.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(obj: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(obj).encode('utf-8')).hexdigest()}"


def _int_string(value: Any, label: str) -> int:
    if not isinstance(value, str) or not value.isdigit():
        raise ValueError(f"{label} must be a non-negative integer string")
    return int(value)


def _address(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        raise ValueError(f"{label} must be a 20-byte hex address")
    try:
        int(value[2:], 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be a 20-byte hex address") from exc
    return value.lower()


@dataclass(frozen=True)
class EVMState:
    chain_id: int
    nonce: int
    base_fee_per_gas: int
    latest_block_number: int
    finalized_block_number: int | None = None


class EVMStateReader(Protocol):
    def read_state(self, account: str, chain_id: int) -> EVMState: ...


class EVMSigner(Protocol):
    def sign_transaction(
        self,
        *,
        prepared_transaction: dict[str, Any],
        capability: dict[str, Any],
    ) -> dict[str, Any]: ...


class EVMSubmitter(Protocol):
    def submit_raw_transaction(self, raw_transaction: str) -> dict[str, Any]: ...

    def get_transaction_receipt(self, transaction_hash: str) -> dict[str, Any] | None: ...

    def get_finalized_block_number(self, chain_id: int) -> int | None: ...


def prepare_native_transfer(
    *,
    transaction: dict[str, Any],
    state_reader: EVMStateReader,
) -> dict[str, Any]:
    policy = transaction.get("evm_policy")
    if not isinstance(policy, dict):
        raise PermissionError("evm_policy is required")

    chain_id = policy.get("chain_id")
    if not isinstance(chain_id, int) or chain_id <= 0:
        raise ValueError("evm_policy.chain_id must be a positive integer")

    source = _address(policy.get("source"), "evm_policy.source")
    destination = _address(transaction.get("destination"), "transaction.destination")
    pinned_destination = policy.get("destination")
    if pinned_destination is not None and destination != _address(pinned_destination, "evm_policy.destination"):
        raise PermissionError("destination is outside the governed EVM policy")

    value_wei = _int_string(transaction.get("amount_wei"), "transaction.amount_wei")
    max_value_wei = _int_string(policy.get("max_value_wei"), "evm_policy.max_value_wei")
    if value_wei > max_value_wei:
        raise PermissionError("native transfer value exceeds governed ceiling")

    calldata = transaction.get("data", "0x")
    if calldata not in {"0x", ""}:
        raise PermissionError("Phase 1 EVM native transfer forbids calldata and contract execution")

    gas_limit = transaction.get("gas_limit", 21000)
    if gas_limit != 21000:
        raise PermissionError("Phase 1 EVM native transfer requires gas_limit 21000")

    max_fee_per_gas = _int_string(transaction.get("max_fee_per_gas_wei"), "transaction.max_fee_per_gas_wei")
    max_priority_fee_per_gas = _int_string(
        transaction.get("max_priority_fee_per_gas_wei"),
        "transaction.max_priority_fee_per_gas_wei",
    )
    fee_ceiling = _int_string(policy.get("max_fee_per_gas_wei"), "evm_policy.max_fee_per_gas_wei")
    priority_ceiling = _int_string(
        policy.get("max_priority_fee_per_gas_wei"),
        "evm_policy.max_priority_fee_per_gas_wei",
    )
    if max_fee_per_gas > fee_ceiling:
        raise PermissionError("maxFeePerGas exceeds governed ceiling")
    if max_priority_fee_per_gas > priority_ceiling:
        raise PermissionError("maxPriorityFeePerGas exceeds governed ceiling")
    if max_priority_fee_per_gas > max_fee_per_gas:
        raise ValueError("maxPriorityFeePerGas cannot exceed maxFeePerGas")

    state = state_reader.read_state(source, chain_id)
    if state.chain_id != chain_id:
        raise ValueError("trusted EVM state reader returned the wrong chain_id")
    if max_fee_per_gas < state.base_fee_per_gas:
        raise PermissionError("maxFeePerGas is below the current trusted base fee")

    max_total_fee = gas_limit * max_fee_per_gas
    max_total_fee_ceiling = _int_string(
        policy.get("max_total_fee_wei"),
        "evm_policy.max_total_fee_wei",
    )
    if max_total_fee > max_total_fee_ceiling:
        raise PermissionError("worst-case transaction fee exceeds governed total fee ceiling")

    prepared = {
        "type": 2,
        "chainId": chain_id,
        "from": source,
        "to": destination,
        "value": str(value_wei),
        "nonce": state.nonce,
        "gas": gas_limit,
        "maxFeePerGas": str(max_fee_per_gas),
        "maxPriorityFeePerGas": str(max_priority_fee_per_gas),
        "data": "0x",
    }
    return {
        "prepared_transaction": prepared,
        "prepared_transaction_hash": _sha256(prepared),
        "trusted_state": {
            "latest_block_number": state.latest_block_number,
            "finalized_block_number": state.finalized_block_number,
            "base_fee_per_gas": str(state.base_fee_per_gas),
        },
        "max_total_fee_wei": str(max_total_fee),
    }


class EVMNativeTransferAdapter:
    """Live EVM native-value settlement adapter with sealed signing."""

    name = "evm-native-v1"
    live = True

    def __init__(
        self,
        *,
        state_reader: EVMStateReader,
        signer: EVMSigner,
        submitter: EVMSubmitter,
    ) -> None:
        self.state_reader = state_reader
        self.signer = signer
        self.submitter = submitter

    def execute(self, capability: dict[str, Any], transaction: dict[str, Any]) -> dict[str, Any]:
        if transaction.get("settlement_mode") != "evm":
            raise ValueError("transaction settlement_mode must be evm")

        prepared_bundle = prepare_native_transfer(transaction=transaction, state_reader=self.state_reader)
        prepared = prepared_bundle["prepared_transaction"]
        prepared_hash = prepared_bundle["prepared_transaction_hash"]

        signed = self.signer.sign_transaction(
            prepared_transaction=prepared,
            capability=capability,
        )
        if not isinstance(signed, dict):
            raise ValueError("sealed signer must return an object")
        if signed.get("prepared_transaction_hash") != prepared_hash:
            raise ValueError("sealed signer attestation does not match prepared transaction")
        raw_transaction = signed.get("raw_transaction")
        transaction_hash = signed.get("transaction_hash")
        if not isinstance(raw_transaction, str) or not raw_transaction.startswith("0x"):
            raise ValueError("sealed signer must return raw_transaction hex")
        if not isinstance(transaction_hash, str) or not transaction_hash.startswith("0x"):
            raise ValueError("sealed signer must return transaction_hash")

        submit = self.submitter.submit_raw_transaction(raw_transaction)
        submitted_hash = submit.get("transaction_hash") if isinstance(submit, dict) else None
        if submitted_hash and submitted_hash.lower() != transaction_hash.lower():
            raise ValueError("submitter transaction hash differs from sealed signer hash")

        receipt = self.submitter.get_transaction_receipt(transaction_hash)
        if receipt is None:
            status = "pending_verification"
            block_number = None
            receipt_status = None
            finalized_block = None
        else:
            receipt_status = receipt.get("status")
            block_number = receipt.get("blockNumber")
            if receipt_status in {"0x0", 0, False}:
                status = "payment_failed"
                finalized_block = self.submitter.get_finalized_block_number(prepared["chainId"])
            elif receipt_status not in {"0x1", 1, True}:
                status = "pending_verification"
                finalized_block = self.submitter.get_finalized_block_number(prepared["chainId"])
            else:
                finalized_block = self.submitter.get_finalized_block_number(prepared["chainId"])
                if isinstance(block_number, str) and block_number.startswith("0x"):
                    block_number_int = int(block_number, 16)
                elif isinstance(block_number, int):
                    block_number_int = block_number
                else:
                    block_number_int = None
                if block_number_int is not None and finalized_block is not None and block_number_int <= finalized_block:
                    status = "settled"
                else:
                    status = "included_pending_finality"

        return {
            "status": status,
            "adapter": self.name,
            "live": self.live,
            "chain_id": prepared["chainId"],
            "source": prepared["from"],
            "destination": prepared["to"],
            "value_wei": prepared["value"],
            "nonce": prepared["nonce"],
            "gas_limit": prepared["gas"],
            "max_fee_per_gas_wei": prepared["maxFeePerGas"],
            "max_priority_fee_per_gas_wei": prepared["maxPriorityFeePerGas"],
            "max_total_fee_wei": prepared_bundle["max_total_fee_wei"],
            "prepared_transaction_hash": prepared_hash,
            "signed_transaction_hash": transaction_hash,
            "receipt_status": receipt_status,
            "block_number": block_number,
            "finalized_block_number": finalized_block,
            "capability_id": capability["capability_id"],
            "economic_mandate_hash": capability["economic_mandate_hash"],
            "policy_decision_hash": capability["policy_decision_hash"],
        }
