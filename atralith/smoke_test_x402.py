#!/usr/bin/env python3
"""Smoke tests for the governed x402 v2 adapter."""

from __future__ import annotations

import base64
import json

from atralith.economic import compile_economic_mandate
from atralith.economic_runtime import execute_economic_action
from atralith.mandate import build_mandate
from atralith.x402_client import HTTPResponse, X402SettlementAdapter


def _b64(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return base64.b64encode(raw).decode()


class MockTransport:
    def __init__(self, required, settlement):
        self.required = required
        self.settlement = settlement
        self.calls = []

    def request(self, method, url, headers, body):
        self.calls.append((method, url, dict(headers), body))
        if len(self.calls) == 1:
            return HTTPResponse(402, {"PAYMENT-REQUIRED": _b64(self.required)}, b"payment required")
        return HTTPResponse(200, {"PAYMENT-RESPONSE": _b64(self.settlement)}, b"resource")


class MockSigner:
    def create_payment_payload(self, *, payment_required, accepted, capability, transaction):
        return {
            "x402Version": 2,
            "resource": payment_required["resource"],
            "accepted": accepted,
            "payload": {"signature": "sealed-signer-test-value"},
            "extensions": payment_required.get("extensions", {}),
        }


def build_economic():
    parent = build_mandate(
        agent_id="agent:hermes.compute",
        action_type="purchase_compute",
        enforcement="enforced",
        scope={
            "maximum_value": "20.00",
            "allowed_assets": ["USDC"],
            "allowed_chains": ["eip155:8453"],
        },
        issued_by="principal:neuro",
    )
    return compile_economic_mandate(
        parent,
        purpose="Purchase one bounded compute job",
        amount="20.00",
        asset="USDC",
        settlement_mode="x402",
        network="eip155:8453",
        counterparty_scope={"allowed_domains": ["compute.example"]},
        approval={"required": True, "method": "human_passkey", "approvers": ["principal:neuro"]},
    )


def main():
    required = {
        "x402Version": 2,
        "resource": {"url": "https://compute.example/render/42", "description": "GPU render"},
        "accepts": [
            {
                "scheme": "exact",
                "network": "eip155:8453",
                "amount": "1500000",
                "asset": "USDC",
                "payTo": "0xabc",
                "maxTimeoutSeconds": 60,
                "extra": {"paymentFlow": "authorization"},
            },
            {
                "scheme": "exact",
                "network": "eip155:8453",
                "amount": "1000000",
                "asset": "USDC",
                "payTo": "0xabc",
                "maxTimeoutSeconds": 60,
                "extra": {"paymentFlow": "upfront"},
            },
        ],
    }
    settlement = {
        "success": True,
        "transaction": "0xsettled",
        "network": "eip155:8453",
        "payer": "0xpayer",
    }

    economic = build_economic()
    transaction = {
        "amount": "1.50",
        "asset": "USDC",
        "settlement_mode": "x402",
        "resource_url": "https://compute.example/render/42",
        "domain": "compute.example",
        "approval_receipt": "approval:test-only",
        "x402_policy": {
            "network": "eip155:8453",
            "asset": "USDC",
            "max_amount_atomic": "1500000",
            "allowed_schemes": ["exact"],
            "allowed_payment_flows": ["authorization"],
            "pay_to": "0xabc",
        },
    }

    adapter = X402SettlementAdapter(MockTransport(required, settlement), MockSigner())

    blocked = False
    try:
        execute_economic_action(economic, transaction, adapter=adapter)
    except PermissionError:
        blocked = True
    assert blocked, "live x402 adapter must be blocked unless allow_live=True"

    result = execute_economic_action(economic, transaction, adapter=adapter, allow_live=True)
    settlement_result = result["settlement_result"]
    assert settlement_result["status"] == "settled"
    assert settlement_result["payment_flow"] == "authorization"
    assert settlement_result["amount_atomic"] == "1500000"

    over_budget_required = dict(required)
    over_budget_required["accepts"] = [dict(required["accepts"][0], amount="2500000")]
    denied = False
    try:
        execute_economic_action(
            economic,
            transaction,
            adapter=X402SettlementAdapter(MockTransport(over_budget_required, settlement), MockSigner()),
            allow_live=True,
        )
    except PermissionError:
        denied = True
    assert denied, "server-required amount above x402 policy ceiling must fail closed"

    wrong_domain = dict(transaction, resource_url="https://evil.example/render/42")
    denied = False
    try:
        execute_economic_action(economic, wrong_domain, adapter=adapter, allow_live=True)
    except PermissionError:
        denied = True
    assert denied, "resource host drift must fail closed"

    upfront_only = dict(required)
    upfront_only["accepts"] = [required["accepts"][1]]
    denied = False
    try:
        execute_economic_action(
            economic,
            transaction,
            adapter=X402SettlementAdapter(MockTransport(upfront_only, settlement), MockSigner()),
            allow_live=True,
        )
    except PermissionError:
        denied = True
    assert denied, "upfront flow must be denied unless explicitly allowed"

    print("PASS: x402 v2 adapter is capability-bound, budgeted, domain-bound, and authorization-first")


if __name__ == "__main__":
    main()
