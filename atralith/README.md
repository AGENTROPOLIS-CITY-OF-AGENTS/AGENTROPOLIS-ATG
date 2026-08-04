# ATRALITH-lite

ATRALITH-lite is the first working slice of the ATRALITH Agent Kit — a reference
implementation of ATG mandate, envelope, and receipt primitives.

It implements a structural RFC-0001 (Trusted Authorization Path) reference
slice: build mandates, construct authorization envelopes, generate receipts, and
cross-check receipt claims and hashes against supplied artifacts. It does not
perform cryptographic signing or verify signer authenticity.

## What it does

| Module | Function | Purpose |
|--------|----------|---------|
| `atralith.mandate` | `build_mandate()` | Build and validate an ATG mandate against the normative schema |
| `atralith.envelope` | `sign_envelope()` | Construct an authorization envelope separating proposal from authority |
| `atralith.receipt` | `generate_receipt()` | Generate a receipt binding mandate → payload → result |
| `atralith.receipt` | `verify_receipt()` | Check receipt structure and supplied artifact claims/hashes |

Every function validates its output against the normative JSON Schema 2020-12
contracts in `contracts/core/`.

## Quick start

```python
from atralith.mandate import build_mandate
from atralith.envelope import sign_envelope
from atralith.receipt import generate_receipt, verify_receipt

# 1. Build a mandate
mandate = build_mandate(
    agent_id="agent:cityflight-01",
    action_type="cityflight",
    enforcement="enforced",
    issued_by="principal:tony",
)

# 2. Construct an authorization envelope
envelope = sign_envelope(
    mandate=mandate,
    payload={"action": "deploy", "artifact_id": "img_7f3a"},
    authorization_class="A3_IRREVERSIBLE",
    authorizer="signer:treasury-01",
    signer_type="hardware_signer",
)

# 3. Generate a receipt
receipt = generate_receipt(
    envelope=envelope,
    result={"status": "deployed", "tx": "0x..."},
    verification_state="deployed",
)

# 4. Verify structural/hash consistency against independently supplied evidence
valid, findings = verify_receipt(receipt, envelope, {"status": "deployed"})
assert valid, findings
```

## CLI

```bash
# Build a mandate
python3 -m atralith.cli build-mandate "agent:test" "read" --issued-by "principal:tony"

# Construct an envelope
# `sign-envelope` is a legacy command name; it does not create a cryptographic signature.
python3 -m atralith.cli sign-envelope mandate.json payload.json --auth-class A2_BOUNDED

# Generate a receipt
python3 -m atralith.cli generate-receipt envelope.json result.json --state deployed

# Verify
python3 -m atralith.cli verify receipt.json --envelope envelope.json --result result.json
```

Successful verification means the receipt structure and supplied artifact
hashes/claims are consistent. It does not verify signer identity, cryptographic
authorization, or cryptographic validity of `receipt_chain` entries.

## Smoke test

```bash
python3 atralith/smoke_test.py
```

Runs a full CITYFLIGHT pipeline: mandate → envelope → receipt → structural/hash
verification → tamper detection.

## Dependencies

- Python ≥ 3.10
- `jsonschema[format]` ≥ 4.18 (`pip install "jsonschema[format]>=4.18"`)

No other dependencies. No network access during operation.

## Status

ATRALITH-lite is a **reference implementation** — it demonstrates the ATG
protocol in working code. It is not the full ATRALITH Agent Kit. It does not
include MCP server, signing device adapters, policy engines, or settlement.

## License

Apache 2.0 — same as AGENTROPOLIS-ATG.
