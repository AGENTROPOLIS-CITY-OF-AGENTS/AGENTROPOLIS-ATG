# ATG Profile: Cinematic Camera Grammar

## Status
Draft v0.1.0

## Purpose

This profile defines how Atralith/ATG expresses cinematic camera intent without coupling the language to any video-generation provider, prompt dialect, camera-control UI, or rendering backend.

ATG owns the semantic instruction. A downstream adapter translates that instruction for the selected execution target. PARALLAX observes the produced scene and issues an evidence-backed motion receipt.

Core rule:

> Camera movement is an ATG semantic contract, not a vendor prompt string.

## Execution path

```text
DIRECTOR
  -> ATG CAMERA INTENT
  -> POLICY / CAPABILITY CHECK
  -> MODEL ADAPTER
  -> VIDEO EXECUTION
  -> PARALLAX OBSERVATION
  -> CAMERA RECEIPT
  -> AUDIT
```

## Canonical camera move object

```yaml
camera_move:
  id: orbit_cw
  family: orbital
  trajectory: orbital
  direction: clockwise
  velocity: slow
  acceleration: ease_in_out
  camera_height: eye_level
  subject_lock: center
  framing_start: medium
  framing_end: medium_close
  lens_behavior: fixed
  parallax_expected: high
  continuity_constraints:
    - preserve_subject_identity
    - preserve_screen_direction
  duration_seconds: 6
```

The registry at `registries/camera-grammar.yaml` defines the canonical field surface.

## Camera families

ATG groups movement into seven interoperable families:

1. **Static** — locked or intentionally unstable stationary cameras.
2. **Linear** — push, pull, truck, pedestal and related translations.
3. **Angular** — pan, tilt and roll rotations.
4. **Orbital** — arcs and orbits around a subject or scene anchor.
5. **Tracking** — follow, lead, chase and lateral subject-relative moves.
6. **Reveal** — pass-through, push-past, crane and rise reveals.
7. **Compound** — coordinated moves such as dolly zoom, orbit push, or truck-pan combinations.

These families are semantic categories, not provider feature claims. A target that cannot natively perform a move may reject it, approximate it under policy, or route it to another capable renderer.

## Adapter boundary

Provider adapters MAY translate ATG semantics into model-specific instructions for systems such as MiniMax H3, Higgsfield, Kling, Seedance, Runway, or future video runtimes.

Adapters MUST NOT:

- redefine the meaning of a canonical camera move;
- promote vendor prompt syntax into authoritative ATG syntax;
- silently drop required motion constraints;
- report success when the requested motion cannot be observed.

When a provider lacks a requested capability, the adapter should return a capability failure or explicit degradation record before execution.

## PARALLAX verification

PARALLAX verifies the observable result rather than trusting the generation request.

A camera receipt should compare requested versus observed values for:

- camera displacement;
- angular displacement;
- trajectory continuity;
- subject screen position;
- start/end framing;
- expected parallax;
- occlusion events;
- timing or speed envelope where measurable.

Example receipt:

```yaml
camera_receipt:
  schema: agentropolis.parallax.camera-receipt.v1
  request_id: shot-042
  requested_move: orbit_cw
  observed:
    trajectory: orbital
    angular_displacement_deg: 71.4
    framing_start: medium
    framing_end: medium_close
    parallax: high
    continuity: continuous
  verdict: PASS
  evidence_refs:
    - frame:0
    - frame:48
    - frame:96
```

## Denied actions

A denied camera action is not proven by the absence of movement. No movement can also mean the request was never dispatched, the renderer failed silently, or the motion control was ignored.

Therefore a denial MUST produce its own explicit record:

```yaml
denial_receipt:
  action: camera.orbit_cw
  decision: DENIED
  policy_rule: spatial.motion.restricted
  dispatched: false
  scene_mutation_expected: false
```

This record remains distinct from the scene observation receipt.

## Director usage

The Director selects composition and movement independently from subject and performance semantics.

```text
SHOT =
  SUBJECT
  + ACTION
  + CAMERA_MOVE
  + COMPOSITION
  + LIGHTING
  + WORLD_STATE
  + CONTINUITY_CONSTRAINTS
```

This separation allows the same scene intent to route across multiple video models while preserving a stable ATG-level cinematic contract.

## Governance

Camera execution follows the normal Agentropolis corridor:

```text
Identity -> Mandate -> Plan -> Execute -> Receipt -> Audit
```

ATG remains declarative until runtime authority is granted. Camera adapters receive only the capability scope required for the current shot. PARALLAX verification should be isolated from the generation adapter whenever practical so the executor is not the sole judge of its own result.

## Design principle

**Describe the shot once. Translate it anywhere. Verify what actually moved.**
