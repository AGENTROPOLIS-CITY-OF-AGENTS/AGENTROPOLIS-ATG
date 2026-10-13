# Gesture-to-Embodiment Integration Contract (proposal)

Status: design-only, not deployed. Owner: Hermes implementation; VERITY evidence review. No autonomous execution authority.

## Pipeline
Camera (opt-in) -> local hand landmark detector -> confidence/debounce -> CHAOS INPUT normalized gesture intent -> AIP adapter -> ATG/Atralith expression/command mapping -> policy/authorization gate -> Three.js spatial runtime -> animation clip playback -> receipt.

Mesh2Motion is an offline/browser authoring candidate for GLB/glTF rigged animation assets, not a runtime gesture recognizer, city engine, ATG interpreter or authorization system. Verify its license and compatibility before importing any dependency.

## Canonical gesture intents
- open_palm: stop UI navigation / cancel pending selection (never emergency-stop infrastructure without separately verified wiring)
- pinch: select object after dwell/confidence threshold
- two_hand_spread: zoom or expand panel
- point: highlight or target, not execute

## Event shape
```json
{"schema":"chaos.gesture.v1","gesture":"pinch","confidence":0.94,"target":"agent-demo-01","timestamp":"ISO-8601","source":"camera-local","mode":"preview","authorized":false}
```

## Acceptance gates
1. Accessible keyboard/mouse/touch fallback; camera opt-in and local processing by default.
2. Explicit calibration, anti-spoofing/rate limits, temporal smoothing, dwell, cancellation, and low-confidence rejection.
3. Gesture alone cannot authorize wallet actions, deployment, purchases, credentials or external side effects.
4. ATG semantics versioned separately from animation IDs; missing clip degrades to text/status.
5. Single sandbox demo: pinch-select GLB agent, agent turns/walks via imported clip, record intent and playback receipts.
6. Performance tests desktop/mobile/iPad; license/SBOM review; no camera frames retained by default.
7. VERITY verifies evidence, AEGIS gates remain architectural until proven deployed; do not claim production readiness.

## Rollout
Read-only inventory -> owner-specific implementation PRs -> demo evidence -> accessibility/security review -> explicit promotion decision. No direct-to-main or mass deployment.
