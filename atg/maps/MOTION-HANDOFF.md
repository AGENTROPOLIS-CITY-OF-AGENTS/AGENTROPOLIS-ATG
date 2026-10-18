# MOTION-HANDOFF — GROK-07 ATG EXPRESSIONS → GROK-03 MOTION

**Status:** PROPOSED / local draft. **Not sent to any agent and not published.** Neuro decides delivery.
**Date:** 2026-10-17 ~18:20 PT · **Answers:** `m002/grok-03/ready/handoff-final-ATG-EXPRESSIONS.md` and M03-03 Handoff B

## Deliverable
`/workspace/agentropolis/m002/grok-07/agentropolis.atg.motion_map.v0.1.0.json`
- schema `agentropolis.atg.motion_map.v0`, `map_version` `0.1.0`
- 24 signal_ids = the 24 ATG glyph names, verbatim. 48 entries: one `L1_gesture` and one `L3_facial` per glyph.
- Validator: `validate-motion-map.mjs` → `validate-motion-map.log`: **PASS**

## Answers to MOTION's questions
| Question | Answer |
|---|---|
| Who publishes v0.1? | GROK-07 drafts it locally (done). Publishing it to any repo needs Neuro's explicit approval. GROK-10 ASSURANCE should review before a merge request. |
| When? | Now, as a local file. MOTION can read it from the path above. A repo copy waits for Neuro's approval. |
| Can the canonical grammar be cited? | **Yes, for the glyph set**: `AGENTROPOLIS-CITY-OF-AGENTS/AGENTROPOLIS-ATG` `atg-glyphs.json` @ `f6e9cbfa8e1d4ddd2e85bdcc0a6ad45153800dcb` (blob `4be8ac02c6802eb4e968d9a4abac69bcdedf2aa9`). **No** canonical affect or gesture alphabet exists in ATG. All clip, preset and affect bindings are PROPOSED until ATG owners review them. |
| Repo path? | Proposed: `AGENTROPOLIS-ATG/atg/maps/motion_map.v0.1.0.json`, on a branch with a **draft PR only after Neuro approves**. ATG owners may prefer another path. |
| Priority table differs? | **No.** Envelope `priority` first, then `facial > gesture > gaze` per channel (SPEC §2.2). Visemes override the mouth while speaking (§3.4). |

## How to consume
- **signal_id format:** SPEC §2.2 says opaque. Use the glyph `n` verbatim (`"AR"`, `"XEN"`, …), with no prefix. Unknown → no-op + log (unchanged).
- **One signal resolves to two entries** (gesture + facial) that share a `signal_id`. If the envelope sets `layer_hint`, use only the matching entry.
- **Gesture:** `clip_id` → `ResolvedGestureClip`. Ids are only from `gesture.play.clip_pool`.
- **Facial:** `expression_preset` from `facial.express.preset_pool` plus `preset_weights` on ARKit-52 channels. One preset per entry, so at most 2 run at once. Weight sums: neutral 0, think 0.8, smile_soft 0.9, frown_soft 1.0 (all ≤ 1.2).
- **Reduced motion:**
  - **Allowed gestures:** 6 glyphs bind `gesture.nod.small` (`allowed: true`). The other 18 have `allowed: false` with no substitute, so a nod never stands in for an unrelated meaning. Each carries `non_motion_cue: "caption:<GLYPH> (<MEANING>)"`, an English observer caption per ATG LANGUAGE.
  - **Facial:** entries say `hold_only` and also carry the caption cue (see mismatch M2).

## REQUESTED_CLIP
None required for v0.1.0. Every binding uses existing `clips.csv` ids, all still TO_BE_AUTHORED there.
Advisory: `gesture.talk.idle` carries 10 of 24 glyphs, so gesture contrast is low. A richer gesture set could be requested in v0.2 after ATG owners confirm glyph → body-language binding is wanted.

## SPEC mismatches / notes for MOTION
- **M1:** The §2.2 `category` enum (`affect|body_language|gesture|viseme_hint`) has no slot for the glyph meaning. Workaround: category is set by layer, and the meaning goes verbatim in an extra `glyph_meaning` field. Please tolerate extra fields.
- **M2:** §7 allows a "single expression hold" under reduced motion, but `statemachine.json.reduced_motion.facial` says "static neutral". Under the baseline, the facial `hold_only` would be dropped, so the caption cue is the real fallback. MOTION should pick one rule.
- **M3:** The envelope carries one `layer_hint`, but a glyph binds two layers. That's why the combined form above exists. A `layer_hint` of absent or null should mean both.
- **M4:** Under reduced motion, 18/24 glyphs lose their gesture entirely (only the nod is allowed). Meaning survives only if the host renders `non_motion_cue`, so the host must support caption rendering.

## v0.1.1 (2026-10-17 PT) — MOTION decisions applied
- M1 accepted: category follows layer; `glyph_meaning` extra field accepted.
- M2 resolved (statemachine.json wins): L3_facial reduced_motion is now `allowed: false, fallback: static_neutral`; caption carries meaning.
- M3 accepted: empty `layer_hint` = play both layers.
- M4 accepted: caption rendering under reduced motion is a required host capability.
- Advisory logged for v0.2: wider gesture set (talk.idle covers 10 glyphs).
- Publishing: on hold pending Neuro approval. v0.1.0 file retained for history.

## Publishing target (v0.1.1)
- Repo file: `AGENTROPOLIS-ATG/atg/maps/motion_map.v0.1.1.json` on branch `feat/atg-motion-map-v0.1.1`, draft PR only (approved by Neuro 2026-10-17 PT). Supersedes the v0.1.0 references above.
