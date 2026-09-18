# Social Economic Intent Profile

AGENTROPOLIS treats economic actions originating from social, creator, game, live, and spatial surfaces as governed **economic intents**, not direct wallet calls.

## Principle

Social state and economic state are separate. SOCIALS remains available when settlement rails are unavailable. Arc, Base, direct providers, and future rails are adapters beneath AGENTROPOLIS authority.

```text
Social Action
  -> Economic Intent
  -> Identity + Mandate
  -> Progressive Governance
  -> Execution Envelope
  -> Settlement Router
  -> Approved rail adapter
  -> Settlement Receipt
  -> Social State Update
```

## Canonical intent types

- `TIP_CREATOR`
- `BUY_OBJECT`
- `TRADE_CARD`
- `ENTER_MATCH`
- `PAY_AGENT`
- `LICENSE_ASSET`
- `SPLIT_REVENUE`
- `CLAIM_REWARD`
- `JOIN_EVENT`
- `UNLOCK_CONTENT`
- `SPONSOR_CREATOR`
- `COMMISSION_AGENT`

## Envelope compilation

ATG SHOULD compile economic intents into existing Execution Envelope fields rather than making a settlement provider authoritative.

- `principal`: human, agent, service, or organization initiating the intent
- `objective`: desired economic outcome
- `mandate`: authority scope and expiration
- `capabilities.required`: settlement, wallet, contract, game, creator, or licensing capabilities
- `authority.allowed`: permitted economic actions
- `authority.approval_required`: spending or irreversible actions requiring human approval
- `authority.budget`: amount, asset, per-action, rolling, and lifetime limits
- `risk.basis.economic_exposure`: value at risk
- `constraints`: rail, asset, jurisdiction, recipient, slippage, fee, and timing bounds
- `placement.preferences`: direct, local, approved network, low-cost, or low-latency preferences
- `placement.prohibitions`: disallowed providers, chains, bridges, contracts, or custodians
- `receipt`: settlement and provenance receipt requirements
- `extensions.social_economic_intent`: social/game/creator correlation metadata

Safety-critical fields MUST be included in `must_understand` so adapters fail closed if unsupported.

## Settlement Router contract

The Settlement Router MUST:

1. receive only ATG-approved intents;
2. select only adapters allowed by the Execution Envelope;
3. preserve provider and chain abstraction;
4. fail closed when an approved route is unavailable and fallback is prohibited;
5. return a normalized receipt containing provider, rail, asset, amount, fees, correlation IDs, status, and provenance;
6. never mutate canonical social identity or reputation directly.

The Settlement Router MUST NOT:

- become a trading brain;
- infer permission from a prompt;
- grant wallet authority;
- make Arc, Base, Circle, or any other third party an AGENTROPOLIS identity authority;
- convert a failed settlement into a failed social event.

## Arc adapter boundary

Arc is an optional settlement rail. Circle Agent Stack, wallets, USDC, x402/nanopayment capabilities, and other Arc services may satisfy approved capabilities, but AGENTROPOLIS owns identity, mandate, routing, risk, policy, and receipts.

## Social correlation

Every economic intent SHOULD preserve when applicable:

- `social_event_id`
- `content_id`
- `creator_entity_id`
- `agent_entity_id`
- `game_event_id`
- `card_or_object_id`
- `live_event_id`
- `spatial_anchor_id`
- `campaign_id`
- `correlation_id`

This allows the city to prove which social/game/creator event produced a settlement without making settlement infrastructure the source of social truth.
