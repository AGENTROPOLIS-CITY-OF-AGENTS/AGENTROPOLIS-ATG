# ATG LINK Profile — Agent Link

Status: Draft
Version: 0.1.0

## Purpose

ATG LINK defines `LINK` as the Agentropolis language primitive for creating a governed relationship between an agent identity and an external surface, workspace, device, application, or peer.

Agent Link is the public reference implementation of this profile.

The human-facing experience may use visual controls and English. The authoritative source is a validated ATG semantic object that compiles into an Execution Envelope and then into a surface-specific binding.

Core rule:

> Pairing establishes a connection. The Execution Envelope establishes authority.

## Public language

A simple Agent Link may render as:

```text
LINK NEURO TO TELEGRAM
ALLOW MESSAGE.READ, MESSAGE.REPLY
GATE GITHUB.DEPLOY
DENY FUNDS.*
VERIFY PASSKEY
UNTIL 30D
RECEIPT REQUIRED
```

The keywords are deliberately small and teach the authority model while the user connects an agent:

- `LINK` — establish a bounded relationship
- `ALLOW` — capability may be exercised inside the compiled envelope
- `GATE` — capability requires an approval step
- `DENY` — capability is explicitly prohibited
- `VERIFY` — required identity/authentication ceremony
- `UNTIL` — expiry or lease duration
- `RECEIPT` — proof requirement for the link lifecycle

## Semantic IR

The source of truth is structured data, not the displayed sentence or glyph rendering.

```json
{
  "version": "1.0.0",
  "link_id": "link:neuro:telegram:example",
  "principal": "identity:owner",
  "agent": "agent:neuro-chief-of-staff",
  "target": {
    "surface": "telegram",
    "account": "@example"
  },
  "authority": {
    "allow": ["message.read", "message.reply"],
    "gate": ["github.deploy"],
    "deny": ["funds.*"]
  },
  "verification": {
    "method": "passkey"
  },
  "pairing": {
    "mechanism": "agent-seal"
  },
  "ttl_seconds": 2592000,
  "receipt_required": true
}
```

## Pairing mechanisms

Agent Link is a protocol, not a QR format. Pairing transports are replaceable.

Initial mechanisms:

- `agent-seal` — short-lived signed visual handshake with no embedded bearer credential or URL
- `link-code` — short-lived human-entered code identifying a pending link request
- `native-handoff` — platform/app authorization handoff
- `nfc` — proximity bootstrap where supported
- `qr` — optional compatibility transport; never the authority source

A captured pairing artifact MUST NOT be sufficient to exercise the link. Verification and envelope compilation are independent gates.

## Compile pipeline

```text
Human intent / visual controls
        ↓
ATG LINK semantic IR
        ↓ validate
Identity verification
        ↓
ATG policy + risk compilation
        ↓
Execution Envelope
        ↓
Surface binding
        ├── BOTBAE
        ├── Hermes
        ├── BUZZ
        └── future consumers
        ↓
Health verification
        ↓
Link Receipt
        ↓
Audit Ledger
```

Risk is assigned during policy compilation. The executing agent MUST NOT self-classify or expand its own risk tier.

## Surface consumers

The same LINK object may target:

- Telegram
- Discord
- Slack
- WhatsApp
- Web
- BUZZ
- Hermes Desktop/mobile
- GitHub or other tool surfaces
- another agent or runtime
- future Agentropolis applications

Surface adapters translate the compiled envelope into platform-specific scopes and configuration. They do not reinterpret authority.

## Human adoption pattern

Agent Link is intended to make ATG useful before a person decides to learn ATG.

Recommended UI behavior:

1. show plain-English controls;
2. render the equivalent ATG statement directly beneath them;
3. keep visual controls and ATG source synchronized in both directions;
4. explain `ALLOW`, `GATE`, and `DENY` in normal language;
5. compile only after explicit verification/approval;
6. show the final receipt and expiry.

Example:

```text
Connect NEURO to Telegram
Messages: Read + Reply
Deployments: Ask me first
Money: No access
Duration: 30 days

LINK NEURO TO TELEGRAM
ALLOW MESSAGE.READ, MESSAGE.REPLY
GATE GITHUB.DEPLOY
DENY FUNDS.*
UNTIL 30D
```

## Safety invariants

- `LINK` never carries raw secrets, private keys, API keys, or bearer credentials.
- A message, mention, DM, role, reaction, or social event never grants authority.
- Pairing success is not authorization success.
- Surface adapters request the minimum scopes derived from the compiled envelope.
- `DENY` is fail-closed and overrides ambiguous or missing grants.
- High-impact capabilities may require step-up human approval even after a link exists.
- Every successful, failed, expired, revoked, or denied link produces a receipt when policy requires it.
- Revocation terminates the relationship and invalidates active link grants; applicable credentials are rotated by the owning surface/runtime.

## Relationship to ATG LANGUAGE

ATG LANGUAGE may render LINK events in Atralith, but presentation does not create authority. English and Atralith are observer/native renderings of the same semantic IR.

Recommended semantic classes:

- link request: `INTENT`
- target routing: `ROUTE`
- allow/gate/deny: `AUTHORITY`
- verification state: `STATE`
- link receipt: `PROVENANCE`
- expiry: `TIME`

## Canonical principle

> Pair once. Govern every surface. Carry the agent, not the credentials.
