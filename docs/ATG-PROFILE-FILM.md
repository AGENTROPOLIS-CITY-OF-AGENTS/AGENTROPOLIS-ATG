# ATG:FILM — Atralith Cinematic Domain Profile (Draft v0.1)

Status: DRAFT / NOT INTEGRATED. This profile extends ATG semantic IR; it does not replace ATG, grant execution authority, or rename the entertainment medium.

## Scope
A model-neutral film direction contract for HERMES Director, Creator Core, Film District, Blender/Parallax and provider adapters (including Higgsfield and MiniMax). The ATG semantic object is authoritative; English and Atralith native surfaces are reversible renderings, not independent commands.

## Required shot contract
Each shot has: schema_version, shot_id, scene_id, timeline_id, duration_seconds, subjects (stable asset IDs), action/performance beats, camera (framing, lens, trajectory), lighting, materials/world_visual_contract, audio, continuity_in, continuity_out, provider_constraints, provenance, verification, and authority (observe_only by default). All referenced assets require rights/provenance review. No provider credentials in artifacts.

## Semantics
- FILM:SHOT: shot boundaries, duration and composition.
- FILM:CAMERA: physically coherent path, lens and focus.
- FILM:PERFORMANCE: character intent, motion and dialogue beats.
- FILM:PHYSICS: causal interaction, collision and object permanence.
- FILM:CONTINUITY: stable identity, costume, scene geography, state carryover.
- FILM:EDIT: transitions and timing, without destroying editable sources.
- FILM:SOUND: diegetic audio, dialogue, ambience and mix intent.
- FILM:WORLD: dimension-specific palette, lighting, material, atmosphere and lore contract.
- FILM:BRANCH: timeline fork with scoped persistence; never mutate global canon automatically.
- FILM:VERIFY: review and receipt state; generated is not verified.

## Third Door semantic concept
Third Door is a *narrative mechanism*, not the name of the language, engine, medium or brand. It describes emergence of a pathway beyond an imposed binary. It is not necessarily a literal third UI button or restricted to three dimensions. Suggested IR intent: `emergent_pathway_from_constrained_choice`; semantic class ROUTE; branch timeline scoped; preserve canonical world rules; record provenance. No Atralith lexical token, glyph or pronunciation is asserted until registered.

## Example semantic IR (illustrative; not a validated executable envelope)
```json
{
  "profile": "ATG:FILM",
  "version": "0.1.0-draft",
  "class": "ROUTE",
  "intent": "emergent_pathway_from_constrained_choice",
  "concept_id": "third_door",
  "scene_id": "scene-example",
  "shot_id": "shot-example",
  "timeline_id": "branch-example",
  "continuity": {"canon_policy": "preserve", "persistence_scope": "timeline"},
  "authority": "observe_only",
  "verification": "unverified"
}
```

## Compilation pipeline
Director brief -> semantic IR -> canon/rights/authority validation -> editable scene/shot plan -> adapter-specific provider prompt or Blender scene instructions -> output inspection -> continuity QC -> receipt. Do not treat provider success as verified cinematic quality. Provider adapters cannot silently alter world contracts or grant new permissions.

## MiniMax influence
Use explicit time beats, coherent camera, stable identity and physically causal transitions, as exemplified by `.agentropolis/prompts/minimax-h3-handmade-reconstruction.md`. These conventions are model-neutral, not MiniMax proprietary syntax.

## Integration gates (not yet completed)
1. Register profile and machine-readable schema with reversible render rules.
2. Add schema validation and tests for invalid durations, missing shot IDs, broken continuity, and unauthorized canon mutation.
3. Connect HERMES Director shot manifests and Creator Core compilers; preserve source project editability.
4. Implement Blender/Parallax and Higgsfield/MiniMax adapters with capability checks and dry runs.
5. Verify 3:33 / 213-second multi-shot film contract and independent branching; no requirement to branch every film.
6. Run a full end-to-end render, human cinematic QC and signed provenance receipt before claiming production readiness.

## Sources
- `docs/ATG-PROFILE-LANGUAGE.md`
- `registries/language-surface.yaml`
- `.agentropolis/prompts/minimax-h3-handmade-reconstruction.md`
