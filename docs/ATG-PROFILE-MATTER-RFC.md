# RFC — ATG:MATTER v0.1

Status: DRAFT / PROPOSED / OFFLINE ONLY
Date: 2026-11-24
Owner: ATG (Atralith semantic contract)
Domain owner: proposed DM54, research incubated by SCIENCE54/MATH54

## Purpose

Describe discoverable, verifiable digital resources and deterministic compositions across heterogeneous ledgers and off-chain computation. TAP/TRAC is an optional adapter, not a semantic dependency. This profile is not a physical theory, asset issuer, wallet, bridge, or settlement engine. No economic value or ownership follows from pattern discovery alone.

## Canonical boundaries

ATG defines meaning and vocabulary; DM54 defines domain rules; MATH54 evaluates deterministic discovery/composition; Ontology represents relations; ENTITY54/AGENT-ENTITY references actors and attribution; AEGIS/APEX54 enforce policy and assurance; FISCALITH defines financial meaning; PAYRAIL selects eligible settlement routes and manages authorized settlement. Execution remains behind the existing Execution Envelope and Capability ABI. See [economic boundary](ATG-ECONOMIC-BOUNDARY.md) and [financial bridge](ATRALITH-FISCALITH-BRIDGE-IMPLEMENTATION.md).

## Vocabulary and message semantics

| Concept | Meaning |
| --- | --- |
| SUBSTRATE | Network or authenticated off-chain source |
| ELEMENT | Evidence-derived resource under a versioned rule |
| COMPOUND | Deterministic composition of referenced elements |
| DISCOVER / EXTRACT | Request identification / retrieval of evidence |
| COMPOSE / TRANSFORM | Request rule-bound computation |
| VERIFY | Request independent evidence and finality verification |
| REGISTER | Request persistent resource record |
| MANIFEST | Request authorized token representation, not an issuance grant |
| CONSERVE | Apply explicit consumption, duplication and accounting policy |
| PROVENANCE / FINALITY | Evidence origin and source-specific confirmation state |

Names are provisional semantic vocabulary, not finalized glyphs or registered schemas. Native rendering must round-trip to canonical structured IR without changing semantics.

## Evidence and identity

Source references MUST distinguish chain identity (CAIP-2 where applicable), network/genesis identity as needed, transaction/block/object reference, event or output index, source commitment, rule ID/version, evidence digest, and finality observation. Off-chain sources MUST identify their trust model, artifact digest and attestation references. Unknown namespaces and unsupported proofs fail closed. Source-chain identity is distinct from settlement destination or rail selection.

Proposed resource ID: domain-separated SHA-256 of canonical, versioned content. Canonicalize JSON using RFC 8785 with constrained data types; encode large integers/quantities as canonical decimal strings, never floats. Include source identity, immutable source coordinates, evidence commitment and rule identifier/version. Exclude mutable observation timestamps, current owner, finality status, and transport metadata from identity. Compound IDs commit to rule/version, ordered inputs (or explicitly sorted if commutative), parameters and output index. Verify canonical bytes across independent implementations before adopting this scheme. Hash identity does not prove truth, exclusivity or rights.

## State, verification, and conservation

Proposed evidence states: UNVERIFIED, VERIFIED, REJECTED, REVOKED. Finality is independently recorded as PENDING, FINAL, or INVALIDATED according to source-specific policy, not asserted by the requesting agent. Keep append-only corrections and invalidate dependent compounds after reorgs or revoked attestations. No cross-chain trust by default.

Classify resources as informational/reusable or exclusive/consumable under explicit rule versions. Deduplicate source coordinates and rule claims; use atomic reservations and durable replay keys for exclusive state changes. Informational composition does not consume underlying evidence. Representations are distinct from resource identity; exclusive representations require an authoritative issuance registry, verified lock/burn or equivalent mechanism and reconciliation before destination issuance. No generic bridge assumption.

## Illustrative request (not a registered ATG envelope)

~~~json
{
  "profile": "ATG:MATTER",
  "version": "0.1.0",
  "intent": "COMPOSE",
  "intent_id": "fixture-compose-001",
  "agent_ref": "fixture-agent",
  "rule_ref": "fixture-rule@1",
  "resource_refs": ["fixture-btc-element", "fixture-xrpl-element"],
  "verification": "REQUIRED",
  "execution_enabled": false
}
~~~

This is a domain payload candidate, not authority. Production integration MUST wrap it in the canonical ATG envelope with mandate, policy, capability and receipt requirements; reject unknown fields and unsupported versions at the integration boundary. Any financial payload MUST use the existing FISCALITH contract and integer-money invariants, with no direct provider selection, credentials, custody or spend authority embedded in the MATTER payload.

## Execution corridor

Intent -> ATG Semantic IR -> actor/mandate -> policy/authority -> Execution Envelope candidate -> approved Capability ABI adapter -> result/evidence -> receipt -> verification/audit. Discovery never authorizes issuance, ownership changes, spending, publication or transfer. Explicit denial receipts and idempotency/replay controls required. No mainnet, wallet signing, paid RPC, bridge or minting in P0.

## P0 acceptance criteria

- Offline fixtures for Bitcoin, XRPL and an EVM network, plus optional off-chain evidence; adapters normalize without changing ATG semantics.
- Independent replay produces identical canonical resource/compound IDs.
- Negative fixtures reject malformed commitments, unsupported source/rule versions, duplicate exclusive claims, forged authority, unknown fields, missing finality and revoked/reorganized evidence.
- Cross-network compound simulation works without a wallet or bridge.
- Verify that existing ATG profiles, economic boundary and Atralith rendering behavior remain unchanged.
- Document receipt/evidence schema and version negotiation; record test commands, results, fixture hashes and limitations.
- EXECUTION_ENABLED=false and MAINNET_ALLOWED=false throughout P0.

## Ownership and rollout

Incubate domain algebra and fixtures in SCIENCE54/MATH54; use TESTNET54 for offline proof. A dedicated DM54 repository is optional until protocol ownership, shared schemas/adapters and conformance tests justify independent versioning. Keep ATG profile in ATG regardless of DM54 repo placement. Ontology, ENTITY54, APEX54, PAYRAIL and Docking District integrations follow separately reviewed proposals. No external dependency or third-party partnership is asserted.

## Open decisions

Canonical schema integration and registry path; resource naming namespace; proof/finality policy by adapter; issuance and exclusive accounting authority; rule registry governance; licensing and source rights; independent conformance implementation. No schema registration, runtime implementation, or deployment is claimed by this RFC.
