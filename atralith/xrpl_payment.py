"""Governed XRPL XRP Payment adapter for ATG RFC-0003.

Reference scope: direct XRP Payment transactions only. No pathfinding, issued
currency, partial payments, raw secrets, or server-side signing.

The runtime injects:
- a state reader that supplies trusted current account/ledger data
- a sealed signer that returns only a signed transaction blob + hash
- a submitter that submits the signed blob and waits for a final/validated result

The adapter itself never receives a seed/private key.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol


TF_PARTIAL_PAYMENT = 0x00020000


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(obj: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(obj).encode('utf-8')).hexdigest()}"


def _uint(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def _drops(value: Any, label: str) -> int:
    if not isinstance(value, str) or not value.isdigit():
        raise ValueError(f"{label} must be a non-negative integer string in XRP drops")
    parsed = int(value)
    if parsed <= 0:
        raise ValueError(f"{label} must be greater than zero")
    return parsed


def _address(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("r") or len(value) < 25:
        raise ValueError(f"{label} must be an XRPL classic address")
    return value


@dataclass(frozen=True)
class XRPLAccountState:
    account: str
    sequence: int
    validated_ledger_index: int
    recommended_fee_drops: str


class XRPLStateReader(Protocol):
    def get_account_state(self, account: str) -> XRPLAccountState: ...


class XRPLSealedSigner(Protocol):
    """Production implementations keep signing keys behind HSM/KMS/wallet boundaries."""

    def sign(self, transaction: dict[str, Any], capability: dict[str, Any]) -> dict[str, str]: ...


class XRPLSubmitter(Protocol):
    """Submit a signed blob and wait for a final or expiry-aware result."""

    def submit_and_wait(self, tx_blob: str, *, last_ledger_sequence: int) -> dict[str, Any]: ...


def prepare_xrp_payment(
    *,
    capability: dict[str, Any],
    transaction: dict[str, Any],
    state: XRPLAccountState,
) -> dict[str, Any]:
    """Build an exact, bounded XRP Payment from trusted state + 54-T policy."""

    if transaction.get("settlement_mode") != "xrpl":
        raise ValueError("transaction settlement_mode must be xrpl")

    policy = transaction.get("xrpl_policy")
    if not isinstance(policy, dict):
        raise PermissionError("xrpl_policy is required; adapter will not infer spend authority")

    account = _address(policy.get("account"), "xrpl_policy.account")
    destination = _address(transaction.get("destination"), "transaction.destination")
    if state.account != account:
        raise PermissionError("trusted XRPL account state does not match approved source account")

    allowed_destinations = policy.get("allowed_destinations") or []
    if not isinstance(allowed_destinations, list) or destination not in allowed_destinations:
        raise PermissionError("XRPL destination is outside the approved destination scope")

    amount_drops = _drops(transaction.get("amount_drops"), "transaction.amount_drops")
    max_amount_drops = _drops(policy.get("max_amount_drops"), "xrpl_policy.max_amount_drops")
    if amount_drops > max_amount_drops:
        raise PermissionError("XRPL payment exceeds approved XRP amount ceiling")

    fee_drops = _drops(state.recommended_fee_drops, "state.recommended_fee_drops")
    max_fee_drops = _drops(policy.get("max_fee_drops"), "xrpl_policy.max_fee_drops")
    if fee_drops > max_fee_drops:
        raise PermissionError("current XRPL fee exceeds approved fee ceiling")

    current_ledger = _uint(state.validated_ledger_index, "state.validated_ledger_index", minimum=1)
    sequence = _uint(state.sequence, "state.sequence", minimum=1)
    ledger_window = _uint(policy.get("last_ledger_offset", 20), "xrpl_policy.last_ledger_offset", minimum=2)
    last_ledger_sequence = current_ledger + ledger_window

    flags = transaction.get("flags", 0)
    flags = _uint(flags, "transaction.flags")
    if flags & TF_PARTIAL_PAYMENT:
        raise PermissionError("tfPartialPayment is forbidden for the direct-XRP profile")

    prepared: dict[str, Any] = {
        "TransactionType": "Payment",
        "Account": account,
        "Destination": destination,
        "Amount": str(amount_drops),
        "Fee": str(fee_drops),
        "Sequence": sequence,
        "LastLedgerSequence": last_ledger_sequence,
        "Flags": flags,
    }

    destination_tag = transaction.get("destination_tag")
    if destination_tag is not None:
        prepared["DestinationTag"] = _uint(destination_tag, "transaction.destination_tag")

    source_tag = transaction.get("source_tag")
    required_source_tag = policy.get("required_source_tag")
    if required_source_tag is not None:
        required_source_tag = _uint(required_source_tag, "xrpl_policy.required_source_tag")
        if source_tag != required_source_tag:
            raise PermissionError("XRPL SourceTag does not match the policy-required attribution tag")
    if source_tag is not None:
        prepared["SourceTag"] = _uint(source_tag, "transaction.source_tag")

    # Explicitly reject fields that can expand payment semantics in this profile.
    forbidden = {"DeliverMin", "SendMax", "Paths", "InvoiceID"}
    supplied = set(transaction.get("extra_fields") or {})
    if supplied & forbidden:
        raise PermissionError("XRPL advanced payment fields are forbidden in the direct-XRP profile")

    return prepared


def validate_signed_result(
    signed: dict[str, str],
    prepared: dict[str, Any],
) -> tuple[str, str]:
    if not isinstance(signed, dict):
        raise ValueError("sealed signer must return an object")
    tx_blob = signed.get("tx_blob")
    tx_hash = signed.get("hash")
    prepared_hash = signed.get("prepared_hash")
    if not isinstance(tx_blob, str) or not tx_blob:
        raise ValueError("sealed signer did not return tx_blob")
    if not isinstance(tx_hash, str) or not tx_hash:
        raise ValueError("sealed signer did not return transaction hash")
    expected = _sha256(prepared)
    if prepared_hash != expected:
        raise PermissionError("sealed signer did not attest to the exact prepared transaction")
    return tx_blob, tx_hash


class XRPLXRPSettlementAdapter:
    """Live XRPL adapter for bounded direct-XRP payments."""

    name = "xrpl-xrp-payment"
    live = True

    def __init__(
        self,
        state_reader: XRPLStateReader,
        signer: XRPLSealedSigner,
        submitter: XRPLSubmitter,
    ) -> None:
        self.state_reader = state_reader
        self.signer = signer
        self.submitter = submitter

    def execute(self, capability: dict[str, Any], transaction: dict[str, Any]) -> dict[str, Any]:
        policy = transaction.get("xrpl_policy")
        if not isinstance(policy, dict):
            raise PermissionError("xrpl_policy is required")

        account = _address(policy.get("account"), "xrpl_policy.account")
        state = self.state_reader.get_account_state(account)
        prepared = prepare_xrp_payment(
            capability=capability,
            transaction=transaction,
            state=state,
        )

        signed = self.signer.sign(prepared, capability)
        tx_blob, tx_hash = validate_signed_result(signed, prepared)
        final = self.submitter.submit_and_wait(
            tx_blob,
            last_ledger_sequence=prepared["LastLedgerSequence"],
        )
        if not isinstance(final, dict):
            raise ValueError("XRPL submitter returned invalid result")

        validated = final.get("validated") is True
        meta = final.get("meta") or {}
        result_code = meta.get("TransactionResult") if isinstance(meta, dict) else None
        reported_hash = final.get("hash")
        if reported_hash is not None and reported_hash != tx_hash:
            raise ValueError("XRPL final result hash does not match sealed signer transaction hash")

        if validated and result_code == "tesSUCCESS":
            status = "settled"
        elif validated:
            status = "payment_failed"
        else:
            status = "pending_verification"

        return {
            "status": status,
            "adapter": self.name,
            "live": self.live,
            "network": policy.get("network", "xrpl:mainnet"),
            "asset": "XRP",
            "amount_drops": prepared["Amount"],
            "fee_drops": prepared["Fee"],
            "source": prepared["Account"],
            "destination": prepared["Destination"],
            "sequence": prepared["Sequence"],
            "last_ledger_sequence": prepared["LastLedgerSequence"],
            "validated": validated,
            "transaction_result": result_code,
            "transaction_id": tx_hash,
            "prepared_transaction_hash": _sha256(prepared),
            "final_result_hash": _sha256(final),
            "capability_id": capability["capability_id"],
            "economic_mandate_hash": capability["economic_mandate_hash"],
            "policy_decision_hash": capability["policy_decision_hash"],
        }
