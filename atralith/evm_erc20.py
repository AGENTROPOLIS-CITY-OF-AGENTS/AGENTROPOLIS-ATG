"""Governed ERC-20 transfer-only adapter for ATG RFC-0003.

This profile permits exactly one EIP-20 `transfer(address,uint256)` call to a
policy-pinned token contract. It forbids approvals, transferFrom, arbitrary
calldata, delegatecall surfaces, and raw key material.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol

TRANSFER_SELECTOR = "a9059cbb"


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


def encode_transfer(destination: str, amount_units: int) -> str:
    to_word = destination[2:].lower().rjust(64, "0")
    amount_word = hex(amount_units)[2:].rjust(64, "0")
    return "0x" + TRANSFER_SELECTOR + to_word + amount_word


@dataclass(frozen=True)
class ERC20State:
    chain_id: int
    nonce: int
    base_fee_per_gas: int
    latest_block_number: int
    finalized_block_number: int | None = None


@dataclass(frozen=True)
class ERC20TokenInfo:
    contract: str
    code_hash: str
    decimals: int | None = None
    symbol: str | None = None


class ERC20StateReader(Protocol):
    def read_state(self, account: str, chain_id: int) -> ERC20State: ...
    def inspect_token(self, contract: str, chain_id: int) -> ERC20TokenInfo: ...
    def estimate_gas(self, transaction: dict[str, Any]) -> int: ...


class ERC20Signer(Protocol):
    def sign_transaction(
        self,
        *,
        prepared_transaction: dict[str, Any],
        capability: dict[str, Any],
    ) -> dict[str, Any]: ...


class ERC20Submitter(Protocol):
    def submit_raw_transaction(self, raw_transaction: str) -> dict[str, Any]: ...
    def get_transaction_receipt(self, transaction_hash: str) -> dict[str, Any] | None: ...
    def get_finalized_block_number(self, chain_id: int) -> int | None: ...


def prepare_erc20_transfer(*, transaction: dict[str, Any], state_reader: ERC20StateReader) -> dict[str, Any]:
    policy = transaction.get("erc20_policy")
    if not isinstance(policy, dict):
        raise PermissionError("erc20_policy is required")

    chain_id = policy.get("chain_id")
    if not isinstance(chain_id, int) or chain_id <= 0:
        raise ValueError("erc20_policy.chain_id must be a positive integer")

    source = _address(policy.get("source"), "erc20_policy.source")
    token_contract = _address(transaction.get("token_contract"), "transaction.token_contract")
    pinned_contract = _address(policy.get("token_contract"), "erc20_policy.token_contract")
    if token_contract != pinned_contract:
        raise PermissionError("token contract is outside the governed ERC-20 policy")

    destination = _address(transaction.get("destination"), "transaction.destination")
    pinned_destination = policy.get("destination")
    if pinned_destination is not None and destination != _address(pinned_destination, "erc20_policy.destination"):
        raise PermissionError("destination is outside the governed ERC-20 policy")

    amount_units = _int_string(transaction.get("amount_units"), "transaction.amount_units")
    max_amount_units = _int_string(policy.get("max_amount_units"), "erc20_policy.max_amount_units")
    if amount_units <= 0:
        raise ValueError("ERC-20 transfer amount must be greater than zero")
    if amount_units > max_amount_units:
        raise PermissionError("ERC-20 transfer exceeds governed token-unit ceiling")

    token = state_reader.inspect_token(token_contract, chain_id)
    if _address(token.contract, "trusted token contract") != token_contract:
        raise ValueError("trusted token inspector returned a different contract")
    pinned_code_hash = policy.get("token_code_hash")
    if pinned_code_hash is not None and token.code_hash != pinned_code_hash:
        raise PermissionError("token contract code hash differs from governed policy")
    if not isinstance(token.code_hash, str) or not token.code_hash:
        raise ValueError("trusted token inspector must return a code hash")

    expected_decimals = policy.get("token_decimals")
    if expected_decimals is not None and token.decimals != expected_decimals:
        raise PermissionError("token decimals differ from governed policy")

    state = state_reader.read_state(source, chain_id)
    if state.chain_id != chain_id:
        raise ValueError("trusted EVM state reader returned the wrong chain_id")

    max_fee_per_gas = _int_string(transaction.get("max_fee_per_gas_wei"), "transaction.max_fee_per_gas_wei")
    max_priority_fee_per_gas = _int_string(
        transaction.get("max_priority_fee_per_gas_wei"),
        "transaction.max_priority_fee_per_gas_wei",
    )
    fee_ceiling = _int_string(policy.get("max_fee_per_gas_wei"), "erc20_policy.max_fee_per_gas_wei")
    priority_ceiling = _int_string(
        policy.get("max_priority_fee_per_gas_wei"),
        "erc20_policy.max_priority_fee_per_gas_wei",
    )
    if max_fee_per_gas > fee_ceiling:
        raise PermissionError("maxFeePerGas exceeds governed ceiling")
    if max_priority_fee_per_gas > priority_ceiling:
        raise PermissionError("maxPriorityFeePerGas exceeds governed ceiling")
    if max_priority_fee_per_gas > max_fee_per_gas:
        raise ValueError("maxPriorityFeePerGas cannot exceed maxFeePerGas")
    if max_fee_per_gas < state.base_fee_per_gas:
        raise PermissionError("maxFeePerGas is below the current trusted base fee")

    data = encode_transfer(destination, amount_units)
    skeleton = {
        "type": 2,
        "chainId": chain_id,
        "from": source,
        "to": token_contract,
        "value": "0",
        "nonce": state.nonce,
        "maxFeePerGas": str(max_fee_per_gas),
        "maxPriorityFeePerGas": str(max_priority_fee_per_gas),
        "data": data,
    }

    gas_limit = state_reader.estimate_gas(skeleton)
    if not isinstance(gas_limit, int) or gas_limit <= 0:
        raise ValueError("trusted gas estimator returned an invalid gas limit")
    max_gas_limit = policy.get("max_gas_limit")
    if not isinstance(max_gas_limit, int) or max_gas_limit <= 0:
        raise ValueError("erc20_policy.max_gas_limit must be a positive integer")
    if gas_limit > max_gas_limit:
        raise PermissionError("estimated ERC-20 gas exceeds governed ceiling")

    max_total_fee = gas_limit * max_fee_per_gas
    total_fee_ceiling = _int_string(policy.get("max_total_fee_wei"), "erc20_policy.max_total_fee_wei")
    if max_total_fee > total_fee_ceiling:
        raise PermissionError("worst-case ERC-20 transaction fee exceeds governed ceiling")

    prepared = dict(skeleton)
    prepared["gas"] = gas_limit
    return {
        "prepared_transaction": prepared,
        "prepared_transaction_hash": _sha256(prepared),
        "token_info": {
            "contract": token_contract,
            "code_hash": token.code_hash,
            "decimals": token.decimals,
            "symbol": token.symbol,
        },
        "transfer": {"destination": destination, "amount_units": str(amount_units)},
        "max_total_fee_wei": str(max_total_fee),
    }


class EVMERC20TransferAdapter:
    name = "evm-erc20-transfer-v1"
    live = True

    def __init__(self, *, state_reader: ERC20StateReader, signer: ERC20Signer, submitter: ERC20Submitter) -> None:
        self.state_reader = state_reader
        self.signer = signer
        self.submitter = submitter

    def execute(self, capability: dict[str, Any], transaction: dict[str, Any]) -> dict[str, Any]:
        if transaction.get("settlement_mode") != "evm_erc20":
            raise ValueError("transaction settlement_mode must be evm_erc20")

        bundle = prepare_erc20_transfer(transaction=transaction, state_reader=self.state_reader)
        prepared = bundle["prepared_transaction"]
        prepared_hash = bundle["prepared_transaction_hash"]

        signed = self.signer.sign_transaction(prepared_transaction=prepared, capability=capability)
        if not isinstance(signed, dict):
            raise ValueError("sealed signer must return an object")
        if signed.get("prepared_transaction_hash") != prepared_hash:
            raise ValueError("sealed signer attestation does not match prepared ERC-20 transaction")
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
            receipt_status = None
            block_number = None
            finalized_block = None
        else:
            receipt_status = receipt.get("status")
            block_number = receipt.get("blockNumber")
            finalized_block = self.submitter.get_finalized_block_number(prepared["chainId"])
            if receipt_status in {"0x0", 0, False}:
                status = "payment_failed"
            elif receipt_status not in {"0x1", 1, True}:
                status = "pending_verification"
            else:
                if isinstance(block_number, str) and block_number.startswith("0x"):
                    block_number_int = int(block_number, 16)
                elif isinstance(block_number, int):
                    block_number_int = block_number
                else:
                    block_number_int = None
                status = (
                    "settled"
                    if block_number_int is not None and finalized_block is not None and block_number_int <= finalized_block
                    else "included_pending_finality"
                )

        return {
            "status": status,
            "adapter": self.name,
            "live": self.live,
            "chain_id": prepared["chainId"],
            "source": prepared["from"],
            "token_contract": bundle["token_info"]["contract"],
            "token_code_hash": bundle["token_info"]["code_hash"],
            "token_decimals": bundle["token_info"]["decimals"],
            "token_symbol": bundle["token_info"]["symbol"],
            "destination": bundle["transfer"]["destination"],
            "amount_units": bundle["transfer"]["amount_units"],
            "nonce": prepared["nonce"],
            "gas_limit": prepared["gas"],
            "max_fee_per_gas_wei": prepared["maxFeePerGas"],
            "max_priority_fee_per_gas_wei": prepared["maxPriorityFeePerGas"],
            "max_total_fee_wei": bundle["max_total_fee_wei"],
            "prepared_transaction_hash": prepared_hash,
            "signed_transaction_hash": transaction_hash,
            "receipt_status": receipt_status,
            "block_number": block_number,
            "finalized_block_number": finalized_block,
            "capability_id": capability["capability_id"],
            "economic_mandate_hash": capability["economic_mandate_hash"],
            "policy_decision_hash": capability["policy_decision_hash"],
        }
