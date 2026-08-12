# AGENTROPOLIS-ATG

**Agent Transaction Grammar for autonomous systems.**

AGENTROPOLIS-ATG is an open semantic protocol for agent identity, capability discovery, mandates, authority, evidence, receipts, reputation, and economic exchange.

> **ATG tells agents how to communicate. ATRALITH gives them the software to do it.**

## Public site — WebGPU Intelligence Grid

The public landing page is a scroll-directed **Intelligence Grid** control-plane experience:

- cinematic 3D AGENTROPOLIS city behind the protocol UI
- Three.js `WebGPURenderer` with vendored builds (no CDN on the production page)
- automatic **WebGL2** fallback when WebGPU is unavailable
- **STATIC** CSS sky fallback if renderer initialization fails
- five colored districts, central governance spire, atmospheric particles, and orbiting protocol ring
- scroll-keyed camera stages with subtle pointer parallax
- interactive 24-glyph canonical Atranic alphabet
- simulated mandate compiler console

### Renderer modes

| Badge   | Meaning |
|---------|---------|
| `WEBGPU` | Preferred path via Three.js WebGPURenderer |
| `WEBGL2` | Automatic backend fallback inside WebGPURenderer |
| `STATIC` | Canvas hidden; CSS atmosphere remains; site content still works |

### Browser requirements

- Modern Chromium, Firefox, or Safari with ES modules
- WebGPU where available; WebGL2 otherwise
- Local HTTP server recommended (module imports and renderer init)

### Reduced motion

When `prefers-reduced-motion: reduce` is active:

- continuous camera animation stops
- governance rings and drifting particles do not animate
- blinking / looping UI motion is disabled
- camera snaps to the active section
- the scene renders on section change or resize only

### Truth labels (important)

This repository is a **public prototype**.

- The mandate console is a **simulated compiler**
- Receipts use preview states such as `receipt_pending`, `simulated`, `pending_verification`, and `unsigned_preview`
- Do **not** assume live autonomous execution, cryptographic signing, settlement, custody, or production MCP routing already exist
- The formal ATG RFC, ATRALITH reference implementation, signed receipts, and live settlement are **not complete**

## Security doctrine — Trusted Authorization Path

ATG separates four properties that are often incorrectly collapsed into the word “security”:

1. **Key custody** — where authority-bearing secrets reside.
2. **Intent integrity** — whether the reviewed action matches the executable payload.
3. **Authority scope** — whether the action is permitted by the active mandate and policy.
4. **Accountability** — whether the full authorization chain can be independently verified afterward.

The host may propose an action. It may not silently redefine the authority that approves it.

For consequential actions, Agentropolis should minimize the trusted computing base, prevent silent downgrade, declare blind-signing states, bind reviewed intent to the exact payload, and produce receipts covering the mandate, policy decision, rendering path, authorization method, execution, and result.

See [`docs/RFC-0001-TRUSTED-AUTHORIZATION-PATH.md`](docs/RFC-0001-TRUSTED-AUTHORIZATION-PATH.md).

## Economic authority and settlement

ATG now defines a draft economic authority profile for governed agent transactions.

Core rule:

> **User intent is not transaction authority.**

The profile separates commerce discovery from execution authority and compiles each economic action into the smallest effective capability surface:

```text
Intent -> Inspect -> Simulate -> Preview -> Approve -> Execute -> Verify -> Receipt
```

Key controls include:

- purpose-bound economic mandates
- amount, asset, merchant, address, network, time, use-count, retry, recurrence, and delegation limits
- third-party impact checks
- passkey, physical, quorum, machine-policy, or dual-control approval classes
- capability handles, ephemeral tokens, bounded session wallets, single-use credentials, or sealed signers instead of raw production secrets
- crypto-native modes for `$XENTS`, x402, XRPL, EVM, and Solana
- optional fiat/card bridges as adapters rather than constitutional dependencies
- durable ATG receipts for consequential execution

See:

- [`docs/RFC-0003-ECONOMIC-AUTHORITY-AND-SETTLEMENT.md`](docs/RFC-0003-ECONOMIC-AUTHORITY-AND-SETTLEMENT.md)
- [`contracts/core/economic-mandate.schema.json`](contracts/core/economic-mandate.schema.json)
- [`examples/economic-mandate.example.json`](examples/economic-mandate.example.json)

## File structure

```text
index.html
css/atg.css
js/grid.js
vendor/three.webgpu.min.js
vendor/three.core.min.js
assets/
contracts/
docs/
examples/
README.md
```

Three.js **0.185.1** is vendored locally. `three.webgpu.min.js` imports `./three.core.min.js`.

## Run locally

```bash
python3 -m http.server 8080
```

Open:

```text
http://localhost:8080
```

Validate JavaScript syntax:

```bash
node --check js/grid.js
```

## Optional image assets

The page reserves styled fallback slots for later binary assets. Add these files when ready — the site works without them and will not request missing images:

- `assets/images/agentropolis-intelligence-grid.webp` — canonical ATG architecture visual
- `assets/images/motionforge-control-plane.webp` — downstream district implementation example

Replace the corresponding `.asset-slot` fallback panels in `index.html` with `<img>` tags once the files exist.

## What this repository is

Protocol layer materials:

- RFCs
- normative schemas
- message types
- authority and risk semantics
- receipt requirements
- versioning
- compatibility tests
- protocol governance
- Atral Script visual mappings

ATG is implementation-neutral. Agents can adopt it without joining AGENTROPOLIS or running ATRALITH.

## What ATRALITH is

ATRALITH is the **planned** reference Agent Kit that will implement ATG through:

- MCP server
- TypeScript and Python SDKs
- schema validator
- mandate builder
- receipt generator and verifier
- agent matching
- framework adapters
- CLI and hosted services

See [`docs/PROTOCOL_VS_AGENT_KIT.md`](docs/PROTOCOL_VS_AGENT_KIT.md).

## Architecture

- **AGENTROPOLIS** — Intelligence Grid and flagship ecosystem
- **ATG** — open Agent Transaction Grammar protocol
- **Atranic** — structured semantic language carried by ATG messages
- **Atral Script** — visual glyph and identity layer
- **ATRALITH** — reference Agent Kit (under construction)

```text
ATG Protocol
    ↓ implemented by
ATRALITH Agent Kit
    ↓ used by
Agents, MCP hosts, applications, and AGENTROPOLIS
```

## Enable GitHub Pages

1. Open **Pages** in repository settings.
2. Select **Deploy from a branch**.
3. Choose `main` and `/ (root)`.
4. Save.

## License

Apache License 2.0.
