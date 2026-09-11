# ATG TRANSFORM

ATG TRANSFORM is the provider-neutral transformation family for reconstructing, synthesizing, validating, simulating, packaging, and verifying media, spatial assets, interfaces, software behavior, data, and future multimodal world-state representations.

ATG remains the canonical language/specification. The runtime/compiler that interprets ATG is a Utility Grid service. Applications consume the language and runtime; they do not redefine it.

## Core rule

> ATG describes what must remain true. Providers determine how to produce it.

Provider syntax is never the canonical representation.

## Family

```text
ATG TRANSFORM
├── RECON       reconstruction / restoration
├── VIS         image / visual synthesis
├── FILM        cinematic sequencing
├── GEO         geometry / 2.5D / 3D / spatial reconstruction
├── MAT         materials / appearance
├── AUDIO       speech / sound / music reconstruction
├── MOTION      pose / animation / temporal continuity
├── SIM         physics / simulation / digital twins
├── GEN         procedural / generative systems
├── CONSTRAINT  compatibility / physics / policy constraints
├── VERIFY      QC / confidence / provenance / receipts
└── PACKAGE     delivery / target compilation
```

## Universal transformation corridor

```text
OBSERVE
→ ASSESS
→ DECOMPOSE
→ RECOVER
→ INFER
→ SYNTHESIZE
→ ALIGN
→ CONSTRAIN
→ SIMULATE
→ VERIFY
→ IDENTIFY
→ PACKAGE
→ RECEIPT
```

### OBSERVE
Capture available evidence: image, film, audio, point cloud, text, screenshot, DOM, accessibility tree, sensor stream, CAD, scan, code, structured data, or future modalities.

### ASSESS
Classify quality, provenance, compression, incompleteness, calibration, trust, and source uncertainty.

### DECOMPOSE
Break the source into semantically meaningful units: objects, layers, alpha mattes, geometry, shots, audio stems, UI components, code paths, state transitions, materials, relations.

### RECOVER
Restore information that is actually present but degraded: denoise, deblock, stabilize, calibrate, normalize, repair encoding, restore timing.

### INFER
Estimate information not directly observable: depth, hidden geometry, lighting, occlusion, topology, motion, intent, state relationships. Inferred values must remain labeled inferred.

### SYNTHESIZE
Create new canonical material where source evidence does not contain enough information: parametric redraw, procedural geometry, generated textures, missing states, new interaction scaffolding.

### ALIGN
Map outputs to a canonical coordinate, identity, time, state, rig, camera, schema, or semantic frame.

### CONSTRAIN
Apply geometry, continuity, policy, rights, compatibility, physics, accessibility, game, and authority constraints.

### SIMULATE
Predict behavior or state transition before committing an irreversible or expensive operation.

### VERIFY
Perform deterministic and numerical QC first; escalate ambiguity/high-impact canon decisions to a human or authorized agent.

### IDENTIFY
Version, hash, bind provenance, define deterministic DNA/entity identity, and preserve relationships.

### PACKAGE
Compile the verified ATG IR into a target representation such as film prompt, collectible package, WebMCP surface, game asset, USDZ/GLB, robotics plan, simulation input, world-model object, or future adapter.

### RECEIPT
Record the evidence, transformations, inferred/synthesized portions, constraints, confidence, tool/provider versions, approvals, output hashes, and verification results.

## Epistemic state is first-class

Every transformed property SHOULD carry one of:

- `OBSERVED` — directly present in trusted input
- `RECOVERED` — present but restored from degradation
- `INFERRED` — estimated from evidence/priors
- `SYNTHESIZED` — newly created canonical material

Do not collapse these states into one undifferentiated value.

Example:

```text
left_eye.geometry.state = OBSERVED
left_shoe.texture.state = RECOVERED
hidden_sleeve.geometry.state = INFERRED
rear_pocket.artwork.state = SYNTHESIZED
```

## Uncertainty is first-class

A value may carry:

```text
value
confidence
error_bounds
source_state
method
provider_or_model
version
human_approval_state
```

An application may reject or escalate outputs based on uncertainty without understanding the provider that produced them.

## Canonical world primitives

ATG TRANSFORM is designed for future world-model systems, not only current media generators.

The IR MAY express:

```text
ENTITY
STATE
SPACE
TIME
RELATION
ACTION
MATERIAL
FORCE
CAMERA
AGENT
INTENT
AUTHORITY
CONSTRAINT
EVIDENCE
UNCERTAINTY
TRANSFORMATION
```

These primitives are target-independent.

## Forward, inverse, and round-trip modes

### Forward

`SPEC → ASSET / WORLD / BEHAVIOR`

### Inverse

`ASSET / WORLD / BEHAVIOR → STRUCTURE`

### Round-trip

`OBSERVED ASSET → INFER STRUCTURE → CANONICAL IR → REGENERATE → COMPARE → REFINE`

This enables reconstruction workflows, visual reverse engineering, software/UI reconstruction, digital twins, and future multimodal agents.

## Constraint graphs

Constraints SHOULD be modeled as a graph or machine-checkable predicate set rather than free-text instructions alone.

Examples:

```text
hood_up conflicts_with fitted_cap
joint requires hand_pose:v_clutch
barrel_pants requires shoe_anchor:wide_hem
long_hair occludes rear_jewelry
mint_button enabled_when collection.live && user.eligible
```

The runtime may satisfy these constraints using deterministic graph/SAT/CSP solvers before invoking probabilistic generation.

## Physics hooks

The grammar reserves semantic hooks for:

- gravity
- collision
- cloth
- rigidity
- friction
- fluids
- smoke
- hair
- soft body
- joint limits
- contact
- force

No current implementation is required to support every hook.

## Materials

ATG should distinguish geometry from material/appearance. Material properties may include:

- base color
- roughness
- metalness
- normal
- emissive
- transmission
- anisotropy
- subsurface behavior
- spectral/volumetric parameters

This allows one entity to compile into flat art, foil materials, game assets, spatial assets, or future renderers.

## Continuity graph

Canonical entities SHOULD preserve identity across media and applications.

Example:

```text
ENTITY HoodTerp_0033
  appearance
  geometry
  traits
  wardrobe
  voice
  movement
  lore
  rights
  provenance
  game_state
```

Creator Core can compile the entity for film. Holofoil can compile it for a collectible/game object. Parallax/WebMCP can compile related interactions. The entity remains canonical.

## Future modalities

The observation layer MUST remain extensible to inputs such as:

- RGB
- depth
- LiDAR
- radar
- thermal
- hyperspectral
- event camera
- IMU
- motion capture
- tactile
- point cloud
- neural fields
- Gaussian splats
- NeRF-like representations
- volumetric video
- future sensor or latent representations

Unknown modalities must not require redesign of the core epistemic/provenance model.

## Runtime boundary

```text
ATG language/spec
      ↓
ATG Transform IR
      ↓
ATG Runtime / Compiler Utility
      ↓
provider / engine adapters
```

ATG itself is not moved into Utility Grid. The runtime/compiler belongs there as a shared execution utility.

## Consumers

Initial consumers include:

- Agentropolis Creator Core / filmmaking
- Holofoil
- Parallax Spatial MCP
- WebMCP Challenge
- ARCANA54

Future consumers may include robotics, simulation, digital twins, spatial operating systems, scientific visualization, world models, and hardware agents.

## Governance boundary

Transformation semantics do not grant execution authority.

ATG may express `INTENT`, `CONSTRAINT`, and `AUTHORITY` state, but execution still follows the applicable Agentropolis governance corridor and Execution Envelope.

## Standing principle

> Preserve truth across transformation: what was observed, what was recovered, what was inferred, what was synthesized, and what was actually verified.
