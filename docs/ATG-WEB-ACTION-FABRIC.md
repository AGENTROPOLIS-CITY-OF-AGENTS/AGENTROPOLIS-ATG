# ATG Web Action Fabric

Status: Production candidate
Version: 0.1.0

## Purpose

The Web Action Fabric is the provider-neutral ATG contract for agents that discover, navigate, observe, interact with and verify web interfaces.

Browser providers are adapters. ATG owns semantic intent, authority, policy, evidence and receipts.

Initial adapter families may include:

- WebMCP
- Browser Use
- Hermes Browser/Desktop
- Chromium/CDP or Playwright-class deterministic automation
- computer-use / visual interaction models
- future browser and GUI execution providers

No adapter becomes canonical merely because it is connected or capable.

## Canonical flow

```text
DISCOVER
  -> CAPABILITY DECLARATION
  -> IDENTITY + MANDATE
  -> RISK / POLICY CLASSIFICATION
  -> EXECUTION ENVELOPE
  -> ADAPTER SELECTION
  -> OBSERVE
  -> ACT
  -> OBSERVE
  -> VERIFY
  -> RECEIPT
  -> AUDIT
```

## Web Action Envelope

A web action SHOULD resolve to a structured envelope containing at least:

```json
{
  "profile": "ATG:WEB_ACTION",
  "version": "0.1.0",
  "action_id": "wa_...",
  "correlation_id": "corr_...",
  "principal": "agent-or-human-principal",
  "mandate_ref": "mandate_...",
  "intent": "navigate|read|search|click|type|upload|download|submit|purchase|publish|delete|authenticate",
  "target": {
    "origin": "https://example.com",
    "resource": "logical-resource-or-route"
  },
  "risk_tier": "observe|low|material|high",
  "authority": {
    "mode": "read_only|bounded_write|approval_required",
    "scope": []
  },
  "adapter": {
    "family": "browser-use|webmcp|hermes|cdp|computer-use|other",
    "capability_ref": "cap_..."
  },
  "evidence_requirements": [],
  "receipt_required": true
}
```

## Adapter contract

Every adapter MUST expose enough metadata for the router to evaluate:

- supported actions
- deterministic vs probabilistic interaction mode
- authentication requirements
- session isolation characteristics
- file upload/download capability
- visual observation capability
- DOM/structured observation capability
- write/destructive action support
- cost and latency metadata when available
- evidence capture capability
- cancellation/timeout behavior
- health state

## Routing principles

Prefer the least-powerful adapter that can safely complete the mandate.

Suggested ordering is capability- and policy-dependent rather than vendor-dependent:

1. structured/native interface when available
2. deterministic browser automation
3. agentic browser execution
4. visual/computer-use execution when structure is unavailable
5. human escalation when confidence or authority is insufficient

The router may change providers without changing the ATG mandate.

## Risk gates

### Observe

Examples: open, read, inspect, search, screenshot, extract public information.

May execute under read-only authority when policy permits.

### Low-impact write

Examples: bounded form entry, draft creation, non-public workspace edits.

Requires scoped write authority and receipt.

### Material action

Examples: send, publish, submit an application, modify account state, create an external record, upload sensitive material.

Requires explicit material-action authority and verification.

### High-impact action

Examples: purchase, transfer value, execute trades, delete material data, change security settings, expose secrets, create irreversible public/legal commitments.

Requires explicit high-impact policy, human approval where configured, verification and durable receipt.

## Authentication and secrets

ATG messages MUST NOT contain raw passwords, private keys, seed phrases or unrestricted bearer tokens.

Adapters receive credential references through approved secret boundaries. Sessions SHOULD be isolated by principal, mandate and risk tier where practical.

## Observe-act-observe-verify

An agentic browser action is not complete after a click or submit event.

The adapter must collect post-action state sufficient to determine whether the intended result occurred. Verification evidence may include structured DOM state, URL/route state, application confirmation, generated resource identifiers, screenshots, downloaded artifacts, response metadata or provider-native receipts.

## Receipt minimum

A Web Action Receipt SHOULD contain:

- action and correlation IDs
- principal and mandate reference
- adapter/provider identity and version when known
- target origin/resource
- requested intent
- actual actions performed
- timestamps
- authority/risk decision references
- pre/post observations or hashes/references
- verification result
- artifacts created or modified
- cost/usage metadata when available
- denial, timeout, cancellation or escalation state

## Invariants

> Discovery is not authority.

> Connectivity is not permission.

> A successful click is not a verified result.

> Provider capability does not expand mandate scope.

> Browser state does not override ATG policy.

> Consequential web actions must be receiptable and auditable.

## Consumers

The Web Action Fabric may be consumed by CREATOR, CREATOR-CORE, Arcana54, Holofoil, BotBae, Hermes, Mission Control, District operators, the Utility Grid and future AGENTROPOLIS applications across both organizations.
