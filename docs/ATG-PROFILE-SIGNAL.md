# ATG SIGNAL Profile

Status: Draft
Version: 0.1.0

## Purpose

ATG SIGNAL defines how AGENTROPOLIS artifacts carry governed authenticity, provenance, and verification evidence without turning watermarking into a covert command or data-exfiltration surface.

Core rule:

> Provenance is authoritative. Watermarking is supporting evidence.

ATG SIGNAL is implementation-neutral. It may be backed by signed manifests, detached signatures, statistical text watermarking, robust media watermarking, C2PA-compatible content credentials, or future registered mechanisms, but no mechanism may expand authority or encode arbitrary hidden payloads.

## Security invariants

Conforming implementations MUST enforce all of the following:

- arbitrary covert payloads are forbidden
- user-specific identity tracking is forbidden by default
- raw secrets, credentials, prompts, URLs, commands, wallet instructions, or executable content MUST NOT be encoded in a watermark
- verification MUST NOT execute artifact content
- watermark presence MUST NOT confer execution authority
- model output remains untrusted until normal ATG / 54-T policy checks complete
- code provenance MUST use cryptographic manifests/signatures rather than token-choice manipulation
- signing keys MUST remain outside model context and be exposed only through scoped signing capability handles
- key rotation, revocation, and versioning MUST be supported
- verification confidence and provenance state MUST be recorded separately

## Signal classes

### signed_manifest
Primary provenance authority for all artifact classes.

### detached_signature
Cryptographic signature over artifact and/or manifest digests.

### statistical_text
Optional secondary evidence for natural-language text. The signal SHOULD answer only whether content is statistically consistent with a registered ATG generation profile. It MUST NOT carry arbitrary data.

### robust_media
Optional secondary evidence embedded in image, audio, video, 3D, or mixed-media artifacts. It MUST NOT carry executable semantics or hidden arbitrary payloads.

### none
Explicitly records that no embedded signal was applied. Provenance may still be established by signed manifests and receipts.

## Artifact corridor

```text
Human or Agent Intent
        -> ATG mandate / capability resolution
        -> policy / risk / 54-T verification
        -> generation or transformation
        -> artifact digest
        -> signed provenance manifest
        -> optional ATG SIGNAL embedding
        -> verification
        -> ATG receipt / audit ledger
        -> downstream use
```

Downstream use requires its own authority check. A valid ATG SIGNAL does not authorize execution, publication, spending, messaging, or tool access.

## Verification states

A conforming verifier may report:

- `verified` - cryptographic provenance and digest checks succeeded
- `consistent` - secondary watermark evidence is statistically or robustly consistent
- `inconsistent` - secondary evidence conflicts with the claimed profile
- `unknown` - insufficient evidence
- `tampered` - manifest/signature/digest evidence indicates modification
- `expired` - key or profile epoch expired
- `revoked` - signing/profile authority was revoked
- `not_checked` - no verification performed

A statistical watermark alone SHOULD NOT produce `verified`; it should normally produce `consistent` at most.

## Privacy model

ATG SIGNAL MUST NOT encode personal identity, IP address, device identifier, account identifier, prompt contents, conversation identifier, or secret material into the embedded signal unless a future explicit privacy-reviewed profile is created. Version 0.1.0 forbids identity encoding entirely.

Receipts may contain governed principal or district references outside the artifact when policy permits. Those references remain in the provenance system, not in the watermark carrier.

## Anti-covert-channel rule

ATG SIGNAL exposes no general-purpose API equivalent to:

```text
watermark(payload=<arbitrary bytes>)
```

A conforming encoder accepts a registered signal profile and artifact context only. The embedded signal is bounded to authenticity/provenance classification and SHALL NOT transport arbitrary user or agent data.

This prevents ATG SIGNAL from becoming an endorsed steganographic command bus.

## Code artifacts

Source code, bytecode, scripts, manifests, and infrastructure-as-code MUST NOT be modified for the purpose of statistical token-choice watermarking.

For code, use:

- artifact digest
- signed provenance manifest
- detached signature
- build attestation when applicable
- ATG receipt

This avoids introducing syntax, semantic, formatting, reproducibility, or supply-chain risk merely to preserve an embedded signal.

## Keys and signing

Signing and watermark detector/encoder keys MUST be managed by sealed infrastructure.

Agents and models receive capability handles such as:

- `provenance.sign`
- `provenance.verify`
- `signal.embed.text`
- `signal.embed.media`
- `signal.detect.text`
- `signal.detect.media`

They do not receive raw key material.

Every key profile SHOULD include a version and key epoch and MUST support revocation.

## 54-T integration

ATG SIGNAL adds a specific covert-generative-channel check to the normal 54-T security corridor.

54-T SHOULD detect or flag:

- unregistered statistical token-selection schemes
- suspicious model-to-model signaling
- artifact transformations designed to smuggle hidden commands
- watermark implementations with arbitrary payload support
- attempts to encode secrets or identity in embedded signals
- attempts to treat verification as execution authority
- detector or signing-key access outside sealed infrastructure

## Ingest Membrane behavior

External artifacts are sensors only.

On ingest:

1. compute artifact digest
2. inspect available provenance manifest/signature
3. detect registered ATG SIGNAL profiles when applicable
4. record verification state and confidence
5. pass artifact through ordinary content, policy, and risk checks
6. prohibit automatic execution based solely on provenance or watermark status
7. issue an ingest receipt

A valid provenance signature says who/what signed an artifact. It does not say the artifact is safe.

## Receipts

An ATG SIGNAL receipt SHOULD include:

- artifact identifier and digest
- media class
- generator/model class and version when available
- signal profile and version
- key epoch
- manifest/signature references
- verification state
- confidence for statistical/robust detection where applicable
- policy state
- tamper/revocation state
- parent artifact references for transformations
- audit reference

## Interoperability

ATG SIGNAL SHOULD prefer open provenance standards where suitable. C2PA-compatible content credentials may be used as one signed-manifest representation, but ATG core semantics must not depend on C2PA or any single vendor.

Embedded watermark providers are adapters, not constitutional dependencies.

## Non-goals

ATG SIGNAL does not:

- promise perfect attribution
- make generated content impossible to rewrite or strip
- detect all AI-generated content
- authorize tool use
- classify content as truthful or safe merely because provenance verifies
- expose a steganography service
- identify a human user through hidden artifact data

## Canonical principle

> ATG SIGNAL proves lineage where possible, indicates origin where useful, and never turns hidden structure into hidden authority.
