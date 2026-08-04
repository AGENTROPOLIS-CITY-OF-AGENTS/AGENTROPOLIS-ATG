#!/usr/bin/env python3
"""End-to-end smoke test for ATRALITH-lite — CITYFLIGHT pipeline walkthrough."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from atralith.envelope import sign_envelope
from atralith.mandate import build_mandate
from atralith.receipt import generate_receipt, verify_receipt


REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "atralith.cli", *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_failed_without_traceback(completed: subprocess.CompletedProcess[str]) -> None:
    output = completed.stdout + completed.stderr
    assert completed.returncode == 1, output
    assert "FAILED" in output, output
    assert "Traceback" not in output, output


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

    # 2. Construct an authorization envelope (A3_IRREVERSIBLE — CITYFLIGHT release)
    print("2. Constructing authorization envelope (A3_IRREVERSIBLE)...")
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

    # 4. Full verification requires independently supplied evidence.
    print("4. Verifying receipt with supplied envelope and result...")
    valid, findings = verify_receipt(receipt, envelope, result)
    assert valid, f"Verification failed: {findings}"
    print("   ✓ receipt structure and supplied artifact hashes/claims are consistent")

    print("5. Receipt-only verification is rejected...")
    valid, findings = verify_receipt(receipt)
    assert not valid, "Receipt-only verification must fail without independent evidence"
    assert any("envelope" in finding.lower() for finding in findings)
    assert any("result" in finding.lower() for finding in findings)
    print(f"   ✓ receipt-only verification correctly rejected ({len(findings)} findings)")

    # 6. Verify tamper detection for hashes, claims, and date-time format.
    print("6. Tamper detection and schema formats...")
    tampered = dict(receipt)
    tampered["mandate_hash"] = "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    valid, findings = verify_receipt(tampered, envelope, result)
    assert not valid, "Tampered receipt should fail verification"
    assert any("mandate_hash" in finding for finding in findings)

    tampered = dict(receipt)
    tampered["authorization_class"] = "A2_BOUNDED"
    valid, findings = verify_receipt(tampered, envelope, result)
    assert not valid, "Mismatched authorization class should fail verification"
    assert any("authorization_class" in finding for finding in findings)

    tampered = dict(receipt)
    tampered["display_trust"] = "host_rendered"
    valid, findings = verify_receipt(tampered, envelope, result)
    assert not valid, "Mismatched display trust should fail verification"
    assert any("display_trust" in finding for finding in findings)

    tampered = dict(receipt)
    tampered["created_at"] = "not-a-date-time"
    valid, findings = verify_receipt(tampered, envelope, result)
    assert not valid, "An invalid receipt created_at must fail format validation"
    assert any("created_at" in finding and "date-time" in finding for finding in findings)
    print("   ✓ hashes, claims, and invalid date-time are rejected")

    # 7. Canonical result serialization handles every JSON result value.
    print("7. Canonical result serialization...")
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
    for json_result in (["ok", {"count": 1}], 7, True, None):
        simple_receipt = generate_receipt(
            envelope=simple_envelope,
            result=json_result,
            verification_state="verified",
        )
        valid, findings = verify_receipt(simple_receipt, simple_envelope, json_result)
        assert valid, f"JSON result {json_result!r} did not round-trip: {findings}"

    valid, findings = verify_receipt(simple_receipt, simple_envelope, {"not": "serializable?"})
    assert not valid and any("result_hash" in finding for finding in findings)
    valid, findings = verify_receipt(simple_receipt, simple_envelope, {"unsupported"})
    assert not valid and any("Result serialization" in finding for finding in findings)
    print("   ✓ arrays, scalars, booleans, null, mismatches, and unsupported values are handled")

    # 8. Schema defaults must compare as false when fallback_used is absent.
    print("8. Optional fallback_used normalization...")
    no_fallback_envelope = copy.deepcopy(simple_envelope)
    no_fallback_envelope["authorization"].pop("fallback_used", None)
    no_fallback_receipt = generate_receipt(
        no_fallback_envelope, {"status": "ok"}, verification_state="verified"
    )
    no_fallback_receipt.pop("fallback_used", None)
    valid, findings = verify_receipt(
        no_fallback_receipt, no_fallback_envelope, {"status": "ok"}
    )
    assert valid, findings
    print("   ✓ missing fallback_used compares as false on both artifacts")

    # 9. Exercise CLI generation/verification and malformed receipt failures.
    print("9. CLI JSON result and malformed-receipt regressions...")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        envelope_path = temp_path / "envelope.json"
        envelope_path.write_text(json.dumps(simple_envelope))

        for index, json_result in enumerate((["ok", 1], 42, False, None)):
            result_path = temp_path / f"result-{index}.json"
            receipt_path = temp_path / f"receipt-{index}.json"
            result_path.write_text(json.dumps(json_result))
            generated = _run_cli(
                "generate-receipt", str(envelope_path), str(result_path), "--state", "verified"
            )
            assert generated.returncode == 0, generated.stdout + generated.stderr
            assert "Traceback" not in generated.stdout + generated.stderr
            receipt_path.write_text(generated.stdout)
            verified = _run_cli(
                "verify", str(receipt_path), "--envelope", str(envelope_path), "--result", str(result_path)
            )
            assert verified.returncode == 0, verified.stdout + verified.stderr
            assert "CONSISTENT" in verified.stdout
            assert "Traceback" not in verified.stdout + verified.stderr

        mismatch_path = temp_path / "mismatch.json"
        mismatch_path.write_text(json.dumps(["different"]))
        mismatch = _run_cli(
            "verify", str(temp_path / "receipt-0.json"), "--envelope", str(envelope_path), "--result", str(mismatch_path)
        )
        _assert_failed_without_traceback(mismatch)

        for name, malformed_receipt in {
            "array": [],
            "string": "not a receipt",
            "null": None,
        }.items():
            receipt_path = temp_path / f"malformed-{name}.json"
            receipt_path.write_text(json.dumps(malformed_receipt))
            malformed = _run_cli(
                "verify", str(receipt_path), "--envelope", str(envelope_path), "--result", str(mismatch_path)
            )
            _assert_failed_without_traceback(malformed)
    print("   ✓ CLI supports all JSON result types and fails malformed inputs cleanly")

    print(f"\n{'=' * 50}")
    print(f"All tests passed. {'No errors.' if errors == 0 else f'{errors} errors.'}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
