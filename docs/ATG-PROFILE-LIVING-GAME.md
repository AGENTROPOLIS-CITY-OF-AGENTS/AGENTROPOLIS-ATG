# ATG:LIVING-GAME Profile

Status: Draft

ATG:LIVING-GAME is a bounded domain profile of ATG for the project-, franchise-, chain-, device-, platform-, model-, and rules-engine-agnostic Living Game Protocol owned by [AGENTROPOLIS-GAMING-DISTRICT](https://github.com/AGENTROPOLIS-CITY-OF-AGENTS/AGENTROPOLIS-GAMING-DISTRICT/blob/main/docs/LIVING-GAME-PROTOCOL.md). It does not redefine the ATG protocol and it does not introduce a second envelope.

## One Execution Envelope

There is exactly one canonical Execution Envelope: `contracts/core/execution-envelope.schema.json`. Living Game semantics travel inside it under `extensions.living_game`, described by `contracts/profiles/living-game-extension.schema.json`, and the envelope must list `living_game` in `must_understand`. Gaming District, Utility Grid, Creator Core, BOTBAE, and Ontology consume envelopes by `envelope_id`; none of them compile, verify, or mint envelopes.

## Canonical schemas consumed (never redefined)

- `https://agentropolis.dev/schemas/living-game-object-v1.schema.json`
- `https://agentropolis.dev/schemas/live-reality-session-v1.schema.json`

## When an envelope is required

| Action class | Envelope | Additional requirement |
|---|---|---|
| discovery, lore reveal, preview, private vision, party play, capability negotiation | no | Utility Grid / game runtime handle it; receipts still emitted |
| `reward.value` | yes | `rules_engine.verification_receipt_id`, `object_refs` |
| `access.grant` / `access.revoke` | yes | |
| `ownership.transfer` | yes | rules-engine verification; never automatic; never from an NFC tap alone |
| `publish.public_broadcast` | yes | `session_ref.lease_id` (Utility Grid renewable lease), `privacy.public_broadcast_authorized = true` |
| `publish.clip` / `publish.social` | yes | `human_signal_entity` with Dock consent receipt and publishing scopes |
| `settlement.optional_commerce` | yes | economic corridor (ATG:MARKET / Atralith) |
| `object.mint` / `object.retire` / `tournament.result_finalize` | yes | rules engine as source of truth |

## Evidence vs authority

`extensions.living_game.evidence_refs[]` records what motivated the mandate: NFC taps, QR scans, camera/model observations, game results, social events, NEURO advisories, Utility Grid receipts. Every entry carries `grants_authority: false` (schema constant). Authority lives only in the envelope `authority` block compiled by ATG under a mandate and risk policy.

- An NFC tap, camera access, QR scan, wallet connection, follower count, social message, or device connection never grants permission.
- High engagement cannot promote a claim, expand authority, or weaken a gate.
- NEURO is advisory only.
- High-value NFC claims require `assurance_tier` of `high_assurance` or `managed_installation` and `replay_protected: true` on the evidence ref; ATG risk policy raises the tier accordingly.

## Risk tiering guidance

| Action class | Suggested minimum tier |
|---|---|
| publish.clip / publish.social (own account, disclosed) | R2 |
| publish.public_broadcast | R3 |
| reward.value (non-transferable progression) | R2 |
| reward.value (transferable / monetary) | R4 |
| ownership.transfer / settlement.optional_commerce | R4–R5, approval required |

## Privacy and accessibility constants

- `privacy.face_recognition` is `false` by schema constant; no envelope can enable face recognition.
- `accessibility.wallet_required_every_step` is `false` by schema constant.
- `accessibility.alternatives_available` must be `true` before a physical-trigger reward can be authorized.

## Responsibility split

- **ATG:** mandate compilation, risk tier, approval requirements, the single envelope, receipt/audit correlation.
- **Gaming District:** protocol, canonical schemas, game/campaign/tournament/quest/registry governance.
- **Utility Grid:** NFC registry and assurance, device routing, metering, renewable broadcast leases, receipts.
- **Creator Core:** provider-neutral runtime interfaces and authoring/publishing pipelines.
- **BOTBAE:** least-privilege conversational operations; no camera, credential, treasury, Recognition, or policy authority.
- **Ontology:** semantics for Living Game Object, Human Signal Entity, device capability, physical authenticator, quest trigger, live session, broadcast destination, interoperability adapter.
- **NEURO:** observation and advisory only.

## Runtime

Envelopes compile to governed AGENTROPOLIS runtimes (Hermes, NemoClaw/Nemotron routes) per `docs/HERMES_EXECUTION_ENVELOPE_PROFILE.md`. OpenClaw is not a permitted execution target.

## Example

See `examples/living-game-reward-envelope.example.json` and `tests/test_living_game_profile.py`.
