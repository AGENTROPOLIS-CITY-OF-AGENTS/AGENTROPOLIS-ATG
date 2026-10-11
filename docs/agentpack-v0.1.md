# AgentPack v0.1

AgentPack is the portable commercial product contract for governed agents and crews.

## Why it exists

AgentPack separates the agent product from any one model, runtime, marketplace, or messaging surface. A single governed agent can be compiled to Twin-style stores, web/PWA, mobile, ChatGPT/Claude-style tool surfaces, Slack, Discord, Telegram, WhatsApp, email, voice, MCP, APIs, and future marketplaces without moving canonical authority into the destination platform.

AgentPack is **not** an authority grant. Authority remains in the ATG-compiled Execution Envelope.

## Contract boundary

```text
Agent / Crew definition
  -> AgentPack
  -> BOTBAE experience + surface compiler
  -> destination adapter
  -> ATG Execution Envelope at execution time
  -> runtime
  -> receipt / verification / audit
```

## Core domains

- Identity and publisher provenance
- Skills, tools, model and runtime compatibility
- Context contracts
- Governance and risk profile
- Surface/store distribution targets
- Agent Link install flow and minimum scopes
- Pricing and metering
- Evaluation and receipt profile
- Build provenance

## Non-negotiable rules

1. The same AgentPack MAY target many surfaces.
2. Surface adapters MUST request minimum permissions.
3. A store listing MUST NOT become a source of runtime authority.
4. Secrets are referenced, never serialized in AgentPack.
5. Model/provider names describe compatibility, not identity.
6. Economics MAY vary by distribution target, but canonical agent identity and provenance remain stable.
7. All privileged execution still passes Identity -> Mandate -> Policy/Risk -> Execution Envelope -> Dispatch -> Receipt -> Verification -> Audit.
8. Unknown optional fields may be tolerated; safety-critical extensions belong in `must_understand`.

## Initial target surfaces

- `twin-store`
- `web`
- `pwa`
- `mobile`
- `slack`
- `discord`
- `telegram`
- `whatsapp`
- `email`
- `voice`
- `mcp`
- `api`
- `chatgpt`
- `claude`
- `spotify-agentic`

`spotify-agentic` is a capability class, not a claim of private Spotify APIs. It represents the product pattern of being callable by outside agents while also supporting native first-party agent experiences.

## Next implementation work

BOTBAE should compile AgentPack targets into destination-specific experience bindings. Utility Grid should provide runtime routing, Context Capsule/Context Graph hydration, metering telemetry, and receipt transport. Creator Core should generate AgentPacks from natural-language product definitions and existing governed agents.
