# ATG Profile: CITYFLIGHT

**Status:** Draft  
**Category:** Mandate & Receipt Profile  
**Applies to:** ATG mandates, receipts, and policy gates for CITYFLIGHT generation, validation, release, deployment, and rollback.

## Abstract

CITYFLIGHT is a provider-neutral profile for governed flight of agent-generated content, assets, or compute jobs through a staged pipeline: generation → validation → release → deployment → rollback. This profile defines the mandate scope, spend ceilings, required evidence, receipt states, and invariants that any ATG implementation must respect when handling CITYFLIGHT operations.

## Scope

CITYFLIGHT applies to:

- Generation of agent-authored artifacts (images, video, audio, code, data)
- Validation against policy, safety, and quality gates
- Release approval binding
- Deployment to downstream runtimes or distribution layers
- Rollback of deployed artifacts when invariants are violated

## Mandate Shape

A CITYFLIGHT mandate MUST contain:

```json
{
  "mandate_id": "mdt_cityflight_...",
  "agent_id": "agent:cityflight-01",
  "action": {
    "type": "cityflight",
    "stage": "generation|validation|release|deployment|rollback"
  },
  "scope": {
    "max_spend_per_generation": "100.00",
    "max_generations_per_hour": 10,
    "allowed_providers": ["openai", "fal", "anthropic", "local"],
    "allowed_output_types": ["image", "video", "audio", "code", "data"],
    "forbidden_destinations": ["public_web", "untrusted_registry"]
  },
  "constraints": {
    "valid_from": "...",
    "valid_until": "...",
    "required_evidence": ["policy_pass", "safety_scan", "quality_gate"],
    "required_approvers": ["principal:cityflight-approver"],
    "required_signer_class": "hardware_signer"
  },
  "enforcement": "enforced"
}
```

### Spend Ceilings

- `max_spend_per_generation` — per-generation budget in USD (or provider-native credits)
- `max_generations_per_hour` — rate limit
- `allowed_providers` — explicit allowlist; anything not listed is forbidden
- `allowed_output_types` — restricts artifact classes
- `forbidden_destinations` — destinations that must never receive CITYFLIGHT output

## Required Evidence

A CITYFLIGHT mandate MUST declare `required_evidence` including at minimum:

- `policy_pass` — policy gate evaluation result
- `safety_scan` — content safety / toxicity scan
- `quality_gate` — provider-specific quality or coherence check

Each evidence item MUST be recorded in the receipt's `receipt_chain` with a hash and verifier.

## Receipt States

CITYFLIGHT receipts use the standard ATG receipt schema with the following `verification_state` semantics:

| State | Meaning |
|-------|---------|
| `generation_pending` | Generation requested but not yet complete |
| `validation_pending` | Generated artifact awaiting policy/safety/quality gates |
| `validation_passed` | All required evidence collected and verified |
| `release_approved` | Human or quorum approval bound to the release step |
| `deployed` | Artifact successfully deployed to destination runtime |
| `rollback_triggered` | Rollback initiated due to invariant violation |
| `rejected` | Failed a gate or failed to meet evidence requirements |

Receipts for `release_approved` and `deployed` MUST include a `rendered_intent_hash` that binds the human-readable release decision to the exact payload hash.

## Invariants

1. **No silent downgrade.** A CITYFLIGHT action classified `A3_IRREVERSIBLE` or `A4_ROOT` MUST NOT silently fall back to a weaker signer or display path.
2. **Rollback must be receipt-bound.** Any rollback MUST produce a receipt with `verification_state: rollback_triggered` and a reference to the original `receipt_id` that is being rolled back.
3. **Spend ceiling enforcement.** If spend ceiling is exceeded, the policy gate MUST block the action and emit a risk condition with `required_action: escalate_or_abort`.
4. **Release approval binding.** Release approval receipts MUST bind `rendered_intent_hash` to the exact payload hash. Blind signing of release decisions is forbidden.
5. **Provider neutrality.** The profile does not encode provider-specific credential formats. Provider adapters live in ATRALITH; this profile only constrains the ATG envelope.

## Authorization Classes

CITYFLIGHT stages map to authorization classes:

| Stage | Recommended Class | Rationale |
|-------|-------------------|-----------|
| generation | `A1_REVERSIBLE` or `A2_BOUNDED` | Low-to-moderate cost, reversible within budget limits |
| validation | `A1_REVERSIBLE` | Policy gate evaluation; no irreversible side-effects |
| release | `A2_BOUNDED` or `A3_IRREVERSIBLE` | Binds human intent to deployment payload |
| deployment | `A3_IRREVERSIBLE` | Irreversible publication or runtime mutation |
| rollback | `A2_BOUNDED` or `A3_IRREVERSIBLE` | Depends on rollback impact; always requires receipt chain |

## Example Receipt

```json
{
  "receipt_id": "rcpt_cityflight_...",
  "mandate_hash": "sha256:...",
  "payload_hash": "sha256:...",
  "authorization_class": "A3_IRREVERSIBLE",
  "verification_state": "release_approved",
  "receipt_chain": [
    {"step": "generation_complete", "component": "cityflight-gen", "hash": "sha256:..."},
    {"step": "safety_scan_pass", "component": "aegis", "hash": "sha256:..."},
    {"step": "release_approval", "component": "principal:cityflight-approver", "hash": "sha256:..."}
  ],
  "created_at": "..."
}
```

## References

- RFC-0001: Trusted Authorization Path
- Issue #14: CITYFLIGHT mandate and receipt profile (this document)
- AGENTROPOLIS-CREATOR PR #38 (RCP authority draft)
