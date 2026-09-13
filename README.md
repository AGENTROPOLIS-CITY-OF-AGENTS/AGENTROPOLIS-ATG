# AGENTROPOLIS ATG

**ATG — Agent Transaction Grammar — is the canonical semantic protocol and agent-language contract for AGENTROPOLIS.**

ATG defines how autonomous agents express and exchange identity, intent, capabilities, mandates, authority, policy, routing, state, evidence, provenance, receipts, reputation, and economic meaning across runtimes, tools, districts, applications, and external systems.

> **ATG tells agents how to communicate, negotiate, execute, and prove. Atralith gives AGENTROPOLIS its native agent-language and reference implementation surface.**

ATG is implementation-neutral. No browser provider, model, runtime, chain, district, or application may redefine ATG semantics by itself.

## Canonical relationship

| Layer | Role |
|---|---|
| **ATG** | Open semantic protocol, normative contracts, schemas, authority semantics, receipts, compatibility and domain profiles |
| **Atralith** | Native AGENTROPOLIS agent language and reference implementation/runtime surface for ATG |
| **ATG LANGUAGE** | Atralith-visible language profile derived from structured Semantic IR |
| **Domain profiles** | Bounded extensions such as ATG:SIGNAL, ATG:VERIFY, ATG:IP, ATG:MARKET, ATG:AGENT-LINK, ATG:BROADCAST and ATG:ARCANA54 |
| **Adapters** | Provider/runtime implementations that execute ATG-authorized work without owning the protocol |

## Core execution corridor

```text
HUMAN / AGENT INTENT
        ↓
ATG SEMANTIC IR
        ↓
IDENTITY + MANDATE
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

Authority is never implied by presentation, model confidence, connectivity, a discovered tool, a browser session, a wallet connection, or a social message. Material actions require explicit, scoped ATG authority.

## What ATG owns

- normative message types and schemas
- identity and capability declarations
- mandates and authority semantics
- risk and policy expression
- execution envelopes
- capability ABI contracts
- routing and handoff semantics
- state and status semantics
- evidence and provenance requirements
- receipt requirements and verification states
- economic authority and settlement profiles
- compatibility tests and protocol governance
- Atral Script mappings and ATG LANGUAGE profiles
- domain-profile registration and namespace rules

## Atralith

Atralith is the native AGENTROPOLIS agent-language and reference implementation surface for ATG.

Atralith may provide SDKs, validators, mandate builders, envelope tooling, receipt generation and verification, capability discovery, adapters, settlement implementations, CLI/runtime services, and native visual language rendering.

ATG remains the standard. Atralith conforms to ATG.

See:

- `docs/PROTOCOL_VS_AGENT_KIT.md`
- `docs/ATG-PROFILE-LANGUAGE.md`

## Domain profiles

ATG domain profiles extend the canonical protocol without forking it.

Current and emerging profiles include:

- **ATG:SIGNAL** — signed signals, provenance and event semantics
- **ATG:VERIFY** — verification ingress, evidence and result-state semantics
- **ATG:IP** — intellectual-property authority and rights-scope semantics
- **ATG:MARKET** — governed market evidence and market-action semantics
- **ATG:AGENT-LINK** — agent linking and cross-runtime relationship semantics
- **ATG:BROADCAST** — campaign, KOL, channel, broadcast and attribution semantics
- **ATG:ARCANA54** — programmable-story-world domain vocabulary
- **ATG LANGUAGE** — Atralith native visible language surface

A domain profile may add vocabulary and constraints. It may not silently weaken identity, mandate, policy, authority, receipt, provenance, or verification rules.

## Broadcast and GTM

The persistent campaign, KOL/influencer, distribution, attribution, Social Systems, ATV Network, BotBae, Pixelshop, Chaos Mira and BUZZ integration remains valid functionality, but it is a **consumer/profile of ATG**, not the definition of ATG itself.

See `docs/ATG-PROFILE-BROADCAST.md`.

## Web Action Fabric

ATG also defines the semantic contract for governed web execution.

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
- presentation, Atralith glyphs, UI labels, browser state and model output do not grant authority
- engagement, popularity or economic upside never changes truth-state

## Standing rule

> **ATG is the language contract. Atralith is how the agent city speaks and implements it. Profiles specialize it. Adapters execute it. Receipts prove what happened.**
