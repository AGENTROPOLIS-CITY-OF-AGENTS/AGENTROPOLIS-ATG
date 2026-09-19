# AGENTROPOLIS ATG

**ATG is the Atralith agentic language and canonical semantic contract for AGENTROPOLIS.**

ATG defines how autonomous agents express and exchange identity references, intent, capabilities, mandates, authority references, policy constraints, routing intent, state, evidence, provenance, receipts, reputation, and economic meaning across runtimes, tools, districts, applications, and external systems.

> **ATG tells agents how to communicate, negotiate, express execution meaning, and prove. It does not choose settlement rails, grant itself authority, or become the economic execution engine.**

ATG is implementation-neutral. No browser provider, model, runtime, chain, settlement rail, district, or application may redefine ATG semantics by itself.

See [`docs/ATG-ECONOMIC-BOUNDARY.md`](docs/ATG-ECONOMIC-BOUNDARY.md) for the canonical economic separation.

The executable ATRALITH↔FISCALITH bridge lives in
[`atralith/fiscalith_bridge.py`](atralith/fiscalith_bridge.py) — see
[`docs/ATRALITH-FISCALITH-BRIDGE-IMPLEMENTATION.md`](docs/ATRALITH-FISCALITH-BRIDGE-IMPLEMENTATION.md).
Canonical naming migration requirements are in
[`docs/AGENT-ENTITY-NAMING-MIGRATION.md`](docs/AGENT-ENTITY-NAMING-MIGRATION.md).

## Canonical relationship

| Layer | Role |
|---|---|
| **ATG** | Atralith agentic language, semantic contracts, schemas, authority references, receipts, compatibility and domain profiles |
| **ATG LANGUAGE surface** | Human-visible/native rendering derived from structured Semantic IR |
| **Domain profiles** | Bounded extensions such as ATG:SIGNAL, ATG:VERIFY, ATG:IP, ATG:MARKET, ATG:AGENT-LINK, ATG:BROADCAST and ATG:ARCANA54 |
| **Adapters** | Provider/runtime implementations that execute authorized work without owning language semantics |

## Core execution corridor

```text
HUMAN / AGENT INTENT
        ↓
ATG SEMANTIC IR
        ↓
AGENT-ENTITY + MANDATE REFERENCES
        ↓
POLICY + AUTHORITY
        ↓
EXECUTION ENVELOPE
        ↓
CAPABILITY ABI
        ↓
APPROVED ADAPTER / RUNTIME
        ↓
RESULT + EVIDENCE
        ↓
RECEIPT
        ↓
VERIFICATION + AUDIT
```

Authority is never implied by presentation, model confidence, connectivity, a discovered tool, a browser session, a wallet connection, or a social message. Material actions require explicit, scoped authority enforced outside language presentation.

## What ATG owns

- normative message types and schemas
- identity and capability declarations
- mandate and authority-reference semantics
- risk and policy expression
- execution-envelope semantics
- capability ABI contracts
- routing intent and handoff semantics
- state and status semantics
- evidence and provenance requirements
- receipt requirements and verification states
- economic intent and settlement-requirement semantics
- compatibility tests and language/protocol governance
- Atral Script mappings and visible language profiles
- domain-profile registration and namespace rules

## What ATG does not own

- settlement-rail selection
- treasury or custody
- raw signing credentials
- wallet authority
- AGENT-ENTITY persistent state
- runtime authority merely because an adapter is connected

Economic intent expressed in ATG crosses into the AGENTROPOLIS Economic Fabric. PAYRAIL evaluates eligible settlement routes after policy and authority checks. Arc, Base, XRPL, bank rails, and future providers remain replaceable settlement adapters.

## Domain profiles

ATG domain profiles extend the canonical language contract without forking it.

Current and emerging profiles include:

- **ATG:SIGNAL** — signed signals, provenance and event semantics
- **ATG:VERIFY** — verification ingress, evidence and result-state semantics
- **ATG:IP** — intellectual-property authority and rights-scope semantics
- **ATG:MARKET** — governed market evidence and market-action semantics
- **ATG:AGENT-LINK** — agent linking and cross-runtime relationship semantics
- **ATG:BROADCAST** — campaign, KOL, channel, broadcast and attribution semantics
- **ATG:ARCANA54** — programmable-story-world domain vocabulary
- **ATG LANGUAGE** — native visible language surface

A domain profile may add vocabulary and constraints. It may not silently weaken identity, mandate, policy, authority, receipt, provenance, verification, or settlement-routing boundaries.

## Broadcast and GTM

The persistent campaign, KOL/influencer, distribution, attribution, Social Systems, ATV Network, BotBae, Pixelshop, Chaos Mira and BUZZ integration remains valid functionality, but it is a **consumer/profile of ATG**, not the definition of ATG itself.

See `docs/ATG-PROFILE-BROADCAST.md`.

## Web Action Fabric

ATG defines the semantic contract for governed web execution.

WebMCP, Browser Use, Hermes Browser/Desktop, Chromium/CDP, deterministic browser automation, computer-use models and future providers are execution adapters behind the same authority corridor.

```text
DISCOVER
  ↓
ATG CAPABILITY DECLARATION
  ↓
MANDATE + POLICY + AEGIS / IRON GATE
  ↓
WEB ACTION EXECUTION ENVELOPE
  ↓
ADAPTER
  ↓
OBSERVE → ACT → OBSERVE → VERIFY
  ↓
RECEIPT
```

Discovery is not authority. Connectivity is not permission. Execution adapters do not govern themselves.

See `docs/ATG-WEB-ACTION-FABRIC.md`.

## Security invariants

- authority is a runtime constraint, not a prompt
- credentials are referenced and injected by approved boundaries, not embedded in ATG messages
- high-impact actions require explicit policy and approval paths
- every consequential action must be receiptable
- denied actions require explicit denial state
- adapters must fail closed when required authority is missing or ambiguous
- presentation, glyphs, UI labels, browser state and model output do not grant authority
- engagement, popularity or economic upside never changes truth-state
- settlement connectivity never gives ATG routing authority

## Standing rule

> **AGENT-ENTITY defines the actor. ATG defines the meaning. The Execution Envelope bounds the action. Capability infrastructure executes. The Economic Fabric and PAYRAIL decide how approved value moves. Settlement adapters execute. Receipts prove what happened.**
