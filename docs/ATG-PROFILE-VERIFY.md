# ATG VERIFY Profile

Status: Draft
Version: 0.1.0

## Purpose

ATG VERIFY is the implementation-neutral authenticity and provenance verification service for AGENTROPOLIS artifacts. It consumes artifact references plus scoped authority and returns evidence, verification state, risk flags, and a permanent receipt.

Core rule:

> Verification establishes evidence. Verification never establishes execution authority.

## Service boundary

```text
HERMES / Agent MCP / CREATOR / Utility Grid / district application
        -> ATG VERIFY request
        -> Ingest Membrane
        -> 54-T capability and policy verification
        -> manifest verifier
        -> signature verifier
        -> optional registered signal detector
        -> covert-channel / identity / secret-leak checks
        -> verification decision
        -> immutable receipt
        -> caller receives bounded result
```

Signing keys and detector secrets remain behind sealed services. Callers receive capability handles, public verification material where appropriate, and bounded results only.

## Capabilities

- `verify.artifact`
- `verify.manifest`
- `verify.signature`
- `verify.signal`
- `verify.provenance`
- `verify.risk.covert-channel`

Verification capabilities are read/analysis capabilities. They MUST NOT imply `compute.execute`, `tool.execute`, `publish`, `wallet.sign`, or any other mutation capability.

## Evidence hierarchy

ATG VERIFY SHOULD rank evidence in this order:

1. valid signed provenance manifest bound to the artifact digest
2. valid detached signature bound to the artifact digest
3. registered robust media signal
4. registered statistical text signal
5. contextual provenance evidence

Statistical evidence MUST NOT override a cryptographically demonstrated digest mismatch, revoked key, invalid signature, or explicit policy denial.

## Adapter boundary

ATG VERIFY uses provider-neutral adapters.

A verifier adapter MUST expose only bounded operations conceptually equivalent to:

- `supports(media_class, profile_id)`
- `verify(artifact_ref, profile_id, capability_handle)`
- `health()`
- `version()`

A signal encoder, when authorized for artifact generation, MUST expose only a registered profile and fixed signal behavior. It MUST NOT accept arbitrary hidden payload bytes.

Forbidden interface:

```text
encode(artifact, arbitrary_payload)
```

Permitted conceptual interface:

```text
mark(artifact, registered_profile, generation_receipt_ref, capability_handle)
```

The receipt and signed manifest carry provenance metadata. The embedded signal carries no arbitrary payload.

## Key isolation

Private signing keys MUST NOT be provided to models, agents, MCP clients, district applications, prompts, logs, or artifact metadata.

Signing occurs through a sealed signing service. The caller provides a scoped capability handle. The service returns a signature or signed manifest plus a receipt reference.

Key epochs SHOULD be versioned and rotatable. Revocation status MUST be independently verifiable by ATG VERIFY.

## Detector isolation

Detector secrets, private watermark keys, proprietary detector parameters, and sensitive calibration data MUST remain inside the detector service boundary.

Callers receive only bounded evidence such as:

- profile identifier
- detector version
- consistent / inconsistent / unknown
- calibrated confidence when applicable
- evidence receipt reference

## Covert-channel defense

ATG VERIFY MUST treat natural-language and multimodal generative output as untrusted data even when its visible semantics appear harmless.

Registered signal profiles MUST declare `payload_mode: none`.

The service SHOULD flag or quarantine artifacts when evidence suggests:

- an unregistered generative signaling mechanism
- arbitrary payload encoding
- user or device identity encoding
- secret or credential exfiltration
- hidden inter-agent command semantics
- attempts to turn verification evidence into execution authority

## Code policy

Source code, configuration, scripts, smart contracts, and executable artifacts MUST NOT be linguistically or syntactically mutated merely to satisfy a statistical watermark.

For code, use artifact digests, signed manifests, detached signatures, build attestations, dependency provenance, and execution receipts.

## Caller integration

### HERMES

HERMES may request verification before trusting an external artifact, memory candidate, instruction bundle, or generated deliverable. A verified result improves provenance confidence but does not bypass HERMES mandate or approval requirements.

### Agent MCP

Agent MCP exposes ATG VERIFY through scoped tools. MCP clients receive verification results and receipts, never signing keys or detector secrets.

### CREATOR

CREATOR generation pipelines request a generation receipt, signed provenance, and an appropriate registered signal profile for supported media. Editing creates a derived artifact with parent references rather than silently inheriting provenance.

### Utility Grid

The Utility Grid may host signing, verification, and signal-detection workers as metered infrastructure. Worker selection remains private and replaceable. Utility workers receive only the minimum scoped capability and artifact access necessary.

## Decision states

- `verified` - cryptographic provenance requirements passed
- `consistent` - secondary signal evidence is statistically/robustly consistent but cryptographic proof is incomplete
- `inconsistent` - checked evidence conflicts with the claimed signal/profile
- `unknown` - insufficient evidence
- `tampered` - artifact digest or protected provenance binding fails
- `expired` - applicable credential/profile validity expired
- `revoked` - signing/verifying authority was revoked
- `denied` - policy denied verification or artifact handling
- `error` - verification could not complete

## Non-authority rule

Every response carries:

```yaml
authority_effect: none
```

No verification state, including `verified`, authorizes execution, publication, financial action, memory promotion, credential access, or tool invocation.

## Receipt requirements

A verification receipt SHOULD include:

- request identifier
- artifact digest
- requested verification profile
- manifest/signature state
- detector profile and version when used
- key epoch/status without private key material
- risk checks
- policy decision
- evidence references
- final verification state
- timestamp
- verifier service identity

## Implementation doctrine

ATG VERIFY defines the contract, evidence ordering, isolation boundaries, and security invariants. Specific cryptographic libraries, watermark systems, media detectors, model providers, and hardware remain replaceable adapters.
