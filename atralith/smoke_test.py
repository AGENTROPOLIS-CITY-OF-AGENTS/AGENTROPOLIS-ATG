#!/usr/bin/env python3
"""End-to-end smoke test for ATRALITH-lite — CITYFLIGHT pipeline walkthrough."""

import json
import sys

from atralith.mandate import build_mandate
from atralith.envelope import sign_envelope
from atralith.receipt import generate_receipt, verify_receipt


def main():
    errors = 0

    # 1. Build a CITYFLIGHT mandate
    print("1. Building CITYFLIGHT mandate...")
    mandate = build_mandate(
        agent_id="agent:cityflight-01",
        action_type="cityflight",
        action_stage="generation",
        enforcement="enforced",
        scope={
            "max_spend_per_generation": "100.00",
            "max_generations_per_hour": 10,
            "allowed_providers": ["openai", "fal"],
            "allowed_output_types": ["image", "video"],
        },
        constraints={
            "valid_from": "2026-08-01T00:00:00Z",
            "valid_until": "2026-08-08T00:00:00Z",
            "required_evidence": ["policy_pass", "safety_scan", "quality_gate"],
            "required_signer_class": "hardware_signer",
        },
        issued_by="principal:tony",
    )
    assert mandate["agent_id"] == "agent:cityflight-01"
    assert mandate["enforcement"] == "enforced"
    assert mandate["mandate_hash"].startswith("sha256:")
    print(f"   ✓ mandate_id={mandate['mandate_id']} hash={mandate['mandate_hash'][:18]}...")
    errors += 0

    # 2. Sign an authorization envelope (A3_IRREVERSIBLE — CITYFLIGHT release)
    print("2. Signing authorization envelope (A3_IRREVERSIBLE)...")
    payload = {
        "action": "deploy",
        "artifact_id": "img_7f3a",
        "destination": "registry:cityflight/prod",
    }
    envelope = sign_envelope(
        mandate=mandate,
        payload=payload,
        authorization_class="A3_IRREVERSIBLE",
        authorizer="signer:treasury-01",
        signer_type="hardware_signer",
        key_residency="non_exportable",
        display_trust="independent_trusted_path",
        confirmation="human_physical",
    )
    assert envelope["proposal"]["agent_id"] == "agent:cityflight-01"
    assert envelope["authorization"]["class"] == "A3_IRREVERSIBLE"
    assert envelope["authorization"]["blind_signing"] is False
    print(f"   ✓ class={envelope['authorization']['class']} display_trust={envelope['authorization']['display_trust']}")
    errors += 0

    # 3. Generate a receipt
    print("3. Generating receipt...")
    result = {"status": "deployed", "tx": "0x9a2f...", "timestamp": "2026-08-01T01:00:00Z"}
    receipt_chain = [
        {"step": "generation_complete", "component": "cityflight-gen", "hash": "sha256:aaaa000000000000000000000000000000000000000000000000000000000011"},
        {"step": "safety_scan_pass", "component": "aegis", "hash": "sha256:aaaa000000000000000000000000000000000000000000000000000000000012"},
        {"step": "release_approval", "component": "principal:tony", "hash": "sha256:aaaa000000000000000000000000000000000000000000000000000000000013"},
    ]
    receipt = generate_receipt(
        envelope=envelope,
        result=result,
        verification_state="deployed",
        receipt_chain=receipt_chain,
        verifier="agent:auditor",
    )
    assert receipt["verification_state"] == "deployed"
    assert receipt["authorization_class"] == "A3_IRREVERSIBLE"
    assert len(receipt["receipt_chain"]) == 3
    print(f"   ✓ receipt_id={receipt['receipt_id']} state={receipt['verification_state']}")
    errors += 0

    # 4. Verify the receipt
    print("4. Verifying receipt...")
    valid, findings = verify_receipt(receipt, envelope, result)
    assert valid, f"Verification failed: {findings}"
    print("   ✓ receipt verified — all hash chains match")

    # 5. Verify tamper detection
    print("5. Tamper detection...")
    tampered = dict(receipt)
    tampered["mandate_hash"] = "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    valid, findings = verify_receipt(tampered, envelope, result)
    assert not valid, "Tampered receipt should fail verification"
    assert any("mandate_hash" in f for f in findings)
    print(f"   ✓ tampered receipt correctly rejected ({len(findings)} findings)")

    # 6. Build a revertible mandate and verify it works with A1 class
    print("6. A1_REVERSIBLE flow...")
    simple_mandate = build_mandate(
        agent_id="agent:test",
        action_type="read",
        enforcement="advisory",
        issued_by="principal:tony",
    )
    simple_envelope = sign_envelope(
        mandate=simple_mandate,
        payload={"query": "status"},
        authorization_class="A1_REVERSIBLE",
        authorizer="agent:test",
    )
    simple_receipt = generate_receipt(
        envelope=simple_envelope,
        result={"status": "ok"},
        verification_state="verified",
    )
    valid, _ = verify_receipt(simple_receipt, simple_envelope, {"status": "ok"})
    assert valid
    print("   ✓ A1_REVERSIBLE flow complete")

    print(f"\n{'='*50}")
    print(f"All tests passed. {'No errors.' if errors == 0 else f'{errors} errors.'}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
