# ATG Profile: Identity-Preserving Photo Edit

Status: Draft profile
Namespace: `atg.media.photo_edit.identity_preserving`
Owner: AGENTROPOLIS-CREATOR-CORE semantic contract
Purpose: Carry bounded photo-edit intent between agents and execution adapters without allowing silent subject regeneration.

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

## Canonical message

```json
{
  "profile": "atg.media.photo_edit.identity_preserving",
  "version": "0.1.0",
  "intent": "CAMERA_UPGRADE",
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
    "lighting",
    "contrast",
    "color",
    "sharpness",
    "depth",
    "background_separation",
    "framing"
  ],
  "forbid": [
    "identity_drift",
    "face_reshape",
    "body_reshape",
    "beautification",
    "plastic_skin",
    "unrequested_regeneration"
  ],
  "preview_required": true,
  "human_approval_required": true,
  "receipt_required": true
}
```

## State machine

```
REQUEST
  -> ANALYZED
  -> SUBJECT_LOCKED
  -> SPEC_COMPILED
  -> DISPATCHED
  -> PREVIEWED
  -> VERIFIED
  -> APPROVED
  -> EXPORTED
  -> RECEIPTED
```

Failure branch:

```
PREVIEWED
  -> IDENTITY_DRIFT_DETECTED
  -> REJECTED
  -> RETRY_BOUNDED
```

A retry MUST reuse the same preserve/forbid constraints unless a human modifies the mandate.

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
```

### Human
Approves or rejects the preview before final export when `human_approval_required = true`.

## Receipt

Minimum receipt fields:

```json
{
  "profile": "atg.media.photo_edit.identity_preserving",
  "request_id": "string",
  "source_asset_hash": "string",
  "output_asset_hash": "string",
  "intent": "CAMERA_UPGRADE",
  "subject_lock": true,
  "verification": "PASS",
  "approved_by": "human|policy-authorized-principal",
  "adapter": "string",
  "timestamp": "RFC3339"
}
```

## Boundary

This profile is semantic and transport-level only.

ATG does not:
- perform image generation
- choose a provider
- own the Creator preset library
- bypass human approval
- silently relax preservation constraints

Creator owns creative semantics. Construction may own implementation/runtime. Provider adapters remain replaceable limbs.
