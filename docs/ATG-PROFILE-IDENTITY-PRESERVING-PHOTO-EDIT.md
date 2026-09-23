# ATG Profile: Identity-Preserving Photo Edit

Status: Draft profile, version `0.2.0`
Namespace: `atg.media.photo_edit.identity_preserving`
Owner: AGENTROPOLIS-CREATOR-CORE semantic contract
Purpose: Carry bounded photo-edit intent between agents and execution adapters without allowing silent subject regeneration.

Machine-checked artifacts (reference implementation, not a production runtime):

- Request schema: `contracts/media/photo-edit-request.v1.schema.json`
- Receipt schema: `contracts/media/photo-edit-receipt.v1.schema.json`
- Reference compiler / state machine / receipt checks: `atralith/photo_edit_profile.py`
- Negative regression tests: `atralith/test_photo_edit_profile.py` (run by the `test` workflow)

Enforcement status: controls marked ENFORCED below are enforced by the reference module and its tests in this repository. Wiring the reference module into a live Creator/Construction execution path is PLANNED and is not claimed here.

## Principle

ATG transports the edit contract. It does not decide what the subject should look like.

Default invariant:

`subject_lock = true`

Unless a human explicitly requests a subject change, the following attributes are immutable:

- identity
- facial geometry
- body proportions
- expression
- pose
- hairstyle
- clothing
- natural skin texture
- scene/surroundings

## Intent modes

```
CAMERA_UPGRADE
LIGHTING_REPAIR
CINEMATIC_GRADE
PROFESSIONAL_HEADSHOT
```

### CAMERA_UPGRADE

Mutable domains:
`exposure, optical_depth, sharpness, lens_rendering, background_separation`

Forbidden:
`identity_drift, face_reshape, body_reshape, beautification, feature_regeneration`

### LIGHTING_REPAIR

Mutable domains:
`shadow_balance, highlight_recovery, dark_area_recovery, skin_tone_rendering, directional_light`

Forbidden:
`beauty_filter, artificial_glow, skin_smoothing, identity_drift`

### CINEMATIC_GRADE

Mutable domains:
`tonal_contrast, color_grade, atmosphere, depth`

Required preservation:
`realistic_skin, clothing_texture, facial_detail`

Forbidden:
`fake_haze, excessive_effects, oversaturation, identity_drift`

### PROFESSIONAL_HEADSHOT

Mutable domains:
`framing, exposure, soft_directional_light, background_separation, clarity`

Forbidden:
`face_reshape, plastic_skin, exaggerated_retouching, identity_drift`

### Mutable domains are derived from the intent (ENFORCED)

`mutable` is exactly the selected mode's allowlist; it is never the union across modes. A request whose `mutable` contains a domain outside the selected intent is rejected (`validate_request`, test `IntentDerivedConstraintsTests.test_cross_mode_union_is_rejected`). `preserve` must contain every locked subject attribute (including `pose` and `surroundings`) that a human has not explicitly released via `explicit_subject_changes`; `identity`, `face_geometry`, and `body_proportions` can never be released (`ExplicitSubjectChangeTests`).

## Canonical message

Schema: `contracts/media/photo-edit-request.v1.schema.json` (`additionalProperties: false`).

```json
{
  "profile": "atg.media.photo_edit.identity_preserving",
  "version": "0.2.0",
  "request_id": "REQ-7f3a",
  "intent": "CAMERA_UPGRADE",
  "source_asset": {
    "asset_id": "asset-01",
    "sha256": "<sha256 of the source image bytes>",
    "media_type": "image/png"
  },
  "authority": {
    "principal": { "id": "human:alice", "type": "human" },
    "mandate_ref": "mandate:...",
    "capability_handle_ref": "cap:...",
    "policy_ref": "policy:...",
    "execution_envelope_ref": "envelope:..."
  },
  "subject_lock": true,
  "preserve": [
    "identity",
    "face_geometry",
    "body_proportions",
    "expression",
    "pose",
    "hair",
    "clothing",
    "skin_texture",
    "surroundings"
  ],
  "mutable": [
    "exposure",
    "optical_depth",
    "sharpness",
    "lens_rendering",
    "background_separation"
  ],
  "forbid": [
    "identity_drift",
    "face_reshape",
    "body_reshape",
    "beautification",
    "feature_regeneration",
    "plastic_skin",
    "unrequested_regeneration"
  ],
  "explicit_subject_changes": [],
  "retry_policy": { "max_attempts": 3, "on_exhausted": "FAILED_TERMINAL" },
  "preview_required": true,
  "human_approval_required": true,
  "receipt_required": true
}
```

Required bindings (ENFORCED by schema + `validate_request`):

- `request_id` and `source_asset.{asset_id, sha256}` are required. The receipt's `source_asset_hash` must equal the request's `source_asset.sha256` (`SourceAssetAndRequestIdTests`).
- `authority` carries references only. ATG transports them; it does not grant them. AGENT-ENTITY establishes the principal, AEGIS/policy grants the mandate and capability. Possession of a well-formed message is never permission (`AuthorityGateTests.test_message_requires_every_authority_reference`).
- `retry_policy.max_attempts` is a finite integer in `[1, 5]` and `on_exhausted` is `FAILED_TERMINAL` or `HUMAN_ESCALATION` (`BoundedRetryTests`).

## State machine

Transition table: `TRANSITIONS` in `atralith/photo_edit_profile.py`. Any (state, event) pair not listed is refused.

```
REQUEST
  -> ANALYZED
  -> SUBJECT_LOCKED
  -> SPEC_COMPILED
  -> AUTHORITY_RESOLVED      (ENFORCED: no SPEC_COMPILED -> DISPATCHED edge exists)
  -> DISPATCHED
  -> PREVIEWED
  -> VERIFIED                (verifier PASS, independent verifier, edit actually applied)
  -> APPROVED                (human approval when human_approval_required)
  -> RECEIPTED               (receipt committed and checked)
  -> EXPORTED                (ENFORCED: export refused unless state is RECEIPTED)
```

Failure branches:

```
PREVIEWED  --verify_fail (ANY FAIL_* outcome)-->  REJECTED
VERIFIED   --human_reject-->                      REJECTED
REJECTED   --retry    (attempt < max_attempts)--> RETRY_BOUNDED -> DISPATCHED
REJECTED   --exhaust  (attempt == max_attempts)-> RETRY_EXHAUSTED
RETRY_EXHAUSTED --fail_terminal--> FAILED_TERMINAL      (on_exhausted = FAILED_TERMINAL)
RETRY_EXHAUSTED --escalate-->      HUMAN_ESCALATION     (on_exhausted = HUMAN_ESCALATION)
```

Authority gate (ENFORCED): `DISPATCHED` is reachable only from `AUTHORITY_RESOLVED`. `resolve_authority` requires the authority plane to report every reference (`mandate_ref`, `capability_handle_ref`, `policy_ref`, `execution_envelope_ref`) as `valid`; a missing, revoked, or unresolved reference blocks dispatch (`AuthorityGateTests`). ATG only checks that the answers exist; the answers themselves come from AEGIS/policy.

Retry bound (ENFORCED): a retry MUST reuse the same preserve/forbid constraints unless a human modifies the mandate. `dispatch` refuses once `attempt >= max_attempts`; the terminal state is deterministic from `on_exhausted` (`BoundedRetryTests.test_retry_budget_terminates`).

## Agent responsibilities

### Creator agent
Compiles human creative intent into this profile.

### Execution adapter
Applies only mutations listed in `mutable` and MUST NOT reinterpret locked attributes.

### Verification agent
Checks output against preservation constraints and emits one of:

```
PASS
FAIL_IDENTITY_DRIFT
FAIL_UNREQUESTED_RESHAPE
FAIL_UNREQUESTED_BEAUTIFICATION
FAIL_OUT_OF_SCOPE_MUTATION
FAIL_EDIT_NOT_APPLIED
```

Every `FAIL_*` outcome transitions `PREVIEWED -> REJECTED` (ENFORCED, `VerifierOutcomeTests.test_every_fail_outcome_transitions_to_rejected`).

Independence (ENFORCED): the verifier report must carry `verifier_id`, an `independence` class (`independent_service | independent_agent | human_reviewer`), and an `evidence_digest`. A report whose `verifier_id` equals the execution adapter is refused; generator self-report never yields PASS (`IndependentVerifierTests`).

Edit occurred (ENFORCED): a `PASS` is downgraded to `FAIL_EDIT_NOT_APPLIED` when `edit_applied` is false, `applied_domains` is empty, or the output hash equals the source hash; a `PASS` whose `applied_domains` leave the intent's `mutable` set is downgraded to `FAIL_OUT_OF_SCOPE_MUTATION` (`EditActuallyOccurredTests`).

### Human
Approves or rejects the preview before final export when `human_approval_required = true`.

- Human rejection after a verifier PASS is a first-class edge `VERIFIED -> REJECTED` and consumes a retry (`HumanApprovalTests.test_human_rejection_after_pass_routes_to_rejected_then_retry`).
- When `human_approval_required = true`, a policy-authorized principal cannot approve; the receipt's `approved_by.type` must be `human` (`HumanApprovalTests.test_policy_principal_cannot_approve_human_gated_request`). A policy-authorized principal may approve only when the request set `human_approval_required = false`.
- Approval is bound to the exact preview: `approval_digest = sha256(request_id:preview_digest:approved_by.id)` and is re-derived during receipt check (`HumanApprovalTests.test_receipt_requires_human_principal_and_bound_digest`).

## Receipt

Schema: `contracts/media/photo-edit-receipt.v1.schema.json`. The receipt is committed in state `APPROVED` and is the only path to `RECEIPTED`; export is refused without it (ENFORCED, `ReceiptBeforeExportTests.test_export_refused_without_committed_receipt`).

```json
{
  "profile": "atg.media.photo_edit.identity_preserving",
  "profile_version": "0.2.0",
  "request_id": "string",
  "source_asset_hash": "sha256",
  "output_asset_hash": "sha256",
  "preview_digest": "sha256",
  "intent": "CAMERA_UPGRADE",
  "subject_lock": true,
  "attempt": 1,
  "max_attempts": 3,
  "verification": {
    "result": "PASS",
    "verifier_id": "string (must differ from adapter)",
    "independence": "independent_service|independent_agent|human_reviewer",
    "evidence_digest": "sha256",
    "edit_applied": true,
    "applied_domains": ["exposure"]
  },
  "approval": {
    "approved_by": { "id": "string", "type": "human|policy-authorized-principal" },
    "approval_digest": "sha256(request_id:preview_digest:approved_by.id)"
  },
  "adapter": "string",
  "timestamp": "RFC3339"
}
```

`profile_version` is required and must equal the request `version` (ENFORCED, `ReceiptBeforeExportTests.test_receipt_carries_profile_version`). `verification.result` must be `PASS`, `verifier_id` must differ from `adapter`, `output_asset_hash` must differ from `source_asset_hash`, and `attempt <= max_attempts == request.retry_policy.max_attempts` (`check_receipt`).

## Boundary

This profile is semantic and transport-level only.

ATG does not:
- perform image generation
- choose a provider
- own the Creator preset library
- bypass human approval
- silently relax preservation constraints

Creator owns creative semantics. Construction may own implementation/runtime. Provider adapters remain replaceable limbs.

## Enforcement status

| Control | Status |
| --- | --- |
| Request/receipt schema shape, intent-derived `mutable`, source-asset binding, authority references required | ENFORCED (schema + `validate_request`, tests) |
| No dispatch without resolved authority; bounded retries; all-failures-reject; human rejection edge; independent verifier; edit-occurred; human approval bound to preview; receipt before export | ENFORCED in `PhotoEditRun` reference state machine, tests |
| Actual resolution of mandate/capability/policy references | Owned by AEGIS/policy; ATG only consumes the answer |
| Wiring `PhotoEditRun` into a live Creator/Construction pipeline and provider adapter | PLANNED |
| Pixel-level identity-drift measurement | PLANNED (verifier implementation outside ATG) |
