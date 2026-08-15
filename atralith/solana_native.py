"""Governed Solana native-SOL transfer adapter for ATG RFC-0003.

Phase 1 supports exactly one System Program SOL transfer. It deliberately excludes
SPL tokens, arbitrary program instructions, durable nonces, lookup tables, and raw
key material. All network state, recipient classification, signing, submission, and
confirmation are injected capability interfaces.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol


_BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58_MAP = {ch: idx for idx, ch in enumerate(_BASE58)}


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(obj: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(obj).encode('utf-8')).hexdigest()}"


def _int_string(value: Any, label: str) -> int:
    if not isinstance(value, str) or not value.isdigit():
        raise ValueError(f"{label} must be a non-negative integer string")
    return int(value)


def _base58_decode(value: str) -> bytes:
    number = 0
    for char in value:
        if char not in _BASE58_MAP:
            raise ValueError("invalid base58 character")
        number = number * 58 + _BASE58_MAP[char]
    body = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    leading_zeroes = len(value) - len(value.lstrip("1"))
    return b"\x00" * leading_zeroes + body


def _pubkey(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a base58 Solana public key")
    try:
        decoded = _base58_decode(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a base58 Solana public key") from exc
    if len(decoded) != 32:
        raise ValueError(f"{label} must decode to 32 bytes")
    return value


@dataclass(frozen=True)
class SolanaBlockhashState:
    network: str
    blockhash: str
    last_valid_block_height: int
    current_block_height: int


class SolanaStateReader(Protocol):
    def get_latest_blockhash(self, network: str) -> SolanaBlockhashState: ...
    def classify_recipient(self, network: str, pubkey: str) -> str: ...
    def estimate_fee_lamports(self, network: str, prepared_message: dict[str, Any]) -> int: ...
    def get_block_height(self, network: str) -> int: ...


class SolanaSigner(Protocol):
    def sign_transaction(
        self,
        *,
        prepared_message: dict[str, Any],
        capability: dict[str, Any],
    ) -> dict[str, Any]: ...


class SolanaSubmitter(Protocol):
    def submit_transaction(self, signed_transaction_base64: str) -> dict[str, Any]: ...
    def get_signature_status(self, signature: str) -> dict[str, Any] | None: ...


def prepare_native_sol_transfer(*, transaction: dict[str, Any], state_reader: SolanaStateReader) -> dict[str, Any]:
    policy = transaction.get("solana_policy")
    if not isinstance(policy, dict):
        raise PermissionError("solana_policy is required")

    network = policy.get("network")
    if network not in {"mainnet-beta", "devnet", "testnet", "localnet"}:
        raise ValueError("solana_policy.network must be an explicitly supported cluster name")

    source = _pubkey(policy.get("source"), "solana_policy.source")
    destination = _pubkey(transaction.get("destination"), "transaction.destination")
    pinned_destination = policy.get("destination")
    if pinned_destination is not None and destination != _pubkey(pinned_destination, "solana_policy.destination"):
        raise PermissionError("destination is outside the governed Solana policy")

    lamports = _int_string(transaction.get("amount_lamports"), "transaction.amount_lamports")
    max_lamports = _int_string(policy.get("max_amount_lamports"), "solana_policy.max_amount_lamports")
    if lamports <= 0:
        raise ValueError("native SOL transfer amount must be greater than zero")
    if lamports > max_lamports:
        raise PermissionError("SOL transfer exceeds governed lamport ceiling")

    recipient_kind = state_reader.classify_recipient(network, destination)
    allowed_recipient_kinds = policy.get("allowed_recipient_kinds") or ["system_wallet", "unfunded_on_curve"]
    if recipient_kind not in allowed_recipient_kinds:
        raise PermissionError("recipient classification is not approved for native SOL")

    state = state_reader.get_latest_blockhash(network)
    if state.network != network:
        raise ValueError("trusted Solana state reader returned the wrong network")
    if not isinstance(state.blockhash, str) or not state.blockhash:
        raise ValueError("trusted Solana state reader returned an invalid blockhash")
    if state.last_valid_block_height <= state.current_block_height:
        raise PermissionError("trusted recent blockhash is already expired")

    max_validity_window = policy.get("max_validity_window_blocks", 200)
    if not isinstance(max_validity_window, int) or max_validity_window <= 0:
        raise ValueError("solana_policy.max_validity_window_blocks must be a positive integer")
    validity_window = state.last_valid_block_height - state.current_block_height
    if validity_window > max_validity_window:
        raise PermissionError("trusted blockhash validity window exceeds governed ceiling")

    prepared_message = {
        "network": network,
        "fee_payer": source,
        "recent_blockhash": state.blockhash,
        "last_valid_block_height": state.last_valid_block_height,
        "instructions": [{
            "program": "system_program",
            "instruction": "transfer",
            "from": source,
            "to": destination,
            "lamports": str(lamports),
        }],
    }

    fee_lamports = state_reader.estimate_fee_lamports(network, prepared_message)
    if not isinstance(fee_lamports, int) or fee_lamports < 0:
        raise ValueError("trusted Solana fee estimator returned an invalid fee")
    max_fee_lamports = _int_string(policy.get("max_fee_lamports"), "solana_policy.max_fee_lamports")
    if fee_lamports > max_fee_lamports:
        raise PermissionError("estimated Solana network fee exceeds governed ceiling")

    return {
        "prepared_message": prepared_message,
        "prepared_message_hash": _sha256(prepared_message),
        "recipient_kind": recipient_kind,
        "estimated_fee_lamports": str(fee_lamports),
        "current_block_height": state.current_block_height,
    }


class SolanaNativeTransferAdapter:
    name = "solana-native-v1"
    live = True

    def __init__(self, *, state_reader: SolanaStateReader, signer: SolanaSigner, submitter: SolanaSubmitter) -> None:
        self.state_reader = state_reader
        self.signer = signer
        self.submitter = submitter

    def execute(self, capability: dict[str, Any], transaction: dict[str, Any]) -> dict[str, Any]:
        if transaction.get("settlement_mode") != "solana":
            raise ValueError("transaction settlement_mode must be solana")

        bundle = prepare_native_sol_transfer(transaction=transaction, state_reader=self.state_reader)
        prepared = bundle["prepared_message"]
        prepared_hash = bundle["prepared_message_hash"]

        current_height = self.state_reader.get_block_height(prepared["network"])
        if current_height > prepared["last_valid_block_height"]:
            raise PermissionError("Solana blockhash expired before signing")

        signed = self.signer.sign_transaction(prepared_message=prepared, capability=capability)
        if not isinstance(signed, dict):
            raise ValueError("sealed signer must return an object")
        if signed.get("prepared_message_hash") != prepared_hash:
            raise ValueError("sealed signer attestation does not match prepared Solana message")
        encoded = signed.get("signed_transaction_base64")
        signature = signed.get("signature")
        if not isinstance(encoded, str) or not encoded:
            raise ValueError("sealed signer must return signed_transaction_base64")
        if not isinstance(signature, str) or not signature:
            raise ValueError("sealed signer must return a transaction signature")

        submit = self.submitter.submit_transaction(encoded)
        submitted_signature = submit.get("signature") if isinstance(submit, dict) else None
        if submitted_signature and submitted_signature != signature:
            raise ValueError("submitter signature differs from sealed signer signature")

        status_record = self.submitter.get_signature_status(signature)
        if status_record is None:
            status = "pending_verification"
            confirmation_status = None
            slot = None
            error = None
        else:
            confirmation_status = status_record.get("confirmationStatus")
            slot = status_record.get("slot")
            error = status_record.get("err")
            if error is not None:
                status = "payment_failed"
            elif confirmation_status == "finalized":
                status = "settled"
            elif confirmation_status == "confirmed":
                status = "confirmed_pending_finality"
            else:
                status = "pending_verification"

        return {
            "status": status,
            "adapter": self.name,
            "live": self.live,
            "network": prepared["network"],
            "source": prepared["fee_payer"],
            "destination": prepared["instructions"][0]["to"],
            "amount_lamports": prepared["instructions"][0]["lamports"],
            "recipient_kind": bundle["recipient_kind"],
            "estimated_fee_lamports": bundle["estimated_fee_lamports"],
            "recent_blockhash": prepared["recent_blockhash"],
            "last_valid_block_height": prepared["last_valid_block_height"],
            "prepared_message_hash": prepared_hash,
            "signature": signature,
            "confirmation_status": confirmation_status,
            "slot": slot,
            "error": error,
            "capability_id": capability["capability_id"],
            "economic_mandate_hash": capability["economic_mandate_hash"],
            "policy_decision_hash": capability["policy_decision_hash"],
        }
