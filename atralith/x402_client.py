"""Governed x402 v2 client adapter for ATG RFC-0003.

This module implements the HTTP-side x402 buyer flow without owning wallet keys
or signing material. A caller must inject both a transport and a sealed signer.
The adapter is marked live=True, so ``execute_economic_action`` blocks it unless
``allow_live=True`` is explicitly supplied by the governed caller.

Security posture:
- no private keys or seed phrases enter transaction objects
- no raw wallet credential is stored by this adapter
- x402 payment requirements are checked against an explicit 54-T budget envelope
- pre-handler payment flows (upfront / escrow) are denied by default
- the paid retry must use the exact same resource URL
- settlement is never claimed without a parseable PAYMENT-RESPONSE
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse


PAYMENT_REQUIRED = "PAYMENT-REQUIRED"
PAYMENT_SIGNATURE = "PAYMENT-SIGNATURE"
PAYMENT_RESPONSE = "PAYMENT-RESPONSE"


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(obj: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(obj).encode('utf-8')).hexdigest()}"


def _b64_json_decode(value: str, label: str) -> dict[str, Any]:
    try:
        padding = "=" * (-len(value) % 4)
        raw = base64.b64decode(value + padding, validate=True)
        decoded = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # transport input is untrusted; normalize failures
        raise ValueError(f"invalid {label}: expected base64 JSON") from exc
    if not isinstance(decoded, dict):
        raise ValueError(f"invalid {label}: JSON object required")
    return decoded


def _b64_json_encode(value: dict[str, Any]) -> str:
    return base64.b64encode(_canonical(value).encode("utf-8")).decode("ascii")


def _atomic_int(value: Any, label: str) -> int:
    if not isinstance(value, str) or not value.isdigit():
        raise ValueError(f"{label} must be a non-negative integer string in atomic units")
    return int(value)


def _host(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("x402 resource_url must be an absolute http/https URL")
    return parsed.hostname.lower()


def _headers_lower(headers: Mapping[str, str]) -> dict[str, str]:
    return {str(key).lower(): str(value) for key, value in headers.items()}


@dataclass(frozen=True)
class HTTPResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes = b""


class X402Transport(Protocol):
    """Capability-scoped HTTP transport supplied by the runtime, not the model."""

    def request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
    ) -> HTTPResponse: ...


class X402Signer(Protocol):
    """Sealed signer interface.

    Implementations may use an HSM, hardware wallet, session wallet, or provider
    wallet. The adapter receives only a PaymentPayload back; it never receives
    the signing secret.
    """

    def create_payment_payload(
        self,
        *,
        payment_required: dict[str, Any],
        accepted: dict[str, Any],
        capability: dict[str, Any],
        transaction: dict[str, Any],
    ) -> dict[str, Any]: ...


def parse_payment_required(response: HTTPResponse) -> dict[str, Any]:
    headers = _headers_lower(response.headers)
    value = headers.get(PAYMENT_REQUIRED.lower())
    if not value:
        raise ValueError("402 response missing PAYMENT-REQUIRED header")
    required = _b64_json_decode(value, PAYMENT_REQUIRED)
    if required.get("x402Version") != 2:
        raise ValueError("unsupported x402 version; version 2 required")
    resource = required.get("resource")
    accepts = required.get("accepts")
    if not isinstance(resource, dict) or not isinstance(resource.get("url"), str):
        raise ValueError("PaymentRequired.resource.url is required")
    if not isinstance(accepts, list) or not accepts:
        raise ValueError("PaymentRequired.accepts must be a non-empty array")
    return required


def _payment_flow(requirement: dict[str, Any]) -> str:
    extra = requirement.get("extra")
    if not isinstance(extra, dict):
        return "authorization"
    flow = extra.get("paymentFlow", "authorization")
    if not isinstance(flow, str):
        raise ValueError("paymentFlow must be a string")
    return flow


def select_payment_requirement(
    payment_required: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Select the safest x402 requirement that stays inside a 54-T policy envelope."""

    network = policy.get("network")
    asset = policy.get("asset")
    max_amount_atomic = _atomic_int(policy.get("max_amount_atomic"), "x402_policy.max_amount_atomic")
    allowed_schemes = policy.get("allowed_schemes") or ["exact"]
    allowed_flows = policy.get("allowed_payment_flows") or ["authorization"]
    pay_to = policy.get("pay_to")

    if not isinstance(network, str) or ":" not in network:
        raise ValueError("x402_policy.network must be a CAIP-2 network identifier")
    if not isinstance(asset, str) or not asset:
        raise ValueError("x402_policy.asset is required")
    if not isinstance(allowed_schemes, list) or not allowed_schemes:
        raise ValueError("x402_policy.allowed_schemes must be a non-empty array")
    if not isinstance(allowed_flows, list) or not allowed_flows:
        raise ValueError("x402_policy.allowed_payment_flows must be a non-empty array")

    candidates: list[dict[str, Any]] = []
    for raw in payment_required["accepts"]:
        if not isinstance(raw, dict):
            continue
        try:
            amount = _atomic_int(raw.get("amount"), "PaymentRequirements.amount")
            flow = _payment_flow(raw)
        except ValueError:
            continue
        if raw.get("scheme") not in allowed_schemes:
            continue
        if raw.get("network") != network:
            continue
        if raw.get("asset") != asset:
            continue
        if amount > max_amount_atomic:
            continue
        if pay_to is not None and raw.get("payTo") != pay_to:
            continue
        if flow not in allowed_flows:
            continue
        if not isinstance(raw.get("payTo"), str) or not raw.get("payTo"):
            continue
        if not isinstance(raw.get("maxTimeoutSeconds"), (int, float)):
            continue
        candidates.append(raw)

    if not candidates:
        raise PermissionError("no x402 payment requirement fits the governed policy envelope")

    # Prefer authorization (post-resource settlement) and then the smallest amount.
    candidates.sort(
        key=lambda item: (
            0 if _payment_flow(item) == "authorization" else 1,
            _atomic_int(item["amount"], "PaymentRequirements.amount"),
        )
    )
    return candidates[0]


def validate_payment_payload(
    payload: dict[str, Any],
    payment_required: dict[str, Any],
    accepted: dict[str, Any],
) -> None:
    if not isinstance(payload, dict):
        raise ValueError("sealed signer must return a PaymentPayload object")
    if payload.get("x402Version") != 2:
        raise ValueError("PaymentPayload.x402Version must be 2")
    if payload.get("accepted") != accepted:
        raise ValueError("PaymentPayload.accepted must exactly match selected requirements")
    if not isinstance(payload.get("payload"), dict):
        raise ValueError("PaymentPayload.payload must be a scheme-specific object")

    resource = payload.get("resource")
    if resource is not None:
        if not isinstance(resource, dict):
            raise ValueError("PaymentPayload.resource must be an object when present")
        if resource.get("url") != payment_required["resource"]["url"]:
            raise ValueError("PaymentPayload.resource.url changed after authorization")

    required_extensions = payment_required.get("extensions") or {}
    payload_extensions = payload.get("extensions") or {}
    if not isinstance(required_extensions, dict) or not isinstance(payload_extensions, dict):
        raise ValueError("x402 extensions must be objects")
    for key, value in required_extensions.items():
        if key not in payload_extensions or payload_extensions[key] != value:
            raise ValueError("PaymentPayload extensions may not delete or overwrite server requirements")


def parse_settlement_response(response: HTTPResponse) -> dict[str, Any] | None:
    value = _headers_lower(response.headers).get(PAYMENT_RESPONSE.lower())
    if value is None:
        return None
    settlement = _b64_json_decode(value, PAYMENT_RESPONSE)
    if not isinstance(settlement.get("success"), bool):
        raise ValueError("SettlementResponse.success must be boolean")
    if not isinstance(settlement.get("transaction"), str):
        raise ValueError("SettlementResponse.transaction must be string")
    if not isinstance(settlement.get("network"), str):
        raise ValueError("SettlementResponse.network must be string")
    return settlement


class X402SettlementAdapter:
    """x402 V2 buyer adapter governed by ATG capability handles.

    This is deliberately dependency-injected. The transport and signer are
    runtime capabilities. Neither is discoverable from prompt content.
    """

    name = "x402-v2"
    live = True

    def __init__(self, transport: X402Transport, signer: X402Signer) -> None:
        self.transport = transport
        self.signer = signer

    def execute(self, capability: dict[str, Any], transaction: dict[str, Any]) -> dict[str, Any]:
        if transaction.get("settlement_mode") != "x402":
            raise ValueError("transaction settlement_mode must be x402")

        method = str(transaction.get("method", "GET")).upper()
        resource_url = transaction.get("resource_url")
        expected_domain = transaction.get("domain")
        if not isinstance(resource_url, str):
            raise ValueError("transaction.resource_url is required")
        actual_domain = _host(resource_url)
        if expected_domain and str(expected_domain).lower() != actual_domain:
            raise PermissionError("resource_url host does not match 54-T approved transaction domain")

        policy = transaction.get("x402_policy")
        if not isinstance(policy, dict):
            raise PermissionError("x402_policy is required; the adapter will not infer a spend budget")

        request_headers = transaction.get("request_headers") or {}
        if not isinstance(request_headers, dict):
            raise ValueError("request_headers must be an object")
        if PAYMENT_SIGNATURE.lower() in _headers_lower(request_headers):
            raise PermissionError("caller may not pre-inject PAYMENT-SIGNATURE")

        body = transaction.get("request_body")
        if body is None:
            request_body = None
        elif isinstance(body, str):
            request_body = body.encode("utf-8")
        else:
            raise ValueError("request_body must be a string or null in the reference adapter")

        first = self.transport.request(method, resource_url, request_headers, request_body)
        if first.status != 402:
            return {
                "status": "not_required",
                "adapter": self.name,
                "live": self.live,
                "http_status": first.status,
                "resource_url": resource_url,
                "resource_body_hash": f"sha256:{hashlib.sha256(first.body).hexdigest()}",
                "capability_id": capability["capability_id"],
                "economic_mandate_hash": capability["economic_mandate_hash"],
            }

        payment_required = parse_payment_required(first)
        if payment_required["resource"]["url"] != resource_url:
            raise PermissionError("x402 server changed the protected resource URL")

        accepted = select_payment_requirement(payment_required, policy)
        payment_payload = self.signer.create_payment_payload(
            payment_required=payment_required,
            accepted=accepted,
            capability=capability,
            transaction=transaction,
        )
        validate_payment_payload(payment_payload, payment_required, accepted)

        paid_headers = dict(request_headers)
        paid_headers[PAYMENT_SIGNATURE] = _b64_json_encode(payment_payload)
        second = self.transport.request(method, resource_url, paid_headers, request_body)
        settlement = parse_settlement_response(second)

        if settlement is None:
            status = "pending_verification" if 200 <= second.status < 300 else "payment_failed"
        elif settlement["success"] and 200 <= second.status < 300:
            if settlement["network"] != accepted["network"]:
                raise ValueError("SettlementResponse.network does not match selected requirement")
            status = "settled"
        else:
            status = "payment_failed"

        return {
            "status": status,
            "adapter": self.name,
            "live": self.live,
            "http_status": second.status,
            "resource_url": resource_url,
            "scheme": accepted["scheme"],
            "network": accepted["network"],
            "asset": accepted["asset"],
            "amount_atomic": accepted["amount"],
            "pay_to": accepted["payTo"],
            "payment_flow": _payment_flow(accepted),
            "payment_required_hash": _sha256(payment_required),
            "payment_payload_hash": _sha256(payment_payload),
            "settlement_response_hash": _sha256(settlement) if settlement is not None else None,
            "transaction_id": settlement.get("transaction") if settlement else None,
            "payer": settlement.get("payer") if settlement else None,
            "resource_body_hash": f"sha256:{hashlib.sha256(second.body).hexdigest()}",
            "capability_id": capability["capability_id"],
            "economic_mandate_hash": capability["economic_mandate_hash"],
            "policy_decision_hash": capability["policy_decision_hash"],
        }
