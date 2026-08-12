#!/usr/bin/env python3
"""Smoke tests for RFC-0003 economic authority + simulation runtime."""

from atralith.economic import compile_economic_mandate, verify_economic_mandate_hash
from atralith.economic_runtime import execute_economic_action
from atralith.mandate import build_mandate


def main() -> None:
    parent = build_mandate(
        agent_id="agent:hermes.creator",
        action_type="purchase_compute",
        enforcement="enforced",
        scope={
            "maximum_value": "25.00",
            "allowed_assets": ["USDC"],
            "allowed_chains": ["base"],
            "allowed_destinations": ["0xabc"],
        },
        issued_by="principal:neuro",
    )

    economic = compile_economic_mandate(
        parent,
        purpose="Purchase one approved GPU render job",
        amount="18.00",
        asset="USDC",
        settlement_mode="x402",
        network="base",
        adapter="simulation",
        counterparty_scope={
            "allowed_merchants": ["gpu-provider-01"],
            "allowed_domains": ["api.gpu-provider.test"],
            "allowed_addresses": ["0xabc"],
        },
        approval={
            "required": True,
            "method": "human_passkey",
            "approvers": ["principal:neuro"],
        },
    )

    assert verify_economic_mandate_hash(economic)

    result = execute_economic_action(
        economic,
        {
            "amount": "18.00",
            "asset": "USDC",
            "merchant": "gpu-provider-01",
            "domain": "api.gpu-provider.test",
            "destination": "0xabc",
            "approval_receipt": "approval:test-only",
        },
    )
    assert result["verification_state"] == "simulated"
    assert result["settlement_result"]["live"] is False

    denied = False
    try:
        execute_economic_action(
            economic,
            {
                "amount": "26.00",
                "asset": "USDC",
                "merchant": "gpu-provider-01",
                "domain": "api.gpu-provider.test",
                "destination": "0xabc",
                "approval_receipt": "approval:test-only",
            },
        )
    except PermissionError:
        denied = True
    assert denied, "over-limit transaction must fail closed"

    widened = False
    try:
        compile_economic_mandate(
            parent,
            purpose="Attempt privilege widening",
            amount="30.00",
            asset="USDC",
            settlement_mode="x402",
            network="base",
        )
    except ValueError:
        widened = True
    assert widened, "economic compiler must not widen parent authority"

    print("PASS: RFC-0003 economic runtime is bounded, simulation-only, and fail-closed")


if __name__ == "__main__":
    main()
