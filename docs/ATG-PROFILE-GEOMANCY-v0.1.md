# ATG:GEOMANCY — Domain Profile Proposal v0.1

Status: **PROPOSED / NON-NORMATIVE**. No compiler, runtime, deployment, or production authorization is implied.

## Scope
GEOMANCY is a proposed ATG domain profile for mathematical creation of 2D sprites, procedural 3D geometry, characters, environments, simulations and animations. It extends ATG Semantic IR, not the core Atralith grammar. Human-readable declarations are examples only until the canonical ATG LANGUAGE mapping is approved.

## Boundaries
- ATG owns semantics, identity references, mandates, policy constraints, capability descriptions, provenance and receipt contracts.
- GEOMANCY owns domain vocabulary, scene graph schema, deterministic seeds, spatial units, geometric operations and validation semantics.
- Renderer adapters (browser Three.js/WebGPU, Babylon.js or other compatible runtimes) remain replaceable.
- Scene descriptions, generated visuals or agent navigation never grant execution authority.
- Privileged operations require explicit scoped mandate, policy evaluation and an execution envelope.
- Keep source inputs, generated code and external assets untrusted until validated. No unreviewed arbitrary generated-code execution.

## Proposed typed IR payload
```json
{
  "profile": "ATG:GEOMANCY",
  "profile_version": "0.1.0",
  "scene": {
    "id": "builder-commons-demo",
    "seed": 54021,
    "units": "m",
    "coordinate_system": "right-handed-y-up",
    "objects": [
      {
        "id": "atrium",
        "kind": "building",
        "generator": "parametric-box",
        "dimensions": [20, 12, 20],
        "material": {"base_color": "#12141A"}
      }
    ]
  },
  "execution": {
    "mode": "preview-only",
    "authority_ref": null
  }
}
```
This example is **illustrative** and must be aligned to the canonical ATG Semantic IR schema before implementation.

## Proposed modules
1. GEO:MATH — vectors, matrices, fields, constructive solid geometry, seeds.
2. GEO:WORLD — districts, navigation surfaces, buildings, terrains.
3. GEO:LIFE — character skeletons, rig definitions, procedural behavior descriptions.
4. GEO:SPRITE — vector sprites, rasterization, sprite-sheet exports.
5. GEO:PHYSICS — units, collision metadata, simulation contracts.
6. GEO:MOTION — animation tracks, camera paths and kinematic constraints.

## Compiler plan
Natural-language intent → canonical ATG Semantic IR + GEOMANCY payload → schema/type validation → deterministic scene graph → bounded geometry compilation → pluggable rendering/export adapter → provenance/receipt.

## Required v0.1 acceptance gates
- Inspect and reconcile with ATG profile registration, naming and Semantic IR conventions.
- Validate unit types, coordinate system, object IDs, allowed geometry generators and scene size limits.
- Same spec + seed + compiler version yields deterministic geometry (within documented numerical tolerances).
- Invalid dimensions, non-finite numeric values and unsupported generators fail closed.
- Preview mode requires no privileged access; external writes and autonomous actions require approval.
- Test scene: navigable 3D district, modular turbine, animated procedural character, and sprite-sheet export.
- Export manifest contains input digest, parameters, dependency/compiler versions and artifact digest.
- No production or compatibility claims before integration tests and review.

## Relationship to ATG:ARCANA54
GEOMANCY supplies spatial and rendering semantics. ARCANA54 may consume generated scene artifacts for story-world use cases without transferring domain authority.

## Proposed repository placement
Keep this specification in AGENTROPOLIS-ATG for ATG language governance. A future standalone AGENTROPOLIS-GEOMANCY implementation repository may be created separately after the profile contract is approved.
